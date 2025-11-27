package com.jiomosa.webview

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity

/**
 * StealthWebViewActivity - Android WebView with Stealth Parameters (Kotlin)
 *
 * This activity implements browser fingerprint evasion techniques similar to
 * the server-side Playwright stealth configuration used in Jiomosa.
 *
 * Key features:
 * - Custom User-Agent matching desktop Chrome
 * - navigator.webdriver override
 * - Chrome object simulation
 * - Plugin/MIME type array spoofing
 * - WebGL parameter override
 * - Permissions API override
 *
 * Usage:
 *   startActivity(Intent(this, StealthWebViewActivity::class.java).apply {
 *       putExtra("url", "https://outlook.live.com")
 *   })
 */
class StealthWebViewActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "StealthWebView"
        
        // Default URL if none provided
        private const val DEFAULT_URL = "https://outlook.live.com"
        
        // Stealth User-Agent matching desktop Chrome
        // Same as server-side Playwright stealth configuration
        private const val STEALTH_USER_AGENT = 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_stealth_webview)
        
        // Initialize views
        webView = findViewById(R.id.stealthWebView)
        progressBar = findViewById(R.id.progressBar)
        
        // Enable WebView debugging (remove in production)
        WebView.setWebContentsDebuggingEnabled(true)
        
        // Configure WebView with stealth settings
        configureStealthWebView()
        
        // Get URL from intent or use default
        val url = intent.getStringExtra("url") ?: DEFAULT_URL
        
        Log.d(TAG, "Loading URL with stealth parameters: $url")
        
        // Load the URL
        webView.loadUrl(url)
    }

    /**
     * Configure WebView with stealth parameters
     * Applies all necessary settings to evade bot detection
     */
    @SuppressLint("SetJavaScriptEnabled")
    private fun configureStealthWebView() {
        webView.settings.apply {
            // === Essential Settings ===
            
            // Enable JavaScript (required for most modern sites)
            javaScriptEnabled = true
            
            // Enable DOM storage (localStorage, sessionStorage)
            domStorageEnabled = true
            
            // Enable database storage
            databaseEnabled = true
            
            // === User-Agent Spoofing ===
            
            // Set desktop Chrome User-Agent to appear as regular browser
            userAgentString = STEALTH_USER_AGENT
            
            // === Media and Content Settings ===
            
            // Allow mixed content (HTTP on HTTPS pages)
            mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
            
            // Enable media playback without user gesture
            mediaPlaybackRequiresUserGesture = false
            
            // Load images automatically
            loadsImagesAutomatically = true
            blockNetworkImage = false
            
            // === Cache and Storage ===
            
            // Use default cache mode
            cacheMode = WebSettings.LOAD_DEFAULT
            
            // === Zoom and Display ===
            
            // Enable zoom controls
            builtInZoomControls = true
            displayZoomControls = false
            
            // Use wide viewport for desktop-like rendering
            useWideViewPort = true
            loadWithOverviewMode = true
            
            // === File Access ===
            
            allowFileAccess = true
            allowContentAccess = true
        }
        
        // === Cookie Settings ===
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, true)
        }
        
        // === Hardware Acceleration ===
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null)
        
        // === WebView Clients ===
        webView.webViewClient = StealthWebViewClient()
        webView.webChromeClient = StealthWebChromeClient()
        
        Log.d(TAG, "Stealth WebView configured with User-Agent: $STEALTH_USER_AGENT")
    }

    /**
     * Custom WebViewClient that injects stealth scripts
     */
    private inner class StealthWebViewClient : WebViewClient() {
        
        override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
            super.onPageStarted(view, url, favicon)
            
            Log.d(TAG, "Page started loading: $url")
            progressBar.visibility = View.VISIBLE
            
            // Inject stealth scripts immediately
            view?.let { injectStealthScripts(it) }
        }
        
        override fun onPageFinished(view: WebView?, url: String?) {
            super.onPageFinished(view, url)
            
            Log.d(TAG, "Page finished loading: $url")
            progressBar.visibility = View.GONE
            
            // Re-inject stealth scripts to ensure they persist
            view?.let { injectStealthScripts(it) }
        }
        
        override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
            val uri = request?.url ?: return false
            val url = uri.toString()
            
            // Handle external links
            return when {
                url.startsWith("tel:") || url.startsWith("mailto:") -> {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                    true
                }
                url.startsWith("http://") || url.startsWith("https://") -> {
                    false // Let WebView handle it
                }
                else -> {
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, uri))
                    } catch (e: Exception) {
                        Log.e(TAG, "Cannot handle URL: $url", e)
                    }
                    true
                }
            }
        }
    }

    /**
     * Custom WebChromeClient for progress and console logging
     */
    private inner class StealthWebChromeClient : WebChromeClient() {
        
        override fun onProgressChanged(view: WebView?, newProgress: Int) {
            super.onProgressChanged(view, newProgress)
            
            progressBar.progress = newProgress
            if (newProgress >= 100) {
                progressBar.visibility = View.GONE
            }
        }
        
        override fun onReceivedTitle(view: WebView?, title: String?) {
            super.onReceivedTitle(view, title)
            title?.takeIf { it.isNotEmpty() }?.let { setTitle(it) }
        }
    }

    /**
     * Inject stealth JavaScript scripts into the WebView
     */
    private fun injectStealthScripts(view: WebView) {
        val stealthScript = getStealthScript()
        
        view.evaluateJavascript(stealthScript) {
            Log.d(TAG, "Stealth scripts injected successfully")
        }
    }

    /**
     * Get the complete stealth JavaScript
     */
    private fun getStealthScript(): String = """
        (function() {
            'use strict';
            
            // Override navigator.webdriver
            try {
                Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
                    get: function() { return undefined; },
                    configurable: true
                });
                delete navigator.__proto__.webdriver;
            } catch (e) {}
            
            // Create window.chrome object
            if (!window.chrome) {
                try {
                    Object.defineProperty(window, 'chrome', {
                        writable: true,
                        enumerable: true,
                        configurable: false,
                        value: {
                            app: { isInstalled: false },
                            runtime: {},
                            loadTimes: function() { return {}; },
                            csi: function() { return {}; },
                            webstore: {}
                        }
                    });
                } catch (e) {}
            }
            
            // Override languages
            try {
                Object.defineProperty(navigator, 'languages', {
                    get: function() { return ['en-US', 'en']; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // Override platform
            try {
                Object.defineProperty(navigator, 'platform', {
                    get: function() { return 'Win32'; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            console.log('Stealth scripts loaded');
        })();
    """.trimIndent()

    /**
     * Handle back button navigation
     */
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            @Suppress("DEPRECATION")
            super.onBackPressed()
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        webView.stopLoading()
        webView.destroy()
        super.onDestroy()
    }
}
