"""
Stream Processor for Real-time Feature Computation

This service consumes metrics from Kafka, computes rolling features,
and publishes enhanced metrics for AI prediction.
"""

import asyncio
import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ProcessedMetrics:
    """Enhanced metrics with computed features"""
    timestamp: str
    hostname: str
    
    # Original metrics
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
    
    # Computed features
    cpu_rolling_mean: float
    cpu_rolling_std: float
    cpu_trend: float
    memory_trend: float
    response_time_trend: float
    network_throughput: float
    system_load_score: float
    anomaly_score: float

class StreamProcessor:
    """Processes metrics streams and computes features"""
    
    def __init__(self):
        self.kafka_consumer = None
        self.kafka_producer = None
        self.influx_client = None
        self.write_api = None
        
        # Rolling windows for each hostname
        self.metrics_windows = defaultdict(lambda: {
            'cpu': deque(maxlen=60),  # 60 seconds window
            'memory': deque(maxlen=60),
            'response_time': deque(maxlen=60),
            'network_sent': deque(maxlen=60),
            'network_recv': deque(maxlen=60),
            'timestamps': deque(maxlen=60)
        })
        
        self.setup_kafka()
        self.setup_influxdb()
    
    def setup_kafka(self):
        """Initialize Kafka consumer and producer"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
            # Consumer for raw metrics
            self.kafka_consumer = KafkaConsumer(
                'system_metrics',
                bootstrap_servers=[bootstrap_servers],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='stream_processor',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Producer for processed metrics
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
    
    def compute_rolling_features(self, hostname: str, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Compute rolling features for the given metrics"""
        window = self.metrics_windows[hostname]
        
        # Add current metrics to window
        window['cpu'].append(metrics['cpu_percent'])
        window['memory'].append(metrics['memory_percent'])
        window['response_time'].append(metrics['response_time'])
        window['network_sent'].append(metrics['network_bytes_sent'])
        window['network_recv'].append(metrics['network_bytes_recv'])
        window['timestamps'].append(datetime.utcnow())
        
        features = {}
        
        if len(window['cpu']) >= 5:  # Need at least 5 points for meaningful features
            # CPU features
            cpu_values = np.array(window['cpu'])
            features['cpu_rolling_mean'] = float(np.mean(cpu_values))
            features['cpu_rolling_std'] = float(np.std(cpu_values))
            features['cpu_trend'] = float(np.polyfit(range(len(cpu_values)), cpu_values, 1)[0])
            
            # Memory features
            memory_values = np.array(window['memory'])
            features['memory_trend'] = float(np.polyfit(range(len(memory_values)), memory_values, 1)[0])
            
            # Response time features
            response_values = np.array(window['response_time'])
            features['response_time_trend'] = float(np.polyfit(range(len(response_values)), response_values, 1)[0])
            
            # Network throughput (bytes per second)
            if len(window['network_sent']) >= 2:
                sent_delta = window['network_sent'][-1] - window['network_sent'][-2]
                recv_delta = window['network_recv'][-1] - window['network_recv'][-2]
                features['network_throughput'] = float(sent_delta + recv_delta)
            else:
                features['network_throughput'] = 0.0
            
            # System load score (combination of CPU, memory, and response time)
            cpu_score = min(1.0, cpu_values[-1] / 100.0)
            memory_score = min(1.0, memory_values[-1] / 100.0)
            response_score = min(1.0, response_values[-1] / 1000.0)  # Normalize to 1 second
            features['system_load_score'] = float((cpu_score + memory_score + response_score) / 3.0)
            
            # Simple anomaly score based on deviation from rolling mean
            cpu_deviation = abs(cpu_values[-1] - features['cpu_rolling_mean']) / max(features['cpu_rolling_std'], 0.1)
            memory_deviation = abs(memory_values[-1] - np.mean(memory_values)) / max(np.std(memory_values), 0.1)
            response_deviation = abs(response_values[-1] - np.mean(response_values)) / max(np.std(response_values), 0.1)
            features['anomaly_score'] = float((cpu_deviation + memory_deviation + response_deviation) / 3.0)
        else:
            # Default values for insufficient data
            features = {
                'cpu_rolling_mean': metrics['cpu_percent'],
                'cpu_rolling_std': 0.0,
                'cpu_trend': 0.0,
                'memory_trend': 0.0,
                'response_time_trend': 0.0,
                'network_throughput': 0.0,
                'system_load_score': 0.0,
                'anomaly_score': 0.0
            }
        
        return features
    
    def process_metrics(self, raw_metrics: Dict[str, Any]) -> Optional[ProcessedMetrics]:
        """Process raw metrics and compute features"""
        try:
            hostname = raw_metrics['hostname']
            features = self.compute_rolling_features(hostname, raw_metrics)
            
            # Create processed metrics
            processed = ProcessedMetrics(
                timestamp=raw_metrics['timestamp'],
                hostname=hostname,
                cpu_percent=raw_metrics['cpu_percent'],
                memory_percent=raw_metrics['memory_percent'],
                memory_available=raw_metrics['memory_available'],
                disk_usage_percent=raw_metrics['disk_usage_percent'],
                disk_free=raw_metrics['disk_free'],
                network_bytes_sent=raw_metrics['network_bytes_sent'],
                network_bytes_recv=raw_metrics['network_bytes_recv'],
                load_average=raw_metrics['load_average'],
                process_count=raw_metrics['process_count'],
                response_time=raw_metrics['response_time'],
                **features
            )
            
            return processed
        except Exception as e:
            print(f"❌ Error processing metrics: {e}")
            return None
    
    def publish_processed_metrics(self, processed_metrics: ProcessedMetrics):
        """Publish processed metrics to Kafka"""
        try:
            if self.kafka_producer:
                topic = 'processed_metrics'
                key = f"{processed_metrics.hostname}_{int(time.time())}"
                value = asdict(processed_metrics)
                
                self.kafka_producer.send(topic, key=key, value=value)
                self.kafka_producer.flush()
                print(f"📤 Published processed metrics to Kafka topic '{topic}'")
        except Exception as e:
            print(f"❌ Failed to publish processed metrics: {e}")
    
    def write_to_influxdb(self, processed_metrics: ProcessedMetrics):
        """Write processed metrics to InfluxDB"""
        try:
            if self.write_api:
                point = Point("processed_metrics") \
                    .tag("hostname", processed_metrics.hostname) \
                    .field("cpu_percent", processed_metrics.cpu_percent) \
                    .field("memory_percent", processed_metrics.memory_percent) \
                    .field("response_time", processed_metrics.response_time) \
                    .field("cpu_rolling_mean", processed_metrics.cpu_rolling_mean) \
                    .field("cpu_rolling_std", processed_metrics.cpu_rolling_std) \
                    .field("cpu_trend", processed_metrics.cpu_trend) \
                    .field("memory_trend", processed_metrics.memory_trend) \
                    .field("response_time_trend", processed_metrics.response_time_trend) \
                    .field("network_throughput", processed_metrics.network_throughput) \
                    .field("system_load_score", processed_metrics.system_load_score) \
                    .field("anomaly_score", processed_metrics.anomaly_score) \
                    .time(datetime.utcnow())
                
                self.write_api.write(bucket=self.influx_bucket, record=point)
                print(f"📊 Wrote processed metrics to InfluxDB")
        except Exception as e:
            print(f"❌ Failed to write to InfluxDB: {e}")
    
    async def process_stream(self):
        """Main processing loop"""
        print("🚀 Starting stream processing...")
        
        try:
            for message in self.kafka_consumer:
                try:
                    raw_metrics = message.value
                    print(f"📥 Received metrics from {raw_metrics.get('hostname', 'unknown')}")
                    
                    # Process metrics
                    processed_metrics = self.process_metrics(raw_metrics)
                    if processed_metrics:
                        # Publish processed metrics
                        self.publish_processed_metrics(processed_metrics)
                        
                        # Write to InfluxDB
                        self.write_to_influxdb(processed_metrics)
                        
                        print(f"🔄 Processed metrics: "
                              f"CPU={processed_metrics.cpu_percent:.1f}%, "
                              f"Anomaly={processed_metrics.anomaly_score:.2f}, "
                              f"Load={processed_metrics.system_load_score:.2f}")
                
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print("🛑 Stopping stream processing...")
        except Exception as e:
            print(f"❌ Error in processing loop: {e}")
    
    def close(self):
        """Clean up resources"""
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.influx_client:
            self.influx_client.close()

async def main():
    """Main application entry point"""
    print("🔧 Stream Processor Starting...")
    
    processor = StreamProcessor()
    
    try:
        await processor.process_stream()
    finally:
        processor.close()

if __name__ == "__main__":
    asyncio.run(main())
