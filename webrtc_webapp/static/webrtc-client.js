/**
 * Jiomosa WebRTC Client
 * Modern WebRTC client for streaming browser content to Android devices
 */

class JiomosaWebRTCClient {
    constructor(serverUrl, sessionId) {
        this.serverUrl = serverUrl;
        this.sessionId = sessionId;
        this.ws = null;
        this.pc = null;
        this.dataChannel = null;
        this.videoElement = null;
        this.statusCallback = null;
        this.errorCallback = null;
        
        // WebRTC configuration
        this.config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        // Connection state
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // ms
        
        console.log('JiomosaWebRTCClient initialized', { serverUrl, sessionId });
    }
    
    /**
     * Connect to the signaling server and establish WebRTC connection
     */
    async connect(videoElement) {
        this.videoElement = videoElement;
        
        try {
            // Connect to WebSocket signaling server
            await this._connectWebSocket();
            
            // Create peer connection
            this._createPeerConnection();
            
            // Join session
            this._sendMessage({ type: 'join', session_id: this.sessionId });
            
            this._updateStatus('connecting', 'Connecting to server...');
            
        } catch (error) {
            console.error('Connection error:', error);
            this._handleError('Failed to connect', error);
        }
    }
    
    /**
     * Disconnect and cleanup
     */
    disconnect() {
        console.log('Disconnecting...');
        
        if (this.dataChannel) {
            this.dataChannel.close();
            this.dataChannel = null;
        }
        
        if (this.pc) {
            this.pc.close();
            this.pc = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        this.connected = false;
        this._updateStatus('disconnected', 'Disconnected');
    }
    
    /**
     * Send click event to the server
     */
    sendClick(x, y) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready');
            return;
        }
        
        this.dataChannel.send(JSON.stringify({
            type: 'click',
            x: Math.round(x),
            y: Math.round(y)
        }));
    }
    
    /**
     * Send scroll event to the server
     */
    sendScroll(deltaY) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready');
            return;
        }
        
        this.dataChannel.send(JSON.stringify({
            type: 'scroll',
            deltaY: Math.round(deltaY)
        }));
    }
    
    /**
     * Send text input to the server
     */
    sendText(text) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready');
            return;
        }
        
        this.dataChannel.send(JSON.stringify({
            type: 'text',
            text: text
        }));
    }
    
    /**
     * Set status callback
     */
    onStatus(callback) {
        this.statusCallback = callback;
    }
    
    /**
     * Set error callback
     */
    onError(callback) {
        this.errorCallback = callback;
    }
    
    // Private methods
    
    _connectWebSocket() {
        return new Promise((resolve, reject) => {
            const wsUrl = this.serverUrl.replace('http', 'ws') + '/ws/signaling';
            console.log('Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                resolve();
            };
            
            this.ws.onmessage = async (event) => {
                await this._handleSignalingMessage(JSON.parse(event.data));
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this._handleDisconnect();
            };
        });
    }
    
    _createPeerConnection() {
        console.log('Creating peer connection');
        this.pc = new RTCPeerConnection(this.config);
        
        // Handle incoming tracks (video)
        this.pc.ontrack = (event) => {
            console.log('Received remote track');
            if (this.videoElement && event.streams && event.streams[0]) {
                this.videoElement.srcObject = event.streams[0];
                this._updateStatus('connected', 'Streaming');
                this.connected = true;
            }
        };
        
        // Handle ICE candidates
        this.pc.onicecandidate = (event) => {
            if (event.candidate) {
                this._sendMessage({
                    type: 'ice-candidate',
                    candidate: {
                        candidate: event.candidate.candidate,
                        sdpMid: event.candidate.sdpMid,
                        sdpMLineIndex: event.candidate.sdpMLineIndex
                    }
                });
            }
        };
        
        // Handle connection state changes
        this.pc.onconnectionstatechange = () => {
            console.log('Connection state:', this.pc.connectionState);
            
            if (this.pc.connectionState === 'connected') {
                this._updateStatus('connected', 'Connected');
                this.connected = true;
            } else if (this.pc.connectionState === 'failed') {
                this._handleError('Connection failed', new Error('WebRTC connection failed'));
                this._attemptReconnect();
            } else if (this.pc.connectionState === 'disconnected') {
                this._updateStatus('disconnected', 'Disconnected');
                this.connected = false;
            }
        };
        
        // Handle ICE connection state changes
        this.pc.oniceconnectionstatechange = () => {
            console.log('ICE connection state:', this.pc.iceConnectionState);
        };
        
        // Handle data channel
        this.pc.ondatachannel = (event) => {
            console.log('Data channel received');
            this._setupDataChannel(event.channel);
        };
    }
    
    _setupDataChannel(channel) {
        this.dataChannel = channel;
        
        this.dataChannel.onopen = () => {
            console.log('Data channel opened');
        };
        
        this.dataChannel.onclose = () => {
            console.log('Data channel closed');
        };
        
        this.dataChannel.onerror = (error) => {
            console.error('Data channel error:', error);
        };
    }
    
    async _handleSignalingMessage(message) {
        console.log('Received signaling message:', message.type);
        
        switch (message.type) {
            case 'offer':
                await this._handleOffer(message.offer);
                break;
                
            case 'ready':
                console.log('WebRTC connection ready');
                this._updateStatus('ready', 'Ready');
                break;
                
            case 'error':
                console.error('Server error:', message.message);
                this._handleError('Server error', new Error(message.message));
                break;
                
            case 'pong':
                // Keep-alive response
                break;
                
            default:
                console.warn('Unknown message type:', message.type);
        }
    }
    
    async _handleOffer(offer) {
        try {
            console.log('Handling offer');
            
            // Set remote description
            await this.pc.setRemoteDescription(new RTCSessionDescription(offer));
            
            // Create answer
            const answer = await this.pc.createAnswer();
            await this.pc.setLocalDescription(answer);
            
            // Send answer to server
            this._sendMessage({
                type: 'answer',
                answer: {
                    sdp: answer.sdp,
                    type: answer.type
                }
            });
            
            console.log('Sent answer');
            
        } catch (error) {
            console.error('Error handling offer:', error);
            this._handleError('Failed to create answer', error);
        }
    }
    
    _sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not ready, message not sent');
        }
    }
    
    _updateStatus(state, message) {
        console.log('Status update:', state, message);
        if (this.statusCallback) {
            this.statusCallback(state, message);
        }
    }
    
    _handleError(message, error) {
        console.error('Error:', message, error);
        if (this.errorCallback) {
            this.errorCallback(message, error);
        }
    }
    
    _handleDisconnect() {
        if (this.connected) {
            this.connected = false;
            this._updateStatus('disconnected', 'Connection lost');
            this._attemptReconnect();
        }
    }
    
    async _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this._handleError('Max reconnect attempts reached', new Error('Could not reconnect'));
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;
        
        this._updateStatus('reconnecting', `Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts})`);
        
        setTimeout(async () => {
            try {
                await this.connect(this.videoElement);
            } catch (error) {
                console.error('Reconnect failed:', error);
            }
        }, delay);
    }
    
    /**
     * Start keep-alive pings
     */
    startKeepAlive() {
        setInterval(() => {
            this._sendMessage({ type: 'ping' });
        }, 30000); // 30 seconds
    }
}

// Export for use in browser
if (typeof window !== 'undefined') {
    window.JiomosaWebRTCClient = JiomosaWebRTCClient;
}
