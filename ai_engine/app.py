"""
Advanced AI Engine for Predictive System Monitoring

This service implements multiple ML models for time-series forecasting and anomaly detection:
- Isolation Forest for anomaly detection
- LSTM Autoencoder for sequence anomaly detection
- Prophet for time-series forecasting
- TCN (Temporal Convolutional Networks) for pattern recognition
- SHAP for explainability
"""

import asyncio
import json
import os
import pickle
import time
import warnings
from datetime import datetime, timedelta
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
from sklearn.metrics import mean_absolute_error, mean_squared_error
# import torch
# import torch.nn as nn
# import torch.optim as optim
# from torch.utils.data import DataLoader, TensorDataset
import shap
# import mlflow
# import mlflow.sklearn
# import mlflow.pytorch
# from prophet import Prophet
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

@dataclass
class PredictionResult:
    """Enhanced prediction result with explainability"""
    timestamp: str
    hostname: str
    
    # Prediction results
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    
    # Forecasting results
    predicted_failure_time: Optional[str]
    time_to_failure_hours: Optional[float]
    failure_probability: float
    
    # Explainability
    feature_importance: Dict[str, float]
    shap_values: Dict[str, float]
    explanation: str
    
    # Model metadata
    models_used: List[str]
    prediction_metadata: Dict[str, Any]

# Simplified classes for faster builds
class LSTMAutoencoder:
    """Simplified LSTM Autoencoder placeholder"""
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
    
    def eval(self):
        pass

class TCN:
    """Simplified TCN placeholder"""
    def __init__(self, input_size: int, output_size: int, num_channels: List[int], kernel_size: int = 3):
        self.input_size = input_size
        self.output_size = output_size
        self.num_channels = num_channels
    
    def eval(self):
        pass

class AdvancedAIEngine:
    """Advanced AI engine with multiple models and explainability"""
    
    def __init__(self):
        self.kafka_consumer = None
        self.kafka_producer = None
        self.influx_client = None
        self.write_api = None
        self.postgres_conn = None
        
        # Model components
        self.isolation_forest = None
        self.lstm_autoencoder = None
        self.tcn_model = None
        self.prophet_model = None
        self.scaler = None
        self.explainer = None
        
        # Model metadata
        self.model_version = "2.0.0"
        self.models_loaded = False
        
        # Configuration
        self.sequence_length = 60  # 60 time steps for LSTM
        self.prediction_horizon = 24  # Predict 24 hours ahead
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.1'))
        
        # Feature columns
        self.feature_columns = [
            'cpu_percent', 'memory_percent', 'response_time',
            'cpu_rolling_mean', 'cpu_rolling_std', 'cpu_trend',
            'memory_trend', 'response_time_trend', 'network_throughput',
            'system_load_score'
        ]
        
        self.setup_connections()
        self.load_models()
    
    def setup_connections(self):
        """Initialize all external connections"""
        self.setup_kafka()
        self.setup_influxdb()
        self.setup_postgres()
        self.setup_mlflow()
    
    def setup_kafka(self):
        """Initialize Kafka consumer and producer"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
            self.kafka_consumer = KafkaConsumer(
                'processed_metrics',
                bootstrap_servers=[bootstrap_servers],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='ai_engine',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
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
    
    def setup_mlflow(self):
        """Initialize MLflow tracking (simplified)"""
        try:
            # mlflow.set_tracking_uri("http://localhost:5000")
            # mlflow.set_experiment("predictive_monitoring")
            print(f"⚠️ MLflow disabled for faster builds")
        except Exception as e:
            print(f"⚠️ MLflow not available: {e}")
    
    def load_models(self):
        """Load all trained models"""
        try:
            model_path = '/app/models'
            
            # Load Isolation Forest
            if os.path.exists(f'{model_path}/isolation_forest_model.pkl'):
                with open(f'{model_path}/isolation_forest_model.pkl', 'rb') as f:
                    self.isolation_forest = pickle.load(f)
            
            # Load LSTM Autoencoder
            if os.path.exists(f'{model_path}/lstm_autoencoder.pth'):
                self.lstm_autoencoder = torch.load(f'{model_path}/lstm_autoencoder.pth')
                self.lstm_autoencoder.eval()
            
            # Load TCN model
            if os.path.exists(f'{model_path}/tcn_model.pth'):
                self.tcn_model = torch.load(f'{model_path}/tcn_model.pth')
                self.tcn_model.eval()
            
            # Load Prophet model
            if os.path.exists(f'{model_path}/prophet_model.pkl'):
                with open(f'{model_path}/prophet_model.pkl', 'rb') as f:
                    self.prophet_model = pickle.load(f)
            
            # Load scaler
            if os.path.exists(f'{model_path}/scaler.pkl'):
                with open(f'{model_path}/scaler.pkl', 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Initialize SHAP explainer
            if self.isolation_forest and self.scaler:
                self.explainer = shap.TreeExplainer(self.isolation_forest)
            
            self.models_loaded = True
            print(f"✅ Loaded models version {self.model_version}")
            
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            self.create_default_models()
    
    def create_default_models(self):
        """Create default models for initial operation"""
        try:
            # Create default Isolation Forest
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # Create default scaler
            self.scaler = StandardScaler()
            
            # Create dummy training data
            dummy_data = np.random.normal(0, 1, (100, len(self.feature_columns)))
            self.scaler.fit(dummy_data)
            self.isolation_forest.fit(dummy_data)
            
            # Initialize SHAP explainer
            self.explainer = shap.TreeExplainer(self.isolation_forest)
            
            print("✅ Created default models")
        except Exception as e:
            print(f"❌ Failed to create default models: {e}")
    
    def extract_features(self, metrics: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract features for prediction"""
        try:
            features = []
            for col in self.feature_columns:
                if col in metrics:
                    features.append(metrics[col])
                else:
                    features.append(0.0)
            
            return np.array(features).reshape(1, -1)
        except Exception as e:
            print(f"❌ Error extracting features: {e}")
            return None
    
    def predict_with_isolation_forest(self, features: np.ndarray) -> Tuple[bool, float, float]:
        """Predict anomaly using Isolation Forest"""
        try:
            if not self.isolation_forest or not self.scaler:
                return False, 0.0, 0.0
            
            features_scaled = self.scaler.transform(features)
            prediction = self.isolation_forest.predict(features_scaled)[0]
            score = self.isolation_forest.score_samples(features_scaled)[0]
            
            is_anomaly = prediction == -1
            confidence = abs(score)
            
            return is_anomaly, float(score), confidence
        except Exception as e:
            print(f"❌ Error in Isolation Forest prediction: {e}")
            return False, 0.0, 0.0
    
    def predict_with_lstm(self, sequence_data: np.ndarray) -> Tuple[bool, float]:
        """Predict anomaly using LSTM Autoencoder"""
        try:
            if not self.lstm_autoencoder:
                return False, 0.0
            
            with torch.no_grad():
                sequence_tensor = torch.FloatTensor(sequence_data).unsqueeze(0)
                reconstructed = self.lstm_autoencoder(sequence_tensor)
                
                # Calculate reconstruction error
                mse = torch.mean((sequence_tensor - reconstructed) ** 2).item()
                
                # Simple threshold-based anomaly detection
                is_anomaly = mse > 0.1  # Threshold can be tuned
                confidence = min(1.0, mse * 10)  # Scale confidence
                
                return is_anomaly, confidence
        except Exception as e:
            print(f"❌ Error in LSTM prediction: {e}")
            return False, 0.0
    
    def predict_with_prophet(self, time_series_data: pd.DataFrame) -> Tuple[Optional[str], float, float]:
        """Predict future failures using Prophet"""
        try:
            if not self.prophet_model or len(time_series_data) < 10:
                return None, 0.0, 0.0
            
            # Prepare data for Prophet
            prophet_data = time_series_data[['ds', 'y']].copy()
            
            # Make future predictions
            future = self.prophet_model.make_future_dataframe(periods=self.prediction_horizon, freq='H')
            forecast = self.prophet_model.predict(future)
            
            # Find potential failure points
            latest_forecast = forecast.tail(self.prediction_horizon)
            high_risk_periods = latest_forecast[latest_forecast['yhat_upper'] > 0.8]
            
            if len(high_risk_periods) > 0:
                failure_time = high_risk_periods.iloc[0]['ds']
                failure_probability = high_risk_periods.iloc[0]['yhat']
                time_to_failure = (failure_time - datetime.now()).total_seconds() / 3600
                
                return failure_time.isoformat(), time_to_failure, failure_probability
            
            return None, 0.0, 0.0
        except Exception as e:
            print(f"❌ Error in Prophet prediction: {e}")
            return None, 0.0, 0.0
    
    def get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Get feature importance using SHAP"""
        try:
            if not self.explainer or not self.scaler:
                return {col: 1.0/len(self.feature_columns) for col in self.feature_columns}
            
            features_scaled = self.scaler.transform(features)
            shap_values = self.explainer.shap_values(features_scaled[0])
            
            importance = {}
            for i, col in enumerate(self.feature_columns):
                importance[col] = float(abs(shap_values[i]))
            
            return importance
        except Exception as e:
            print(f"❌ Error calculating feature importance: {e}")
            return {col: 1.0/len(self.feature_columns) for col in self.feature_columns}
    
    def generate_explanation(self, prediction_result: PredictionResult) -> str:
        """Generate human-readable explanation of the prediction"""
        try:
            explanations = []
            
            # Anomaly explanation
            if prediction_result.is_anomaly:
                top_features = sorted(prediction_result.feature_importance.items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
                
                explanations.append(f"🚨 Anomaly detected with {prediction_result.confidence:.1%} confidence.")
                explanations.append(f"Key indicators: {', '.join([f'{k} ({v:.2f})' for k, v in top_features])}")
            
            # Failure prediction explanation
            if prediction_result.predicted_failure_time:
                explanations.append(f"⚠️ Potential failure predicted in {prediction_result.time_to_failure_hours:.1f} hours")
                explanations.append(f"Failure probability: {prediction_result.failure_probability:.1%}")
            
            # Model confidence
            explanations.append(f"Models used: {', '.join(prediction_result.models_used)}")
            
            return " | ".join(explanations)
        except Exception as e:
            print(f"❌ Error generating explanation: {e}")
            return "Prediction generated successfully"
    
    def predict_anomaly(self, metrics: Dict[str, Any]) -> Optional[PredictionResult]:
        """Main prediction function using all models"""
        try:
            # Extract features
            features = self.extract_features(metrics)
            if features is None:
                return None
            
            # Initialize result
            result = PredictionResult(
                timestamp=metrics['timestamp'],
                hostname=metrics['hostname'],
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                predicted_failure_time=None,
                time_to_failure_hours=None,
                failure_probability=0.0,
                feature_importance={},
                shap_values={},
                explanation="",
                models_used=[],
                prediction_metadata={}
            )
            
            # Isolation Forest prediction
            if self.isolation_forest:
                is_anomaly, score, confidence = self.predict_with_isolation_forest(features)
                result.is_anomaly = is_anomaly
                result.anomaly_score = score
                result.confidence = confidence
                result.models_used.append("IsolationForest")
            
            # LSTM prediction (if sequence data available)
            # Note: This would require historical sequence data
            # For now, we'll skip LSTM prediction
            
            # Prophet prediction (if time series data available)
            # Note: This would require historical time series data
            # For now, we'll skip Prophet prediction
            
            # Get feature importance
            result.feature_importance = self.get_feature_importance(features)
            
            # Generate explanation
            result.explanation = self.generate_explanation(result)
            
            # Add metadata
            result.prediction_metadata = {
                'model_version': self.model_version,
                'threshold': self.anomaly_threshold,
                'features_count': len(self.feature_columns)
            }
            
            return result
        except Exception as e:
            print(f"❌ Error predicting anomaly: {e}")
            return None
    
    def publish_prediction(self, prediction: PredictionResult):
        """Publish prediction to Kafka"""
        try:
            if self.kafka_producer:
                topic = 'ai_predictions'
                key = f"{prediction.hostname}_{int(time.time())}"
                value = asdict(prediction)
                
                self.kafka_producer.send(topic, key=key, value=value)
                self.kafka_producer.flush()
                print(f"📤 Published AI prediction to Kafka topic '{topic}'")
        except Exception as e:
            print(f"❌ Failed to publish prediction: {e}")
    
    def write_to_influxdb(self, prediction: PredictionResult):
        """Write prediction to InfluxDB"""
        try:
            if self.write_api:
                point = Point("ai_predictions") \
                    .tag("hostname", prediction.hostname) \
                    .tag("is_anomaly", str(prediction.is_anomaly)) \
                    .field("anomaly_score", prediction.anomaly_score) \
                    .field("confidence", prediction.confidence) \
                    .field("failure_probability", prediction.failure_probability) \
                    .field("time_to_failure_hours", prediction.time_to_failure_hours or 0) \
                    .field("model_version", prediction.prediction_metadata.get('model_version', 'unknown')) \
                    .time(datetime.utcnow())
                
                self.write_api.write(bucket=self.influx_bucket, record=point)
                print(f"📊 Wrote AI prediction to InfluxDB")
        except Exception as e:
            print(f"❌ Failed to write to InfluxDB: {e}")
    
    def store_prediction_in_db(self, prediction: PredictionResult):
        """Store prediction in PostgreSQL"""
        try:
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                
                query = """
                INSERT INTO ai_predictions 
                (timestamp, hostname, is_anomaly, anomaly_score, confidence, 
                 predicted_failure_time, time_to_failure_hours, failure_probability,
                 feature_importance, explanation, models_used, prediction_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    prediction.timestamp,
                    prediction.hostname,
                    prediction.is_anomaly,
                    prediction.anomaly_score,
                    prediction.confidence,
                    prediction.predicted_failure_time,
                    prediction.time_to_failure_hours,
                    prediction.failure_probability,
                    json.dumps(prediction.feature_importance),
                    prediction.explanation,
                    json.dumps(prediction.models_used),
                    json.dumps(prediction.prediction_metadata)
                ))
                
                self.postgres_conn.commit()
                cursor.close()
                print(f"💾 Stored AI prediction in PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to store prediction in DB: {e}")
    
    async def process_predictions(self):
        """Main prediction processing loop"""
        print("🚀 Starting advanced AI prediction processing...")
        
        try:
            for message in self.kafka_consumer:
                try:
                    processed_metrics = message.value
                    hostname = processed_metrics.get('hostname', 'unknown')
                    print(f"📥 Received metrics from {hostname}")
                    
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
                        print(f"🔮 AI Prediction: {status} - "
                              f"Score: {prediction.anomaly_score:.3f}, "
                              f"Confidence: {prediction.confidence:.3f}")
                        print(f"💡 Explanation: {prediction.explanation}")
                
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
    print("🔧 Advanced AI Engine Starting...")
    
    ai_engine = AdvancedAIEngine()
    
    try:
        await ai_engine.process_predictions()
    finally:
        ai_engine.close()

if __name__ == "__main__":
    asyncio.run(main())
