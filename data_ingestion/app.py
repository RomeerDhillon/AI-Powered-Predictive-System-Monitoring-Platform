"""
Advanced Data Ingestion Service

This service collects and processes multiple types of telemetry data:
- System metrics (CPU, memory, disk, network)
- Application logs (structured and unstructured)
- Distributed traces
- User activity and behavior metrics
- Custom business metrics
"""

import asyncio
import json
import os
import time
import random
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class SystemMetrics:
    """Enhanced system metrics with additional telemetry"""
    timestamp: str
    hostname: str
    
    # Core system metrics
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    disk_free: int
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: float
    process_count: int
    response_time: float
    
    # Enhanced metrics
    cpu_cores: int
    memory_total: int
    disk_total: int
    network_connections: int
    open_files: int
    context_switches: int
    interrupts: int

@dataclass
class ApplicationLog:
    """Structured application log entry"""
    timestamp: str
    level: str
    service: str
    hostname: str
    message: str
    trace_id: Optional[str]
    span_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class UserActivity:
    """User behavior and activity metrics"""
    timestamp: str
    user_id: str
    session_id: str
    action: str
    endpoint: str
    response_time: float
    status_code: int
    user_agent: str
    ip_address: str
    metadata: Dict[str, Any]

@dataclass
class BusinessMetric:
    """Custom business metrics"""
    timestamp: str
    metric_name: str
    metric_value: float
    metric_type: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]

class AdvancedDataIngestion:
    """Advanced data ingestion service"""
    
    def __init__(self):
        self.kafka_producer = None
        self.influx_client = None
        self.write_api = None
        self.hostname = os.getenv('HOSTNAME', 'monitoring-host')
        
        # Network counters for delta calculation
        self.prev_network_sent = 0
        self.prev_network_recv = 0
        self.prev_context_switches = 0
        self.prev_interrupts = 0
        
        # User activity simulation
        self.user_sessions = {}
        self.endpoints = [
            '/api/users', '/api/orders', '/api/products', '/api/payments',
            '/api/auth', '/api/search', '/api/recommendations'
        ]
        self.actions = [
            'login', 'logout', 'view_product', 'add_to_cart', 'checkout',
            'search', 'filter', 'sort', 'paginate', 'api_call'
        ]
        
        self.setup_kafka()
        self.setup_influxdb()
        self.setup_logging()
    
    def setup_kafka(self):
        """Initialize Kafka producer"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
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
    
    def setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_enhanced_metrics(self) -> SystemMetrics:
        """Collect enhanced system metrics"""
        try:
            # Get basic system information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate network deltas
            network_sent = network.bytes_sent - self.prev_network_sent
            network_recv = network.bytes_recv - self.prev_network_recv
            self.prev_network_sent = network.bytes_sent
            self.prev_network_recv = network.bytes_recv
            
            # Get additional metrics
            cpu_cores = psutil.cpu_count()
            memory_total = memory.total
            disk_total = disk.total
            network_connections = len(psutil.net_connections())
            open_files = len(psutil.Process().open_files()) if hasattr(psutil.Process(), 'open_files') else 0
            
            # Get system stats
            cpu_stats = psutil.cpu_stats()
            context_switches = cpu_stats.ctx_switches - self.prev_context_switches
            interrupts = cpu_stats.interrupts - self.prev_interrupts
            self.prev_context_switches = cpu_stats.ctx_switches
            self.prev_interrupts = cpu_stats.interrupts
            
            # Simulate response time
            response_time = random.uniform(50, 200)
            
            # Simulate occasional anomalies
            if random.random() < 0.05:  # 5% chance of anomaly
                cpu_percent = min(100, cpu_percent * random.uniform(1.5, 3.0))
                response_time = random.uniform(500, 2000)
            
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                hostname=self.hostname,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_usage_percent=disk.percent,
                disk_free=disk.free,
                network_bytes_sent=network_sent,
                network_bytes_recv=network_recv,
                load_average=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
                process_count=len(psutil.pids()),
                response_time=response_time,
                cpu_cores=cpu_cores,
                memory_total=memory_total,
                disk_total=disk_total,
                network_connections=network_connections,
                open_files=open_files,
                context_switches=context_switches,
                interrupts=interrupts
            )
        except Exception as e:
            print(f"❌ Error collecting metrics: {e}")
            return None
    
    def generate_application_log(self) -> ApplicationLog:
        """Generate realistic application log entry"""
        try:
            levels = [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
            level = random.choice(levels)
            
            # Generate realistic log messages
            messages = {
                LogLevel.INFO: [
                    "User authentication successful",
                    "Database connection established",
                    "Cache hit for key: user_123",
                    "API request processed successfully",
                    "Background job completed"
                ],
                LogLevel.WARNING: [
                    "High memory usage detected",
                    "Database connection pool 80% full",
                    "Slow query detected: 2.5s execution time",
                    "Rate limit approaching for user 456",
                    "Disk space 85% utilized"
                ],
                LogLevel.ERROR: [
                    "Database connection failed",
                    "Authentication token expired",
                    "External API timeout after 30s",
                    "Memory allocation failed",
                    "File system error: permission denied"
                ]
            }
            
            message = random.choice(messages[level])
            
            return ApplicationLog(
                timestamp=datetime.utcnow().isoformat(),
                level=level.value,
                service=random.choice(['api-gateway', 'user-service', 'order-service', 'payment-service']),
                hostname=self.hostname,
                message=message,
                trace_id=f"trace_{random.randint(100000, 999999)}" if random.random() < 0.7 else None,
                span_id=f"span_{random.randint(10000, 99999)}" if random.random() < 0.7 else None,
                user_id=f"user_{random.randint(1000, 9999)}" if random.random() < 0.8 else None,
                session_id=f"session_{random.randint(100000, 999999)}" if random.random() < 0.6 else None,
                metadata={
                    'request_id': f"req_{random.randint(1000000, 9999999)}",
                    'duration_ms': random.randint(10, 1000),
                    'status_code': random.choice([200, 201, 400, 401, 404, 500])
                }
            )
        except Exception as e:
            print(f"❌ Error generating log: {e}")
            return None
    
    def generate_user_activity(self) -> UserActivity:
        """Generate realistic user activity"""
        try:
            user_id = f"user_{random.randint(1000, 9999)}"
            session_id = f"session_{random.randint(100000, 999999)}"
            action = random.choice(self.actions)
            endpoint = random.choice(self.endpoints)
            
            # Simulate realistic response times
            response_time = random.uniform(50, 500)
            if action in ['checkout', 'payment']:
                response_time = random.uniform(200, 1000)
            
            # Simulate error rates
            status_code = 200
            if random.random() < 0.05:  # 5% error rate
                status_code = random.choice([400, 401, 404, 500])
                response_time = random.uniform(100, 2000)
            
            return UserActivity(
                timestamp=datetime.utcnow().isoformat(),
                user_id=user_id,
                session_id=session_id,
                action=action,
                endpoint=endpoint,
                response_time=response_time,
                status_code=status_code,
                user_agent=random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ]),
                ip_address=f"192.168.1.{random.randint(1, 254)}",
                metadata={
                    'referrer': random.choice(['google.com', 'facebook.com', 'direct', 'email']),
                    'device_type': random.choice(['desktop', 'mobile', 'tablet']),
                    'location': random.choice(['US', 'EU', 'APAC'])
                }
            )
        except Exception as e:
            print(f"❌ Error generating user activity: {e}")
            return None
    
    def generate_business_metric(self) -> BusinessMetric:
        """Generate custom business metrics"""
        try:
            metric_names = [
                'orders_per_minute', 'revenue_per_hour', 'user_registrations',
                'cart_abandonment_rate', 'conversion_rate', 'customer_satisfaction',
                'api_calls_per_second', 'error_rate', 'uptime_percentage'
            ]
            
            metric_name = random.choice(metric_names)
            metric_type = random.choice([MetricType.COUNTER, MetricType.GAUGE, MetricType.HISTOGRAM])
            
            # Generate realistic values based on metric type
            if metric_name == 'orders_per_minute':
                value = random.randint(5, 50)
            elif metric_name == 'revenue_per_hour':
                value = random.uniform(1000, 10000)
            elif metric_name == 'conversion_rate':
                value = random.uniform(0.02, 0.15)
            elif metric_name == 'error_rate':
                value = random.uniform(0.001, 0.05)
            else:
                value = random.uniform(0, 100)
            
            return BusinessMetric(
                timestamp=datetime.utcnow().isoformat(),
                metric_name=metric_name,
                metric_value=value,
                metric_type=metric_type.value,
                tags={
                    'environment': random.choice(['production', 'staging', 'development']),
                    'region': random.choice(['us-east', 'us-west', 'eu-central', 'ap-southeast']),
                    'service': random.choice(['api', 'web', 'mobile', 'admin'])
                },
                metadata={
                    'source': 'business_analytics',
                    'version': '1.0.0'
                }
            )
        except Exception as e:
            print(f"❌ Error generating business metric: {e}")
            return None
    
    def publish_to_kafka(self, data: Any, topic: str):
        """Publish data to Kafka topic"""
        try:
            if self.kafka_producer:
                key = f"{self.hostname}_{int(time.time())}"
                value = asdict(data) if hasattr(data, '__dataclass_fields__') else data
                
                self.kafka_producer.send(topic, key=key, value=value)
                self.kafka_producer.flush()
                print(f"📤 Published to Kafka topic '{topic}'")
        except Exception as e:
            print(f"❌ Failed to publish to Kafka: {e}")
    
    def write_to_influxdb(self, data: Any, measurement: str):
        """Write data to InfluxDB"""
        try:
            if self.write_api:
                point = Point(measurement)
                
                # Add tags and fields based on data type
                if hasattr(data, '__dataclass_fields__'):
                    for field_name, field_value in asdict(data).items():
                        if field_name == 'timestamp':
                            continue
                        elif isinstance(field_value, str) and field_name in ['hostname', 'level', 'service', 'user_id']:
                            point = point.tag(field_name, field_value)
                        else:
                            point = point.field(field_name, field_value)
                
                point = point.time(datetime.utcnow())
                self.write_api.write(bucket=self.influx_bucket, record=point)
                print(f"📊 Wrote {measurement} to InfluxDB")
        except Exception as e:
            print(f"❌ Failed to write to InfluxDB: {e}")
    
    async def collect_and_publish(self):
        """Main collection loop"""
        print("🚀 Starting advanced data ingestion...")
        
        while True:
            try:
                # Collect system metrics
                metrics = self.collect_enhanced_metrics()
                if metrics:
                    self.publish_to_kafka(metrics, 'system_metrics')
                    self.write_to_influxdb(metrics, 'system_metrics')
                    print(f"📈 System metrics: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_percent:.1f}%")
                
                # Generate application logs (every 5 seconds)
                if int(time.time()) % 5 == 0:
                    log_entry = self.generate_application_log()
                    if log_entry:
                        self.publish_to_kafka(log_entry, 'application_logs')
                        self.write_to_influxdb(log_entry, 'application_logs')
                        print(f"📝 Log: {log_entry.level} - {log_entry.message[:50]}...")
                
                # Generate user activity (every 3 seconds)
                if int(time.time()) % 3 == 0:
                    user_activity = self.generate_user_activity()
                    if user_activity:
                        self.publish_to_kafka(user_activity, 'user_activity')
                        self.write_to_influxdb(user_activity, 'user_activity')
                        print(f"👤 User activity: {user_activity.action} on {user_activity.endpoint}")
                
                # Generate business metrics (every 10 seconds)
                if int(time.time()) % 10 == 0:
                    business_metric = self.generate_business_metric()
                    if business_metric:
                        self.publish_to_kafka(business_metric, 'business_metrics')
                        self.write_to_influxdb(business_metric, 'business_metrics')
                        print(f"📊 Business metric: {business_metric.metric_name}={business_metric.metric_value:.2f}")
                
                # Wait before next collection
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("🛑 Stopping data ingestion...")
                break
            except Exception as e:
                print(f"❌ Error in collection loop: {e}")
                await asyncio.sleep(5)
    
    def close(self):
        """Clean up resources"""
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.influx_client:
            self.influx_client.close()

# FastAPI app for health checks and manual triggers
app = FastAPI(title="Advanced Data Ingestion Service", version="2.0.0")

ingestion = AdvancedDataIngestion()

@app.get("/")
async def root():
    return {"service": "advanced-data-ingestion", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "kafka_connected": ingestion.kafka_producer is not None,
        "influxdb_connected": ingestion.influx_client is not None
    }

@app.post("/collect/metrics")
async def manual_collect_metrics():
    """Manually trigger metrics collection"""
    metrics = ingestion.collect_enhanced_metrics()
    if metrics:
        ingestion.publish_to_kafka(metrics, 'system_metrics')
        ingestion.write_to_influxdb(metrics, 'system_metrics')
        return {"status": "success", "metrics": asdict(metrics)}
    return {"status": "failed"}

@app.post("/collect/logs")
async def manual_collect_logs():
    """Manually trigger log generation"""
    log_entry = ingestion.generate_application_log()
    if log_entry:
        ingestion.publish_to_kafka(log_entry, 'application_logs')
        ingestion.write_to_influxdb(log_entry, 'application_logs')
        return {"status": "success", "log": asdict(log_entry)}
    return {"status": "failed"}

@app.post("/collect/user-activity")
async def manual_collect_user_activity():
    """Manually trigger user activity generation"""
    user_activity = ingestion.generate_user_activity()
    if user_activity:
        ingestion.publish_to_kafka(user_activity, 'user_activity')
        ingestion.write_to_influxdb(user_activity, 'user_activity')
        return {"status": "success", "activity": asdict(user_activity)}
    return {"status": "failed"}

async def main():
    """Main application entry point"""
    print("🔧 Advanced Data Ingestion Service Starting...")
    
    try:
        await ingestion.collect_and_publish()
    finally:
        ingestion.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8002)
    else:
        # Run both collector and server
        import threading
        
        # Start the collector in a separate thread
        collector_thread = threading.Thread(target=lambda: asyncio.run(main()))
        collector_thread.daemon = True
        collector_thread.start()
        
        # Start the FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8002)
