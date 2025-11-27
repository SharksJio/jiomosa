package com.jiomosa.webview;

/**
 * StealthWebViewHelper - Provides JavaScript stealth scripts for WebView
 * 
 * This helper class contains the JavaScript code that overrides browser
 * fingerprinting detection mechanisms. The scripts are directly ported from
 * the server-side Playwright stealth configuration used in Jiomosa.
 * 
 * The scripts handle:
 * - navigator.webdriver override (removes automation detection)
 * - window.chrome object simulation (complete Chrome API structure)
 * - Plugin array creation (PDF plugins, Native Client)
 * - MIME types array creation (associated with plugins)
 * - WebGL parameter overrides (vendor/renderer strings)
 * - Permissions API override (notifications handling)
 * - Languages array override (English locale)
 */
public class StealthWebViewHelper {

    /**
     * Returns the complete stealth JavaScript to inject into WebView
     * This script should be executed before the page's own JavaScript runs
     * 
     * @return Complete stealth JavaScript as a single string
     */
    public static String getStealthScript() {
        return STEALTH_SCRIPT;
    }
    
    /**
     * Complete stealth script - directly ported from Jiomosa's browser_pool.py
     * 
     * This script implements the same evasion techniques as the server-side
     * Playwright stealth configuration, adapted for Android WebView.
     */
    private static final String STEALTH_SCRIPT = 
        // Wrap in IIFE to avoid polluting global scope
        "(function() {\n" +
        "    'use strict';\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 1. Override navigator.webdriver\n" +
        "    // ==========================================\n" +
        "    // This is the most important evasion - removes automation detection\n" +
        "    try {\n" +
        "        Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {\n" +
        "            get: function() { return undefined; },\n" +
        "            configurable: true\n" +
        "        });\n" +
        "        delete navigator.__proto__.webdriver;\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override webdriver:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 2. Create complete window.chrome object\n" +
        "    // ==========================================\n" +
        "    // Outlook and other sites check for this object's structure\n" +
        "    if (!window.chrome) {\n" +
        "        try {\n" +
        "            Object.defineProperty(window, 'chrome', {\n" +
        "                writable: true,\n" +
        "                enumerable: true,\n" +
        "                configurable: false,\n" +
        "                value: {\n" +
        "                    app: {\n" +
        "                        isInstalled: false,\n" +
        "                        InstallState: {\n" +
        "                            DISABLED: 'disabled',\n" +
        "                            INSTALLED: 'installed',\n" +
        "                            NOT_INSTALLED: 'not_installed'\n" +
        "                        },\n" +
        "                        RunningState: {\n" +
        "                            CANNOT_RUN: 'cannot_run',\n" +
        "                            READY_TO_RUN: 'ready_to_run',\n" +
        "                            RUNNING: 'running'\n" +
        "                        }\n" +
        "                    },\n" +
        "                    runtime: {\n" +
        "                        OnInstalledReason: {\n" +
        "                            CHROME_UPDATE: 'chrome_update',\n" +
        "                            INSTALL: 'install',\n" +
        "                            SHARED_MODULE_UPDATE: 'shared_module_update',\n" +
        "                            UPDATE: 'update'\n" +
        "                        },\n" +
        "                        OnRestartRequiredReason: {\n" +
        "                            APP_UPDATE: 'app_update',\n" +
        "                            OS_UPDATE: 'os_update',\n" +
        "                            PERIODIC: 'periodic'\n" +
        "                        },\n" +
        "                        PlatformArch: {\n" +
        "                            ARM: 'arm',\n" +
        "                            ARM64: 'arm64',\n" +
        "                            X86_32: 'x86-32',\n" +
        "                            X86_64: 'x86-64'\n" +
        "                        },\n" +
        "                        PlatformOs: {\n" +
        "                            ANDROID: 'android',\n" +
        "                            CROS: 'cros',\n" +
        "                            LINUX: 'linux',\n" +
        "                            MAC: 'mac',\n" +
        "                            WIN: 'win'\n" +
        "                        }\n" +
        "                    },\n" +
        "                    loadTimes: function() { return {}; },\n" +
        "                    csi: function() { return {}; },\n" +
        "                    webstore: {}\n" +
        "                }\n" +
        "            });\n" +
        "        } catch (e) {\n" +
        "            console.warn('Failed to create chrome object:', e);\n" +
        "        }\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 3. Create plugin and MIME type arrays\n" +
        "    // ==========================================\n" +
        "    // Real browsers have plugins; automation tools often don't\n" +
        "    try {\n" +
        "        var createMimeType = function(type, suffixes, description) {\n" +
        "            return {\n" +
        "                type: type,\n" +
        "                suffixes: suffixes,\n" +
        "                description: description,\n" +
        "                enabledPlugin: null\n" +
        "            };\n" +
        "        };\n" +
        "\n" +
        "        var pdfPlugin = {\n" +
        "            name: 'Chrome PDF Plugin',\n" +
        "            filename: 'internal-pdf-viewer',\n" +
        "            description: 'Portable Document Format',\n" +
        "            length: 2,\n" +
        "            0: createMimeType('application/x-google-chrome-pdf', 'pdf', 'Portable Document Format'),\n" +
        "            1: createMimeType('application/pdf', 'pdf', 'Portable Document Format')\n" +
        "        };\n" +
        "\n" +
        "        var pdfViewerPlugin = {\n" +
        "            name: 'Chrome PDF Viewer',\n" +
        "            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',\n" +
        "            description: '',\n" +
        "            length: 1,\n" +
        "            0: createMimeType('application/pdf', 'pdf', '')\n" +
        "        };\n" +
        "\n" +
        "        var naclPlugin = {\n" +
        "            name: 'Native Client',\n" +
        "            filename: 'internal-nacl-plugin',\n" +
        "            description: '',\n" +
        "            length: 2,\n" +
        "            0: createMimeType('application/x-nacl', '', 'Native Client Executable'),\n" +
        "            1: createMimeType('application/x-pnacl', '', 'Portable Native Client Executable')\n" +
        "        };\n" +
        "\n" +
        "        // Set plugin references\n" +
        "        pdfPlugin[0].enabledPlugin = pdfPlugin;\n" +
        "        pdfPlugin[1].enabledPlugin = pdfPlugin;\n" +
        "        pdfViewerPlugin[0].enabledPlugin = pdfViewerPlugin;\n" +
        "        naclPlugin[0].enabledPlugin = naclPlugin;\n" +
        "        naclPlugin[1].enabledPlugin = naclPlugin;\n" +
        "\n" +
        "        // Create PluginArray\n" +
        "        var pluginArray = [pdfPlugin, pdfViewerPlugin, naclPlugin];\n" +
        "        pluginArray.item = function(index) { return this[index] || null; };\n" +
        "        pluginArray.namedItem = function(name) {\n" +
        "            for (var i = 0; i < this.length; i++) {\n" +
        "                if (this[i].name === name) return this[i];\n" +
        "            }\n" +
        "            return null;\n" +
        "        };\n" +
        "        pluginArray.refresh = function() {};\n" +
        "\n" +
        "        Object.defineProperty(navigator, 'plugins', {\n" +
        "            get: function() { return pluginArray; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "\n" +
        "        // Create MimeTypeArray\n" +
        "        var mimeTypeArray = [\n" +
        "            pdfPlugin[0], pdfPlugin[1],\n" +
        "            pdfViewerPlugin[0],\n" +
        "            naclPlugin[0], naclPlugin[1]\n" +
        "        ];\n" +
        "        mimeTypeArray.item = function(index) { return this[index] || null; };\n" +
        "        mimeTypeArray.namedItem = function(name) {\n" +
        "            for (var i = 0; i < this.length; i++) {\n" +
        "                if (this[i].type === name) return this[i];\n" +
        "            }\n" +
        "            return null;\n" +
        "        };\n" +
        "\n" +
        "        Object.defineProperty(navigator, 'mimeTypes', {\n" +
        "            get: function() { return mimeTypeArray; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to create plugins:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 4. Override WebGL parameters\n" +
        "    // ==========================================\n" +
        "    // Spoof GPU information to look like a real browser\n" +
        "    try {\n" +
        "        var overrideWebGL = function(context) {\n" +
        "            var getParameter = context.prototype.getParameter;\n" +
        "            context.prototype.getParameter = function(parameter) {\n" +
        "                // UNMASKED_VENDOR_WEBGL\n" +
        "                if (parameter === 37445) {\n" +
        "                    return 'Google Inc. (Google)';\n" +
        "                }\n" +
        "                // UNMASKED_RENDERER_WEBGL\n" +
        "                if (parameter === 37446) {\n" +
        "                    return 'ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)';\n" +
        "                }\n" +
        "                return getParameter.call(this, parameter);\n" +
        "            };\n" +
        "        };\n" +
        "\n" +
        "        if (typeof WebGLRenderingContext !== 'undefined') {\n" +
        "            overrideWebGL(WebGLRenderingContext);\n" +
        "        }\n" +
        "        if (typeof WebGL2RenderingContext !== 'undefined') {\n" +
        "            overrideWebGL(WebGL2RenderingContext);\n" +
        "        }\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override WebGL:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 5. Override Permissions API\n" +
        "    // ==========================================\n" +
        "    // Handle permission queries gracefully\n" +
        "    try {\n" +
        "        if (navigator.permissions && navigator.permissions.query) {\n" +
        "            var originalQuery = navigator.permissions.query;\n" +
        "            navigator.permissions.query = function(parameters) {\n" +
        "                if (parameters.name === 'notifications') {\n" +
        "                    return Promise.resolve({ state: 'prompt' });\n" +
        "                }\n" +
        "                return originalQuery.apply(this, arguments);\n" +
        "            };\n" +
        "        }\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override permissions:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 6. Override languages\n" +
        "    // ==========================================\n" +
        "    // Set consistent language preferences\n" +
        "    try {\n" +
        "        Object.defineProperty(navigator, 'languages', {\n" +
        "            get: function() { return ['en-US', 'en']; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override languages:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 7. Additional browser properties\n" +
        "    // ==========================================\n" +
        "    try {\n" +
        "        // Platform override (appear as Windows)\n" +
        "        Object.defineProperty(navigator, 'platform', {\n" +
        "            get: function() { return 'Win32'; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "\n" +
        "        // Hardware concurrency (typical desktop value)\n" +
        "        Object.defineProperty(navigator, 'hardwareConcurrency', {\n" +
        "            get: function() { return 8; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "\n" +
        "        // Device memory (typical desktop value in GB)\n" +
        "        Object.defineProperty(navigator, 'deviceMemory', {\n" +
        "            get: function() { return 8; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "\n" +
        "        // Max touch points (0 for desktop)\n" +
        "        Object.defineProperty(navigator, 'maxTouchPoints', {\n" +
        "            get: function() { return 0; },\n" +
        "            enumerable: true,\n" +
        "            configurable: true\n" +
        "        });\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override additional properties:', e);\n" +
        "    }\n" +
        "\n" +
        "    // ==========================================\n" +
        "    // 8. Override Connection API\n" +
        "    // ==========================================\n" +
        "    try {\n" +
        "        if (navigator.connection) {\n" +
        "            Object.defineProperty(navigator.connection, 'effectiveType', {\n" +
        "                get: function() { return '4g'; },\n" +
        "                enumerable: true,\n" +
        "                configurable: true\n" +
        "            });\n" +
        "            Object.defineProperty(navigator.connection, 'downlink', {\n" +
        "                get: function() { return 10; },\n" +
        "                enumerable: true,\n" +
        "                configurable: true\n" +
        "            });\n" +
        "            Object.defineProperty(navigator.connection, 'rtt', {\n" +
        "                get: function() { return 50; },\n" +
        "                enumerable: true,\n" +
        "                configurable: true\n" +
        "            });\n" +
        "        }\n" +
        "    } catch (e) {\n" +
        "        console.warn('Failed to override connection:', e);\n" +
        "    }\n" +
        "\n" +
        "    console.log('Stealth scripts loaded successfully');\n" +
        "})();\n";
}
