"""
Alert Service for Anomaly Notifications

This service consumes anomaly predictions and sends alerts via multiple channels
(Slack, Email, Console) when anomalies are detected.
"""

import asyncio
import json
import os
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from kafka import KafkaConsumer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Alert:
    """Alert data structure"""
    timestamp: str
    hostname: str
    alert_type: str
    severity: str
    message: str
    anomaly_score: float
    confidence: float
    channels_sent: List[str]
    metadata: Dict[str, Any]

class AlertService:
    """Handles alerting for anomaly detection"""
    
    def __init__(self):
        self.kafka_consumer = None
        self.postgres_conn = None
        
        # Alert configuration
        self.alert_threshold = float(os.getenv('ALERT_THRESHOLD', '0.5'))
        self.alert_cooldown = int(os.getenv('ALERT_COOLDOWN', '300'))  # 5 minutes
        
        # Channel configurations
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.email_config = {
            'smtp_host': os.getenv('EMAIL_SMTP_HOST'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('EMAIL_FROM', 'alerts@monitoring.com'),
            'to_emails': os.getenv('EMAIL_TO', '').split(',')
        }
        
        # Track recent alerts to avoid spam
        self.recent_alerts = {}
        
        self.setup_connections()
    
    def setup_connections(self):
        """Initialize all external connections"""
        self.setup_kafka()
        self.setup_postgres()
    
    def setup_kafka(self):
        """Initialize Kafka consumer"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
            self.kafka_consumer = KafkaConsumer(
                'anomaly_predictions',
                bootstrap_servers=[bootstrap_servers],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='alert_service',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            print(f"✅ Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
    
    def setup_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            postgres_url = os.getenv('POSTGRES_URL', 'postgresql://admin:admin123@localhost:5432/monitoring')
            self.postgres_conn = psycopg2.connect(postgres_url)
            print(f"✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
    
    def should_send_alert(self, hostname: str, anomaly_score: float) -> bool:
        """Check if alert should be sent based on cooldown and threshold"""
        current_time = time.time()
        
        # Check threshold
        if anomaly_score < self.alert_threshold:
            return False
        
        # Check cooldown
        if hostname in self.recent_alerts:
            last_alert_time = self.recent_alerts[hostname]
            if current_time - last_alert_time < self.alert_cooldown:
                return False
        
        # Update last alert time
        self.recent_alerts[hostname] = current_time
        return True
    
    def get_recommended_actions(self, prediction: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on prediction"""
        actions = []
        anomaly_score = prediction.get('anomaly_score', 0.0)
        feature_importance = prediction.get('feature_importance', {})
        
        # CPU-related actions
        if feature_importance.get('cpu_percent', 0) > 0.3:
            if anomaly_score > 0.7:
                actions.append("Scale up CPU resources immediately")
                actions.append("Check for runaway processes")
            else:
                actions.append("Monitor CPU usage trends")
                actions.append("Consider horizontal scaling")
        
        # Memory-related actions
        if feature_importance.get('memory_percent', 0) > 0.3:
            if anomaly_score > 0.7:
                actions.append("Check for memory leaks")
                actions.append("Restart affected services")
                actions.append("Increase memory allocation")
            else:
                actions.append("Monitor memory usage patterns")
                actions.append("Review garbage collection settings")
        
        # Response time actions
        if feature_importance.get('response_time', 0) > 0.3:
            if anomaly_score > 0.7:
                actions.append("Check database query performance")
                actions.append("Review network connectivity")
                actions.append("Scale application instances")
            else:
                actions.append("Monitor response time trends")
                actions.append("Review caching strategies")
        
        # Network-related actions
        if feature_importance.get('network_throughput', 0) > 0.3:
            actions.append("Check network bandwidth utilization")
            actions.append("Review network configuration")
        
        # System load actions
        if feature_importance.get('system_load_score', 0) > 0.3:
            actions.append("Review system resource allocation")
            actions.append("Check for resource contention")
        
        # Failure prediction actions
        predicted_failure_time = prediction.get('predicted_failure_time')
        if predicted_failure_time:
            time_to_failure = prediction.get('time_to_failure_hours', 0)
            if time_to_failure < 2:
                actions.append("URGENT: Implement immediate mitigation")
                actions.append("Prepare rollback procedures")
            elif time_to_failure < 24:
                actions.append("Schedule maintenance window")
                actions.append("Prepare scaling resources")
            else:
                actions.append("Plan capacity increase")
                actions.append("Monitor trends closely")
        
        # General actions based on severity
        if anomaly_score > 0.8:
            actions.append("Escalate to on-call engineer")
            actions.append("Prepare incident response")
        elif anomaly_score > 0.6:
            actions.append("Increase monitoring frequency")
            actions.append("Prepare mitigation plans")
        else:
            actions.append("Continue monitoring")
            actions.append("Document patterns for future reference")
        
        return actions[:5]  # Limit to top 5 actions
    
    def create_alert(self, prediction: Dict[str, Any]) -> Alert:
        """Create alert from prediction with recommended actions"""
        hostname = prediction['hostname']
        anomaly_score = prediction['anomaly_score']
        confidence = prediction['confidence']
        
        # Determine severity
        if anomaly_score > 0.8:
            severity = "CRITICAL"
        elif anomaly_score > 0.6:
            severity = "HIGH"
        elif anomaly_score > 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        # Generate recommended actions based on prediction
        recommended_actions = self.get_recommended_actions(prediction)
        
        # Create enhanced alert message
        message = f"🚨 Anomaly detected on {hostname}\n" \
                 f"Severity: {severity}\n" \
                 f"Anomaly Score: {anomaly_score:.3f}\n" \
                 f"Confidence: {confidence:.3f}\n" \
                 f"Timestamp: {prediction['timestamp']}\n" \
                 f"Explanation: {prediction.get('explanation', 'No explanation available')}\n" \
                 f"Recommended Actions:\n" + "\n".join([f"• {action}" for action in recommended_actions])
        
        return Alert(
            timestamp=prediction['timestamp'],
            hostname=hostname,
            alert_type="anomaly_detection",
            severity=severity,
            message=message,
            anomaly_score=anomaly_score,
            confidence=confidence,
            channels_sent=[],
            metadata={
                'model_version': prediction.get('prediction_metadata', {}).get('model_version', 'unknown'),
                'features_used': prediction.get('features_used', []),
                'recommended_actions': recommended_actions,
                'explanation': prediction.get('explanation', ''),
                'predicted_failure_time': prediction.get('predicted_failure_time'),
                'time_to_failure_hours': prediction.get('time_to_failure_hours')
            }
        )
    
    def send_slack_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            if not self.slack_webhook:
                print("⚠️ Slack webhook not configured")
                return False
            
            # Create Slack message
            slack_message = {
                "text": f"🚨 Monitoring Alert",
                "attachments": [
                    {
                        "color": "danger" if alert.severity in ["CRITICAL", "HIGH"] else "warning",
                        "fields": [
                            {"title": "Hostname", "value": alert.hostname, "short": True},
                            {"title": "Severity", "value": alert.severity, "short": True},
                            {"title": "Anomaly Score", "value": f"{alert.anomaly_score:.3f}", "short": True},
                            {"title": "Confidence", "value": f"{alert.confidence:.3f}", "short": True},
                            {"title": "Timestamp", "value": alert.timestamp, "short": False}
                        ]
                    }
                ]
            }
            
            response = requests.post(self.slack_webhook, json=slack_message, timeout=10)
            response.raise_for_status()
            
            print(f"📱 Sent Slack alert for {alert.hostname}")
            return True
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False
    
    def send_email_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            if not all([self.email_config['smtp_host'], self.email_config['username'], 
                       self.email_config['password'], self.email_config['to_emails']]):
                print("⚠️ Email configuration incomplete")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            msg['Subject'] = f"🚨 Monitoring Alert - {alert.hostname} - {alert.severity}"
            
            # Email body
            body = f"""
Monitoring Alert

Hostname: {alert.hostname}
Severity: {alert.severity}
Anomaly Score: {alert.anomaly_score:.3f}
Confidence: {alert.confidence:.3f}
Timestamp: {alert.timestamp}

Message:
{alert.message}

This is an automated alert from the monitoring system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_host'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Sent email alert for {alert.hostname}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def send_console_alert(self, alert: Alert) -> bool:
        """Send alert to console (always succeeds)"""
        try:
            print(f"\n{'='*60}")
            print(f"🚨 ALERT: {alert.severity} - {alert.hostname}")
            print(f"{'='*60}")
            print(f"Timestamp: {alert.timestamp}")
            print(f"Anomaly Score: {alert.anomaly_score:.3f}")
            print(f"Confidence: {alert.confidence:.3f}")
            print(f"Message: {alert.message}")
            print(f"{'='*60}\n")
            return True
        except Exception as e:
            print(f"❌ Failed to send console alert: {e}")
            return False
    
    def send_alert(self, alert: Alert) -> Alert:
        """Send alert through all configured channels"""
        channels_sent = []
        
        # Always send to console
        if self.send_console_alert(alert):
            channels_sent.append("console")
        
        # Send to Slack
        if self.send_slack_alert(alert):
            channels_sent.append("slack")
        
        # Send to Email
        if self.send_email_alert(alert):
            channels_sent.append("email")
        
        alert.channels_sent = channels_sent
        return alert
    
    def store_alert_in_db(self, alert: Alert):
        """Store alert in PostgreSQL"""
        try:
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                
                query = """
                INSERT INTO alerts 
                (timestamp, hostname, alert_type, severity, message, anomaly_score, 
                 confidence, channels_sent, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    alert.timestamp,
                    alert.hostname,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    alert.anomaly_score,
                    alert.confidence,
                    json.dumps(alert.channels_sent),
                    json.dumps(alert.metadata)
                ))
                
                self.postgres_conn.commit()
                cursor.close()
                print(f"💾 Stored alert in PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to store alert in DB: {e}")
    
    async def process_alerts(self):
        """Main alert processing loop"""
        print("🚀 Starting alert processing...")
        
        try:
            for message in self.kafka_consumer:
                try:
                    prediction = message.value
                    hostname = prediction.get('hostname', 'unknown')
                    anomaly_score = prediction.get('anomaly_score', 0.0)
                    
                    print(f"📥 Received prediction from {hostname} (score: {anomaly_score:.3f})")
                    
                    # Check if alert should be sent
                    if self.should_send_alert(hostname, anomaly_score):
                        # Create and send alert
                        alert = self.create_alert(prediction)
                        alert = self.send_alert(alert)
                        
                        # Store alert in database
                        self.store_alert_in_db(alert)
                        
                        print(f"🚨 Alert sent for {hostname} via {', '.join(alert.channels_sent)}")
                    else:
                        print(f"⏭️ Skipping alert for {hostname} (cooldown or low score)")
                
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print("🛑 Stopping alert processing...")
        except Exception as e:
            print(f"❌ Error in alert loop: {e}")
    
    def close(self):
        """Clean up resources"""
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.postgres_conn:
            self.postgres_conn.close()

async def main():
    """Main application entry point"""
    print("🔧 Alert Service Starting...")
    
    alert_service = AlertService()
    
    try:
        await alert_service.process_alerts()
    finally:
        alert_service.close()

if __name__ == "__main__":
    asyncio.run(main())
