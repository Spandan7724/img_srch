# Image Search Benchmark Suite

Comprehensive performance benchmarking tools for the image search application.

## Overview

This benchmark suite measures key performance metrics across four critical areas:

1. **Search Response Time** - API response latency for search queries
2. **Indexing Speed** - Image processing and embedding extraction throughput
3. **Memory Usage** - RAM consumption during indexing and searching
4. **Concurrent Load** - Multi-user performance and WebSocket capabilities

## Quick Start

### Prerequisites

1. **Start the backend server:**
   ```bash
   cd ../server
   uvicorn server.main:app --reload
   ```

2. **Install benchmark dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure you have some images indexed** (place images in `server/data/` or use the API to index a folder)

### Run All Benchmarks

```bash
# Full benchmark suite (takes 5-10 minutes)
python run_all_benchmarks.py

# Quick mode (reduced iterations, takes 2-3 minutes)
python run_all_benchmarks.py --quick
```

### Run Individual Benchmarks

```bash
# Search response time only
python search_benchmark.py

# Indexing speed only
python indexing_benchmark.py

# Memory usage only
python memory_benchmark.py

# Concurrent load testing only
python concurrent_benchmark.py
```

## Benchmark Details

### 1. Search Benchmark (`search_benchmark.py`)
- Tests 15 different query types
- Measures response time, success rate, and result confidence
- Generates statistics: avg/min/max/95th percentile response times
- **Key Metrics:** Sub-Xms response times, Y% success rate

### 2. Indexing Benchmark (`indexing_benchmark.py`)
- Tests different dataset sizes (10, 50, 100, 200+ images)
- Measures processing speed (images/second)
- Tests both synthetic and real image datasets
- **Key Metrics:** X images/second processing speed, peak throughput

### 3. Memory Benchmark (`memory_benchmark.py`)
- Monitors RAM usage during indexing operations
- Tests different image sizes and quantities
- Calculates memory efficiency (MB per image)
- **Key Metrics:** X MB per image, handles Y images on 4GB RAM

### 4. Concurrent Benchmark (`concurrent_benchmark.py`)
- Tests multiple simultaneous users (1-50 concurrent)
- Progressive load testing
- WebSocket connection testing
- **Key Metrics:** Handles X concurrent users, Y requests/second peak

## Output Files

After running benchmarks, you'll get:

- `comprehensive_benchmark_results.json` - Full detailed results
- `resume_metrics.json` - Key metrics formatted for resume use
- Individual result files for each benchmark

## Sample Resume Metrics

The benchmark suite generates ready-to-use resume metrics like:

```
• Engineered high-performance image search system with sub-150ms average search response time
• Built scalable FastAPI backend processing 45+ images/second with real-time WebSocket notifications  
• Deployed cross-platform solution supporting 30+ concurrent users with efficient memory usage (2000+ images on 4GB RAM)
• Implemented CLIP-based embedding pipeline with 95%+ search accuracy across 4 image formats
```

## Troubleshooting

### Server Not Responding
```
❌ Server not responding at http://localhost:8000
```
**Solution:** Start the backend server with `uvicorn server.main:app --reload`

### No Images Found
```
❌ No images found for indexing
```
**Solution:** Add images to `server/data/` or use the web interface to index a folder

### Import Errors
```
❌ ModuleNotFoundError: No module named 'aiohttp'
```
**Solution:** Install dependencies with `pip install -r requirements.txt`

### Memory Errors
```
⚠️ Warning: Low available memory. Results may be affected.
```
**Solution:** Close other applications or run with `--quick` mode

## Understanding Results

### Response Time Metrics
- **Sub-200ms:** Excellent (real-time feel)
- **200-500ms:** Good (responsive)
- **500ms+:** Needs optimization

### Throughput Metrics
- **20+ images/second:** Good for real-time indexing
- **50+ images/second:** Excellent performance
- **100+ images/second:** Outstanding (GPU-accelerated level)

### Memory Efficiency
- **<5MB per image:** Excellent efficiency
- **5-10MB per image:** Good efficiency
- **>10MB per image:** Consider optimization

### Concurrent Performance
- **10+ users:** Good for personal/small team use
- **25+ users:** Good for department/organization
- **50+ users:** Excellent scalability

## Customization

### Adding New Test Queries
Edit `CONCURRENT_TEST_QUERIES` in `concurrent_benchmark.py`:
```python
CONCURRENT_TEST_QUERIES = [
    "your custom query",
    "another test query",
    # ... more queries
]
```

### Adjusting Test Parameters
Modify test parameters in individual benchmark files:
- Image counts in `create_test_images(count=100)`
- Concurrent user counts in `concurrent_search_test(concurrent_users=30)`
- Memory monitoring intervals in `start_monitoring(interval=0.1)`

### Custom Output Formats
The master benchmark generates JSON output that can be processed for:
- CSV exports for spreadsheet analysis
- Custom report formats
- Integration with monitoring systems

## Performance Targets

Based on modern web application standards:

| Metric | Good | Excellent | Outstanding |
|--------|------|-----------|-------------|
| Search Response | <300ms | <150ms | <100ms |
| Indexing Speed | 20+ img/sec | 50+ img/sec | 100+ img/sec |
| Memory Usage | <8MB/img | <5MB/img | <3MB/img |
| Concurrent Users | 10+ | 25+ | 50+ |
| Success Rate | 95%+ | 98%+ | 99%+ |

Use these targets to evaluate your system's performance and identify optimization opportunities.