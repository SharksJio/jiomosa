package com.jiomosa.webview

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.pm.ShortcutInfoCompat
import androidx.core.content.pm.ShortcutManagerCompat
import androidx.core.graphics.drawable.IconCompat

/**
 * Main launcher activity with app selector and shortcut creation.
 * On first launch, offers to create home screen shortcuts for each app.
 */
class MainActivity : AppCompatActivity() {

    private val apps = arrayOf(
        "Outlook Mail",
        "Microsoft Teams",
        "OneDrive",
        "Whiteboard"
    )
    
    private val activities = arrayOf(
        OutlookActivity::class.java,
        TeamsActivity::class.java,
        OneDriveActivity::class.java,
        WhiteboardActivity::class.java
    )
    
    private val icons = intArrayOf(
        R.mipmap.ic_outlook,
        R.mipmap.ic_teams,
        R.mipmap.ic_onedrive,
        R.mipmap.ic_whiteboard
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val prefs = getSharedPreferences("jiomosa_prefs", MODE_PRIVATE)
        val shortcutsCreated = prefs.getBoolean("shortcuts_created", false)
        
        // Auto-create shortcuts on first launch
        if (!shortcutsCreated && ShortcutManagerCompat.isRequestPinShortcutSupported(this)) {
            createAllShortcuts()
            prefs.edit().putBoolean("shortcuts_created", true).apply()
        }
        
        showAppSelector()
    }
    
    private fun createAllShortcuts() {
        Toast.makeText(
            this,
            "Creating shortcuts on home screen...",
            Toast.LENGTH_SHORT
        ).show()
        
        // Create shortcuts with delay to avoid Android rate limiting
        android.os.Handler(mainLooper).post {
            for (i in apps.indices) {
                android.os.Handler(mainLooper).postDelayed({
                    createSingleShortcut(i)
                }, (i * 500).toLong())
            }
        }
        
        showAppSelector()
    }
    
    private fun createSingleShortcut(index: Int) {
        val intent = Intent(this, activities[index]).apply {
            action = Intent.ACTION_VIEW
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        
        val shortcut = ShortcutInfoCompat.Builder(this, "shortcut_${activities[index].simpleName}")
            .setShortLabel(apps[index])
            .setLongLabel(apps[index])
            .setIcon(IconCompat.createWithResource(this, icons[index]))
            .setIntent(intent)
            .build()
        
        ShortcutManagerCompat.requestPinShortcut(this, shortcut, null)
    }
    
    private fun showAppSelector() {
        AlertDialog.Builder(this)
            .setTitle("Select App")
            .setItems(apps) { _, which ->
                startActivity(Intent(this, activities[which]))
                finish()
            }
            .setNeutralButton("Add Shortcuts") { _, _ ->
                createAllShortcuts()
                finish()
            }
            .setOnCancelListener {
                finish()
            }
            .show()
    }
}
