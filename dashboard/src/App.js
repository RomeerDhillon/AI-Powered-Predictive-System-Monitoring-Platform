import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import axios from 'axios';
import './App.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [metrics, setMetrics] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch data from backend
  const fetchData = async () => {
    try {
      // In a real implementation, you would fetch from your backend API
      // For now, we'll simulate data
      const mockMetrics = generateMockMetrics();
      const mockPredictions = generateMockPredictions();
      const mockAlerts = generateMockAlerts();

      setMetrics(mockMetrics);
      setPredictions(mockPredictions);
      setAlerts(mockAlerts);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch data');
      setLoading(false);
    }
  };

  // Generate mock metrics data
  const generateMockMetrics = () => {
    const data = [];
    const now = new Date();
    
    for (let i = 59; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 1000);
      data.push({
        timestamp: timestamp.toISOString(),
        hostname: 'monitoring-host',
        cpu_percent: Math.random() * 100,
        memory_percent: Math.random() * 100,
        response_time: Math.random() * 500 + 50,
        system_load_score: Math.random()
      });
    }
    
    return data;
  };

  // Generate mock predictions data with enhanced features
  const generateMockPredictions = () => {
    const data = [];
    const now = new Date();
    
    for (let i = 59; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 1000);
      const isAnomaly = Math.random() < 0.1; // 10% chance of anomaly
      const anomalyScore = Math.random();
      const confidence = Math.random();
      
      data.push({
        timestamp: timestamp.toISOString(),
        hostname: 'monitoring-host',
        is_anomaly: isAnomaly,
        anomaly_score: anomalyScore,
        confidence: confidence,
        predicted_failure_time: isAnomaly && Math.random() < 0.3 ? 
          new Date(now.getTime() + Math.random() * 24 * 60 * 60 * 1000).toISOString() : null,
        time_to_failure_hours: isAnomaly && Math.random() < 0.3 ? 
          Math.random() * 48 : null,
        failure_probability: isAnomaly ? Math.random() * 0.8 + 0.2 : Math.random() * 0.1,
        explanation: isAnomaly ? 
          `High CPU usage (${(Math.random() * 30 + 70).toFixed(1)}%) and memory pressure detected. System likely to experience performance degradation.` :
          'System operating within normal parameters.',
        feature_importance: {
          'cpu_percent': Math.random(),
          'memory_percent': Math.random(),
          'response_time': Math.random(),
          'system_load_score': Math.random()
        },
        models_used: ['IsolationForest', 'LSTM', 'Prophet'],
        recommended_actions: isAnomaly ? [
          'Scale up CPU resources',
          'Check for memory leaks',
          'Monitor system load trends'
        ] : ['Continue monitoring']
      });
    }
    
    return data;
  };

  // Generate mock alerts data
  const generateMockAlerts = () => {
    const alerts = [];
    const now = new Date();
    
    for (let i = 0; i < 5; i++) {
      const timestamp = new Date(now.getTime() - i * 300000); // 5 minutes apart
      alerts.push({
        timestamp: timestamp.toISOString(),
        hostname: 'monitoring-host',
        severity: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
        message: `Anomaly detected on monitoring-host`,
        anomaly_score: Math.random()
      });
    }
    
    return alerts;
  };

  useEffect(() => {
    fetchData();
    
    // Refresh data every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Prepare chart data
  const prepareChartData = (data, field) => {
    return {
      labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
      datasets: [
        {
          label: field,
          data: data.map(d => d[field]),
          borderColor: field === 'cpu_percent' ? '#3b82f6' : 
                      field === 'memory_percent' ? '#10b981' : 
                      field === 'response_time' ? '#f59e0b' : '#8b5cf6',
          backgroundColor: field === 'cpu_percent' ? '#3b82f620' : 
                          field === 'memory_percent' ? '#10b98120' : 
                          field === 'response_time' ? '#f59e0b20' : '#8b5cf620',
          tension: 0.4
        }
      ]
    };
  };

  // Prepare anomaly chart data
  const prepareAnomalyData = () => {
    return {
      labels: predictions.map(p => new Date(p.timestamp).toLocaleTimeString()),
      datasets: [
        {
          label: 'Anomaly Score',
          data: predictions.map(p => p.anomaly_score),
          borderColor: '#ef4444',
          backgroundColor: '#ef444420',
          tension: 0.4
        },
        {
          label: 'Confidence',
          data: predictions.map(p => p.confidence),
          borderColor: '#8b5cf6',
          backgroundColor: '#8b5cf620',
          tension: 0.4
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#e2e8f0'
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#94a3b8'
        },
        grid: {
          color: '#334155'
        }
      },
      y: {
        ticks: {
          color: '#94a3b8'
        },
        grid: {
          color: '#334155'
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">🚀 AI Monitoring Dashboard</h1>
              <p className="text-slate-300 mt-2">Predictive system monitoring with explainable AI</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Last Updated</div>
              <div className="text-white font-mono">{new Date().toLocaleTimeString()}</div>
            </div>
          </div>
          
          {/* Status Legend */}
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-slate-300">Healthy</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-slate-300">Warning</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-slate-300">Critical</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-slate-300">Info</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-400">CPU Usage</h3>
                <p className="text-3xl font-bold text-white mt-2">
                  {metrics.length > 0 ? metrics[metrics.length - 1].cpu_percent.toFixed(1) : 0}%
                </p>
                <p className="text-sm text-slate-400 mt-1">Current processor utilization</p>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                metrics.length > 0 && metrics[metrics.length - 1].cpu_percent > 80 ? 'bg-red-500' :
                metrics.length > 0 && metrics[metrics.length - 1].cpu_percent > 60 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}></div>
            </div>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-green-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-400">Memory Usage</h3>
                <p className="text-3xl font-bold text-white mt-2">
                  {metrics.length > 0 ? metrics[metrics.length - 1].memory_percent.toFixed(1) : 0}%
                </p>
                <p className="text-sm text-slate-400 mt-1">RAM utilization</p>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                metrics.length > 0 && metrics[metrics.length - 1].memory_percent > 85 ? 'bg-red-500' :
                metrics.length > 0 && metrics[metrics.length - 1].memory_percent > 70 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}></div>
            </div>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-yellow-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-yellow-400">Response Time</h3>
                <p className="text-3xl font-bold text-white mt-2">
                  {metrics.length > 0 ? metrics[metrics.length - 1].response_time.toFixed(0) : 0}ms
                </p>
                <p className="text-sm text-slate-400 mt-1">Average API response time</p>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                metrics.length > 0 && metrics[metrics.length - 1].response_time > 1000 ? 'bg-red-500' :
                metrics.length > 0 && metrics[metrics.length - 1].response_time > 500 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}></div>
            </div>
          </div>
          
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-purple-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-purple-400">Active Alerts</h3>
                <p className="text-3xl font-bold text-white mt-2">
                  {alerts.filter(alert => alert.severity === 'CRITICAL' || alert.severity === 'HIGH').length}
                </p>
                <p className="text-sm text-slate-400 mt-1">High priority alerts</p>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                alerts.filter(alert => alert.severity === 'CRITICAL' || alert.severity === 'HIGH').length > 0 ? 'bg-red-500' : 'bg-green-500'
              }`}></div>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* CPU Chart */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white">💻 CPU Usage</h3>
                <p className="text-sm text-slate-400">Processor utilization over time</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-400">
                  {metrics.length > 0 ? metrics[metrics.length - 1].cpu_percent.toFixed(1) : 0}%
                </div>
                <div className="text-xs text-slate-500">Current</div>
              </div>
            </div>
            <div className="h-64">
              <Line data={prepareChartData(metrics, 'cpu_percent')} options={chartOptions} />
            </div>
            <div className="mt-3 text-xs text-slate-500">
              💡 <strong>Thresholds:</strong> Green &lt; 60%, Yellow 60-80%, Red &gt; 80%
            </div>
          </div>

          {/* Memory Chart */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-green-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white">🧠 Memory Usage</h3>
                <p className="text-sm text-slate-400">RAM utilization over time</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-400">
                  {metrics.length > 0 ? metrics[metrics.length - 1].memory_percent.toFixed(1) : 0}%
                </div>
                <div className="text-xs text-slate-500">Current</div>
              </div>
            </div>
            <div className="h-64">
              <Line data={prepareChartData(metrics, 'memory_percent')} options={chartOptions} />
            </div>
            <div className="mt-3 text-xs text-slate-500">
              💡 <strong>Thresholds:</strong> Green &lt; 70%, Yellow 70-85%, Red &gt; 85%
            </div>
          </div>

          {/* Response Time Chart */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-yellow-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white">⚡ Response Time</h3>
                <p className="text-sm text-slate-400">API response latency over time</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-yellow-400">
                  {metrics.length > 0 ? metrics[metrics.length - 1].response_time.toFixed(0) : 0}ms
                </div>
                <div className="text-xs text-slate-500">Current</div>
              </div>
            </div>
            <div className="h-64">
              <Line data={prepareChartData(metrics, 'response_time')} options={chartOptions} />
            </div>
            <div className="mt-3 text-xs text-slate-500">
              💡 <strong>Thresholds:</strong> Green &lt; 500ms, Yellow 500-1000ms, Red &gt; 1000ms
            </div>
          </div>

          {/* Anomaly Detection Chart */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-purple-500 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white">🤖 AI Anomaly Detection</h3>
                <p className="text-sm text-slate-400">AI confidence and anomaly scores</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-purple-400">
                  {predictions.length > 0 ? (predictions[predictions.length - 1].confidence * 100).toFixed(1) : 0}%
                </div>
                <div className="text-xs text-slate-500">Confidence</div>
              </div>
            </div>
            <div className="h-64">
              <Line data={prepareAnomalyData()} options={chartOptions} />
            </div>
            <div className="mt-3 text-xs text-slate-500">
              💡 <strong>Legend:</strong> Red = Anomaly Score, Purple = AI Confidence
            </div>
          </div>
        </div>

        {/* AI Predictions Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Prediction Explanations */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">🤖 AI Predictions</h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-slate-400">Live Analysis</span>
              </div>
            </div>
            
            {predictions.filter(p => p.is_anomaly).length === 0 ? (
              <div className="text-center py-6">
                <div className="text-green-400 text-3xl mb-2">✅</div>
                <p className="text-slate-400">No anomalies detected</p>
                <p className="text-sm text-slate-500 mt-1">System operating normally</p>
              </div>
            ) : (
              <div className="space-y-4">
                {predictions.filter(p => p.is_anomaly).slice(0, 3).map((prediction, index) => (
                  <div key={index} className="bg-red-900/20 border border-red-500 rounded-lg p-4 hover:bg-red-900/30 transition-colors">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-red-400 text-lg">🚨</span>
                        <span className="text-red-400 font-semibold">Anomaly Detected</span>
                      </div>
                      <span className="text-sm text-slate-400">
                        {new Date(prediction.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <p className="text-sm text-slate-300 mb-3 leading-relaxed">{prediction.explanation}</p>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="bg-slate-700/50 p-2 rounded">
                        <span className="text-slate-400 block">Anomaly Score</span>
                        <span className="text-red-400 font-mono font-bold">{prediction.anomaly_score.toFixed(3)}</span>
                      </div>
                      <div className="bg-slate-700/50 p-2 rounded">
                        <span className="text-slate-400 block">Confidence</span>
                        <span className="text-white font-mono font-bold">{(prediction.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                    
                    {prediction.time_to_failure_hours && (
                      <div className="mt-3 p-3 bg-orange-900/20 border border-orange-500 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <span className="text-orange-400">⏰</span>
                          <span className="text-orange-400 font-semibold">Predicted Failure Time</span>
                        </div>
                        <p className="text-orange-300 mt-1">
                          {prediction.time_to_failure_hours.toFixed(1)} hours from now
                        </p>
                      </div>
                    )}
                    
                    <div className="mt-3 text-xs text-slate-500">
                      Models: {prediction.models_used.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Feature Importance */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">📊 Feature Analysis</h3>
              <span className="text-sm text-slate-400">Current Impact</span>
            </div>
            
            <div className="space-y-4">
              {predictions.length > 0 && Object.entries(predictions[predictions.length - 1].feature_importance)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([feature, importance], index) => (
                <div key={index} className="group">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-slate-300 capitalize font-medium">
                        {feature.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-slate-500">
                        {index === 0 ? '🔴 High Impact' : 
                         index === 1 ? '🟡 Medium Impact' : 
                         '🟢 Low Impact'}
                      </span>
                    </div>
                    <span className="text-sm text-slate-400 font-mono">
                      {(importance * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="w-full bg-slate-700 rounded-full h-3 group-hover:h-4 transition-all">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        index === 0 ? 'bg-red-500' :
                        index === 1 ? 'bg-orange-500' :
                        index === 2 ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${importance * 100}%` }}
                    ></div>
                  </div>
                  
                  <div className="text-xs text-slate-500 mt-1">
                    {feature === 'cpu_percent' && 'Processor utilization level'}
                    {feature === 'memory_percent' && 'RAM usage percentage'}
                    {feature === 'response_time' && 'API response latency'}
                    {feature === 'system_load_score' && 'Overall system load'}
                    {feature === 'cpu_rolling_mean' && 'Average CPU over time'}
                    {feature === 'cpu_rolling_std' && 'CPU variability'}
                    {feature === 'cpu_trend' && 'CPU usage trend direction'}
                    {feature === 'memory_trend' && 'Memory usage trend'}
                    {feature === 'response_time_trend' && 'Response time trend'}
                    {feature === 'network_throughput' && 'Network data transfer rate'}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-slate-700/30 rounded-lg">
              <p className="text-xs text-slate-400">
                💡 <strong>How to read:</strong> Higher percentages indicate features that are most influential 
                in the AI's decision-making process for anomaly detection.
              </p>
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">System Alerts</h3>
            <div className="flex space-x-2">
              <span className="text-sm text-slate-400">Total: {alerts.length}</span>
              <span className="text-sm text-red-400">Critical: {alerts.filter(a => a.severity === 'CRITICAL').length}</span>
              <span className="text-sm text-orange-400">High: {alerts.filter(a => a.severity === 'HIGH').length}</span>
            </div>
          </div>
          
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-green-400 text-4xl mb-2">✅</div>
              <p className="text-slate-400">No active alerts - System is healthy</p>
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert, index) => (
                <div key={index} className={`p-4 rounded-lg border-l-4 transition-all hover:shadow-lg ${
                  alert.severity === 'CRITICAL' ? 'bg-red-900/20 border-red-500 hover:bg-red-900/30' :
                  alert.severity === 'HIGH' ? 'bg-orange-900/20 border-orange-500 hover:bg-orange-900/30' :
                  alert.severity === 'MEDIUM' ? 'bg-yellow-900/20 border-yellow-500 hover:bg-yellow-900/30' :
                  'bg-blue-900/20 border-blue-500 hover:bg-blue-900/30'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        alert.severity === 'CRITICAL' ? 'bg-red-500' :
                        alert.severity === 'HIGH' ? 'bg-orange-500' :
                        alert.severity === 'MEDIUM' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`}></div>
                      <div>
                        <h4 className="font-semibold text-white">
                          {alert.severity === 'CRITICAL' ? '🚨 Critical Alert' :
                           alert.severity === 'HIGH' ? '⚠️ High Priority Alert' :
                           alert.severity === 'MEDIUM' ? '⚡ Medium Priority Alert' :
                           'ℹ️ Low Priority Alert'}
                        </h4>
                        <p className="text-sm text-slate-400">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      alert.severity === 'CRITICAL' ? 'bg-red-500 text-white' :
                      alert.severity === 'HIGH' ? 'bg-orange-500 text-white' :
                      alert.severity === 'MEDIUM' ? 'bg-yellow-500 text-black' :
                      'bg-blue-500 text-white'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                  
                  <div className="ml-5">
                    <p className="text-slate-300 mb-3">{alert.message}</p>
                    
                    {/* Alert Details */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-400">Anomaly Score:</span>
                        <span className="text-white ml-2 font-mono">{alert.anomaly_score.toFixed(3)}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Host:</span>
                        <span className="text-white ml-2">{alert.hostname}</span>
                      </div>
                    </div>
                    
                    {/* Recommended Actions */}
                    {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                      <div className="mt-3 p-3 bg-slate-700/50 rounded-lg">
                        <h5 className="text-sm font-semibold text-blue-400 mb-2">📋 Recommended Actions:</h5>
                        <ul className="text-sm text-slate-300 space-y-1">
                          {alert.recommended_actions.map((action, actionIndex) => (
                            <li key={actionIndex} className="flex items-start">
                              <span className="text-blue-400 mr-2">•</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
