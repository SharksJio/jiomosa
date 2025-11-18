/**
 * WebSocket-based Real-time Frame Streaming Client
 * Connects to Jiomosa renderer service and streams frames in real-time
 */

class FrameStreamingClient {
    constructor(options = {}) {
        this.serverUrl = options.serverUrl || `http://${window.location.hostname}:5000`;
        this.sessionId = options.sessionId;
        this.onFrame = options.onFrame || (() => {});
        this.onError = options.onError || (() => {});
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        
        this.socket = null;
        this.isConnected = false;
        this.isStreaming = false;
        this.frameCount = 0;
        this.lastFrameTime = null;
        this.adaptiveMode = true;
        this.currentQuality = 85;
        this.currentFps = 30;
        
        // Statistics
        this.stats = {
            framesReceived: 0,
            bytesReceived: 0,
            lastBandwidthMbps: 0,
            avgFrameSize: 0,
            frameLatency: 0
        };
        
        this.init();
    }
    
    init() {
        /**
         * Initialize Socket.IO client for WebSocket communication
         * Socket.IO handles WebSocket with fallback to polling
         */
        this.socket = io(this.serverUrl, {
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity,
            transports: ['websocket', 'polling']
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        /**
         * Connection/Disconnection Events
         */
        this.socket.on('connect', () => {
            console.log('[Streaming] WebSocket connected');
            this.isConnected = true;
            this.onConnect();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.warn(`[Streaming] WebSocket disconnected: ${reason}`);
            this.isConnected = false;
            this.isStreaming = false;
            this.onDisconnect(reason);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('[Streaming] Connection error:', error);
            this.onError(`Connection error: ${error.message}`);
        });
        
        /**
         * Subscription Events
         */
        this.socket.on('subscribed', (data) => {
            console.log('[Streaming] Subscribed to session:', data.session_id);
            this.isStreaming = true;
            this.currentQuality = data.quality || 85;
            this.currentFps = data.fps || 30;
            this.adaptiveMode = data.adaptive_mode !== false;
            this.frameCount = 0;
            this.lastFrameTime = Date.now();
            
            // Notify UI of streaming status
            this.onConnect();
        });
        
        this.socket.on('subscribe:response', (data) => {
            console.log('[Streaming] Subscribe response:', data);
            this.isStreaming = true;
        });
        
        this.socket.on('unsubscribed', (data) => {
            console.log('[Streaming] Unsubscribed from session');
            this.isStreaming = false;
        });
        
        /**
         * Frame Events
         */
        this.socket.on('frame', (data) => {
            this.handleFrame(data);
        });
        
        this.socket.on('frame:data', (data) => {
            // Alternative frame event name
            this.handleFrame(data);
        });
        
        /**
         * Input Acknowledgment Events
         */
        this.socket.on('input:acknowledged', (data) => {
            console.log('[Streaming] Input acknowledged:', data.type);
        });
        
        this.socket.on('input:click:response', (data) => {
            if (!data.success) {
                console.warn('[Streaming] Click failed:', data.message);
            }
        });
        
        this.socket.on('input:scroll:response', (data) => {
            if (!data.success) {
                console.warn('[Streaming] Scroll failed:', data.message);
            }
        });
        
        this.socket.on('input:text:response', (data) => {
            if (!data.success) {
                console.warn('[Streaming] Text input failed:', data.message);
            }
        });
        
        /**
         * Quality Control Events
         */
        this.socket.on('quality:updated', (data) => {
            this.currentQuality = data.quality;
            console.log(`[Streaming] Quality updated to ${data.quality}`);
        });
        
        this.socket.on('fps:updated', (data) => {
            this.currentFps = data.fps;
            console.log(`[Streaming] FPS updated to ${data.fps}`);
        });
        
        this.socket.on('adaptive:updated', (data) => {
            this.adaptiveMode = data.enabled;
            console.log(`[Streaming] Adaptive mode: ${data.enabled ? 'ON' : 'OFF'}`);
        });
        
        /**
         * Error Events
         */
        this.socket.on('error', (data) => {
            console.error('[Streaming] Server error:', data.message);
            this.onError(data.message || 'Unknown error');
        });
        
        this.socket.on('status', (data) => {
            console.log('[Streaming] Status:', data.message);
        });
    }
    
    handleFrame(data) {
        /**
         * Handle incoming frame data
         * data should contain: {image: 'base64-encoded-jpeg', timestamp, size}
         */
        if (!data.image) {
            console.warn('[Streaming] Received frame without image data');
            return;
        }
        
        try {
            // Update statistics
            this.frameCount++;
            this.stats.framesReceived++;
            
            if (data.size) {
                this.stats.bytesReceived += data.size;
                this.stats.avgFrameSize = Math.round(this.stats.bytesReceived / this.frameCount);
            }
            
            // Calculate frame latency
            const now = Date.now();
            if (this.lastFrameTime) {
                this.stats.frameLatency = now - this.lastFrameTime;
            }
            this.lastFrameTime = now;
            
            // Calculate bandwidth (in Mbps)
            if (data.size && this.stats.frameLatency > 0) {
                const bps = (data.size * 8) / (this.stats.frameLatency / 1000);
                this.stats.lastBandwidthMbps = bps / 1_000_000;
            }
            
            // Callback with frame data
            this.onFrame({
                image: `data:image/jpeg;base64,${data.image}`,
                timestamp: data.timestamp || now,
                stats: {
                    frameNumber: this.frameCount,
                    latency: this.stats.frameLatency,
                    quality: this.currentQuality,
                    fps: this.currentFps,
                    adaptive: this.adaptiveMode,
                    bandwidthMbps: this.stats.lastBandwidthMbps.toFixed(2)
                }
            });
            
            // Log every 30 frames for debugging
            if (this.frameCount % 30 === 0) {
                console.log(
                    `[Streaming] Frame ${this.frameCount}: ` +
                    `${this.stats.frameLatency}ms latency, ` +
                    `${this.stats.avgFrameSize}B avg, ` +
                    `${this.stats.lastBandwidthMbps.toFixed(2)}Mbps, ` +
                    `Quality: ${this.currentQuality}, FPS: ${this.currentFps}`
                );
            }
        } catch (e) {
            console.error('[Streaming] Error handling frame:', e);
        }
    }
    
    subscribe(sessionId) {
        /**
         * Subscribe to frame stream for a session
         */
        if (!this.isConnected) {
            this.onError('Not connected to server');
            return;
        }
        
        this.sessionId = sessionId;
        console.log('[Streaming] Subscribing to session:', sessionId);
        
        this.socket.emit('subscribe', {
            session_id: sessionId
        });
    }
    
    unsubscribe() {
        /**
         * Unsubscribe from frame stream
         */
        if (this.sessionId) {
            console.log('[Streaming] Unsubscribing from session:', this.sessionId);
            this.socket.emit('unsubscribe', {
                session_id: this.sessionId
            });
        }
    }
    
    sendClick(x, y) {
        /**
         * Send click event to browser
         */
        if (!this.isStreaming) {
            console.warn('[Streaming] Not streaming - cannot send click');
            return;
        }
        
        this.socket.emit('input:click', {
            x: Math.round(x),
            y: Math.round(y)
        });
    }
    
    sendScroll(deltaX, deltaY) {
        /**
         * Send scroll event to browser
         */
        if (!this.isStreaming) {
            console.warn('[Streaming] Not streaming - cannot send scroll');
            return;
        }
        
        this.socket.emit('input:scroll', {
            deltaX: Math.round(deltaX),
            deltaY: Math.round(deltaY)
        });
    }
    
    sendText(text) {
        /**
         * Send text input to browser
         */
        if (!this.isStreaming) {
            console.warn('[Streaming] Not streaming - cannot send text');
            return;
        }
        
        this.socket.emit('input:text', {
            text: text
        });
    }
    
    setQuality(quality) {
        /**
         * Manually set JPEG quality (1-100)
         * Setting this disables adaptive mode
         */
        quality = Math.max(1, Math.min(100, quality));
        console.log('[Streaming] Setting quality to:', quality);
        
        this.socket.emit('quality:set', {
            quality: quality
        });
    }
    
    setFps(fps) {
        /**
         * Manually set frame rate (1-60)
         * Setting this disables adaptive mode
         */
        fps = Math.max(1, Math.min(60, fps));
        console.log('[Streaming] Setting FPS to:', fps);
        
        this.socket.emit('fps:set', {
            fps: fps
        });
    }
    
    toggleAdaptive(enabled) {
        /**
         * Toggle adaptive quality mode
         */
        console.log('[Streaming] Toggling adaptive mode:', enabled);
        
        this.socket.emit('adaptive:toggle', {
            enabled: enabled
        });
    }
    
    getStats() {
        /**
         * Get streaming statistics
         */
        return {
            connected: this.isConnected,
            streaming: this.isStreaming,
            frameCount: this.frameCount,
            quality: this.currentQuality,
            fps: this.currentFps,
            adaptiveMode: this.adaptiveMode,
            ...this.stats
        };
    }
    
    disconnect() {
        /**
         * Disconnect from server
         */
        if (this.socket) {
            this.unsubscribe();
            this.socket.disconnect();
            this.isConnected = false;
            this.isStreaming = false;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrameStreamingClient;
}
