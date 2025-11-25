# WebRTC WebApp Architecture

## Overview

This document provides a comprehensive explanation of the WebRTC WebApp architecture, focusing on **why WebSocket and WebRTC are used together** in the same technology stack.

## The Key Question: Why Both WebSocket AND WebRTC?

**Short Answer**: WebSocket is used for **signaling** (control channel), while WebRTC is used for **media streaming** (data channel). They serve complementary purposes - WebSocket establishes and manages the connection, WebRTC delivers the actual video stream.

## Technology Stack Roles

### 1. WebSocket - The "Handshake" (Signaling)

WebSocket handles the **signaling process** which is essential for WebRTC to work:

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Signaling Flow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Client                         Server                          │
│      │                              │                            │
│      │──── 1. WS Connect ──────────>│  WebSocket connection     │
│      │                              │                            │
│      │──── 2. Join Session ─────────>│  Request to join          │
│      │                              │                            │
│      │<─── 3. SDP Offer ────────────│  Server sends WebRTC offer │
│      │                              │                            │
│      │──── 4. SDP Answer ───────────>│  Client sends answer       │
│      │                              │                            │
│      │<──> 5. ICE Candidates ──────>│  NAT traversal info        │
│      │                              │                            │
│      │<─── 6. Ready ────────────────│  Signaling complete        │
│      │                              │                            │
│      │──── 7. Ping/Pong ───────────>│  Keep-alive heartbeat      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Why WebSocket for Signaling?**

1. **WebRTC requires signaling**: WebRTC does NOT have a built-in signaling mechanism. It needs an external channel to exchange:
   - **SDP (Session Description Protocol)** offers and answers
   - **ICE (Interactive Connectivity Establishment)** candidates for NAT traversal

2. **Reliable bidirectional communication**: WebSocket provides guaranteed message delivery which is critical for signaling - you can't miss an SDP offer or ICE candidate.

3. **Always connected**: WebSocket maintains a persistent connection that can be used for keep-alive pings and session management.

### 2. WebRTC - The "Media Stream" (Video)

WebRTC handles the actual **video streaming**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebRTC Media Stream Flow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Browser Pool                WebRTC                  Client     │
│   (Playwright)                Renderer                           │
│       │                          │                        │      │
│       │── Screenshot (PNG) ─────>│                        │      │
│       │                          │                        │      │
│       │                    Convert to Video Frame         │      │
│       │                    (av.VideoFrame)                │      │
│       │                          │                        │      │
│       │                    H.264 Encoding                 │      │
│       │                    (aiortc)                       │      │
│       │                          │                        │      │
│       │                          │──── RTP/SRTP ────────>│      │
│       │                          │    (WebRTC Stream)     │      │
│       │                          │                        │      │
│       │                          │<─── DataChannel ──────│      │
│       │                          │    (Input Events)      │      │
│                                                                  │
│   30 FPS Loop: Screenshots → Frames → H.264 → WebRTC Stream     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Why WebRTC for Media Streaming?**

1. **Ultra-low latency**: WebRTC uses UDP-based transport (RTP/SRTP) designed for real-time media, achieving <50ms latency vs 100ms+ for WebSocket.

2. **H.264 codec support**: Native video codec support with hardware acceleration on both server (encoding) and client (decoding).

3. **Adaptive bitrate**: Automatic bandwidth estimation and bitrate adjustment.

4. **DataChannel for input**: WebRTC DataChannel provides low-latency bidirectional communication for mouse/touch events.

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        webrtc_webapp Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                    Android/Web Client (Port 9000)                     │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  index.html - App Launcher (Material Design 3)                 │  │  │
│   │  │  - Popular website shortcuts (YouTube, Facebook, etc.)         │  │  │
│   │  │  - Custom URL input                                            │  │  │
│   │  │  - Progressive Web App (PWA) capable                           │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  viewer.html - WebRTC Viewer                                   │  │  │
│   │  │  - <video> element for WebRTC stream                           │  │  │
│   │  │  - Touch/mouse event handlers                                  │  │  │
│   │  │  - Connection status UI                                        │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  webrtc-client.js - JavaScript Client                          │  │  │
│   │  │                                                                 │  │  │
│   │  │  ┌───────────────────┐      ┌────────────────────────────────┐│  │  │
│   │  │  │  WebSocket Client │      │  RTCPeerConnection             ││  │  │
│   │  │  │                   │      │                                ││  │  │
│   │  │  │  - connect()      │      │  - createAnswer()              ││  │  │
│   │  │  │  - join session   │      │  - setRemoteDescription()      ││  │  │
│   │  │  │  - send answer    │      │  - ontrack (video stream)      ││  │  │
│   │  │  │  - ICE candidates │      │  - ondatachannel (input)       ││  │  │
│   │  │  │  - ping/pong      │      │  - addIceCandidate()           ││  │  │
│   │  │  └───────────────────┘      └────────────────────────────────┘│  │  │
│   │  │         ↓                              ↑                       │  │  │
│   │  │    Signaling                      Media Stream                 │  │  │
│   │  └─────────│─────────────────────────────│────────────────────────┘  │  │
│   └────────────│─────────────────────────────│───────────────────────────┘  │
│                │                             │                               │
│                │ WebSocket                   │ WebRTC (UDP)                  │
│                │ (TCP, reliable)             │ (Low latency, H.264)          │
│                │                             │                               │
│   ┌────────────▼─────────────────────────────▼───────────────────────────┐  │
│   │                 WebRTC Renderer (Port 8000)                           │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  main.py - FastAPI Application                                  │  │  │
│   │  │                                                                 │  │  │
│   │  │  REST API Endpoints:                                            │  │  │
│   │  │  ├── GET  /health                 - Health check                │  │  │
│   │  │  ├── GET  /api/info               - Service info                │  │  │
│   │  │  ├── POST /api/session/create     - Create browser session      │  │  │
│   │  │  ├── POST /api/session/{id}/load  - Load URL                    │  │  │
│   │  │  ├── DELETE /api/session/{id}     - Close session               │  │  │
│   │  │  └── GET  /api/sessions           - List sessions               │  │  │
│   │  │                                                                 │  │  │
│   │  │  WebSocket Endpoint:                                            │  │  │
│   │  │  └── WS /ws/signaling             - WebRTC signaling            │  │  │
│   │  │       ├── "join"        → Create WebRTC peer, send offer        │  │  │
│   │  │       ├── "answer"      → Set remote description                │  │  │
│   │  │       ├── "ice-candidate" → Add ICE candidate                   │  │  │
│   │  │       └── "ping/pong"   → Keep-alive                            │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  webrtc_manager.py - WebRTC Peer Management                     │  │  │
│   │  │                                                                 │  │  │
│   │  │  class WebRTCPeer:                                              │  │  │
│   │  │  ├── RTCPeerConnection (aiortc)                                 │  │  │
│   │  │  ├── BrowserVideoTrack (custom video track)                     │  │  │
│   │  │  ├── DataChannel for input events                               │  │  │
│   │  │  ├── ICE servers configuration (STUN/TURN)                      │  │  │
│   │  │  └── create_offer() / set_answer() / add_ice_candidate()        │  │  │
│   │  │                                                                 │  │  │
│   │  │  class WebRTCManager:                                           │  │  │
│   │  │  └── Manages all peer connections                               │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  video_track.py - Browser Video Streaming                       │  │  │
│   │  │                                                                 │  │  │
│   │  │  class BrowserVideoTrack(VideoStreamTrack):                     │  │  │
│   │  │  ├── Captures screenshots from browser (30 FPS)                 │  │  │
│   │  │  ├── Converts PNG → PIL Image → av.VideoFrame                   │  │  │
│   │  │  ├── Rate limiting to maintain target FPS                       │  │  │
│   │  │  └── recv() method called by WebRTC for each frame              │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   │  ┌────────────────────────────────────────────────────────────────┐  │  │
│   │  │  browser_pool.py - Playwright Browser Management                │  │  │
│   │  │                                                                 │  │  │
│   │  │  class BrowserPool:                                             │  │  │
│   │  │  ├── Manages Chromium browser instances (Playwright)            │  │  │
│   │  │  ├── create_session() - New browser context + page              │  │  │
│   │  │  ├── navigate() - Load URLs                                     │  │  │
│   │  │  ├── screenshot() - Capture page screenshot                     │  │  │
│   │  │  ├── click() / scroll() / type_text() - Input handling          │  │  │
│   │  │  └── cleanup_stale_sessions() - Session timeout                 │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Complete Connection Flow

### Step-by-Step: User Opens YouTube

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Complete Connection Flow Example                         │
├─────────────────────────────────────────────────────────────────────────────┤

1. USER ACTION: Clicks "YouTube" icon in webrtc_webapp (index.html)
   └─> Redirects to /viewer?url=https://m.youtube.com

2. REST API: Create browser session
   └─> fetch(WEBRTC_SERVER/api/session/create)
   └─> Response: { session_id: "abc123" }

3. REST API: Load URL in browser session
   └─> fetch(WEBRTC_SERVER/api/session/abc123/load, { url: "https://m.youtube.com" })
   └─> Server: browser_pool.navigate("abc123", "https://m.youtube.com")
   └─> Playwright opens YouTube in headless Chromium

4. WEBSOCKET: Connect for signaling
   └─> new WebSocket("ws://server:8000/ws/signaling")
   └─> Server: websocket.accept(), peer_id = uuid4()

5. WEBSOCKET: Join session
   └─> Client sends: { type: "join", session_id: "abc123" }
   └─> Server: webrtc_manager.create_peer("abc123", peer_id)
   └─> Server: Creates RTCPeerConnection, BrowserVideoTrack, DataChannel

6. WEBRTC SIGNALING: Server sends offer
   └─> Server: peer.create_offer()
   └─> Server sends via WebSocket: { type: "offer", offer: { sdp: "...", type: "offer" } }
   └─> Client: pc.setRemoteDescription(offer)
   └─> Client: pc.createAnswer()
   └─> Client sends via WebSocket: { type: "answer", answer: { sdp: "...", type: "answer" } }
   └─> Server: peer.set_answer(answer)

7. ICE CANDIDATES EXCHANGE (via WebSocket)
   └─> Client: pc.onicecandidate → Send to server
   └─> Server: peer.add_ice_candidate(candidate)
   └─> NAT traversal negotiation complete

8. WEBRTC: Video stream starts
   └─> Client: pc.ontrack → video.srcObject = stream
   └─> Server: video_track.recv() called 30 times/second
       ├─> browser_pool.screenshot("abc123") → PNG bytes
       ├─> PIL.Image.open(PNG) → RGB image
       ├─> VideoFrame.from_image(img) → av.VideoFrame
       └─> Frame streamed via WebRTC (H.264 encoded)

9. USER INPUT: Touch/Click on video
   └─> Client: click event → calculate coordinates
   └─> Client: dataChannel.send({ type: "click", x: 100, y: 200 })
   └─> Server: peer._handle_data_channel_message(message)
   └─> Server: browser_pool.click("abc123", 100, 200)
   └─> Playwright: page.mouse.click(100, 200)
   └─> YouTube responds to click in next frame

10. KEEP-ALIVE: Ping/Pong (every 30 seconds)
    └─> Client: ws.send({ type: "ping" })
    └─> Server: ws.send({ type: "pong" })

11. SESSION END: User navigates away
    └─> Client: client.disconnect()
    └─> Client: fetch(DELETE /api/session/abc123)
    └─> Server: webrtc_manager.close_peer(peer_id)
    └─> Server: browser_pool.close_session("abc123")
    └─> Chromium browser closes

└─────────────────────────────────────────────────────────────────────────────┘
```

## Code Location Reference

### Client-Side (webrtc_webapp/)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `app.py` | FastAPI webapp server | Routes for `/`, `/viewer`, `/health` |
| `templates/index.html` | App launcher UI | Material Design grid, URL input |
| `templates/viewer.html` | WebRTC viewer | `<video>` element, input handlers, `init()` |
| `static/webrtc-client.js` | WebRTC client library | `JiomosaWebRTCClient` class |

### Server-Side (webrtc_renderer/)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `main.py` | FastAPI application | REST endpoints, WebSocket `/ws/signaling` |
| `webrtc_manager.py` | WebRTC peer management | `WebRTCPeer`, `WebRTCManager` |
| `video_track.py` | Video frame streaming | `BrowserVideoTrack.recv()` |
| `browser_pool.py` | Browser automation | `BrowserPool.screenshot()`, `.click()` |
| `config.py` | Configuration settings | `Settings` pydantic model |

## Why Not Just WebSocket OR Just WebRTC?

### WebSocket-Only Approach (Previous Architecture)

The original Jiomosa used WebSocket for everything:

**Pros**:
- Simple, works everywhere, reliable delivery

**Cons**:
- Higher latency (~100ms+ due to TCP)
- No hardware video codec support (JPEG frames)
- Higher bandwidth (JPEG 2-5 Mbps vs H.264 1-2 Mbps)
- Higher CPU usage (software decoding)

### WebRTC-Only Approach

Using WebRTC DataChannels for signaling:

- **Problem**: WebRTC requires SDP/ICE exchange BEFORE the connection is established
- **Chicken-and-egg problem**: Can't use DataChannel to exchange offers/answers because DataChannel doesn't exist yet
- **Solution**: External signaling channel (WebSocket) is required

### Current Hybrid Approach (Best of Both)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Technology Comparison                         │
├─────────────────┬─────────────────┬────────────────────────────┤
│ Feature         │ WebSocket       │ WebRTC                     │
├─────────────────┼─────────────────┼────────────────────────────┤
│ Transport       │ TCP             │ UDP (RTP/SRTP)             │
│ Latency         │ ~100ms          │ <50ms                      │
│ Reliability     │ Guaranteed      │ Best-effort (video)        │
│ Video Codec     │ JPEG (software) │ H.264 (hardware)           │
│ Bandwidth       │ 2-5 Mbps        │ 0.5-3 Mbps (adaptive)      │
│ NAT Traversal   │ N/A             │ ICE/STUN/TURN              │
│ Use in Jiomosa  │ Signaling only  │ Video + Input              │
└─────────────────┴─────────────────┴────────────────────────────┘
```

## Data Channel Usage

WebRTC DataChannel is used for **input events** (click, scroll, text):

```javascript
// Client sends input via DataChannel
dataChannel.send(JSON.stringify({
    type: 'click',
    x: 100,
    y: 200
}));
```

```python
# Server receives and processes input
async def _handle_data_channel_message(self, message: str):
    data = json.loads(message)
    if data.get('type') == 'click':
        await browser_pool.click(self.session_id, data['x'], data['y'])
```

**Why DataChannel instead of WebSocket for input?**
- Lower latency (UDP vs TCP)
- Already established as part of WebRTC connection
- Avoids adding more load to WebSocket

## Summary

| Component | Protocol | Purpose | Location |
|-----------|----------|---------|----------|
| REST API | HTTP | Session management (create, load, close) | `main.py` |
| Signaling | WebSocket | SDP/ICE exchange for WebRTC setup | `main.py /ws/signaling` |
| Video Stream | WebRTC | H.264 video frames from browser | `video_track.py` |
| Input Events | WebRTC DataChannel | Click, scroll, text input | `webrtc_manager.py` |
| Keep-alive | WebSocket | Connection health monitoring | `webrtc-client.js` |

**The key insight**: WebSocket and WebRTC are **complementary technologies**, not alternatives. WebSocket handles the reliable control plane (signaling), while WebRTC handles the low-latency data plane (video streaming and input).
