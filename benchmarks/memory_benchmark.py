#!/usr/bin/env python3
"""
Memory Usage Benchmark
Measures memory consumption during image indexing and searching
"""

import os
import sys
import time
import json
import psutil
import threading
import tempfile
import shutil
from typing import Dict, List
import numpy as np
from PIL import Image

# Add server directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from services.embeddings import index_folder_async, embeddings_db, count_images_in_folder, search_images
import asyncio

class MemoryMonitor:
    def __init__(self):
        self.memory_samples = []
        self.monitoring = False
        self.monitor_thread = None
        self.process = psutil.Process()
    
    def start_monitoring(self, interval: float = 0.1):
        """Start monitoring memory usage"""
        self.monitoring = True
        self.memory_samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring memory usage"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: float):
        """Internal monitoring loop"""
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                self.memory_samples.append({
                    'timestamp': time.time(),
                    'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
                    'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
                })
                time.sleep(interval)
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                break
    
    def get_stats(self) -> Dict:
        """Get memory usage statistics"""
        if not self.memory_samples:
            return {"error": "No memory samples collected"}
        
        rss_values = [sample['rss_mb'] for sample in self.memory_samples]
        vms_values = [sample['vms_mb'] for sample in self.memory_samples]
        
        return {
            'samples_count': len(self.memory_samples),
            'duration_seconds': self.memory_samples[-1]['timestamp'] - self.memory_samples[0]['timestamp'],
            'rss_stats': {
                'initial_mb': rss_values[0],
                'final_mb': rss_values[-1],
                'peak_mb': max(rss_values),
                'min_mb': min(rss_values),
                'avg_mb': sum(rss_values) / len(rss_values),
                'increase_mb': rss_values[-1] - rss_values[0]
            },
            'vms_stats': {
                'initial_mb': vms_values[0],
                'final_mb': vms_values[-1],
                'peak_mb': max(vms_values),
                'min_mb': min(vms_values),
                'avg_mb': sum(vms_values) / len(vms_values),
                'increase_mb': vms_values[-1] - vms_values[0]
            }
        }

class MemoryBenchmark:
    def __init__(self):
        self.monitor = MemoryMonitor()
        self.temp_dirs = []
    
    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def create_test_images(self, count: int, size: tuple = (512, 512)) -> str:
        """Create test images in a temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix="img_mem_bench_")
        self.temp_dirs.append(temp_dir)
        
        print(f"Creating {count} test images ({size[0]}x{size[1]}) in {temp_dir}...")
        
        for i in range(count):
            # Create random colored image
            img_array = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            # Save as JPEG to save disk space
            filename = f"test_image_{i:04d}.jpg"
            filepath = os.path.join(temp_dir, filename)
            img.save(filepath, quality=85)
        
        return temp_dir
    
    async def measure_indexing_memory(self, folder_path: str, test_name: str) -> Dict:
        """Measure memory usage during indexing"""
        print(f"\n🧠 Testing memory usage: {test_name}")
        
        image_count = count_images_in_folder(folder_path)
        print(f"   Images to process: {image_count}")
        
        if image_count == 0:
            return {"error": "No images found"}
        
        # Clear existing embeddings
        embeddings_db.clear()
        
        # Start memory monitoring
        self.monitor.start_monitoring(interval=0.1)
        
        start_time = time.perf_counter()
        
        try:
            await index_folder_async(folder_path)
            end_time = time.perf_counter()
            
            # Stop monitoring after a short delay to capture final state
            await asyncio.sleep(0.5)
            self.monitor.stop_monitoring()
            
            memory_stats = self.monitor.get_stats()
            
            # Calculate memory per image
            embeddings_count = len(embeddings_db)
            
            result = {
                "test_name": test_name,
                "folder_path": folder_path,
                "total_images": image_count,
                "embeddings_created": embeddings_count,
                "indexing_time_seconds": end_time - start_time,
                "memory_stats": memory_stats,
                "status": "success"
            }
            
            # Calculate efficiency metrics
            if embeddings_count > 0 and memory_stats.get('rss_stats'):
                memory_per_image = memory_stats['rss_stats']['increase_mb'] / embeddings_count
                result['memory_per_image_mb'] = memory_per_image
                result['peak_memory_mb'] = memory_stats['rss_stats']['peak_mb']
                result['memory_efficiency'] = {
                    'mb_per_image': memory_per_image,
                    'images_per_gb': 1024 / memory_per_image if memory_per_image > 0 else 0,
                    'peak_mb': memory_stats['rss_stats']['peak_mb']
                }
            
            return result
            
        except Exception as e:
            self.monitor.stop_monitoring()
            return {
                "test_name": test_name,
                "folder_path": folder_path,
                "total_images": image_count,
                "status": "failed",
                "error": str(e)
            }
    
    def measure_search_memory(self, query_count: int = 20) -> Dict:
        """Measure memory usage during searching"""
        print(f"\n🔍 Testing search memory usage ({query_count} queries)")
        
        if not embeddings_db:
            return {"error": "No embeddings available for search"}
        
        test_queries = [
            "cat", "dog", "car", "house", "tree", "person", "food", "water",
            "mountain", "sky", "flower", "animal", "building", "nature", "city",
            "sunset", "beach", "forest", "road", "bridge"
        ]
        
        # Start memory monitoring
        self.monitor.start_monitoring(interval=0.05)
        
        start_time = time.perf_counter()
        
        try:
            # Perform multiple searches
            search_results = []
            for i in range(query_count):
                query = test_queries[i % len(test_queries)]
                # Create a mock request object
                class MockRequest:
                    base_url = "http://localhost:8000/"
                
                results = search_images(query, MockRequest())
                search_results.append(len(results))
            
            end_time = time.perf_counter()
            
            # Stop monitoring
            time.sleep(0.2)
            self.monitor.stop_monitoring()
            
            memory_stats = self.monitor.get_stats()
            
            return {
                "test_name": f"Search Memory Usage ({query_count} queries)",
                "query_count": query_count,
                "search_time_seconds": end_time - start_time,
                "avg_results_per_query": sum(search_results) / len(search_results),
                "memory_stats": memory_stats,
                "status": "success"
            }
            
        except Exception as e:
            self.monitor.stop_monitoring()
            return {
                "test_name": "Search Memory Usage",
                "query_count": query_count,
                "status": "failed",
                "error": str(e)
            }
    
    async def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive memory benchmark"""
        print("🧠 Running comprehensive memory usage benchmark...")
        
        results = []
        
        # Get baseline memory
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"📊 Baseline memory usage: {baseline_memory:.1f} MB")
        
        # Test 1: Small dataset memory usage
        print("\n🧪 Test 1: Small dataset memory (25 images)")
        small_dir = self.create_test_images(25)
        result1 = await self.measure_indexing_memory(small_dir, "Small Dataset Memory (25 images)")
        results.append(result1)
        
        # Test 2: Medium dataset memory usage
        print("\n🧪 Test 2: Medium dataset memory (100 images)")
        medium_dir = self.create_test_images(100)
        result2 = await self.measure_indexing_memory(medium_dir, "Medium Dataset Memory (100 images)")
        results.append(result2)
        
        # Test 3: Large dataset memory usage
        print("\n🧪 Test 3: Large dataset memory (200 images)")
        large_dir = self.create_test_images(200)
        result3 = await self.measure_indexing_memory(large_dir, "Large Dataset Memory (200 images)")
        results.append(result3)
        
        # Test 4: High resolution images
        print("\n🧪 Test 4: High resolution images (50 images, 1024x1024)")
        hires_dir = self.create_test_images(50, size=(1024, 1024))
        result4 = await self.measure_indexing_memory(hires_dir, "High Resolution Memory (50 images)")
        results.append(result4)
        
        # Test 5: Search memory usage
        print("\n🧪 Test 5: Search operations memory usage")
        result5 = self.measure_search_memory(query_count=50)
        results.append(result5)
        
        # Calculate aggregate statistics
        successful_results = [r for r in results if r.get("status") == "success" and "memory_per_image_mb" in r]
        
        if successful_results:
            memory_per_image_values = [r["memory_per_image_mb"] for r in successful_results]
            peak_memory_values = [r["peak_memory_mb"] for r in successful_results]
            
            aggregate_stats = {
                "baseline_memory_mb": baseline_memory,
                "total_tests": len(results),
                "successful_tests": len(successful_results),
                "avg_memory_per_image_mb": sum(memory_per_image_values) / len(memory_per_image_values),
                "min_memory_per_image_mb": min(memory_per_image_values),
                "max_memory_per_image_mb": max(memory_per_image_values),
                "avg_peak_memory_mb": sum(peak_memory_values) / len(peak_memory_values),
                "max_peak_memory_mb": max(peak_memory_values),
                "estimated_capacity": {
                    "images_per_gb_ram": 1024 / (sum(memory_per_image_values) / len(memory_per_image_values)),
                    "images_for_4gb_ram": 4 * 1024 / (sum(memory_per_image_values) / len(memory_per_image_values)),
                    "images_for_8gb_ram": 8 * 1024 / (sum(memory_per_image_values) / len(memory_per_image_values))
                }
            }
        else:
            aggregate_stats = {"error": "No successful indexing tests"}
        
        return {
            "aggregate_stats": aggregate_stats,
            "individual_results": results
        }
    
    def print_results(self, results: Dict):
        """Print formatted benchmark results"""
        if not results or "error" in results.get("aggregate_stats", {}):
            print("❌ No successful benchmark results")
            return
        
        stats = results["aggregate_stats"]
        print("\n" + "="*60)
        print("🧠 MEMORY USAGE BENCHMARK RESULTS")
        print("="*60)
        
        print(f"📊 MEMORY EFFICIENCY:")
        print(f"   • Baseline Memory: {stats['baseline_memory_mb']:.1f} MB")
        print(f"   • Average Memory per Image: {stats['avg_memory_per_image_mb']:.2f} MB")
        print(f"   • Most Efficient: {stats['min_memory_per_image_mb']:.2f} MB per image")
        print(f"   • Peak Memory Usage: {stats['max_peak_memory_mb']:.1f} MB")
        print(f"   • Average Peak Memory: {stats['avg_peak_memory_mb']:.1f} MB")
        
        capacity = stats['estimated_capacity']
        print(f"\n📈 CAPACITY ESTIMATES:")
        print(f"   • Images per GB RAM: ~{capacity['images_per_gb_ram']:.0f} images")
        print(f"   • 4GB RAM Capacity: ~{capacity['images_for_4gb_ram']:.0f} images")
        print(f"   • 8GB RAM Capacity: ~{capacity['images_for_8gb_ram']:.0f} images")
        
        print(f"\n🔥 KEY RESUME METRICS:")
        print(f"   • Efficient {stats['avg_memory_per_image_mb']:.1f}MB memory per image")
        print(f"   • Can handle {capacity['images_for_4gb_ram']:.0f}+ images on 4GB RAM")
        print(f"   • Peak memory usage under {stats['max_peak_memory_mb']:.0f}MB")
        print(f"   • Scales to {capacity['images_for_8gb_ram']:.0f}+ images on standard hardware")
        
        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for result in results["individual_results"]:
            if result.get("status") == "success":
                if "memory_per_image_mb" in result:
                    print(f"   • {result['test_name']}: {result['memory_per_image_mb']:.2f} MB/image (Peak: {result['peak_memory_mb']:.1f} MB)")
                else:
                    memory_stats = result.get('memory_stats', {}).get('rss_stats', {})
                    if memory_stats:
                        print(f"   • {result['test_name']}: Peak {memory_stats.get('peak_mb', 0):.1f} MB")
            else:
                print(f"   • {result['test_name']}: FAILED - {result.get('error', 'Unknown error')}")

def main():
    benchmark = MemoryBenchmark()
    
    try:
        print("Starting memory usage benchmark...")
        print("This will measure RAM consumption during image processing\n")
        
        # Check available memory
        available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024
        print(f"💾 Available system memory: {available_memory:.1f} GB")
        
        if available_memory < 2:
            print("⚠️  Warning: Low available memory. Results may be affected.")
        
        # Run the benchmark
        results = asyncio.run(benchmark.run_comprehensive_benchmark())
        
        # Print results
        benchmark.print_results(results)
        
        # Save results to file
        with open("memory_benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: memory_benchmark_results.json")
        
    finally:
        # Clean up temporary directories
        benchmark.cleanup()

if __name__ == "__main__":
    main()