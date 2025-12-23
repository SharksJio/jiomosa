package com.jiomosa.webview

import android.content.Intent

class OneDriveActivity : StealthWebViewActivity() {
    override fun provideInitialUrl(intent: Intent): String = "https://rilcloud-my.sharepoint.com"
}
