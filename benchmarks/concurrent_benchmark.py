#!/usr/bin/env python3
"""
Concurrent Load Testing Benchmark
Measures how the system handles multiple simultaneous search requests
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import Dict, List
import concurrent.futures
import threading

BASE_URL = "http://localhost:8000"

# Test queries for concurrent testing
CONCURRENT_TEST_QUERIES = [
    "cat sitting", "dog running", "car driving", "person walking", "tree in forest",
    "house with garden", "food on plate", "water flowing", "mountain peak", "blue sky",
    "sunset colors", "green grass", "red flower", "white cloud", "black bird",
    "city street", "beach sand", "snow falling", "rain drops", "fire burning",
    "boat sailing", "plane flying", "train moving", "bike riding", "horse galloping",
    "fish swimming", "bird singing", "wind blowing", "sun shining", "moon glowing"
]

class ConcurrentBenchmark:
    def __init__(self):
        self.results = []
        
    def test_server_connection(self) -> bool:
        """Test if the server is running"""
        import requests
        try:
            response = requests.get(f"{BASE_URL}/indexing-status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def single_search_request(self, session: aiohttp.ClientSession, query: str, request_id: int) -> Dict:
        """Make a single search request"""
        start_time = time.perf_counter()
        
        try:
            async with session.post(
                f"{BASE_URL}/search/",
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                
                if response.status == 200:
                    results = await response.json()
                    return {
                        "request_id": request_id,
                        "query": query,
                        "response_time_ms": response_time_ms,
                        "status": "success",
                        "results_count": len(results),
                        "status_code": response.status
                    }
                else:
                    return {
                        "request_id": request_id,
                        "query": query,
                        "response_time_ms": response_time_ms,
                        "status": "error",
                        "status_code": response.status
                    }
                    
        except asyncio.TimeoutError:
            end_time = time.perf_counter()
            return {
                "request_id": request_id,
                "query": query,
                "response_time_ms": (end_time - start_time) * 1000,
                "status": "timeout"
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "request_id": request_id,
                "query": query,
                "response_time_ms": (end_time - start_time) * 1000,
                "status": "failed",
                "error": str(e)
            }
    
    async def concurrent_search_test(self, concurrent_users: int, requests_per_user: int) -> Dict:
        """Test concurrent search requests"""
        print(f"🚀 Testing {concurrent_users} concurrent users, {requests_per_user} requests each")
        
        total_requests = concurrent_users * requests_per_user
        
        async with aiohttp.ClientSession() as session:
            # Create all tasks
            tasks = []
            request_id = 0
            
            for user in range(concurrent_users):
                for req in range(requests_per_user):
                    query = CONCURRENT_TEST_QUERIES[request_id % len(CONCURRENT_TEST_QUERIES)]
                    task = self.single_search_request(session, query, request_id)
                    tasks.append(task)
                    request_id += 1
            
            # Execute all requests concurrently
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            
            # Process results
            successful_requests = []
            failed_requests = []
            timeout_requests = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_requests.append({"error": str(result), "status": "exception"})
                elif result["status"] == "success":
                    successful_requests.append(result)
                elif result["status"] == "timeout":
                    timeout_requests.append(result)
                else:
                    failed_requests.append(result)
            
            # Calculate statistics
            if successful_requests:
                response_times = [r["response_time_ms"] for r in successful_requests]
                
                stats = {
                    "concurrent_users": concurrent_users,
                    "requests_per_user": requests_per_user,
                    "total_requests": total_requests,
                    "total_time_seconds": total_time,
                    "requests_per_second": total_requests / total_time,
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "timeout_requests": len(timeout_requests),
                    "success_rate": len(successful_requests) / total_requests * 100,
                    "avg_response_time_ms": statistics.mean(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "median_response_time_ms": statistics.median(response_times),
                    "95th_percentile_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                    "std_deviation_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
                }
            else:
                stats = {
                    "concurrent_users": concurrent_users,
                    "requests_per_user": requests_per_user,
                    "total_requests": total_requests,
                    "total_time_seconds": total_time,
                    "successful_requests": 0,
                    "failed_requests": len(failed_requests),
                    "timeout_requests": len(timeout_requests),
                    "success_rate": 0,
                    "error": "No successful requests"
                }
            
            return {
                "stats": stats,
                "successful_results": successful_requests[:10],  # Sample of successful results
                "failed_results": failed_requests[:5],  # Sample of failed results
                "timeout_results": timeout_requests[:5]  # Sample of timeout results
            }
    
    async def websocket_concurrent_test(self, concurrent_connections: int, duration_seconds: int = 30) -> Dict:
        """Test concurrent WebSocket connections"""
        print(f"🔌 Testing {concurrent_connections} concurrent WebSocket connections for {duration_seconds}s")
        
        connected_count = 0
        messages_received = 0
        connection_errors = 0
        
        async def websocket_client(client_id: int):
            nonlocal connected_count, messages_received, connection_errors
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(f"{BASE_URL.replace('http', 'ws')}/ws") as ws:
                        connected_count += 1
                        
                        # Listen for messages for the specified duration
                        end_time = time.time() + duration_seconds
                        while time.time() < end_time:
                            try:
                                msg = await asyncio.wait_for(ws.receive(), timeout=1.0)
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    messages_received += 1
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    break
                            except asyncio.TimeoutError:
                                continue  # No message received, continue listening
                            
            except Exception as e:
                connection_errors += 1
                print(f"WebSocket client {client_id} error: {e}")
        
        # Create WebSocket client tasks
        tasks = [websocket_client(i) for i in range(concurrent_connections)]
        
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        actual_duration = time.time() - start_time
        
        return {
            "concurrent_connections": concurrent_connections,
            "requested_duration_seconds": duration_seconds,
            "actual_duration_seconds": actual_duration,
            "connected_count": connected_count,
            "messages_received": messages_received,
            "connection_errors": connection_errors,
            "connection_success_rate": connected_count / concurrent_connections * 100,
            "messages_per_second": messages_received / actual_duration if actual_duration > 0 else 0
        }
    
    async def progressive_load_test(self) -> Dict:
        """Test with progressively increasing load"""
        print("📈 Running progressive load test...")
        
        test_scenarios = [
            {"users": 1, "requests": 5},
            {"users": 5, "requests": 3},
            {"users": 10, "requests": 2},
            {"users": 20, "requests": 2},
            {"users": 50, "requests": 1},
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n📊 Testing {scenario['users']} users × {scenario['requests']} requests...")
            result = await self.concurrent_search_test(scenario['users'], scenario['requests'])
            
            result['test_scenario'] = scenario
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        return results
    
    async def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive concurrent load testing"""
        print("🔥 Running comprehensive concurrent load benchmark...")
        
        if not self.test_server_connection():
            return {"error": "Server not responding at http://localhost:8000"}
        
        benchmark_results = {}
        
        # Test 1: Progressive load testing
        print("\n🧪 Test 1: Progressive Load Testing")
        progressive_results = await self.progressive_load_test()
        benchmark_results["progressive_load"] = progressive_results
        
        # Test 2: High concurrency burst test
        print("\n🧪 Test 2: High Concurrency Burst Test")
        burst_result = await self.concurrent_search_test(concurrent_users=30, requests_per_user=2)
        benchmark_results["burst_test"] = burst_result
        
        # Test 3: WebSocket concurrent connections
        print("\n🧪 Test 3: WebSocket Concurrent Connections")
        websocket_result = await self.websocket_concurrent_test(concurrent_connections=10, duration_seconds=15)
        benchmark_results["websocket_test"] = websocket_result
        
        # Calculate aggregate statistics
        successful_tests = [r for r in progressive_results if r.get("stats", {}).get("success_rate", 0) > 0]
        
        if successful_tests:
            success_rates = [r["stats"]["success_rate"] for r in successful_tests]
            requests_per_second = [r["stats"]["requests_per_second"] for r in successful_tests]
            response_times = [r["stats"]["avg_response_time_ms"] for r in successful_tests]
            max_concurrent_users = max(r["stats"]["concurrent_users"] for r in successful_tests)
            
            aggregate_stats = {
                "total_tests": len(progressive_results) + 2,  # +2 for burst and websocket
                "successful_load_tests": len(successful_tests),
                "max_concurrent_users_tested": max_concurrent_users,
                "avg_success_rate": statistics.mean(success_rates),
                "min_success_rate": min(success_rates),
                "max_requests_per_second": max(requests_per_second),
                "avg_requests_per_second": statistics.mean(requests_per_second),
                "avg_response_time_under_load": statistics.mean(response_times),
                "websocket_connections_supported": websocket_result.get("connected_count", 0),
                "websocket_success_rate": websocket_result.get("connection_success_rate", 0)
            }
        else:
            aggregate_stats = {"error": "No successful load tests"}
        
        benchmark_results["aggregate_stats"] = aggregate_stats
        
        return benchmark_results
    
    def print_results(self, results: Dict):
        """Print formatted benchmark results"""
        if "error" in results:
            print(f"❌ Benchmark failed: {results['error']}")
            return
        
        if "error" in results.get("aggregate_stats", {}):
            print("❌ No successful load test results")
            return
        
        stats = results["aggregate_stats"]
        print("\n" + "="*60)
        print("🚀 CONCURRENT LOAD TESTING RESULTS")
        print("="*60)
        
        print(f"📊 CONCURRENCY PERFORMANCE:")
        print(f"   • Max Concurrent Users Tested: {stats['max_concurrent_users_tested']}")
        print(f"   • Peak Requests/Second: {stats['max_requests_per_second']:.1f} req/sec")
        print(f"   • Average Success Rate: {stats['avg_success_rate']:.1f}%")
        print(f"   • Average Response Time Under Load: {stats['avg_response_time_under_load']:.1f} ms")
        print(f"   • WebSocket Connections Supported: {stats['websocket_connections_supported']}")
        print(f"   • WebSocket Success Rate: {stats['websocket_success_rate']:.1f}%")
        
        print(f"\n🔥 KEY RESUME METRICS:")
        print(f"   • Handles {stats['max_concurrent_users_tested']}+ concurrent users")
        print(f"   • Peak throughput: {stats['max_requests_per_second']:.0f} requests/second")
        print(f"   • {stats['avg_success_rate']:.0f}% success rate under load")
        print(f"   • Maintains sub-{stats['avg_response_time_under_load']:.0f}ms response times under load")
        print(f"   • Supports {stats['websocket_connections_supported']} simultaneous WebSocket connections")
        
        # Progressive load test details
        progressive_results = results.get("progressive_load", [])
        print(f"\n📈 PROGRESSIVE LOAD TEST DETAILS:")
        for i, result in enumerate(progressive_results, 1):
            if result.get("stats", {}).get("success_rate", 0) > 0:
                s = result["stats"]
                print(f"   {i}. {s['concurrent_users']} users: {s['requests_per_second']:.1f} req/sec, {s['success_rate']:.1f}% success")
            else:
                s = result.get("stats", {})
                print(f"   {i}. {s.get('concurrent_users', 'N/A')} users: FAILED")
        
        # Burst test details
        burst_result = results.get("burst_test", {})
        if burst_result.get("stats", {}).get("success_rate", 0) > 0:
            s = burst_result["stats"]
            print(f"\n💥 BURST TEST RESULTS:")
            print(f"   • {s['concurrent_users']} concurrent users × {s['requests_per_user']} requests")
            print(f"   • {s['requests_per_second']:.1f} requests/second")
            print(f"   • {s['success_rate']:.1f}% success rate")
            print(f"   • {s['avg_response_time_ms']:.1f} ms average response time")

def main():
    benchmark = ConcurrentBenchmark()
    
    print("Starting concurrent load testing benchmark...")
    print("Make sure your server is running: uvicorn server.main:app --reload")
    print("And that you have indexed some images\n")
    
    # Run the benchmark
    results = asyncio.run(benchmark.run_comprehensive_benchmark())
    
    # Print results
    benchmark.print_results(results)
    
    # Save results to file
    with open("concurrent_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: concurrent_benchmark_results.json")

if __name__ == "__main__":
    main()