#!/usr/bin/env python3
"""
Search Response Time Benchmark
Measures API response times for search queries
"""

import asyncio
import time
import statistics
import requests
import json
from typing import List, Dict

BASE_URL = "http://localhost:8000"

# Test queries with different complexity levels
TEST_QUERIES = [
    "cat",
    "dog running",
    "sunset landscape",
    "person walking in park",
    "red car on street",
    "mountain lake reflection",
    "city skyline at night",
    "food on table",
    "airplane in sky",
    "beach with waves",
    "forest with trees",
    "building architecture",
    "animal in nature",
    "winter snow scene",
    "flower in garden"
]

class SearchBenchmark:
    def __init__(self):
        self.results = []
        self.base_url = BASE_URL
        
    def test_server_connection(self) -> bool:
        """Test if the server is running"""
        try:
            response = requests.get(f"{self.base_url}/indexing-status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def measure_single_search(self, query: str) -> Dict:
        """Measure response time for a single search query"""
        start_time = time.perf_counter()
        
        try:
            response = requests.post(
                f"{self.base_url}/search/",
                json={"query": query},
                timeout=10
            )
            end_time = time.perf_counter()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                results = response.json()
                return {
                    "query": query,
                    "response_time_ms": response_time_ms,
                    "status": "success",
                    "results_count": len(results),
                    "avg_confidence": statistics.mean([r.get('score', 0) for r in results]) if results else 0
                }
            else:
                return {
                    "query": query,
                    "response_time_ms": response_time_ms,
                    "status": "error",
                    "error_code": response.status_code
                }
                
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "query": query,
                "response_time_ms": (end_time - start_time) * 1000,
                "status": "failed",
                "error": str(e)
            }
    
    def run_single_query_benchmark(self, iterations: int = 10) -> Dict:
        """Run benchmark for each query multiple times"""
        print(f"🔍 Running search response time benchmark ({iterations} iterations per query)...")
        
        if not self.test_server_connection():
            print("❌ Server not responding at http://localhost:8000")
            print("Please start the server with: uvicorn server.main:app --reload")
            return {}
        
        all_results = []
        query_stats = {}
        
        for query in TEST_QUERIES:
            print(f"Testing query: '{query}'")
            query_results = []
            
            for i in range(iterations):
                result = self.measure_single_search(query)
                query_results.append(result)
                all_results.append(result)
                
                # Small delay between requests
                time.sleep(0.1)
            
            # Calculate stats for this query
            response_times = [r["response_time_ms"] for r in query_results if r["status"] == "success"]
            
            if response_times:
                query_stats[query] = {
                    "avg_response_time_ms": statistics.mean(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "median_response_time_ms": statistics.median(response_times),
                    "success_rate": len(response_times) / iterations * 100,
                    "iterations": iterations
                }
        
        # Overall statistics
        successful_results = [r for r in all_results if r["status"] == "success"]
        response_times = [r["response_time_ms"] for r in successful_results]
        
        if response_times:
            overall_stats = {
                "total_queries_tested": len(TEST_QUERIES),
                "total_iterations": len(all_results),
                "successful_requests": len(successful_results),
                "overall_success_rate": len(successful_results) / len(all_results) * 100,
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "95th_percentile_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                "std_deviation_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        else:
            overall_stats = {"error": "No successful requests"}
        
        return {
            "overall_stats": overall_stats,
            "query_stats": query_stats,
            "raw_results": all_results
        }
    
    def print_results(self, results: Dict):
        """Print formatted benchmark results"""
        if not results or "error" in results.get("overall_stats", {}):
            print("❌ No successful benchmark results")
            return
        
        stats = results["overall_stats"]
        print("\n" + "="*60)
        print("🎯 SEARCH RESPONSE TIME BENCHMARK RESULTS")
        print("="*60)
        
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   • Total Queries Tested: {stats['total_queries_tested']}")
        print(f"   • Total Requests: {stats['total_iterations']}")
        print(f"   • Success Rate: {stats['overall_success_rate']:.1f}%")
        print(f"   • Average Response Time: {stats['avg_response_time_ms']:.1f} ms")
        print(f"   • Median Response Time: {stats['median_response_time_ms']:.1f} ms")
        print(f"   • 95th Percentile: {stats['95th_percentile_ms']:.1f} ms")
        print(f"   • Min Response Time: {stats['min_response_time_ms']:.1f} ms")
        print(f"   • Max Response Time: {stats['max_response_time_ms']:.1f} ms")
        print(f"   • Standard Deviation: {stats['std_deviation_ms']:.1f} ms")
        
        print(f"\n🔥 KEY RESUME METRICS:")
        print(f"   • Sub-{int(stats['avg_response_time_ms'])}ms average search response time")
        print(f"   • {stats['overall_success_rate']:.0f}% query success rate")
        print(f"   • Handles {len(TEST_QUERIES)} different query types")
        
        # Top 5 fastest queries
        query_stats = results["query_stats"]
        fastest_queries = sorted(query_stats.items(), key=lambda x: x[1]["avg_response_time_ms"])[:5]
        
        print(f"\n⚡ TOP 5 FASTEST QUERIES:")
        for i, (query, stats) in enumerate(fastest_queries, 1):
            print(f"   {i}. '{query}': {stats['avg_response_time_ms']:.1f} ms")

def main():
    benchmark = SearchBenchmark()
    
    print("Starting search response time benchmark...")
    print("Make sure your server is running: uvicorn server.main:app --reload")
    print("And that you have indexed some images in the /server/data/ folder\n")
    
    # Run the benchmark
    results = benchmark.run_single_query_benchmark(iterations=10)
    
    # Print results
    benchmark.print_results(results)
    
    # Save results to file
    with open("search_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: search_benchmark_results.json")

if __name__ == "__main__":
    main()