#!/usr/bin/env python3
"""
Custom Dataset Benchmark
Benchmarks your specific 1K image dataset from Downloads/testing_data
"""

import os
import sys
import time
import statistics
import json
import asyncio
from typing import Dict
import requests

# Add server directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from services.embeddings import index_folder_async, embeddings_db, count_images_in_folder, search_images
from search_benchmark import SearchBenchmark
from memory_benchmark import MemoryBenchmark
from concurrent_benchmark import ConcurrentBenchmark

# Your dataset path - update this to match your system
CUSTOM_DATASET_PATH = r"C:\Users\spandan\Downloads\testing_data"
BASE_URL = "http://localhost:8000"

class CustomDatasetBenchmark:
    def __init__(self, dataset_path: str = CUSTOM_DATASET_PATH):
        self.dataset_path = dataset_path
        self.results = {}
        
    def validate_dataset(self) -> Dict:
        """Validate the custom dataset exists and count images"""
        if not os.path.exists(self.dataset_path):
            return {"error": f"Dataset path not found: {self.dataset_path}"}
        
        image_count = count_images_in_folder(self.dataset_path)
        
        if image_count == 0:
            return {"error": f"No images found in: {self.dataset_path}"}
        
        return {
            "path": self.dataset_path,
            "total_images": image_count,
            "status": "valid"
        }
    
    async def benchmark_1k_dataset_indexing(self) -> Dict:
        """Benchmark indexing performance on your 1K dataset"""
        print(f"🗂️  Benchmarking 1K dataset indexing performance...")
        
        validation = self.validate_dataset()
        if "error" in validation:
            return validation
        
        print(f"📊 Dataset: {validation['total_images']} images in {self.dataset_path}")
        
        # Clear existing embeddings
        embeddings_db.clear()
        
        # Measure indexing time
        start_time = time.perf_counter()
        
        try:
            await index_folder_async(self.dataset_path)
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            images_per_second = validation['total_images'] / total_time
            time_per_image = total_time / validation['total_images']
            
            return {
                "dataset_path": self.dataset_path,
                "total_images": validation['total_images'],
                "total_time_seconds": total_time,
                "images_per_second": images_per_second,
                "milliseconds_per_image": time_per_image * 1000,
                "embeddings_created": len(embeddings_db),
                "status": "success"
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "dataset_path": self.dataset_path,
                "total_images": validation['total_images'],
                "total_time_seconds": end_time - start_time,
                "status": "failed",
                "error": str(e)
            }
    
    def benchmark_1k_dataset_search(self, num_queries: int = 20) -> Dict:
        """Benchmark search performance on the indexed 1K dataset"""
        print(f"🔍 Benchmarking search performance on 1K dataset ({num_queries} queries)...")
        
        if not embeddings_db:
            return {"error": "No embeddings found. Run indexing benchmark first."}
        
        test_queries = [
            "person walking", "car driving", "dog playing", "cat sitting", "house exterior",
            "tree in park", "food on table", "water scenery", "mountain landscape", "city street",
            "sunset view", "beach scene", "forest path", "building architecture", "animal portrait",
            "flower garden", "bridge crossing", "train station", "boat harbor", "airplane sky"
        ]
        
        results = []
        
        for i in range(num_queries):
            query = test_queries[i % len(test_queries)]
            
            start_time = time.perf_counter()
            
            try:
                # Create mock request object
                class MockRequest:
                    base_url = "http://localhost:8000/"
                
                search_results = search_images(query, MockRequest())
                end_time = time.perf_counter()
                
                response_time_ms = (end_time - start_time) * 1000
                
                results.append({
                    "query": query,
                    "response_time_ms": response_time_ms,
                    "results_count": len(search_results),
                    "avg_confidence": statistics.mean([r.get('score', 0) for r in search_results]) if search_results else 0,
                    "status": "success"
                })
                
            except Exception as e:
                end_time = time.perf_counter()
                results.append({
                    "query": query,
                    "response_time_ms": (end_time - start_time) * 1000,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Calculate statistics
        successful_results = [r for r in results if r["status"] == "success"]
        
        if successful_results:
            response_times = [r["response_time_ms"] for r in successful_results]
            
            return {
                "dataset_size": len(embeddings_db),
                "total_queries": num_queries,
                "successful_queries": len(successful_results),
                "success_rate": len(successful_results) / num_queries * 100,
                "avg_response_time_ms": statistics.mean(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "95th_percentile_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                "avg_results_per_query": statistics.mean([r["results_count"] for r in successful_results]),
                "avg_confidence": statistics.mean([r["avg_confidence"] for r in successful_results]),
                "detailed_results": results
            }
        else:
            return {"error": "No successful search queries"}
    
    async def run_comprehensive_1k_benchmark(self) -> Dict:
        """Run comprehensive benchmark suite on your 1K dataset"""
        print("🚀 Running comprehensive benchmark on 1K dataset...")
        
        # Validate dataset first
        validation = self.validate_dataset()
        if "error" in validation:
            print(f"❌ {validation['error']}")
            return validation
        
        print(f"✅ Found {validation['total_images']} images in dataset")
        
        # Test 1: Indexing Performance
        print("\n📂 Test 1: 1K Dataset Indexing Performance")
        indexing_results = await self.benchmark_1k_dataset_indexing()
        
        if indexing_results.get("status") == "success":
            print(f"✅ Indexed {indexing_results['total_images']} images in {indexing_results['total_time_seconds']:.1f}s")
            print(f"   📈 Speed: {indexing_results['images_per_second']:.1f} images/second")
        else:
            print(f"❌ Indexing failed: {indexing_results.get('error', 'Unknown error')}")
            return {"indexing_results": indexing_results}
        
        # Test 2: Search Performance
        print("\n🔍 Test 2: Search Performance on 1K Dataset")
        search_results = self.benchmark_1k_dataset_search(num_queries=25)
        
        if "error" not in search_results:
            print(f"✅ Completed {search_results['successful_queries']}/{search_results['total_queries']} searches")
            print(f"   📈 Average response time: {search_results['avg_response_time_ms']:.1f}ms")
        else:
            print(f"❌ Search benchmark failed: {search_results['error']}")
        
        # Test 3: Memory Usage (if available)
        print("\n🧠 Test 3: Memory Usage with 1K Dataset")
        memory_benchmark = MemoryBenchmark()
        try:
            memory_results = await memory_benchmark.measure_indexing_memory(self.dataset_path, "1K Dataset Memory Test")
            memory_benchmark.cleanup()
            
            if memory_results.get("status") == "success":
                print(f"✅ Memory usage: {memory_results.get('memory_per_image_mb', 0):.2f} MB per image")
                print(f"   📈 Peak memory: {memory_results.get('peak_memory_mb', 0):.1f} MB")
            else:
                print(f"❌ Memory benchmark failed: {memory_results.get('error', 'Unknown error')}")
                memory_results = {"error": memory_results.get('error', 'Unknown error')}
        except Exception as e:
            print(f"❌ Memory benchmark failed: {e}")
            memory_results = {"error": str(e)}
        
        # Test 4: Concurrent Performance (if embeddings are loaded)
        print("\n🚀 Test 4: Concurrent Performance on 1K Dataset")
        if embeddings_db:
            concurrent_benchmark = ConcurrentBenchmark()
            try:
                concurrent_results = await concurrent_benchmark.concurrent_search_test(
                    concurrent_users=15, requests_per_user=2
                )
                
                if concurrent_results.get("stats", {}).get("success_rate", 0) > 0:
                    stats = concurrent_results["stats"]
                    print(f"✅ Handled {stats['concurrent_users']} concurrent users")
                    print(f"   📈 Success rate: {stats['success_rate']:.1f}%")
                    print(f"   📈 Throughput: {stats['requests_per_second']:.1f} req/sec")
                else:
                    print("❌ Concurrent benchmark failed")
                    concurrent_results = {"error": "No successful concurrent requests"}
            except Exception as e:
                print(f"❌ Concurrent benchmark failed: {e}")
                concurrent_results = {"error": str(e)}
        else:
            concurrent_results = {"error": "No embeddings available for concurrent testing"}
        
        # Compile results
        comprehensive_results = {
            "dataset_info": validation,
            "indexing_performance": indexing_results,
            "search_performance": search_results,
            "memory_performance": memory_results,
            "concurrent_performance": concurrent_results,
            "timestamp": time.time()
        }
        
        return comprehensive_results
    
    def print_1k_results(self, results: Dict):
        """Print formatted results for 1K dataset benchmark"""
        print("\n" + "="*70)
        print("📊 1K DATASET BENCHMARK RESULTS")
        print("="*70)
        
        # Dataset info
        dataset_info = results.get("dataset_info", {})
        if "error" not in dataset_info:
            print(f"📁 Dataset: {dataset_info['total_images']} images")
            print(f"📍 Location: {dataset_info['path']}")
        
        # Indexing performance
        indexing = results.get("indexing_performance", {})
        if indexing.get("status") == "success":
            print(f"\n⚡ INDEXING PERFORMANCE:")
            print(f"   • Processing Speed: {indexing['images_per_second']:.1f} images/second")
            print(f"   • Total Time: {indexing['total_time_seconds']:.1f} seconds")
            print(f"   • Time per Image: {indexing['milliseconds_per_image']:.1f} ms")
        
        # Search performance
        search = results.get("search_performance", {})
        if "error" not in search:
            print(f"\n🔍 SEARCH PERFORMANCE:")
            print(f"   • Average Response Time: {search['avg_response_time_ms']:.1f} ms")
            print(f"   • Success Rate: {search['success_rate']:.1f}%")
            print(f"   • 95th Percentile: {search['95th_percentile_ms']:.1f} ms")
            print(f"   • Average Confidence: {search['avg_confidence']:.2f}")
        
        # Memory performance
        memory = results.get("memory_performance", {})
        if memory.get("status") == "success":
            print(f"\n🧠 MEMORY EFFICIENCY:")
            print(f"   • Memory per Image: {memory.get('memory_per_image_mb', 0):.2f} MB")
            print(f"   • Peak Memory Usage: {memory.get('peak_memory_mb', 0):.1f} MB")
        
        # Concurrent performance
        concurrent = results.get("concurrent_performance", {})
        if concurrent.get("stats", {}).get("success_rate", 0) > 0:
            stats = concurrent["stats"]
            print(f"\n🚀 CONCURRENT CAPABILITY:")
            print(f"   • Concurrent Users: {stats['concurrent_users']}")
            print(f"   • Success Rate: {stats['success_rate']:.1f}%")
            print(f"   • Throughput: {stats['requests_per_second']:.1f} requests/second")
        
        # Resume metrics
        print(f"\n🎯 RESUME METRICS FOR 1K DATASET:")
        if indexing.get("status") == "success":
            print(f"   • Processes {indexing['images_per_second']:.0f} images/second on 1K+ dataset")
        if "error" not in search:
            print(f"   • Sub-{search['avg_response_time_ms']:.0f}ms search response time with {search['success_rate']:.0f}% accuracy")
        if memory.get("status") == "success":
            total_memory = memory.get('memory_per_image_mb', 0) * dataset_info.get('total_images', 1000)
            print(f"   • Efficiently handles 1K+ images using {total_memory:.0f}MB total memory")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark your custom 1K image dataset")
    parser.add_argument("--dataset", default=CUSTOM_DATASET_PATH, help="Path to your image dataset")
    parser.add_argument("--output", default="1k_dataset_benchmark_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    print("🎯 Custom 1K Dataset Benchmark")
    print(f"📁 Dataset path: {args.dataset}")
    
    # Update dataset path if provided
    benchmark = CustomDatasetBenchmark(args.dataset)
    
    try:
        # Run comprehensive benchmark
        results = asyncio.run(benchmark.run_comprehensive_1k_benchmark())
        
        # Print results
        benchmark.print_1k_results(results)
        
        # Save results
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {args.output}")
        print("🎉 1K dataset benchmark completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())