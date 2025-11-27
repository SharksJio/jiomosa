/**
 * Jiomosa Stealth Scripts for Android WebView
 * 
 * This file contains standalone JavaScript stealth scripts that can be
 * injected into an Android WebView to evade bot detection mechanisms.
 * 
 * These scripts are ported from the server-side Playwright stealth
 * configuration used in Jiomosa's browser_pool.py.
 * 
 * Usage in Android WebView:
 *   Load this file content and execute via webView.evaluateJavascript()
 *   The script should be injected BEFORE the page's own JavaScript runs
 *   (in WebViewClient.onPageStarted() callback)
 */

(function() {
    'use strict';

    // ==========================================
    // 1. Override navigator.webdriver
    // ==========================================
    // This is the most critical evasion technique
    // Removes the automation detection flag that WebDriver sets
    try {
        Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
            get: function() { return undefined; },
            configurable: true
        });
        delete navigator.__proto__.webdriver;
    } catch (e) {
        console.warn('Stealth: Failed to override webdriver:', e);
    }

    // ==========================================
    // 2. Create complete window.chrome object
    // ==========================================
    // Microsoft Outlook and other sites check for the presence
    // and structure of the window.chrome object
    if (!window.chrome) {
        try {
            Object.defineProperty(window, 'chrome', {
                writable: true,
                enumerable: true,
                configurable: false,
                value: {
                    app: {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        },
                        RunningState: {
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }
                    },
                    runtime: {
                        OnInstalledReason: {
                            CHROME_UPDATE: 'chrome_update',
                            INSTALL: 'install',
                            SHARED_MODULE_UPDATE: 'shared_module_update',
                            UPDATE: 'update'
                        },
                        OnRestartRequiredReason: {
                            APP_UPDATE: 'app_update',
                            OS_UPDATE: 'os_update',
                            PERIODIC: 'periodic'
                        },
                        PlatformArch: {
                            ARM: 'arm',
                            ARM64: 'arm64',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        },
                        PlatformOs: {
                            ANDROID: 'android',
                            CROS: 'cros',
                            LINUX: 'linux',
                            MAC: 'mac',
                            WIN: 'win'
                        }
                    },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    webstore: {}
                }
            });
        } catch (e) {
            console.warn('Stealth: Failed to create chrome object:', e);
        }
    }

    // ==========================================
    // 3. Create plugin and MIME type arrays
    // ==========================================
    // Real browsers have plugins; automation tools often don't
    // We simulate Chrome's default plugins
    try {
        var createMimeType = function(type, suffixes, description) {
            return {
                type: type,
                suffixes: suffixes,
                description: description,
                enabledPlugin: null
            };
        };

        // Chrome PDF Plugin
        var pdfPlugin = {
            name: 'Chrome PDF Plugin',
            filename: 'internal-pdf-viewer',
            description: 'Portable Document Format',
            length: 2,
            0: createMimeType('application/x-google-chrome-pdf', 'pdf', 'Portable Document Format'),
            1: createMimeType('application/pdf', 'pdf', 'Portable Document Format')
        };

        // Chrome PDF Viewer
        var pdfViewerPlugin = {
            name: 'Chrome PDF Viewer',
            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
            description: '',
            length: 1,
            0: createMimeType('application/pdf', 'pdf', '')
        };

        // Native Client (NaCl)
        var naclPlugin = {
            name: 'Native Client',
            filename: 'internal-nacl-plugin',
            description: '',
            length: 2,
            0: createMimeType('application/x-nacl', '', 'Native Client Executable'),
            1: createMimeType('application/x-pnacl', '', 'Portable Native Client Executable')
        };

        // Set plugin references (plugins reference each other)
        pdfPlugin[0].enabledPlugin = pdfPlugin;
        pdfPlugin[1].enabledPlugin = pdfPlugin;
        pdfViewerPlugin[0].enabledPlugin = pdfViewerPlugin;
        naclPlugin[0].enabledPlugin = naclPlugin;
        naclPlugin[1].enabledPlugin = naclPlugin;

        // Create proper PluginArray
        var pluginArray = [pdfPlugin, pdfViewerPlugin, naclPlugin];
        pluginArray.item = function(index) { return this[index] || null; };
        pluginArray.namedItem = function(name) {
            for (var i = 0; i < this.length; i++) {
                if (this[i].name === name) return this[i];
            }
            return null;
        };
        pluginArray.refresh = function() {};

        Object.defineProperty(navigator, 'plugins', {
            get: function() { return pluginArray; },
            enumerable: true,
            configurable: true
        });

        // Create proper MimeTypeArray
        var mimeTypeArray = [
            pdfPlugin[0], pdfPlugin[1],
            pdfViewerPlugin[0],
            naclPlugin[0], naclPlugin[1]
        ];
        mimeTypeArray.item = function(index) { return this[index] || null; };
        mimeTypeArray.namedItem = function(name) {
            for (var i = 0; i < this.length; i++) {
                if (this[i].type === name) return this[i];
            }
            return null;
        };

        Object.defineProperty(navigator, 'mimeTypes', {
            get: function() { return mimeTypeArray; },
            enumerable: true,
            configurable: true
        });
    } catch (e) {
        console.warn('Stealth: Failed to create plugins:', e);
    }

    // ==========================================
    // 4. Override WebGL parameters
    // ==========================================
    // WebGL fingerprinting is common; we spoof GPU info
    try {
        var overrideWebGL = function(context) {
            var getParameter = context.prototype.getParameter;
            context.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL (37445)
                if (parameter === 37445) {
                    return 'Google Inc. (Google)';
                }
                // UNMASKED_RENDERER_WEBGL (37446)
                if (parameter === 37446) {
                    return 'ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)';
                }
                return getParameter.call(this, parameter);
            };
        };

        if (typeof WebGLRenderingContext !== 'undefined') {
            overrideWebGL(WebGLRenderingContext);
        }
        if (typeof WebGL2RenderingContext !== 'undefined') {
            overrideWebGL(WebGL2RenderingContext);
        }
    } catch (e) {
        console.warn('Stealth: Failed to override WebGL:', e);
    }

    // ==========================================
    // 5. Override Permissions API
    // ==========================================
    // Handle permission queries gracefully
    try {
        if (navigator.permissions && navigator.permissions.query) {
            var originalQuery = navigator.permissions.query;
            navigator.permissions.query = function(parameters) {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: 'prompt' });
                }
                return originalQuery.apply(this, arguments);
            };
        }
    } catch (e) {
        console.warn('Stealth: Failed to override permissions:', e);
    }

    // ==========================================
    // 6. Override language properties
    // ==========================================
    // Set consistent language preferences
    try {
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en']; },
            enumerable: true,
            configurable: true
        });
    } catch (e) {
        console.warn('Stealth: Failed to override languages:', e);
    }

    // ==========================================
    // 7. Additional browser properties
    // ==========================================
    try {
        // Platform - appear as Windows for desktop mode
        Object.defineProperty(navigator, 'platform', {
            get: function() { return 'Win32'; },
            enumerable: true,
            configurable: true
        });

        // Hardware concurrency (typical desktop value)
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: function() { return 8; },
            enumerable: true,
            configurable: true
        });

        // Device memory (typical desktop value in GB)
        Object.defineProperty(navigator, 'deviceMemory', {
            get: function() { return 8; },
            enumerable: true,
            configurable: true
        });

        // Max touch points (0 for desktop)
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: function() { return 0; },
            enumerable: true,
            configurable: true
        });
    } catch (e) {
        console.warn('Stealth: Failed to override additional properties:', e);
    }

    // ==========================================
    // 8. Override Connection API
    // ==========================================
    // Spoof network connection details
    try {
        if (navigator.connection) {
            Object.defineProperty(navigator.connection, 'effectiveType', {
                get: function() { return '4g'; },
                enumerable: true,
                configurable: true
            });
            Object.defineProperty(navigator.connection, 'downlink', {
                get: function() { return 10; },
                enumerable: true,
                configurable: true
            });
            Object.defineProperty(navigator.connection, 'rtt', {
                get: function() { return 50; },
                enumerable: true,
                configurable: true
            });
        }
    } catch (e) {
        console.warn('Stealth: Failed to override connection:', e);
    }

    // ==========================================
    // 9. Canvas fingerprint protection
    // ==========================================
    // Add slight noise to canvas to defeat fingerprinting
    try {
        var originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            // Only modify for fingerprinting attempts (small canvases)
            if (this.width < 500 && this.height < 100) {
                var context = this.getContext('2d');
                if (context) {
                    var imageData = context.getImageData(0, 0, this.width, this.height);
                    var data = imageData.data;
                    // Add minimal noise (±1 to random pixels)
                    for (var i = 0; i < data.length; i += Math.floor(Math.random() * 10) + 10) {
                        data[i] = data[i] ^ 1;
                    }
                    context.putImageData(imageData, 0, 0);
                }
            }
            return originalToDataURL.apply(this, arguments);
        };
    } catch (e) {
        console.warn('Stealth: Failed to protect canvas:', e);
    }

    // Log success
    console.log('Jiomosa Stealth: All scripts loaded successfully');
})();
