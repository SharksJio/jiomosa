/**
 * Clipboard Bridge
 * Enables web pages inside the WebView to access Android clipboard content,
 * including images, and simulate paste into common controls.
 */
(function() {
    'use strict';

    if (window.AndroidClipboardBridgeInjected) {
        console.log('[ClipboardBridge] Already injected');
        return;
    }

    const bridge = window.ClipboardBridge;
    if (!bridge) {
        console.warn('[ClipboardBridge] Native ClipboardBridge not available');
        return;
    }

    function dataUrlToBlob(dataUrl) {
        try {
            const parts = dataUrl.split(',');
            if (parts.length < 2) return null;
            const header = parts[0];
            const base64 = parts[1];
            const mimeMatch = /data:([^;]+);base64/.exec(header);
            const mime = mimeMatch ? mimeMatch[1] : 'image/png';
            const bytes = atob(base64);
            const len = bytes.length;
            const arr = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                arr[i] = bytes.charCodeAt(i);
            }
            return new Blob([arr], { type: mime });
        } catch (err) {
            console.error('[ClipboardBridge] Failed to convert data URL to blob', err);
            return null;
        }
    }

    function isFileInput(el) {
        return el && el.tagName === 'INPUT' && el.type === 'file';
    }

    function isEditable(el) {
        if (!el) return false;
        if (el.isContentEditable) return true;
        if (el.tagName === 'TEXTAREA') return true;
        if (el.tagName === 'INPUT' && el.type !== 'file' && el.type !== 'button') return true;
        return false;
    }

    function insertImageIntoEditable(dataUrl, target) {
        try {
            const img = document.createElement('img');
            img.src = dataUrl;
            img.alt = 'clipboard-image';
            const selection = (document.getSelection && document.getSelection()) || null;
            const range = selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
            if (range) {
                range.deleteContents();
                range.insertNode(img);
                range.collapse(false);
            } else if (document.execCommand) {
                document.execCommand('insertImage', false, dataUrl);
            } else {
                target.value = (target.value || '') + dataUrl;
            }
        } catch (err) {
            console.error('[ClipboardBridge] Failed to insert image', err);
        }
    }

    function attachPasteListener() {
        document.addEventListener('paste', async function(event) {
            try {
                // If the browser already provides files, let default flow run
                if (event.clipboardData && event.clipboardData.files && event.clipboardData.files.length) {
                    return;
                }

                if (!bridge.hasImage()) {
                    return;
                }

                const dataUrl = bridge.getImageDataUrl();
                if (!dataUrl) {
                    console.warn('[ClipboardBridge] No data URL returned for clipboard image');
                    return;
                }

                event.preventDefault();

                const blob = dataUrlToBlob(dataUrl);
                if (!blob) return;

                const fileName = 'clipboard-image.' + (blob.type.split('/')[1] || 'png');
                const file = new File([blob], fileName, { type: blob.type });

                const dt = (typeof DataTransfer !== 'undefined') ? new DataTransfer() : null;
                if (dt && dt.items) {
                    dt.items.add(file);
                }

                const target = event.target;

                if (isFileInput(target) && dt && dt.files) {
                    target.files = dt.files;
                    target.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log('[ClipboardBridge] Populated file input from Android clipboard image');
                    return;
                }

                if (isEditable(target)) {
                    insertImageIntoEditable(dataUrl, target);
                    console.log('[ClipboardBridge] Inserted clipboard image into editable');
                    return;
                }

                // Fallback: dispatch synthetic paste with file payload
                if (dt) {
                    try {
                        const synthetic = new ClipboardEvent('paste', { clipboardData: dt });
                        target.dispatchEvent(synthetic);
                        console.log('[ClipboardBridge] Dispatched synthetic paste with clipboard image');
                    } catch (err) {
                        console.warn('[ClipboardBridge] Synthetic paste not supported', err);
                    }
                }
            } catch (err) {
                console.error('[ClipboardBridge] Paste handler error', err);
            }
        }, true);

        console.log('[ClipboardBridge] Paste listener attached');
    }

    // Expose a small helper for manual calls from the page if needed
    window.AndroidClipboard = {
        hasImage: () => bridge.hasImage(),
        getImageDataUrl: () => bridge.getImageDataUrl()
    };

    attachPasteListener();
    window.AndroidClipboardBridgeInjected = true;
    console.log('[ClipboardBridge] Initialized');
})();
