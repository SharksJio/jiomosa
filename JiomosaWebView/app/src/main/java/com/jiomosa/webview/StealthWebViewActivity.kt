package com.jiomosa.webview

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
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
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

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
open class StealthWebViewActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "StealthWebView"
        
        // Fallback URL if no metadata found
        private const val FALLBACK_URL = "https://portal.manage.microsoft.com"
        
        // Modern Chrome User-Agent for December 2025
        // Matches real desktop Chrome to pass Google OAuth security checks
        private const val STEALTH_USER_AGENT = 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    /**
     * Subclasses can provide a fixed initial URL for their shortcut.
     * This enables "one instance per shortcut" while keeping shared WebView storage.
     */
    protected open fun provideInitialUrl(intent: Intent): String? = null

    /**
     * Get the default URL from activity metadata or use fallback.
     */
    protected fun getDefaultUrl(intent: Intent): String {
        return try {
            // Read metadata from the component that launched this activity
            val launchComponent = intent.component ?: componentName
            
            val activityInfo = packageManager.getActivityInfo(
                launchComponent,
                android.content.pm.PackageManager.GET_META_DATA
            )
            
            // Metadata can store string directly or as resource reference
            val url = activityInfo.metaData?.getString("default_url")
            
            Log.d(TAG, "Reading metadata from: ${launchComponent.shortClassName}")
            Log.d(TAG, "Metadata URL: $url")
            
            if (url != null) {
                url
            } else {
                FALLBACK_URL
            }
        } catch (e: Exception) {
            Log.w(TAG, "Could not read metadata, using fallback URL", e)
            FALLBACK_URL
        }
    }

    private fun resolveInitialUrl(intent: Intent): String {
        intent.getStringExtra("url")?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }

        intent.dataString?.trim()?.takeIf {
            it.startsWith("https://") || it.startsWith("http://")
        }?.let { return it }

        provideInitialUrl(intent)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }

        return getDefaultUrl(intent)
    }

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorView: LinearLayout
    private lateinit var errorTitle: TextView
    private lateinit var errorMessage: TextView
    private lateinit var errorDetails: TextView
    private lateinit var retryButton: Button

    private lateinit var mainUrl: String
    
    // File chooser support
    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null
    private lateinit var fileChooserLauncher: ActivityResultLauncher<Intent>
    private lateinit var permissionLauncher: ActivityResultLauncher<Array<String>>

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_stealth_webview)
        
        // Log app version for debugging
        try {
            val versionName = packageManager.getPackageInfo(packageName, 0).versionName
            val versionCode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                packageManager.getPackageInfo(packageName, 0).longVersionCode
            } else {
                @Suppress("DEPRECATION")
                packageManager.getPackageInfo(packageName, 0).versionCode.toLong()
            }
            Log.i(TAG, "JiomosaWebView v$versionName (build $versionCode)")
        } catch (e: Exception) {
            Log.e(TAG, "Error getting app version", e)
        }
        
        // Enable ActionBar
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            setDisplayShowHomeEnabled(true)
        }
        
        // Initialize file chooser activity result launcher
        fileChooserLauncher = registerForActivityResult(
            ActivityResultContracts.StartActivityForResult()
        ) { result ->
            handleFileChooserResult(result.resultCode, result.data)
        }
        
        // Initialize permission request launcher
        permissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->
            val allGranted = permissions.values.all { it }
            if (allGranted) {
                Log.d(TAG, "All storage permissions granted")
                Toast.makeText(this, "Permissions granted", Toast.LENGTH_SHORT).show()
            } else {
                Log.w(TAG, "Some storage permissions denied")
                Toast.makeText(
                    this,
                    "Storage permission required for file attachments",
                    Toast.LENGTH_LONG
                ).show()
            }
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

        // Enable WebView debugging only in debug builds
        //WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
        
        // Configure WebView with stealth settings
        configureStealthWebView()
        
        // Setup modern back press handling
        setupBackPressHandler()
        
        // Get URL from intent, subclass, metadata, or use fallback
        // Priority: Intent extra > Intent data URL > Subclass default > Activity metadata > Fallback
        mainUrl = resolveInitialUrl(intent)

        Log.d(TAG, "Loading URL with stealth parameters: $mainUrl")
        Log.d(TAG, "Launched from: ${intent.component?.shortClassName ?: componentName.shortClassName}")
        //Log.d(TAG, "Task affinity: $taskAffinity")


        // Load the URL
        webView.loadUrl(mainUrl)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)

        // With launchMode="singleTask", tapping the same shortcut again routes here.
        // Do NOT reload unless the requested URL actually changed.
        val nextUrl = resolveInitialUrl(intent)
        if (::mainUrl.isInitialized && nextUrl == mainUrl) {
            Log.d(TAG, "onNewIntent: same URL, not reloading: $nextUrl")
            return
        }

        Log.d(TAG, "onNewIntent: switching URL: ${if (::mainUrl.isInitialized) mainUrl else "<unset>"} -> $nextUrl")
        mainUrl = nextUrl
        if (::webView.isInitialized) {
            hideError()
            webView.loadUrl(mainUrl)
        }
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
            
            // === Persistent Storage ===
            // Enable AppCache (deprecated but still useful)
            @Suppress("DEPRECATION")
            setAppCacheEnabled(true)
            @Suppress("DEPRECATION")
            setAppCachePath(applicationContext.cacheDir.absolutePath)
            
            // === Performance Optimizations ===
            // Enable smooth scrolling
            setSupportZoom(true)
            
            // Rendering priority
            setRenderPriority(WebSettings.RenderPriority.HIGH)
            
            // Enable safe browsing
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                safeBrowsingEnabled = true
            }
            
            // Text zoom
            textZoom = 100
            
            // Mixed content handling for better compatibility
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            }
        }
        
        // === Cookie Settings ===
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, true)
            // Enable cookie persistence across app restarts (critical for OAuth)
            flush()
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

            // Check for OAuth URLs
            if (url != null && (url.contains("oauth") || url.contains("authorize") || url.contains("signin"))) {
                Log.d(TAG, "OAuth page detected: $url")
            }

            // Inject stealth scripts immediately
            view?.let { injectStealthScripts(it) }
        }
        
        override fun onPageFinished(view: WebView?, url: String?) {
            super.onPageFinished(view, url)
            
            Log.d(TAG, "Page finished loading: $url")
            progressBar.visibility = View.GONE
            
            // Re-inject stealth scripts to ensure they persist
            view?.let { injectStealthScripts(it) }
            
            // Inject file input bridge for modern web apps
            view?.let { injectFileInputBridge(it) }
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
            
            // Log OAuth requests for debugging
            if (url.contains("oauth") || url.contains("authorize") || url.contains("signin")) {
                Log.d(TAG, "OAuth request: $url")
                if (request?.method == "POST") {
                    Log.d(TAG, "POST OAuth request detected")
                }
            }
            
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
     * Custom WebChromeClient that handles progress, title, and file chooser
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
        
        /**
         * Handle file chooser for file uploads (Android 5.0+)
         * This is called when the user clicks on file input fields in the web page
         */
        override fun onShowFileChooser(
            webView: WebView?,
            filePathCallback: ValueCallback<Array<Uri>>?,
            fileChooserParams: FileChooserParams?
        ): Boolean {
            Log.d(TAG, "onShowFileChooser called")
            
            // Cancel any existing file upload callback
            fileUploadCallback?.onReceiveValue(null)
            fileUploadCallback = filePathCallback
            
            // Check and request permissions if needed
            if (!hasStoragePermissions()) {
                Log.d(TAG, "Requesting storage permissions")
                requestStoragePermissions()
                return true
            }
            
            try {
                val intent = createFileChooserIntent(fileChooserParams)
                fileChooserLauncher.launch(intent)
                Log.d(TAG, "File chooser launched")
                return true
            } catch (e: Exception) {
                Log.e(TAG, "Error launching file chooser", e)
                fileUploadCallback?.onReceiveValue(null)
                fileUploadCallback = null
                Toast.makeText(
                    this@StealthWebViewActivity,
                    "Error opening file chooser",
                    Toast.LENGTH_SHORT
                ).show()
                return false
            }
        }
    }

    /**
     * Setup modern back press handling
     */
    private fun setupBackPressHandler() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }
    
    /**
     * Check if storage permissions are granted
     */
    private fun hasStoragePermissions(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Android 13+ uses granular media permissions
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.READ_MEDIA_IMAGES
            ) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.READ_MEDIA_VIDEO
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            // Android 12 and below
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.READ_EXTERNAL_STORAGE
            ) == PackageManager.PERMISSION_GRANTED
        }
    }
    
    /**
     * Request storage permissions based on Android version
     */
    private fun requestStoragePermissions() {
        val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Android 13+ (API 33+)
            arrayOf(
                Manifest.permission.READ_MEDIA_IMAGES,
                Manifest.permission.READ_MEDIA_VIDEO,
                Manifest.permission.READ_MEDIA_AUDIO,
                Manifest.permission.CAMERA
            )
        } else {
            // Android 12 and below
            arrayOf(
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.CAMERA
            )
        }
        
        permissionLauncher.launch(permissions)
    }
    
    /**
     * Create file chooser intent with proper MIME types and options
     */
    private fun createFileChooserIntent(fileChooserParams: WebChromeClient.FileChooserParams?): Intent {
        val acceptTypes = fileChooserParams?.acceptTypes
        val mimeTypes = if (!acceptTypes.isNullOrEmpty() && acceptTypes[0].isNotEmpty()) {
            acceptTypes
        } else {
            // Default to common file types if not specified
            arrayOf("image/*", "video/*", "application/pdf", "*/*")
        }
        
        val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
            putExtra(Intent.EXTRA_MIME_TYPES, mimeTypes)
            
            // Allow multiple file selection if supported
            if (fileChooserParams?.mode == WebChromeClient.FileChooserParams.MODE_OPEN_MULTIPLE) {
                putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
            }
        }
        
        // Create chooser to allow user to select from different apps
        return Intent.createChooser(intent, "Choose File").apply {
            // Add camera option if image capture is accepted
            if (mimeTypes.any { it.startsWith("image/") }) {
                val cameraIntents = mutableListOf<Intent>()
                
                try {
                    val captureIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                    if (captureIntent.resolveActivity(packageManager) != null) {
                        cameraIntents.add(captureIntent)
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Camera intent not available", e)
                }
                
                if (cameraIntents.isNotEmpty()) {
                    putExtra(Intent.EXTRA_INITIAL_INTENTS, cameraIntents.toTypedArray())
                }
            }
        }
    }
    
    /**
     * Handle file chooser result
     */
    private fun handleFileChooserResult(resultCode: Int, data: Intent?) {
        if (resultCode == Activity.RESULT_OK) {
            val results = mutableListOf<Uri>()
            
            data?.let { intent ->
                // Handle single file selection
                intent.data?.let { uri ->
                    results.add(uri)
                    Log.d(TAG, "Single file selected: $uri")
                }
                
                // Handle multiple file selection
                intent.clipData?.let { clipData ->
                    for (i in 0 until clipData.itemCount) {
                        clipData.getItemAt(i).uri?.let { uri ->
                            results.add(uri)
                            Log.d(TAG, "File selected: $uri")
                        }
                    }
                }
            }
            
            if (results.isNotEmpty()) {
                val resultArray = results.toTypedArray()
                fileUploadCallback?.onReceiveValue(resultArray)
                Toast.makeText(this, "${results.size} file(s) selected", Toast.LENGTH_SHORT).show()
            } else {
                fileUploadCallback?.onReceiveValue(null)
            }
        } else {
            Log.d(TAG, "File chooser cancelled")
            fileUploadCallback?.onReceiveValue(null)
        }
        
        fileUploadCallback = null
    }
    
    /**
     * Inject file input bridge JavaScript into the WebView
     */
    private fun injectFileInputBridge(view: WebView) {
        try {
            // Load bridge script from assets
            val bridgeScript = assets.open("file_input_bridge.js").bufferedReader().use { it.readText() }
            
            // Inject into page
            view.evaluateJavascript(bridgeScript) { result ->
                Log.d(TAG, "File input bridge injected, result: $result")
            }
            
            Log.d(TAG, "File input bridge script injected successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Error injecting file input bridge", e)
        }
    }

    /**
     * Inject stealth JavaScript scripts into the WebView
     * Skip script injection on Microsoft login and Outlook pages to prevent interference
     */
    private fun injectStealthScripts(view: WebView) {
        val currentUrl = view.url ?: ""
        
        // Skip ALL script injection on Microsoft login pages and Outlook
        if (currentUrl.contains("login.microsoftonline.com") || 
            currentUrl.contains("login.live.com") ||
            currentUrl.contains("login.microsoft.com") ||
            currentUrl.contains("outlook.office.com")) {
            Log.d(TAG, "Skipping stealth scripts on Microsoft page: $currentUrl")
            return
        }
        
        val stealthScript = getStealthScript()
        
        view.evaluateJavascript(stealthScript) {
            Log.d(TAG, "Stealth scripts injected successfully for: $currentUrl")
        }
    }

    // Cache the stealth script to avoid recreating it each time
    private val cachedStealthScript: String by lazy {
        buildStealthScript()
    }

    /**
     * Get the complete stealth JavaScript
     */
    private fun getStealthScript(): String = cachedStealthScript
    
    /**
     * Build comprehensive stealth script with all evasion techniques
     * Optimized for Google OAuth to avoid "This browser or app may not be secure"
     */
    private fun buildStealthScript(): String = """
        (function() {
            'use strict';
            
            // 1. Override navigator.webdriver (primary Google detection vector)
            try {
                Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
                    get: function() { return undefined; },
                    configurable: true
                });
                delete navigator.__proto__.webdriver;
            } catch (e) {}
            
            // 2. Create comprehensive window.chrome object
            if (!window.chrome) {
                try {
                    Object.defineProperty(window, 'chrome', {
                        writable: true,
                        enumerable: true,
                        configurable: false,
                        value: {
                            app: { isInstalled: false },
                            runtime: { 
                                id: 'chrome-extension-id',
                                getManifest: function() { return {}; },
                                reload: function() {}
                            },
                            loadTimes: function() { return {}; },
                            csi: function() { return {}; },
                            webstore: {}
                        }
                    });
                } catch (e) {}
            }
            
            // 3. Override plugins array (critical for Google detection)
            try {
                Object.defineProperty(navigator, 'plugins', {
                    get: function() {
                        return {
                            length: 3,
                            0: { name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer', version: '1.0' },
                            1: { name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', version: '1.0' },
                            2: { name: 'Native Client Executable', description: '', filename: 'internal-nacl-plugin', version: '1.0' }
                        };
                    },
                    configurable: true
                });
            } catch (e) {}
            
            // 4. Override mimeTypes
            try {
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: function() {
                        return {
                            length: 2,
                            0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Chrome PDF Plugin' },
                            1: { type: 'application/pdf', suffixes: 'pdf', description: 'Chrome PDF Plugin' }
                        };
                    },
                    configurable: true
                });
            } catch (e) {}
            
            // 5. Override languages
            try {
                Object.defineProperty(navigator, 'languages', {
                    get: function() { return ['en-US', 'en']; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 6. Override language
            try {
                Object.defineProperty(navigator, 'language', {
                    get: function() { return 'en-US'; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 7. Override platform
            try {
                Object.defineProperty(navigator, 'platform', {
                    get: function() { return 'Win32'; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 8. Override oscpu
            try {
                Object.defineProperty(navigator, 'oscpu', {
                    get: function() { return 'Windows NT 10.0; Win64; x64'; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 9. Override hardwareConcurrency
            try {
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: function() { return 8; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 10. Override deviceMemory
            try {
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: function() { return 8; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 11. Override maxTouchPoints
            try {
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: function() { return 10; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 12. Override vendor to Google
            try {
                Object.defineProperty(navigator, 'vendor', {
                    get: function() { return 'Google Inc.'; },
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // 13. WebGL spoofing
            try {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.'; // UNMASKED_VENDOR
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER
                    return getParameter.call(this, parameter);
                };
                if (WebGL2RenderingContext) {
                    const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                        return getParameter2.call(this, parameter);
                    };
                }
            } catch (e) {}
            
            // 14. Canvas fingerprint protection
            try {
                const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    if (this.width === 280 && this.height === 60) {
                        const context = this.getContext('2d');
                        context.fillStyle = '#f0f0f0';
                        context.fillRect(0, 0, this.width, this.height);
                    }
                    return toDataURL.apply(this, arguments);
                };
            } catch (e) {}
            
            // 15. Permissions API
            try {
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = function(parameters) {
                        if (parameters.name === 'notifications') {
                            return Promise.resolve({ state: 'denied', onchange: null });
                        }
                        return originalQuery(parameters);
                    };
                }
            } catch (e) {}
            
            // 16. mediaDevices protection
            try {
                if (navigator.mediaDevices) {
                    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                    navigator.mediaDevices.enumerateDevices = function() {
                        return originalEnumerateDevices.call(this).then(function(devices) {
                            return devices.filter(d => d.kind !== 'videoinput' && d.kind !== 'audioinput');
                        });
                    };
                }
            } catch (e) {}
            
            // 17. Battery API hiding
            try {
                if (navigator.getBattery) {
                    navigator.getBattery = undefined;
                }
            } catch (e) {}
            
            // 18. Geolocation error handling
            try {
                if (navigator.geolocation) {
                    const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition;
                    navigator.geolocation.getCurrentPosition = function(success, error) {
                        if (error) {
                            error({ code: 1, message: 'User denied Geolocation' });
                        }
                    };
                }
            } catch (e) {}
            
            // 19. Screen orientation spoofing
            try {
                Object.defineProperty(screen, 'orientation', {
                    value: { type: 'landscape-primary', angle: 0 },
                    writable: false
                });
            } catch (e) {}
            
            console.log('Google-optimized stealth scripts loaded successfully');
        })();
    """.trimIndent()

    /**
     * Get OAuth2 support script for Microsoft and other OAuth providers
     * Handles form submissions and request parameter encoding
     */
    private fun getOAuthSupportScript(): String = """
        (function() {
            'use strict';
            
            // 1. Enhance FormData support for OAuth2 forms
            const OriginalFormData = window.FormData;
            if (OriginalFormData) {
                window.FormData = function() {
                    this._data = new OriginalFormData();
                    this._customData = {};
                };
                
                window.FormData.prototype.append = function(key, value) {
                    this._customData[key] = value;
                    this._data.append(key, value);
                };
                
                window.FormData.prototype.get = function(key) {
                    return this._customData[key];
                };
            }
            
            // 2. Enhance XMLHttpRequest for OAuth2 requests
            const OriginalXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                this._xhr = new OriginalXHR();
            };
            
            ['open', 'send', 'setRequestHeader', 'getResponseHeader', 'getAllResponseHeaders'].forEach(method => {
                window.XMLHttpRequest.prototype[method] = function(...args) {
                    return this._xhr[method].apply(this._xhr, args);
                };
            });
            
            // 3. Enhance fetch API for OAuth2 requests
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                // Log OAuth requests for debugging
                if (url && typeof url === 'string' && (url.includes('oauth') || url.includes('authorize') || url.includes('signin'))) {
                    console.log('OAuth2 fetch request detected:', url);
                    if (options && options.method === 'POST') {
                        console.log('POST request body:', options.body);
                    }
                }
                return originalFetch.apply(this, arguments);
            };
            
            // 4. Monitor form submissions for OAuth flows
            const OriginalFormSubmit = HTMLFormElement.prototype.submit;
            HTMLFormElement.prototype.submit = function() {
                const action = this.getAttribute('action');
                const method = this.getAttribute('method');
                
                if (action && (action.includes('oauth') || action.includes('authorize') || action.includes('signin'))) {
                    console.log('OAuth2 form submission detected');
                    console.log('  Action:', action);
                    console.log('  Method:', method);
                    
                    // Log form data
                    const formData = new FormData(this);
                    for (const [key, value] of formData.entries()) {
                        if (key !== 'password') { // Don't log passwords
                            console.log('  Field:', key, '=', typeof value);
                        }
                    }
                }
                
                return OriginalFormSubmit.call(this);
            };
            
            // 5. Fix missing request parameter if it's removed by WebView
            window.addEventListener('load', function() {
                // Find all forms on the page
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    // Check if this is an OAuth form
                    if (form.action && form.action.includes('oauth')) {
                        const requestField = form.querySelector('input[name="request"]');
                        
                        // If request field exists but is empty, try to reconstruct it
                        if (requestField && !requestField.value) {
                            console.warn('OAuth request field is empty, attempting to restore');
                            // The request parameter will be generated by the server
                            // This is just informational logging
                        }
                    }
                });
            }, false);
            
            // 6. Handle response interception for OAuth errors
            const originalSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.send = function(body) {
                this.addEventListener('load', function() {
                    if (this.status >= 400) {
                        const responseText = this.responseText || '';
                        if (responseText.includes('AADSTS90014') || responseText.includes('request')) {
                            console.error('OAuth error detected:', responseText.substring(0, 200));
                        }
                    }
                });
                return originalSend.apply(this, arguments);
            };
            
            console.log('OAuth2 support scripts loaded successfully');
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
        // Proper WebView cleanup to prevent memory leaks
        // DO NOT clear cache/cookies as this breaks OAuth login sessions
        webView.apply {
            stopLoading()
            webViewClient = null
            webChromeClient = null
            // Don't clear history, cache, or cookies - needed for OAuth persistence
            loadUrl("about:blank")
            removeAllViews()
            destroy()
        }
        super.onDestroy()
    }
}
