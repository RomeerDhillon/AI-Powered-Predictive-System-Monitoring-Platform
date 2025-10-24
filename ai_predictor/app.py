"""
AI Predictor Service for Anomaly Detection

This service consumes processed metrics and performs real-time anomaly detection
using Isolation Forest algorithm. It publishes predictions and alerts.
"""

import asyncio
import json
import os
import pickle
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from kafka import KafkaConsumer, KafkaProducer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class PredictionResult:
    """Anomaly prediction result"""
    timestamp: str
    hostname: str
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    features_used: List[str]
    prediction_metadata: Dict[str, Any]

class AIPredictor:
    """Real-time anomaly detection using Isolation Forest"""
    
    def __init__(self):
        self.kafka_consumer = None
        self.kafka_producer = None
        self.influx_client = None
        self.write_api = None
        self.postgres_conn = None
        
        # Model components
        self.isolation_forest = None
        self.scaler = None
        self.feature_columns = None
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.1'))
        
        # Model metadata
        self.model_version = "1.0.0"
        self.model_trained_at = None
        
        self.setup_connections()
        self.load_model()
    
    def setup_connections(self):
        """Initialize all external connections"""
        self.setup_kafka()
        self.setup_influxdb()
        self.setup_postgres()
    
    def setup_kafka(self):
        """Initialize Kafka consumer and producer"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
            # Consumer for processed metrics
            self.kafka_consumer = KafkaConsumer(
                'processed_metrics',
                bootstrap_servers=[bootstrap_servers],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='ai_predictor',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Producer for predictions
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=[bootstrap_servers],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                acks='all'
            )
            
            print(f"✅ Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
    
    def setup_influxdb(self):
        """Initialize InfluxDB client"""
        try:
            influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
            influx_token = os.getenv('INFLUXDB_TOKEN', 'admin-token')
            influx_org = os.getenv('INFLUXDB_ORG', 'my-org')
            influx_bucket = os.getenv('INFLUXDB_BUCKET', 'metrics')
            
            self.influx_client = InfluxDBClient(
                url=influx_url,
                token=influx_token,
                org=influx_org
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            self.influx_bucket = influx_bucket
            print(f"✅ Connected to InfluxDB at {influx_url}")
        except Exception as e:
            print(f"❌ Failed to connect to InfluxDB: {e}")
    
    def setup_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            postgres_url = os.getenv('POSTGRES_URL', 'postgresql://admin:admin123@localhost:5432/monitoring')
            self.postgres_conn = psycopg2.connect(postgres_url)
            print(f"✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
    
    def load_model(self):
        """Load the trained model from disk"""
        try:
            model_path = os.path.join('/app/models', 'isolation_forest_model.pkl')
            scaler_path = os.path.join('/app/models', 'scaler.pkl')
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                with open(model_path, 'rb') as f:
                    self.isolation_forest = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                # Load feature columns
                self.feature_columns = [
                    'cpu_percent', 'memory_percent', 'response_time',
                    'cpu_rolling_mean', 'cpu_rolling_std', 'cpu_trend',
                    'memory_trend', 'response_time_trend', 'network_throughput',
                    'system_load_score'
                ]
                
                print(f"✅ Loaded model version {self.model_version}")
            else:
                print("⚠️ No trained model found, creating default model...")
                self.create_default_model()
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.create_default_model()
    
    def create_default_model(self):
        """Create a default model for initial operation"""
        try:
            # Create a simple Isolation Forest model
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.scaler = StandardScaler()
            
            # Create dummy training data
            dummy_data = np.random.normal(0, 1, (100, 10))
            self.scaler.fit(dummy_data)
            self.isolation_forest.fit(dummy_data)
            
            self.feature_columns = [
                'cpu_percent', 'memory_percent', 'response_time',
                'cpu_rolling_mean', 'cpu_rolling_std', 'cpu_trend',
                'memory_trend', 'response_time_trend', 'network_throughput',
                'system_load_score'
            ]
            
            print("✅ Created default model")
        except Exception as e:
            print(f"❌ Failed to create default model: {e}")
    
    def extract_features(self, metrics: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract features for prediction"""
        try:
            features = []
            for col in self.feature_columns:
                if col in metrics:
                    features.append(metrics[col])
                else:
                    # Use default value if feature is missing
                    features.append(0.0)
            
            return np.array(features).reshape(1, -1)
        except Exception as e:
            print(f"❌ Error extracting features: {e}")
            return None
    
    def predict_anomaly(self, metrics: Dict[str, Any]) -> Optional[PredictionResult]:
        """Predict if the metrics represent an anomaly"""
        try:
            if not self.isolation_forest or not self.scaler:
                print("❌ Model not loaded")
                return None
            
            # Extract features
            features = self.extract_features(metrics)
            if features is None:
                return None
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict anomaly
            anomaly_prediction = self.isolation_forest.predict(features_scaled)[0]
            anomaly_score = self.isolation_forest.score_samples(features_scaled)[0]
            
            # Convert to boolean (IsolationForest returns -1 for anomalies)
            is_anomaly = anomaly_prediction == -1
            
            # Calculate confidence based on score
            confidence = abs(anomaly_score)
            
            # Create prediction result
            result = PredictionResult(
                timestamp=metrics['timestamp'],
                hostname=metrics['hostname'],
                is_anomaly=is_anomaly,
                anomaly_score=float(anomaly_score),
                confidence=float(confidence),
                features_used=self.feature_columns,
                prediction_metadata={
                    'model_version': self.model_version,
                    'threshold': self.anomaly_threshold,
                    'features_count': len(self.feature_columns)
                }
            )
            
            return result
        except Exception as e:
            print(f"❌ Error predicting anomaly: {e}")
            return None
    
    def publish_prediction(self, prediction: PredictionResult):
        """Publish prediction to Kafka"""
        try:
            if self.kafka_producer:
                topic = 'anomaly_predictions'
                key = f"{prediction.hostname}_{int(time.time())}"
                value = asdict(prediction)
                
                self.kafka_producer.send(topic, key=key, value=value)
                self.kafka_producer.flush()
                print(f"📤 Published prediction to Kafka topic '{topic}'")
        except Exception as e:
            print(f"❌ Failed to publish prediction: {e}")
    
    def write_to_influxdb(self, prediction: PredictionResult):
        """Write prediction to InfluxDB"""
        try:
            if self.write_api:
                point = Point("anomaly_predictions") \
                    .tag("hostname", prediction.hostname) \
                    .tag("is_anomaly", str(prediction.is_anomaly)) \
                    .field("anomaly_score", prediction.anomaly_score) \
                    .field("confidence", prediction.confidence) \
                    .field("model_version", prediction.prediction_metadata.get('model_version', 'unknown')) \
                    .time(datetime.utcnow())
                
                self.write_api.write(bucket=self.influx_bucket, record=point)
                print(f"📊 Wrote prediction to InfluxDB")
        except Exception as e:
            print(f"❌ Failed to write to InfluxDB: {e}")
    
    def store_prediction_in_db(self, prediction: PredictionResult):
        """Store prediction in PostgreSQL"""
        try:
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                
                query = """
                INSERT INTO anomaly_predictions 
                (timestamp, hostname, is_anomaly, anomaly_score, confidence, model_version, features_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    prediction.timestamp,
                    prediction.hostname,
                    prediction.is_anomaly,
                    prediction.anomaly_score,
                    prediction.confidence,
                    prediction.prediction_metadata.get('model_version'),
                    json.dumps(prediction.features_used)
                ))
                
                self.postgres_conn.commit()
                cursor.close()
                print(f"💾 Stored prediction in PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to store prediction in DB: {e}")
    
    async def process_predictions(self):
        """Main prediction processing loop"""
        print("🚀 Starting AI prediction processing...")
        
        try:
            for message in self.kafka_consumer:
                try:
                    processed_metrics = message.value
                    hostname = processed_metrics.get('hostname', 'unknown')
                    print(f"📥 Received processed metrics from {hostname}")
                    
                    # Predict anomaly
                    prediction = self.predict_anomaly(processed_metrics)
                    if prediction:
                        # Publish prediction
                        self.publish_prediction(prediction)
                        
                        # Write to InfluxDB
                        self.write_to_influxdb(prediction)
                        
                        # Store in PostgreSQL
                        self.store_prediction_in_db(prediction)
                        
                        status = "🚨 ANOMALY" if prediction.is_anomaly else "✅ Normal"
                        print(f"🔮 Prediction: {status} - "
                              f"Score: {prediction.anomaly_score:.3f}, "
                              f"Confidence: {prediction.confidence:.3f}")
                
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print("🛑 Stopping AI prediction processing...")
        except Exception as e:
            print(f"❌ Error in prediction loop: {e}")
    
    def close(self):
        """Clean up resources"""
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.influx_client:
            self.influx_client.close()
        if self.postgres_conn:
            self.postgres_conn.close()

async def main():
    """Main application entry point"""
    print("🔧 AI Predictor Service Starting...")
    
    predictor = AIPredictor()
    
    try:
        await predictor.process_predictions()
    finally:
        predictor.close()

if __name__ == "__main__":
    asyncio.run(main())
