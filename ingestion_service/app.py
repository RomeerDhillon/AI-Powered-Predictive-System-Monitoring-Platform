"""
Real-time Metrics Ingestion Service

This service collects system metrics and publishes them to Kafka for processing.
It simulates various system metrics like CPU, memory, disk, and network usage.
"""

import asyncio
import json
import os
import time
import random
import psutil
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI
from kafka import KafkaProducer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: str
    hostname: str
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

class MetricsCollector:
    """Collects system metrics and publishes to Kafka"""
    
    def __init__(self):
        self.kafka_producer = None
        self.influx_client = None
        self.write_api = None
        self.hostname = os.getenv('HOSTNAME', 'monitoring-host')
        self.setup_kafka()
        self.setup_influxdb()
        
        # Network counters for delta calculation
        self.prev_network_sent = 0
        self.prev_network_recv = 0
        
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
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate network deltas
            network_sent = network.bytes_sent - self.prev_network_sent
            network_recv = network.bytes_recv - self.prev_network_recv
            self.prev_network_sent = network.bytes_sent
            self.prev_network_recv = network.bytes_recv
            
            # Simulate response time (in real scenario, this would be actual API response time)
            response_time = random.uniform(50, 200)  # 50-200ms
            
            # Simulate occasional anomalies
            if random.random() < 0.05:  # 5% chance of anomaly
                cpu_percent = min(100, cpu_percent * random.uniform(1.5, 3.0))
                response_time = random.uniform(500, 2000)  # High latency
            
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
                response_time=response_time
            )
        except Exception as e:
            print(f"❌ Error collecting metrics: {e}")
            return None
    
    def publish_to_kafka(self, metrics: SystemMetrics):
        """Publish metrics to Kafka topic"""
        try:
            if self.kafka_producer:
                topic = 'system_metrics'
                key = f"{metrics.hostname}_{int(time.time())}"
                value = asdict(metrics)
                
                self.kafka_producer.send(topic, key=key, value=value)
                self.kafka_producer.flush()
                print(f"📤 Published metrics to Kafka topic '{topic}'")
        except Exception as e:
            print(f"❌ Failed to publish to Kafka: {e}")
    
    def write_to_influxdb(self, metrics: SystemMetrics):
        """Write metrics to InfluxDB"""
        try:
            if self.write_api:
                point = Point("system_metrics") \
                    .tag("hostname", metrics.hostname) \
                    .field("cpu_percent", metrics.cpu_percent) \
                    .field("memory_percent", metrics.memory_percent) \
                    .field("memory_available", metrics.memory_available) \
                    .field("disk_usage_percent", metrics.disk_usage_percent) \
                    .field("disk_free", metrics.disk_free) \
                    .field("network_bytes_sent", metrics.network_bytes_sent) \
                    .field("network_bytes_recv", metrics.network_bytes_recv) \
                    .field("load_average", metrics.load_average) \
                    .field("process_count", metrics.process_count) \
                    .field("response_time", metrics.response_time) \
                    .time(datetime.utcnow())
                
                self.write_api.write(bucket=self.influx_bucket, record=point)
                print(f"📊 Wrote metrics to InfluxDB")
        except Exception as e:
            print(f"❌ Failed to write to InfluxDB: {e}")
    
    async def collect_and_publish(self):
        """Main collection loop"""
        print("🚀 Starting metrics collection...")
        
        while True:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                if metrics:
                    # Publish to Kafka
                    self.publish_to_kafka(metrics)
                    
                    # Write to InfluxDB
                    self.write_to_influxdb(metrics)
                    
                    print(f"📈 Collected metrics: CPU={metrics.cpu_percent:.1f}%, "
                          f"Memory={metrics.memory_percent:.1f}%, "
                          f"Response={metrics.response_time:.1f}ms")
                
                # Wait before next collection
                await asyncio.sleep(1)  # Collect every second
                
            except KeyboardInterrupt:
                print("🛑 Stopping metrics collection...")
                break
            except Exception as e:
                print(f"❌ Error in collection loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def close(self):
        """Clean up resources"""
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.influx_client:
            self.influx_client.close()

# FastAPI app for health checks and manual triggers
app = FastAPI(title="Metrics Ingestion Service", version="1.0.0")

collector = MetricsCollector()

@app.get("/")
async def root():
    return {"service": "metrics-ingestion", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "kafka_connected": collector.kafka_producer is not None,
        "influxdb_connected": collector.influx_client is not None
    }

@app.post("/collect")
async def manual_collect():
    """Manually trigger metrics collection"""
    metrics = collector.collect_metrics()
    if metrics:
        collector.publish_to_kafka(metrics)
        collector.write_to_influxdb(metrics)
        return {"status": "success", "metrics": asdict(metrics)}
    return {"status": "failed"}

async def main():
    """Main application entry point"""
    print("🔧 Metrics Ingestion Service Starting...")
    
    # Start the collection loop
    try:
        await collector.collect_and_publish()
    finally:
        collector.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        # Run as standalone collector
        asyncio.run(main())
