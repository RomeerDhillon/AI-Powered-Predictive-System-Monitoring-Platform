"""
Model Trainer Service for Retraining AI Models

This service periodically retrains the Isolation Forest model using historical data
from InfluxDB and updates the model store for the AI predictor.
"""

import asyncio
import json
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TrainingResult:
    """Model training result"""
    model_version: str
    training_timestamp: str
    training_samples: int
    model_performance: Dict[str, float]
    feature_importance: Dict[str, float]
    training_metadata: Dict[str, Any]

class ModelTrainer:
    """Handles model training and retraining"""
    
    def __init__(self):
        self.influx_client = None
        self.postgres_conn = None
        
        # Training configuration
        self.training_interval = int(os.getenv('TRAINING_INTERVAL', '3600'))  # 1 hour
        self.min_training_samples = int(os.getenv('MIN_TRAINING_SAMPLES', '1000'))
        self.contamination = float(os.getenv('MODEL_CONTAMINATION', '0.1'))
        self.model_version = "1.0.0"
        
        # Feature columns for training
        self.feature_columns = [
            'cpu_percent', 'memory_percent', 'response_time',
            'cpu_rolling_mean', 'cpu_rolling_std', 'cpu_trend',
            'memory_trend', 'response_time_trend', 'network_throughput',
            'system_load_score'
        ]
        
        self.setup_connections()
    
    def setup_connections(self):
        """Initialize all external connections"""
        self.setup_influxdb()
        self.setup_postgres()
    
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
    
    def fetch_training_data(self, hours_back: int = 24) -> Optional[pd.DataFrame]:
        """Fetch training data from InfluxDB"""
        try:
            if not self.influx_client:
                print("❌ InfluxDB not connected")
                return None
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Query processed metrics
            query = f'''
            from(bucket: "{self.influx_bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r._measurement == "processed_metrics")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.influx_client.query_api().query(query)
            
            # Convert to DataFrame
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'timestamp': record.get_time(),
                        'hostname': record.values.get('hostname', 'unknown'),
                        'cpu_percent': record.values.get('cpu_percent', 0.0),
                        'memory_percent': record.values.get('memory_percent', 0.0),
                        'response_time': record.values.get('response_time', 0.0),
                        'cpu_rolling_mean': record.values.get('cpu_rolling_mean', 0.0),
                        'cpu_rolling_std': record.values.get('cpu_rolling_std', 0.0),
                        'cpu_trend': record.values.get('cpu_trend', 0.0),
                        'memory_trend': record.values.get('memory_trend', 0.0),
                        'response_time_trend': record.values.get('response_time_trend', 0.0),
                        'network_throughput': record.values.get('network_throughput', 0.0),
                        'system_load_score': record.values.get('system_load_score', 0.0)
                    })
            
            if not data:
                print("⚠️ No training data found")
                return None
            
            df = pd.DataFrame(data)
            print(f"📊 Fetched {len(df)} training samples")
            return df
            
        except Exception as e:
            print(f"❌ Failed to fetch training data: {e}")
            return None
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data and labels"""
        try:
            # Select features
            X = df[self.feature_columns].fillna(0).values
            
            # Create synthetic labels based on anomaly scores
            # In a real scenario, you'd have labeled anomaly data
            # For now, we'll use a simple heuristic based on extreme values
            labels = np.zeros(len(X))
            
            # Mark as anomalies if any feature is extreme
            for i, row in enumerate(X):
                if (row[0] > 90 or  # CPU > 90%
                    row[1] > 90 or  # Memory > 90%
                    row[2] > 1000 or  # Response time > 1s
                    row[9] > 0.8):  # System load score > 0.8
                    labels[i] = 1
            
            # Ensure we have some anomalies
            if np.sum(labels) == 0:
                # Create some synthetic anomalies
                n_anomalies = max(1, len(X) // 20)  # 5% anomalies
                anomaly_indices = np.random.choice(len(X), n_anomalies, replace=False)
                labels[anomaly_indices] = 1
            
            print(f"📈 Training data: {len(X)} samples, {np.sum(labels)} anomalies ({np.sum(labels)/len(labels)*100:.1f}%)")
            return X, labels
            
        except Exception as e:
            print(f"❌ Failed to prepare training data: {e}")
            return None, None
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Tuple[IsolationForest, StandardScaler, Dict[str, float]]:
        """Train the Isolation Forest model"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Isolation Forest
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                max_features=1.0
            )
            
            model.fit(X_train_scaled)
            
            # Evaluate model
            train_predictions = model.predict(X_train_scaled)
            test_predictions = model.predict(X_test_scaled)
            
            # Convert predictions to binary (1 for anomaly, 0 for normal)
            train_predictions_binary = (train_predictions == -1).astype(int)
            test_predictions_binary = (test_predictions == -1).astype(int)
            
            # Calculate performance metrics
            performance = {
                'train_accuracy': np.mean(train_predictions_binary == y_train),
                'test_accuracy': np.mean(test_predictions_binary == y_test),
                'train_precision': self.calculate_precision(y_train, train_predictions_binary),
                'test_precision': self.calculate_precision(y_test, test_predictions_binary),
                'train_recall': self.calculate_recall(y_train, train_predictions_binary),
                'test_recall': self.calculate_recall(y_test, test_predictions_binary)
            }
            
            print(f"🎯 Model performance: Test Accuracy={performance['test_accuracy']:.3f}")
            
            return model, scaler, performance
            
        except Exception as e:
            print(f"❌ Failed to train model: {e}")
            return None, None, {}
    
    def calculate_precision(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate precision score"""
        try:
            tp = np.sum((y_true == 1) & (y_pred == 1))
            fp = np.sum((y_true == 0) & (y_pred == 1))
            return tp / (tp + fp) if (tp + fp) > 0 else 0.0
        except:
            return 0.0
    
    def calculate_recall(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate recall score"""
        try:
            tp = np.sum((y_true == 1) & (y_pred == 1))
            fn = np.sum((y_true == 1) & (y_pred == 0))
            return tp / (tp + fn) if (tp + fn) > 0 else 0.0
        except:
            return 0.0
    
    def save_model(self, model: IsolationForest, scaler: StandardScaler, performance: Dict[str, float]):
        """Save trained model to disk"""
        try:
            # Create models directory if it doesn't exist
            os.makedirs('/app/models', exist_ok=True)
            
            # Save model
            model_path = '/app/models/isolation_forest_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save scaler
            scaler_path = '/app/models/scaler.pkl'
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            # Save model metadata
            metadata = {
                'model_version': self.model_version,
                'training_timestamp': datetime.utcnow().isoformat(),
                'feature_columns': self.feature_columns,
                'performance': performance,
                'contamination': self.contamination
            }
            
            metadata_path = '/app/models/model_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Model saved to {model_path}")
            print(f"💾 Scaler saved to {scaler_path}")
            print(f"💾 Metadata saved to {metadata_path}")
            
        except Exception as e:
            print(f"❌ Failed to save model: {e}")
    
    def store_training_result(self, result: TrainingResult):
        """Store training result in PostgreSQL"""
        try:
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                
                query = """
                INSERT INTO training_results 
                (model_version, training_timestamp, training_samples, model_performance, 
                 feature_importance, training_metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    result.model_version,
                    result.training_timestamp,
                    result.training_samples,
                    json.dumps(result.model_performance),
                    json.dumps(result.feature_importance),
                    json.dumps(result.training_metadata)
                ))
                
                self.postgres_conn.commit()
                cursor.close()
                print(f"💾 Stored training result in PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to store training result: {e}")
    
    def train_and_update_model(self) -> bool:
        """Main training function"""
        try:
            print("🔄 Starting model training...")
            
            # Fetch training data
            df = self.fetch_training_data(hours_back=24)
            if df is None or len(df) < self.min_training_samples:
                print(f"⚠️ Insufficient training data: {len(df) if df is not None else 0} samples")
                return False
            
            # Prepare training data
            X, y = self.prepare_training_data(df)
            if X is None or y is None:
                print("❌ Failed to prepare training data")
                return False
            
            # Train model
            model, scaler, performance = self.train_model(X, y)
            if model is None or scaler is None:
                print("❌ Failed to train model")
                return False
            
            # Save model
            self.save_model(model, scaler, performance)
            
            # Create training result
            result = TrainingResult(
                model_version=self.model_version,
                training_timestamp=datetime.utcnow().isoformat(),
                training_samples=len(X),
                model_performance=performance,
                feature_importance={col: 1.0/len(self.feature_columns) for col in self.feature_columns},  # Simplified
                training_metadata={
                    'contamination': self.contamination,
                    'feature_columns': self.feature_columns,
                    'training_samples': len(X),
                    'anomaly_samples': int(np.sum(y))
                }
            )
            
            # Store result
            self.store_training_result(result)
            
            print("✅ Model training completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Model training failed: {e}")
            return False
    
    async def training_loop(self):
        """Main training loop"""
        print(f"🚀 Starting model trainer (interval: {self.training_interval}s)...")
        
        while True:
            try:
                # Train model
                success = self.train_and_update_model()
                if success:
                    print(f"✅ Training completed at {datetime.utcnow()}")
                else:
                    print(f"⚠️ Training skipped at {datetime.utcnow()}")
                
                # Wait for next training cycle
                await asyncio.sleep(self.training_interval)
                
            except KeyboardInterrupt:
                print("🛑 Stopping model trainer...")
                break
            except Exception as e:
                print(f"❌ Error in training loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def close(self):
        """Clean up resources"""
        if self.influx_client:
            self.influx_client.close()
        if self.postgres_conn:
            self.postgres_conn.close()

async def main():
    """Main application entry point"""
    print("🔧 Model Trainer Service Starting...")
    
    trainer = ModelTrainer()
    
    try:
        await trainer.training_loop()
    finally:
        trainer.close()

if __name__ == "__main__":
    asyncio.run(main())
