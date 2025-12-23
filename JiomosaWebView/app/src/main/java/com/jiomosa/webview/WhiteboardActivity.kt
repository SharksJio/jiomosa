package com.jiomosa.webview

import android.content.Intent

class WhiteboardActivity : StealthWebViewActivity() {
    override fun provideInitialUrl(intent: Intent): String = "https://whiteboard.cloud.microsoft/"
}
