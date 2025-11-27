package com.jiomosa.webview;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;

import androidx.appcompat.app.AppCompatActivity;

/**
 * StealthWebViewActivity - Android WebView with Stealth Parameters
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
 *   Intent intent = new Intent(this, StealthWebViewActivity.class);
 *   intent.putExtra("url", "https://outlook.office.com/mail");
 *   startActivity(intent);
 */
public class StealthWebViewActivity extends AppCompatActivity {

    private static final String TAG = "StealthWebView";
    
    private WebView webView;
    private ProgressBar progressBar;
    
    // Default URL if none provided - loads actual Outlook Mail directly
    private static final String DEFAULT_URL = "https://outlook.office.com/mail";
    
    // Stealth User-Agent matching desktop Chrome
    // Same as server-side Playwright stealth configuration
    private static final String STEALTH_USER_AGENT = 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_stealth_webview);
        
        // Initialize views
        webView = findViewById(R.id.stealthWebView);
        progressBar = findViewById(R.id.progressBar);
        
        // Enable WebView debugging (remove in production)
        WebView.setWebContentsDebuggingEnabled(true);
        
        // Configure WebView with stealth settings
        configureStealthWebView();
        
        // Get URL from intent or use default
        String url = getIntent().getStringExtra("url");
        if (url == null || url.isEmpty()) {
            url = DEFAULT_URL;
        }
        
        Log.d(TAG, "Loading URL with stealth parameters: " + url);
        
        // Load the URL
        webView.loadUrl(url);
    }
    
    /**
     * Configure WebView with stealth parameters
     * Applies all necessary settings to evade bot detection
     */
    @SuppressLint("SetJavaScriptEnabled")
    private void configureStealthWebView() {
        WebSettings webSettings = webView.getSettings();
        
        // === Essential Settings ===
        
        // Enable JavaScript (required for most modern sites)
        webSettings.setJavaScriptEnabled(true);
        
        // Enable DOM storage (localStorage, sessionStorage)
        webSettings.setDomStorageEnabled(true);
        
        // Enable database storage
        webSettings.setDatabaseEnabled(true);
        
        // === User-Agent Spoofing ===
        
        // Set desktop Chrome User-Agent to appear as regular browser
        // This matches the User-Agent used in server-side Playwright stealth
        webSettings.setUserAgentString(STEALTH_USER_AGENT);
        
        // === Media and Content Settings ===
        
        // Allow mixed content (HTTP on HTTPS pages)
        webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        
        // Enable media playback without user gesture
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        
        // Load images automatically
        webSettings.setLoadsImagesAutomatically(true);
        
        // Block network images initially for faster load (optional)
        webSettings.setBlockNetworkImage(false);
        
        // === Cache and Storage ===
        
        // Use default cache mode
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        
        // Enable app cache (deprecated but still works on older APIs)
        webSettings.setAppCacheEnabled(true);
        
        // === Zoom and Display ===
        
        // Enable zoom controls
        webSettings.setBuiltInZoomControls(true);
        webSettings.setDisplayZoomControls(false);
        
        // Use wide viewport for desktop-like rendering
        webSettings.setUseWideViewPort(true);
        webSettings.setLoadWithOverviewMode(true);
        
        // === File Access ===
        
        // Allow file access from file URLs
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        
        // === Cookie Settings ===
        
        // Enable cookies
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);
        
        // === Hardware Acceleration ===
        
        // Enable hardware acceleration for better performance
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);
        
        // === WebView Clients ===
        
        // Set WebViewClient with stealth script injection
        webView.setWebViewClient(new StealthWebViewClient());
        
        // Set WebChromeClient for progress updates
        webView.setWebChromeClient(new StealthWebChromeClient());
        
        Log.d(TAG, "Stealth WebView configured with User-Agent: " + STEALTH_USER_AGENT);
    }
    
    /**
     * Custom WebViewClient that injects stealth scripts
     */
    private class StealthWebViewClient extends WebViewClient {
        
        @Override
        public void onPageStarted(WebView view, String url, Bitmap favicon) {
            super.onPageStarted(view, url, favicon);
            
            Log.d(TAG, "Page started loading: " + url);
            
            // Show progress bar
            if (progressBar != null) {
                progressBar.setVisibility(View.VISIBLE);
            }
            
            // Inject stealth scripts immediately
            // This runs BEFORE the page's JavaScript
            injectStealthScripts(view);
        }
        
        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            
            Log.d(TAG, "Page finished loading: " + url);
            
            // Hide progress bar
            if (progressBar != null) {
                progressBar.setVisibility(View.GONE);
            }
            
            // Re-inject stealth scripts to ensure they persist
            // Some SPAs may override our changes
            injectStealthScripts(view);
        }
        
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String url = uri.toString();
            
            // Handle external links (e.g., tel:, mailto:)
            if (url.startsWith("tel:") || url.startsWith("mailto:")) {
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                startActivity(intent);
                return true;
            }
            
            // Load HTTP/HTTPS URLs in WebView
            if (url.startsWith("http://") || url.startsWith("https://")) {
                return false; // Let WebView handle it
            }
            
            // Handle other schemes externally
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                startActivity(intent);
            } catch (Exception e) {
                Log.e(TAG, "Cannot handle URL: " + url, e);
            }
            
            return true;
        }
    }
    
    /**
     * Custom WebChromeClient for progress and console logging
     */
    private class StealthWebChromeClient extends WebChromeClient {
        
        @Override
        public void onProgressChanged(WebView view, int newProgress) {
            super.onProgressChanged(view, newProgress);
            
            if (progressBar != null) {
                progressBar.setProgress(newProgress);
                
                if (newProgress >= 100) {
                    progressBar.setVisibility(View.GONE);
                }
            }
        }
        
        @Override
        public void onReceivedTitle(WebView view, String title) {
            super.onReceivedTitle(view, title);
            
            // Update activity title
            if (title != null && !title.isEmpty()) {
                setTitle(title);
            }
        }
    }
    
    /**
     * Inject stealth JavaScript scripts into the WebView
     * These scripts override browser fingerprinting detection
     */
    private void injectStealthScripts(WebView view) {
        String stealthScript = StealthWebViewHelper.getStealthScript();
        
        view.evaluateJavascript(stealthScript, value -> {
            Log.d(TAG, "Stealth scripts injected successfully");
        });
    }
    
    /**
     * Handle back button to navigate within WebView
     */
    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
    
    /**
     * Handle hardware key events
     */
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
        }
    }
    
    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
        }
        super.onDestroy();
    }
}
