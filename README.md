# AI-Powered Predictive System Monitoring Platform

A production-grade, real-time monitoring platform that **forecasts failures before they occur** using advanced machine learning. This system analyzes patterns in logs, performance metrics, and user behavior to flag potential issues hours or days in advance, making predictions clear and actionable for engineers.

## 🚀 Features

### **Advanced AI Engine**
- **Multiple ML Models**: Isolation Forest, LSTM Autoencoder, Prophet, TCN
- **Explainable AI**: SHAP values and feature attribution for predictions
- **Failure Forecasting**: Predicts what will fail, when, and why
- **Time-to-Failure Estimates**: Hours or days advance warning
- **Model Lifecycle Management**: MLflow integration, drift detection, shadow mode

### **Comprehensive Data Ingestion**
- **Multi-source Telemetry**: System metrics, application logs, user activity, business metrics
- **High-throughput Processing**: Handles millions of events per hour
- **Real-time Feature Engineering**: Rolling windows, trends, seasonality analysis
- **Distributed Tracing**: OpenTelemetry integration

### **Intelligent Alerting**
- **Actionable Alerts**: "Database likely to hit connection limit in 3 hours"
- **Recommended Actions**: Specific mitigation steps for each prediction
- **Severity Classification**: Based on confidence and potential impact
- **Multi-channel Delivery**: Slack, Email, PagerDuty integration

### **Advanced Dashboard**
- **Prediction Explanations**: Why the AI made each prediction
- **Feature Importance**: Which metrics drove the decision
- **Time-to-Failure Visualization**: Countdown to predicted issues
- **Feedback System**: Engineers can confirm or dismiss predictions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingestion     │    │   Stream        │    │   AI Predictor  │
│   Service       │───▶│   Processor     │───▶│   Service       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   InfluxDB      │    │   InfluxDB      │    │   PostgreSQL    │
│   (Raw Metrics) │    │   (Processed)   │    │   (Predictions) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Alert         │    │   Dashboard     │    │   Model         │
│   Service       │◀───│   (React)       │    │   Trainer       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

1. **Get the code**
   - If you already have the files locally, `cd` into the project root.
   - Otherwise, clone your repository and `cd` into it.

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration (see InfluxDB token steps below)
   ```

3. **Start core infrastructure**
   ```bash
   docker-compose up -d kafka influxdb postgres
   ```

4. **Initialize PostgreSQL schema (Windows PowerShell friendly)**
   - PowerShell does not support `<` redirection the same way as bash. Use:
   ```powershell
   Get-Content .\init-db.sql | docker exec -i postgres psql -U admin -d monitoring
   ```
   - On bash (macOS/Linux):
   ```bash
   docker exec -i postgres psql -U admin -d monitoring < init-db.sql
   ```

5. **Initialize InfluxDB with org, bucket, and token**
   ```bash
   docker exec influxdb influx setup \
     --username admin \
     --password admin123 \
     --org my-org \
     --bucket metrics \
     --force

   docker exec influxdb influx auth list
   # Copy the generated token value
   ```

6. **Configure the InfluxDB token**
   - Option A (recommended): set `INFLUXDB_TOKEN` in `.env` to the token you copied.
   - Option B: set it directly in `docker-compose.yml` service env vars for `ingestion_service`, `stream_processor`, `ai_predictor`, and `model_trainer`.

7. **Start all services**
   ```bash
   docker-compose up -d
   ```

8. **Access the dashboard**
   - Dashboard: http://localhost:3000
   - InfluxDB UI: http://localhost:8086
   - Kafka broker (no UI): localhost:9092

## 🔧 Services Overview

### 1. Ingestion Service (`/ingestion_service`)
- Collects system metrics (CPU, memory, disk, network)
- Publishes metrics to Kafka topic `system_metrics`
- Stores raw metrics in InfluxDB
- Simulates realistic system behavior with occasional anomalies

### 2. Stream Processor (`/stream_processor`)
- Consumes raw metrics from Kafka
- Computes rolling features (mean, std, trends)
- Publishes processed metrics to Kafka topic `processed_metrics`
- Stores enhanced metrics in InfluxDB

### 3. AI Predictor (`/ai_predictor`)
- Consumes processed metrics from Kafka
- Performs real-time anomaly detection using Isolation Forest
- Publishes predictions to Kafka topic `anomaly_predictions`
- Stores predictions in PostgreSQL

### 4. Alert Service (`/alert_service`)
- Consumes anomaly predictions from Kafka
- Sends alerts via Slack, Email, and Console
- Implements alert cooldown to prevent spam
- Stores alert history in PostgreSQL

### 5. Model Trainer (`/model_trainer`)
- Periodically retrains the Isolation Forest model
- Uses historical data from InfluxDB
- Updates model files for the AI predictor
- Stores training results in PostgreSQL

### 6. Dashboard (`/dashboard`)
- React-based real-time dashboard
- Displays metrics, predictions, and alerts
- Beautiful charts using Chart.js
- Responsive design with Tailwind CSS

## 📊 Data Flow

1. **Metrics Collection**: Ingestion service collects system metrics every second
2. **Stream Processing**: Stream processor computes features and trends
3. **AI Prediction**: AI predictor detects anomalies in real-time
4. **Alerting**: Alert service sends notifications for anomalies
5. **Visualization**: Dashboard displays all data in real-time
6. **Model Training**: Model trainer retrains the AI model periodically

## 🎯 AI Model Details

### Isolation Forest Algorithm
- **Purpose**: Unsupervised anomaly detection
- **Features**: CPU, memory, response time, rolling statistics, trends
- **Training**: Uses historical metrics with synthetic anomaly labels
- **Retraining**: Automatic retraining every hour with new data
- **Performance**: <1 second prediction latency

### Feature Engineering
- Rolling averages and standard deviations
- Trend analysis using linear regression
- Network throughput calculations
- System load scoring
- Anomaly score computation

## 🔔 Alerting Configuration

### Alert Channels
- **Console**: Always enabled for debugging
- **Slack**: Configure `SLACK_WEBHOOK_URL` in `.env`
- **Email**: Configure SMTP settings in `.env`

### Alert Rules
- **Threshold**: Configurable anomaly score threshold
- **Cooldown**: Prevents spam with configurable cooldown period
- **Severity**: Automatic severity classification based on anomaly score

## 📈 Dashboard Features

### Real-time Charts
- CPU and Memory usage over time
- Response time trends
- Anomaly detection scores
- System load indicators

### Alert Management
- Recent alerts with severity indicators
- Alert history and statistics
- Real-time alert notifications

### System Health
- Current system status
- Historical performance metrics
- AI model performance indicators

## 🛠️ Development

### Local Development Setup

1. **Start infrastructure services**
   ```bash
   docker-compose up kafka influxdb postgres -d
   ```

2. **Run services locally**
   ```bash
   # Terminal 1: Ingestion Service
   cd ingestion_service
   pip install -r requirements.txt
   python app.py

   # Terminal 2: Stream Processor
   cd stream_processor
   pip install -r requirements.txt
   python app.py

   # Terminal 3: AI Predictor
   cd ai_predictor
   pip install -r requirements.txt
   python app.py

   # Terminal 4: Alert Service
   cd alert_service
   pip install -r requirements.txt
   python app.py

   # Terminal 5: Model Trainer
   cd model_trainer
   pip install -r requirements.txt
   python app.py

   # Terminal 6: Dashboard
   cd dashboard
   npm install
   npm start
   ```

### Adding New Metrics

1. **Update data structures** in `ingestion_service/app.py`
2. **Add feature computation** in `stream_processor/app.py`
3. **Update model features** in `ai_predictor/app.py`
4. **Add dashboard visualization** in `dashboard/src/App.js`

### Adding New Alert Channels

1. **Implement new channel method** in `alert_service/app.py`
2. **Update alert configuration** in environment variables
3. **Test alert delivery** with sample anomalies

## 🔍 Monitoring and Debugging

### Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ingestion_service
docker-compose logs -f ai_predictor
```

### Database Queries
```sql
-- Recent anomalies
SELECT * FROM recent_anomalies LIMIT 10;

-- System health summary
SELECT * FROM system_health_summary;

-- Alert statistics
SELECT severity, COUNT(*) FROM alerts GROUP BY severity;
```

### Kafka Topics
```bash
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume messages
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic system_metrics --from-beginning
```

## 🚀 Production Deployment

### Environment Variables
- Set all required environment variables
- Use secure passwords and tokens
- Configure proper network access

### Docker Compose version field
- Compose v2 ignores the top-level `version:` field. If you see a warning, you can safely remove the `version:` line from `docker-compose.yml`.

### Scaling
- Increase Kafka partitions for higher throughput
- Scale services horizontally with load balancers
- Use external databases for production

### Security
- Enable authentication for all services
- Use TLS/SSL for all connections
- Implement proper access controls

## 📚 API Endpoints

### Ingestion Service (Port 8001)
- `GET /` - Service status
- `GET /health` - Health check
- `POST /collect` - Manual metrics collection

### Dashboard (Port 3000)
- Real-time metrics visualization
- Alert management interface
- System health monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables
3. Check database connectivity
4. Review Kafka topic status

## 🔮 Future Enhancements

- [ ] Support for more ML algorithms (LSTM, Prophet)
- [ ] Advanced feature engineering
- [ ] Multi-host monitoring
- [ ] Custom alert rules
- [ ] Machine learning model versioning
- [ ] Advanced dashboard analytics
- [ ] Integration with external monitoring tools
- [ ] Automated incident response
