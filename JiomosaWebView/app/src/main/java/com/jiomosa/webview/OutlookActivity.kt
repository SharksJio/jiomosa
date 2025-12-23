package com.jiomosa.webview

import android.content.Intent

class OutlookActivity : StealthWebViewActivity() {
    override fun provideInitialUrl(intent: Intent): String = "https://outlook.office.com/mail"
}
