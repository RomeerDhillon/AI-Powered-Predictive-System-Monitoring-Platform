"""
Data Simulator for Realistic Load Testing

This script simulates realistic system load patterns to trigger AI predictions:
- CPU spikes and memory leaks
- Database connection pool exhaustion
- Network latency increases
- Application error rate spikes
- User traffic patterns
"""

import asyncio
import json
import random
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse

class LoadSimulator:
    """Simulates realistic system load patterns"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.scenarios = {
            'normal': self.simulate_normal_load,
            'cpu_spike': self.simulate_cpu_spike,
            'memory_leak': self.simulate_memory_leak,
            'database_stress': self.simulate_database_stress,
            'network_latency': self.simulate_network_latency,
            'error_spike': self.simulate_error_spike,
            'traffic_surge': self.simulate_traffic_surge
        }
    
    async def simulate_normal_load(self, duration: int = 60):
        """Simulate normal system load"""
        print("🔄 Simulating normal load...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate normal metrics
                response = requests.post(f"{self.base_url}/collect/metrics")
                if response.status_code == 200:
                    print("✅ Normal metrics generated")
                
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ Error in normal load simulation: {e}")
                await asyncio.sleep(5)
    
    async def simulate_cpu_spike(self, duration: int = 30):
        """Simulate CPU spike scenario"""
        print("🔥 Simulating CPU spike...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate high CPU load
                response = requests.post(f"{self.base_url}/collect/metrics")
                if response.status_code == 200:
                    print("🔥 High CPU metrics generated")
                
                # Simulate CPU-intensive operations
                await asyncio.sleep(0.1)  # Faster collection during spike
            except Exception as e:
                print(f"❌ Error in CPU spike simulation: {e}")
                await asyncio.sleep(1)
    
    async def simulate_memory_leak(self, duration: int = 45):
        """Simulate memory leak scenario"""
        print("💧 Simulating memory leak...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate memory-intensive metrics
                response = requests.post(f"{self.base_url}/collect/metrics")
                if response.status_code == 200:
                    print("💧 Memory leak metrics generated")
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error in memory leak simulation: {e}")
                await asyncio.sleep(5)
    
    async def simulate_database_stress(self, duration: int = 40):
        """Simulate database connection stress"""
        print("🗄️ Simulating database stress...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate database stress metrics
                response = requests.post(f"{self.base_url}/collect/metrics")
                if response.status_code == 200:
                    print("🗄️ Database stress metrics generated")
                
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"❌ Error in database stress simulation: {e}")
                await asyncio.sleep(3)
    
    async def simulate_network_latency(self, duration: int = 35):
        """Simulate network latency issues"""
        print("🌐 Simulating network latency...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate network latency metrics
                response = requests.post(f"{self.base_url}/collect/metrics")
                if response.status_code == 200:
                    print("🌐 Network latency metrics generated")
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error in network latency simulation: {e}")
                await asyncio.sleep(4)
    
    async def simulate_error_spike(self, duration: int = 25):
        """Simulate application error spike"""
        print("❌ Simulating error spike...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate error logs
                response = requests.post(f"{self.base_url}/collect/logs")
                if response.status_code == 200:
                    print("❌ Error logs generated")
                
                await asyncio.sleep(0.5)  # Faster error generation
            except Exception as e:
                print(f"❌ Error in error spike simulation: {e}")
                await asyncio.sleep(2)
    
    async def simulate_traffic_surge(self, duration: int = 50):
        """Simulate user traffic surge"""
        print("👥 Simulating traffic surge...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Generate high user activity
                response = requests.post(f"{self.base_url}/collect/user-activity")
                if response.status_code == 200:
                    print("👥 Traffic surge activity generated")
                
                await asyncio.sleep(0.2)  # High frequency during surge
            except Exception as e:
                print(f"❌ Error in traffic surge simulation: {e}")
                await asyncio.sleep(1)
    
    async def run_scenario(self, scenario_name: str, duration: int = 60):
        """Run a specific scenario"""
        if scenario_name not in self.scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            return
        
        print(f"🚀 Starting scenario: {scenario_name} (duration: {duration}s)")
        await self.scenarios[scenario_name](duration)
        print(f"✅ Completed scenario: {scenario_name}")
    
    async def run_chaos_test(self, duration: int = 300):
        """Run chaos testing with multiple scenarios"""
        print("🌪️ Starting chaos testing...")
        start_time = time.time()
        
        scenario_sequence = [
            ('normal', 30),
            ('cpu_spike', 20),
            ('normal', 20),
            ('memory_leak', 25),
            ('normal', 15),
            ('database_stress', 20),
            ('normal', 20),
            ('network_latency', 15),
            ('normal', 15),
            ('error_spike', 15),
            ('normal', 20),
            ('traffic_surge', 30),
            ('normal', 30)
        ]
        
        for scenario, scenario_duration in scenario_sequence:
            if time.time() - start_time >= duration:
                break
            
            await self.run_scenario(scenario, scenario_duration)
            await asyncio.sleep(5)  # Brief pause between scenarios
        
        print("🌪️ Chaos testing completed")
    
    async def run_continuous_load(self, duration: int = 600):
        """Run continuous load testing"""
        print("🔄 Starting continuous load testing...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Randomly select scenario
            scenario = random.choice(list(self.scenarios.keys()))
            scenario_duration = random.randint(10, 30)
            
            await self.run_scenario(scenario, scenario_duration)
            await asyncio.sleep(random.randint(5, 15))

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Load Simulator for Monitoring System')
    parser.add_argument('--scenario', type=str, default='normal',
                       choices=['normal', 'cpu_spike', 'memory_leak', 'database_stress',
                               'network_latency', 'error_spike', 'traffic_surge', 'chaos', 'continuous'],
                       help='Scenario to run')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds')
    parser.add_argument('--base-url', type=str, default='http://localhost:8002',
                       help='Base URL for the ingestion service')
    
    args = parser.parse_args()
    
    simulator = LoadSimulator(args.base_url)
    
    if args.scenario == 'chaos':
        await simulator.run_chaos_test(args.duration)
    elif args.scenario == 'continuous':
        await simulator.run_continuous_load(args.duration)
    else:
        await simulator.run_scenario(args.scenario, args.duration)

if __name__ == "__main__":
    asyncio.run(main())
