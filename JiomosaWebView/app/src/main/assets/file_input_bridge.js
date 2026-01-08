/**
 * File Input Bridge for Modern Web Applications (v2.0)
 * 
 * This script monitors file input elements to help diagnose issues with
 * file attachment in web apps. It does NOT override behavior, but instead
 * logs activity and lets WebView's native onShowFileChooser work.
 * 
 * Key principle: Trust WebView's standard file chooser mechanism.
 */

(function() {
    'use strict';
    
    // Check if bridge is already loaded
    if (window.FileInputBridge) {
        console.log('[FileInputBridge] Already loaded');
        return;
    }
    
    console.log('[FileInputBridge] Initializing v2.0 - Monitoring only');
    
    // Track file inputs for monitoring
    const fileInputs = new WeakSet();
    
    /**
     * Monitor file input element
     */
    function monitorFileInput(input) {
        if (fileInputs.has(input)) return;
        fileInputs.add(input);
        
        console.log('[FileInputBridge] File input detected:', {
            id: input.id,
            name: input.name,
            className: input.className,
            accept: input.accept,
            multiple: input.multiple,
            capture: input.capture,
            hidden: input.style.display === 'none' || input.hidden
        });
        
        // Monitor change events to verify files are selected
        input.addEventListener('change', function(e) {
            const fileCount = this.files ? this.files.length : 0;
            console.log('[FileInputBridge] File input changed:', fileCount, 'file(s) selected');
            
            if (fileCount > 0) {
                for (let i = 0; i < fileCount; i++) {
                    const file = this.files[i];
                    console.log('[FileInputBridge]   File', (i + 1) + ':', file.name, '|', file.type, '|', file.size, 'bytes');
                }
            } else {
                console.log('[FileInputBridge]   No files in input.files');
            }
        }, true);
        
        // Monitor click events
        input.addEventListener('click', function(e) {
            console.log('[FileInputBridge] File input clicked - WebView onShowFileChooser should trigger');
        }, true);
        
        // Monitor focus events
        input.addEventListener('focus', function(e) {
            console.log('[FileInputBridge] File input focused');
        }, true);
    }
    
    /**
     * Scan existing file inputs on page
     */
    function scanExistingInputs() {
        const inputs = document.querySelectorAll('input[type="file"]');
        console.log('[FileInputBridge] Scanning page - found', inputs.length, 'file input(s)');
        inputs.forEach(monitorFileInput);
    }
    
    /**
     * Monitor DOM for dynamically added file inputs
     */
    function monitorDOM() {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'INPUT' && node.type === 'file') {
                            monitorFileInput(node);
                        }
                        // Check children
                        if (node.querySelectorAll) {
                            node.querySelectorAll('input[type="file"]').forEach(monitorFileInput);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
        
        console.log('[FileInputBridge] DOM observer started');
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[FileInputBridge] DOM ready, scanning for file inputs');
            scanExistingInputs();
            monitorDOM();
        });
    } else {
        console.log('[FileInputBridge] DOM already ready, scanning now');
        scanExistingInputs();
        monitorDOM();
    }
    
    // Mark as loaded
    window.FileInputBridge = {
        version: '2.0.0',
        monitorFileInput: monitorFileInput,
        scanExistingInputs: scanExistingInputs
    };
    
    console.log('[FileInputBridge] Initialized successfully - Using WebView native file chooser');
    console.log('[FileInputBridge] To manually scan: window.FileInputBridge.scanExistingInputs()');
})();
