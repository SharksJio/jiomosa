package com.jiomosa.webview

import android.content.Intent

class TeamsActivity : StealthWebViewActivity() {
    override fun provideInitialUrl(intent: Intent): String = "https://teams.microsoft.com"
}
