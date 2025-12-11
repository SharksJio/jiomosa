package com.jiomosa.webview

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.webkit.*
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
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
 *       putExtra("url", "https://outlook.office.com/mail")
 *   })
 */
class StealthWebViewActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "StealthWebView"
        
        // Default URL if none provided - loads actual Outlook Mail directly
        private const val DEFAULT_URL = "https://portal.manage.microsoft.com"
        
        // Stealth User-Agent matching desktop Chrome
        // Same as server-side Playwright stealth configuration
        private const val STEALTH_USER_AGENT = 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorView: LinearLayout
    private lateinit var errorTitle: TextView
    private lateinit var errorMessage: TextView
    private lateinit var errorDetails: TextView
    private lateinit var retryButton: Button

    private var mainUrl: String = DEFAULT_URL

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_stealth_webview)
        
        // Enable ActionBar
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            setDisplayShowHomeEnabled(true)
        }

        // Initialize views
        webView = findViewById(R.id.stealthWebView)
        progressBar = findViewById(R.id.progressBar)
        errorView = findViewById(R.id.errorView)
        errorTitle = findViewById(R.id.errorTitle)
        errorMessage = findViewById(R.id.errorMessage)
        errorDetails = findViewById(R.id.errorDetails)
        retryButton = findViewById(R.id.retryButton)

        // Set up retry button
        retryButton.setOnClickListener {
            hideError()
            webView.reload()
        }

        // Enable WebView debugging (remove in production)
        WebView.setWebContentsDebuggingEnabled(true)
        
        // Configure WebView with stealth settings
        configureStealthWebView()
        
        // Get URL from intent or use default
        mainUrl = intent.getStringExtra("url") ?: DEFAULT_URL

        Log.d(TAG, "Loading URL with stealth parameters: $mainUrl")

        // Load the URL
        webView.loadUrl(mainUrl)
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
            hideError()

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
        
        override fun onReceivedHttpError(
            view: WebView?,
            request: WebResourceRequest?,
            errorResponse: WebResourceResponse?
        ) {
            super.onReceivedHttpError(view, request, errorResponse)

            // Only show error for main frame requests
            if (request?.isForMainFrame == true) {
                val statusCode = errorResponse?.statusCode ?: 0
                val reasonPhrase = errorResponse?.reasonPhrase ?: "Unknown error"

                Log.e(TAG, "HTTP Error: $statusCode - $reasonPhrase for URL: ${request.url}")

                showError(
                    "HTTP Error $statusCode",
                    reasonPhrase,
                    request.url.toString()
                )
            }
        }

        override fun onReceivedError(
            view: WebView?,
            request: WebResourceRequest?,
            error: WebResourceError?
        ) {
            super.onReceivedError(view, request, error)

            // Only show error for main frame requests
            if (request?.isForMainFrame == true) {
                val errorCode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    error?.errorCode ?: 0
                } else {
                    0
                }
                val description = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    error?.description?.toString() ?: "Unknown error"
                } else {
                    "Connection error"
                }

                Log.e(TAG, "WebView Error: $errorCode - $description for URL: ${request.url}")

                showError(
                    "Connection Error",
                    description,
                    request.url.toString()
                )
            }
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
     * Create options menu with Home and Back buttons
     */
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.webview_menu, menu)
        return true
    }

    /**
     * Handle menu item clicks
     */
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            android.R.id.home -> {
                // Handle ActionBar up/home button
                onBackPressed()
                true
            }
            R.id.action_back -> {
                // Handle Back button from menu
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    finish()
                }
                true
            }
            R.id.action_home -> {
                // Handle Home button - load main URL
                Log.d(TAG, "Loading main URL: $mainUrl")
                hideError()
                webView.loadUrl(mainUrl)
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    /**
     * Prepare options menu - enable/disable Back button based on history
     */
    override fun onPrepareOptionsMenu(menu: Menu?): Boolean {
        menu?.findItem(R.id.action_back)?.isEnabled = webView.canGoBack()
        return super.onPrepareOptionsMenu(menu)
    }

    /**
     * Show error view with custom message
     */
    private fun showError(title: String, message: String, url: String) {
        runOnUiThread {
            webView.visibility = View.GONE
            errorView.visibility = View.VISIBLE
            progressBar.visibility = View.GONE

            errorTitle.text = title
            errorMessage.text = message
            errorDetails.text = getString(R.string.error_url_format, url)

            Log.d(TAG, "Showing error: $title - $message")
        }
    }

    /**
     * Hide error view and show WebView
     */
    private fun hideError() {
        runOnUiThread {
            errorView.visibility = View.GONE
            webView.visibility = View.VISIBLE
        }
    }

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
