#!/usr/bin/env python3
"""
Indexing Speed Benchmark
Measures how fast the system can process and index images
"""

import os
import sys
import time
import statistics
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List
import requests
from PIL import Image
import numpy as np

# Add server directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from services.embeddings import index_folder_async, embeddings_db, count_images_in_folder
import asyncio

BASE_URL = "http://localhost:8000"

class IndexingBenchmark:
    def __init__(self):
        self.results = []
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
        temp_dir = tempfile.mkdtemp(prefix="img_bench_")
        self.temp_dirs.append(temp_dir)
        
        print(f"Creating {count} test images in {temp_dir}...")
        
        for i in range(count):
            # Create random colored image
            img_array = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            # Save with different formats
            formats = ['jpg', 'png', 'jpeg', 'webp']
            format_choice = formats[i % len(formats)]
            
            filename = f"test_image_{i:04d}.{format_choice}"
            filepath = os.path.join(temp_dir, filename)
            
            if format_choice == 'webp':
                img.save(filepath, 'WEBP')
            else:
                img.save(filepath)
        
        return temp_dir
    
    def copy_existing_images(self, source_dir: str, target_dir: str = None) -> str:
        """Copy existing images to a test directory"""
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="img_bench_existing_")
            self.temp_dirs.append(target_dir)
        
        copied_count = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(target_dir, f"copy_{copied_count:04d}_{file}")
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_count += 1
                    except Exception as e:
                        print(f"Error copying {src_path}: {e}")
        
        print(f"Copied {copied_count} existing images to {target_dir}")
        return target_dir
    
    async def measure_indexing_speed(self, folder_path: str, test_name: str) -> Dict:
        """Measure indexing speed for a folder"""
        print(f"\n📂 Testing indexing speed: {test_name}")
        
        # Count images first
        image_count = count_images_in_folder(folder_path)
        print(f"   Images to process: {image_count}")
        
        if image_count == 0:
            return {"error": "No images found"}
        
        # Clear existing embeddings
        embeddings_db.clear()
        
        # Measure indexing time
        start_time = time.perf_counter()
        
        try:
            await index_folder_async(folder_path)
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            images_per_second = image_count / total_time
            time_per_image = total_time / image_count
            
            return {
                "test_name": test_name,
                "folder_path": folder_path,
                "total_images": image_count,
                "total_time_seconds": total_time,
                "images_per_second": images_per_second,
                "milliseconds_per_image": time_per_image * 1000,
                "status": "success",
                "embeddings_created": len(embeddings_db)
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "test_name": test_name,
                "folder_path": folder_path,
                "total_images": image_count,
                "total_time_seconds": end_time - start_time,
                "status": "failed",
                "error": str(e)
            }
    
    def test_server_indexing_api(self, folder_path: str) -> Dict:
        """Test indexing through the API endpoint"""
        image_count = count_images_in_folder(folder_path)
        
        start_time = time.perf_counter()
        
        try:
            response = requests.post(
                f"{BASE_URL}/folders",
                json={"folder": folder_path},
                timeout=300  # 5 minute timeout
            )
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            
            if response.status_code == 200:
                return {
                    "test_name": "API Indexing",
                    "total_images": image_count,
                    "total_time_seconds": total_time,
                    "images_per_second": image_count / total_time,
                    "status": "success",
                    "api_response": response.json()
                }
            else:
                return {
                    "test_name": "API Indexing",
                    "total_images": image_count,
                    "total_time_seconds": total_time,
                    "status": "failed",
                    "error_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "test_name": "API Indexing",
                "total_images": image_count,
                "total_time_seconds": end_time - start_time,
                "status": "failed",
                "error": str(e)
            }
    
    async def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive indexing benchmark with different scenarios"""
        print("🏃‍♂️ Running comprehensive indexing speed benchmark...")
        
        results = []
        
        # Test 1: Small dataset (10 images)
        print("\n🧪 Test 1: Small dataset (10 images)")
        small_dir = self.create_test_images(10)
        result1 = await self.measure_indexing_speed(small_dir, "Small Dataset (10 images)")
        results.append(result1)
        
        # Test 2: Medium dataset (50 images)
        print("\n🧪 Test 2: Medium dataset (50 images)")
        medium_dir = self.create_test_images(50)
        result2 = await self.measure_indexing_speed(medium_dir, "Medium Dataset (50 images)")
        results.append(result2)
        
        # Test 3: Large dataset (100 images)
        print("\n🧪 Test 3: Large dataset (100 images)")
        large_dir = self.create_test_images(100)
        result3 = await self.measure_indexing_speed(large_dir, "Large Dataset (100 images)")
        results.append(result3)
        
        # Test 4: Existing images from server/data
        server_data_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'data')
        if os.path.exists(server_data_path):
            existing_count = count_images_in_folder(server_data_path)
            if existing_count > 0:
                print(f"\n🧪 Test 4: Existing images ({existing_count} images)")
                result4 = await self.measure_indexing_speed(server_data_path, f"Existing Dataset ({existing_count} images)")
                results.append(result4)
        
        # Calculate aggregate statistics
        successful_results = [r for r in results if r.get("status") == "success"]
        
        if successful_results:
            images_per_second_values = [r["images_per_second"] for r in successful_results]
            ms_per_image_values = [r["milliseconds_per_image"] for r in successful_results]
            
            aggregate_stats = {
                "total_tests": len(results),
                "successful_tests": len(successful_results),
                "total_images_processed": sum(r["total_images"] for r in successful_results),
                "avg_images_per_second": statistics.mean(images_per_second_values),
                "max_images_per_second": max(images_per_second_values),
                "min_images_per_second": min(images_per_second_values),
                "avg_ms_per_image": statistics.mean(ms_per_image_values),
                "min_ms_per_image": min(ms_per_image_values),
                "max_ms_per_image": max(ms_per_image_values)
            }
        else:
            aggregate_stats = {"error": "No successful tests"}
        
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
        print("⚡ INDEXING SPEED BENCHMARK RESULTS")
        print("="*60)
        
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   • Total Tests: {stats['total_tests']}")
        print(f"   • Successful Tests: {stats['successful_tests']}")
        print(f"   • Total Images Processed: {stats['total_images_processed']}")
        print(f"   • Average Processing Speed: {stats['avg_images_per_second']:.1f} images/second")
        print(f"   • Peak Processing Speed: {stats['max_images_per_second']:.1f} images/second")
        print(f"   • Average Time per Image: {stats['avg_ms_per_image']:.1f} ms")
        print(f"   • Fastest Time per Image: {stats['min_ms_per_image']:.1f} ms")
        
        print(f"\n🔥 KEY RESUME METRICS:")
        print(f"   • Processes {stats['avg_images_per_second']:.0f}+ images per second")
        print(f"   • Peak throughput: {stats['max_images_per_second']:.0f} images/second")
        print(f"   • Sub-{stats['min_ms_per_image']:.0f}ms per image processing time")
        print(f"   • Successfully indexed {stats['total_images_processed']} images")
        
        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for result in results["individual_results"]:
            if result.get("status") == "success":
                print(f"   • {result['test_name']}: {result['images_per_second']:.1f} img/sec ({result['total_images']} images)")
            else:
                print(f"   • {result['test_name']}: FAILED - {result.get('error', 'Unknown error')}")

def main():
    benchmark = IndexingBenchmark()
    
    try:
        print("Starting indexing speed benchmark...")
        print("This will test the image embedding extraction speed\n")
        
        # Run the benchmark
        results = asyncio.run(benchmark.run_comprehensive_benchmark())
        
        # Print results
        benchmark.print_results(results)
        
        # Save results to file
        with open("indexing_benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: indexing_benchmark_results.json")
        
    finally:
        # Clean up temporary directories
        benchmark.cleanup()

if __name__ == "__main__":
    main()