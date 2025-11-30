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
        
        // WebRTC configuration with multiple STUN servers for reliability
        // Include TURN servers for NAT traversal (especially needed for Docker)
        this.config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                // Local TURN server for Docker development
                {
                    urls: 'turn:127.0.0.1:3478',
                    username: 'jiomosa',
                    credential: 'jiomosapass'
                },
                {
                    urls: 'turn:127.0.0.1:3478?transport=tcp',
                    username: 'jiomosa',
                    credential: 'jiomosapass'
                }
            ],
            iceCandidatePoolSize: 10
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
            console.warn('Data channel not ready, state:', this.dataChannel?.readyState);
            return;
        }
        
        const message = JSON.stringify({
            type: 'click',
            x: Math.round(x),
            y: Math.round(y)
        });
        console.log('Sending click:', message);
        this.dataChannel.send(message);
    }
    
    /**
     * Send scroll event to the server
     */
    sendScroll(deltaY) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready, state:', this.dataChannel?.readyState);
            return;
        }
        
        const message = JSON.stringify({
            type: 'scroll',
            deltaY: Math.round(deltaY)
        });
        console.log('Sending scroll:', message);
        this.dataChannel.send(message);
    }
    
    /**
     * Send text input to the server
     */
    sendText(text) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready, state:', this.dataChannel?.readyState);
            return;
        }
        
        const message = JSON.stringify({
            type: 'text',
            text: text
        });
        console.log('Sending text:', message);
        this.dataChannel.send(message);
    }
    
    /**
     * Send key press to the server
     */
    sendKey(key) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            console.warn('Data channel not ready, state:', this.dataChannel?.readyState);
            return;
        }
        
        const message = JSON.stringify({
            type: 'key',
            key: key
        });
        console.log('Sending key:', message);
        this.dataChannel.send(message);
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
            let wsUrl;
            if (this.serverUrl === '' || this.serverUrl === '/') {
                // Use relative WebSocket URL based on current page location
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${protocol}//${window.location.host}/ws/signaling`;
            } else {
                wsUrl = this.serverUrl.replace('http', 'ws') + '/ws/signaling';
            }
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
        
        // Handle incoming tracks (video and audio)
        this.pc.ontrack = (event) => {
            console.log('Received remote track:', event.track.kind);
            if (this.videoElement && event.streams && event.streams[0]) {
                // Assign the stream to the video element (handles both video and audio)
                this.videoElement.srcObject = event.streams[0];
                
                // Log track types received
                const stream = event.streams[0];
                const videoTracks = stream.getVideoTracks();
                const audioTracks = stream.getAudioTracks();
                console.log(`Stream tracks - Video: ${videoTracks.length}, Audio: ${audioTracks.length}`);
                
                if (audioTracks.length > 0) {
                    console.log('Audio track received, audio streaming enabled');
                }
                
                this._updateStatus('connected', 'Streaming');
                this.connected = true;
            }
        };
        
        // Handle ICE candidates
        this.pc.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('Sending ICE candidate:', event.candidate.candidate.substring(0, 80) + '...');
                this._sendMessage({
                    type: 'ice-candidate',
                    candidate: {
                        candidate: event.candidate.candidate,
                        sdpMid: event.candidate.sdpMid,
                        sdpMLineIndex: event.candidate.sdpMLineIndex
                    }
                });
            } else {
                console.log('ICE gathering complete');
            }
        };
        
        // Log ICE gathering state
        this.pc.onicegatheringstatechange = () => {
            console.log('ICE gathering state:', this.pc.iceGatheringState);
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
            console.log('Data channel received:', event.channel.label, 'readyState:', event.channel.readyState);
            this._setupDataChannel(event.channel);
        };
    }
    
    _setupDataChannel(channel) {
        this.dataChannel = channel;
        
        this.dataChannel.onopen = () => {
            console.log('Data channel opened - ready for input events');
            this._updateStatus('ready', 'Ready - Interactive');
        };
        
        this.dataChannel.onclose = () => {
            console.log('Data channel closed');
        };
        
        this.dataChannel.onerror = (error) => {
            console.error('Data channel error:', error);
        };
        
        this.dataChannel.onmessage = (event) => {
            console.log('Data channel message received:', event.data);
        };
    }
    
    async _handleSignalingMessage(message) {
        console.log('Received signaling message:', message.type);
        
        switch (message.type) {
            case 'offer':
                await this._handleOffer(message.offer);
                break;
            
            case 'ice-candidate':
                await this._handleRemoteIceCandidate(message.candidate);
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
    
    async _handleRemoteIceCandidate(candidate) {
        try {
            if (candidate && candidate.candidate && this.pc) {
                console.log('Adding remote ICE candidate');
                await this.pc.addIceCandidate(new RTCIceCandidate(candidate));
            }
        } catch (error) {
            console.error('Error adding remote ICE candidate:', error);
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
