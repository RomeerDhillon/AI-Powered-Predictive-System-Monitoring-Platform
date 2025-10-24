-- Database initialization script for the monitoring system
-- This script creates the necessary tables for storing predictions, alerts, and training results

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS monitoring;

-- Use the monitoring database
\c monitoring;

-- Create ai_predictions table (enhanced)
CREATE TABLE IF NOT EXISTS ai_predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    anomaly_score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    predicted_failure_time TIMESTAMP,
    time_to_failure_hours FLOAT,
    failure_probability FLOAT,
    feature_importance JSONB,
    shap_values JSONB,
    explanation TEXT,
    models_used JSONB,
    prediction_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create anomaly_predictions table (legacy)
CREATE TABLE IF NOT EXISTS anomaly_predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    anomaly_score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    model_version VARCHAR(50),
    features_used JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_timestamp ON anomaly_predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_hostname ON anomaly_predictions(hostname);
CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_is_anomaly ON anomaly_predictions(is_anomaly);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    channels_sent JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for alerts table
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_hostname ON alerts(hostname);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Create training_results table
CREATE TABLE IF NOT EXISTS training_results (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    training_timestamp TIMESTAMP NOT NULL,
    training_samples INTEGER NOT NULL,
    model_performance JSONB NOT NULL,
    feature_importance JSONB NOT NULL,
    training_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for training_results table
CREATE INDEX IF NOT EXISTS idx_training_results_model_version ON training_results(model_version);
CREATE INDEX IF NOT EXISTS idx_training_results_timestamp ON training_results(training_timestamp);

-- Create system_metrics table for historical data
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    cpu_percent FLOAT NOT NULL,
    memory_percent FLOAT NOT NULL,
    memory_available BIGINT NOT NULL,
    disk_usage_percent FLOAT NOT NULL,
    disk_free BIGINT NOT NULL,
    network_bytes_sent BIGINT NOT NULL,
    network_bytes_recv BIGINT NOT NULL,
    load_average FLOAT NOT NULL,
    process_count INTEGER NOT NULL,
    response_time FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for system_metrics table
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_hostname ON system_metrics(hostname);

-- Create processed_metrics table
CREATE TABLE IF NOT EXISTS processed_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    cpu_percent FLOAT NOT NULL,
    memory_percent FLOAT NOT NULL,
    response_time FLOAT NOT NULL,
    cpu_rolling_mean FLOAT NOT NULL,
    cpu_rolling_std FLOAT NOT NULL,
    cpu_trend FLOAT NOT NULL,
    memory_trend FLOAT NOT NULL,
    response_time_trend FLOAT NOT NULL,
    network_throughput FLOAT NOT NULL,
    system_load_score FLOAT NOT NULL,
    anomaly_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for processed_metrics table
CREATE INDEX IF NOT EXISTS idx_processed_metrics_timestamp ON processed_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_metrics_hostname ON processed_metrics(hostname);

-- Insert sample data for testing
INSERT INTO system_metrics (
    timestamp, hostname, cpu_percent, memory_percent, memory_available,
    disk_usage_percent, disk_free, network_bytes_sent, network_bytes_recv,
    load_average, process_count, response_time
) VALUES 
(
    NOW() - INTERVAL '1 hour', 'monitoring-host', 45.2, 67.8, 8589934592,
    23.4, 500000000000, 1024000, 2048000, 1.2, 156, 125.5
),
(
    NOW() - INTERVAL '30 minutes', 'monitoring-host', 52.1, 71.3, 7516192768,
    24.1, 495000000000, 1536000, 3072000, 1.4, 162, 98.7
),
(
    NOW(), 'monitoring-host', 38.7, 63.2, 9126805504,
    22.8, 510000000000, 512000, 1024000, 0.9, 148, 87.3
);

-- Insert sample anomaly predictions
INSERT INTO anomaly_predictions (
    timestamp, hostname, is_anomaly, anomaly_score, confidence, model_version, features_used
) VALUES 
(
    NOW() - INTERVAL '1 hour', 'monitoring-host', false, 0.15, 0.85, '1.0.0', 
    '["cpu_percent", "memory_percent", "response_time", "cpu_rolling_mean", "cpu_rolling_std"]'
),
(
    NOW() - INTERVAL '30 minutes', 'monitoring-host', true, 0.78, 0.92, '1.0.0',
    '["cpu_percent", "memory_percent", "response_time", "cpu_rolling_mean", "cpu_rolling_std"]'
),
(
    NOW(), 'monitoring-host', false, 0.23, 0.88, '1.0.0',
    '["cpu_percent", "memory_percent", "response_time", "cpu_rolling_mean", "cpu_rolling_std"]'
);

-- Insert sample alerts
INSERT INTO alerts (
    timestamp, hostname, alert_type, severity, message, anomaly_score, confidence, channels_sent, metadata
) VALUES 
(
    NOW() - INTERVAL '30 minutes', 'monitoring-host', 'anomaly_detection', 'HIGH',
    'Anomaly detected on monitoring-host - High CPU usage and response time', 0.78, 0.92,
    '["console", "slack"]', '{"model_version": "1.0.0", "features_used": ["cpu_percent", "response_time"]}'
);

-- Insert sample training results
INSERT INTO training_results (
    model_version, training_timestamp, training_samples, model_performance, feature_importance, training_metadata
) VALUES 
(
    '1.0.0', NOW() - INTERVAL '2 hours', 1000,
    '{"test_accuracy": 0.89, "test_precision": 0.85, "test_recall": 0.82}',
    '{"cpu_percent": 0.25, "memory_percent": 0.20, "response_time": 0.30, "cpu_rolling_mean": 0.15, "cpu_rolling_std": 0.10}',
    '{"contamination": 0.1, "feature_columns": ["cpu_percent", "memory_percent", "response_time"], "training_samples": 1000, "anomaly_samples": 100}'
);

-- Create a view for recent anomalies
CREATE OR REPLACE VIEW recent_anomalies AS
SELECT 
    ap.timestamp,
    ap.hostname,
    ap.anomaly_score,
    ap.confidence,
    ap.model_version
FROM anomaly_predictions ap
WHERE ap.is_anomaly = true
AND ap.timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY ap.timestamp DESC;

-- Create a view for system health summary
CREATE OR REPLACE VIEW system_health_summary AS
SELECT 
    hostname,
    AVG(cpu_percent) as avg_cpu,
    AVG(memory_percent) as avg_memory,
    AVG(response_time) as avg_response_time,
    MAX(cpu_percent) as max_cpu,
    MAX(memory_percent) as max_memory,
    MAX(response_time) as max_response_time,
    COUNT(*) as sample_count
FROM system_metrics
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY hostname;

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- Print success message
\echo 'Database initialization completed successfully!'
\echo 'Created tables: anomaly_predictions, alerts, training_results, system_metrics, processed_metrics'
\echo 'Created views: recent_anomalies, system_health_summary'
\echo 'Inserted sample data for testing'
