# Performance Optimization Plan

## Current Performance Metrics

### Bottleneck Analysis (from code review):
- **screenshot():** 20-50ms per frame (PRIMARY BOTTLENECK)
- **PIL decode:** 5-10ms per frame (SECONDARY)
- **RGB conversion:** 2-5ms per frame
- **VideoFrame creation:** 3-5ms per frame
- **Total:** 30-70ms = **14-33 FPS actual** (not 60 FPS configured)

### Capacity Limits:
- **Current:** 10 sessions max
- **RAM per session:** 250-600MB
- **Available RAM:** 13.55GB
- **Theoretical capacity:** 20-40 sessions with current RAM

## 🔥 HIGH IMPACT Optimizations

### 1. CDP Screencast (10x+ improvement) ⭐⭐⭐⭐⭐
**Impact:** Reduce frame capture from 20-50ms to 3-5ms
**Expected Result:** Achieve 60+ FPS easily

**Implementation:**
```python
# Replace Playwright screenshot() with CDP Page.startScreencast()
# Current: browser_pool.py line 203-211
async def get_frame_cdp(self, session_id: str):
    session = self.sessions[session_id]
    # Use CDP screencast API
    frame = await session['cdp'].Page.captureScreenshot(format='jpeg', quality=85)
    return base64.b64decode(frame['data'])
```

**Benefits:**
- Direct JPEG/PNG from browser rendering engine
- No filesystem operations
- Hardware-accelerated encoding
- Minimal CPU overhead

**Effort:** Medium (2-3 hours)
**Risk:** Low (CDP is stable)

### 2. Hardware Acceleration ⭐⭐⭐⭐
**Impact:** 20-30% performance improvement + reduce CPU load

**Implementation:**
```yaml
# docker-compose.webrtc-no-volumes.yml
services:
  webrtc-renderer:
    devices:
      - /dev/dri:/dev/dri  # GPU access
    environment:
      - CHROMIUM_FLAGS=--enable-accelerated-video-decode --enable-gpu-rasterization --use-gl=egl
```

**Dockerfile additions:**
```dockerfile
# Install VA-API drivers
RUN apt-get update && apt-get install -y \
    vainfo \
    intel-media-va-driver-non-free \
    mesa-va-drivers
```

**Effort:** Low (30 minutes)
**Risk:** Low (fallback to software rendering)

### 3. Frame Buffering & Skip Logic ⭐⭐⭐⭐
**Impact:** Maintain steady FPS even under load

**Implementation:**
```python
# video_track.py: Add frame buffer queue
from collections import deque

class BrowserVideoTrack(VideoStreamTrack):
    def __init__(self, ...):
        self.frame_buffer = deque(maxlen=2)  # Keep only latest 2 frames
        
    async def recv(self):
        # Skip frames if behind schedule
        if len(self.frame_buffer) > 1:
            logger.warning(f"Skipping {len(self.frame_buffer) - 1} frames")
            # Take only latest frame
            self.frame_buffer.clear()
```

**Effort:** Low (1 hour)
**Risk:** Low (improves stability)

## 🔧 MEDIUM IMPACT Optimizations

### 4. Optimize Image Pipeline ⭐⭐⭐
**Impact:** 5-10ms reduction per frame

**Replace PIL with numpy:**
```python
# video_track.py lines 81-88: Remove PIL dependency
import numpy as np

# Direct numpy array from JPEG
img_array = np.frombuffer(screenshot_data, dtype=np.uint8)
frame = VideoFrame.from_ndarray(img_array, format="rgb24")
```

**Effort:** Medium (2 hours)
**Risk:** Medium (need to validate color space)

### 5. Parallel Frame Capture ⭐⭐⭐
**Impact:** Support more concurrent sessions

**Implementation:**
```python
# browser_pool.py: Add worker pool
from concurrent.futures import ThreadPoolExecutor

self.screenshot_pool = ThreadPoolExecutor(max_workers=4)

async def get_frame_parallel(self, session_id: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        self.screenshot_pool,
        self._screenshot_sync,
        session_id
    )
```

**Effort:** Medium (2 hours)
**Risk:** Medium (thread safety concerns)

### 6. Reduce Browser Overhead ⭐⭐
**Impact:** Lower memory per session (250MB → 150MB)

**Additional Chromium flags:**
```python
# browser_pool.py: Add to browser args
"--disable-features=TranslateUI",
"--disable-background-networking",
"--disable-sync",
"--disable-extensions",
"--disable-component-extensions-with-background-pages",
"--blink-settings=imagesEnabled=false",  # For non-interactive sessions
```

**Effort:** Low (15 minutes)
**Risk:** Low (may affect some websites)

## 📊 LOW IMPACT Optimizations

### 7. Increase Workers ⭐⭐
**Current:** 2 workers in config.py
**Recommendation:** 4-8 workers (match CPU cores)

**Effort:** 5 minutes
**Risk:** None

### 8. Dynamic Bitrate Adjustment ⭐
**Current:** Fixed bitrate range
**Recommendation:** Adjust based on network conditions

**Effort:** High (4+ hours)
**Risk:** High (complex WebRTC logic)

## 🎯 Capacity Scaling Plan

### Phase 1: Test Current Limits (IMMEDIATE)
```python
# config.py: Increase to 20 sessions
browser_max_sessions: int = 20
max_concurrent_sessions: int = 20
```

**Monitor with:**
```bash
watch -n 1 'docker stats --no-stream'
curl http://localhost:8000/api/info
```

### Phase 2: Optimize for 50 Sessions (1-2 weeks)
**Requirements:**
- CDP screencast implementation (10x FPS improvement)
- Hardware acceleration enabled
- Frame buffering implemented
- Optimized image pipeline
- Session hibernation (pause inactive sessions)

**Expected RAM:** 50 sessions × 200MB = **10GB** (with optimizations)

### Phase 3: Scale to 100+ Sessions (1-2 months)
**Requirements:**
- Dedicated GPU server
- 16+ CPU cores
- 32GB+ RAM
- Redis for distributed state
- Load balancer
- Multiple renderer instances

## 🚦 Implementation Roadmap

### Quick Wins (Today - 2 hours):
1. ✅ Increase session limit: 10 → 20
2. ✅ Increase workers: 2 → 4
3. ✅ Add hardware acceleration flags
4. ✅ Add frame skip logic

### High Impact (This Week - 1-2 days):
1. 🎯 Implement CDP screencast (biggest FPS boost)
2. 🎯 Optimize image pipeline (remove PIL)
3. 🎯 Add frame buffering

### Medium Impact (Next Week - 3-5 days):
1. Parallel frame capture
2. Session hibernation
3. Monitoring & metrics

### Long Term (Next Month):
1. Multi-instance deployment
2. Redis distributed state
3. Load balancing
4. Auto-scaling

## 📈 Expected Results

### After Quick Wins:
- FPS: 14-33 → 20-40 (30% improvement)
- Sessions: 10 → 20 (2x capacity)
- CPU: Better utilization with 4 workers

### After High Impact:
- FPS: 20-40 → 60+ (3x improvement)
- CPU: 50% reduction with hardware acceleration
- Sessions: 20 → 40 (4x capacity)
- Latency: <50ms end-to-end

### After Medium Impact:
- Sessions: 40 → 50 (5x capacity)
- Stability: No frame drops under load
- Monitoring: Real-time metrics

## 🛠️ Testing Strategy

### Load Testing Script:
```bash
# tests/load_test.sh
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/session/create \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"load-test-$i\"}" &
done
wait
```

### Monitor Resources:
```bash
# Check every second
watch -n 1 'docker stats --no-stream && echo "" && curl -s http://localhost:8000/api/info'
```

### FPS Benchmark:
```python
# tests/benchmark_fps.py
import time
import asyncio
from renderer.browser_pool import BrowserPool

async def benchmark():
    pool = BrowserPool()
    await pool.create_session("bench")
    
    frames = 0
    start = time.time()
    
    for _ in range(100):
        await pool.get_frame("bench")
        frames += 1
    
    duration = time.time() - start
    print(f"Average FPS: {frames / duration:.2f}")
```

## 💡 Recommendations

### For 60 FPS Streaming:
1. **MUST HAVE:** CDP screencast (replaces screenshot())
2. **SHOULD HAVE:** Hardware acceleration
3. **NICE TO HAVE:** Frame buffering

### For 50+ Sessions:
1. **MUST HAVE:** Optimized image pipeline (numpy)
2. **SHOULD HAVE:** Session hibernation
3. **NICE TO HAVE:** Multiple renderer instances

### For Production Deployment:
1. **MUST HAVE:** Monitoring & alerts
2. **SHOULD HAVE:** Auto-scaling
3. **NICE TO HAVE:** Multi-region deployment

## 🎬 Next Steps

**IMMEDIATE (choose one):**
- [ ] Implement CDP screencast (biggest FPS impact)
- [ ] Increase session limit to 20 (test capacity)
- [ ] Enable hardware acceleration (reduce CPU)

**Which optimization should we implement first?**
