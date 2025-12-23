# Add project specific ProGuard rules here.

# ===========================
# WebView JavaScript Interface
# ===========================
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebView classes
-keep class android.webkit.** { *; }
-keep class androidx.webkit.** { *; }
-dontwarn android.webkit.**
-dontwarn androidx.webkit.**

# ===========================
# Kotlin
# ===========================
-keep class kotlin.** { *; }
-keep class kotlin.Metadata { *; }
-dontwarn kotlin.**
-keepclassmembers class **$WhenMappings {
    <fields>;
}
-keepclassmembers class kotlin.Metadata {
    public <methods>;
}
-assumenosideeffects class kotlin.jvm.internal.Intrinsics {
    static void checkParameterIsNotNull(java.lang.Object, java.lang.String);
}

# ===========================
# AndroidX
# ===========================
-keep class androidx.** { *; }
-keep interface androidx.** { *; }
-dontwarn androidx.**

# ===========================
# Application Classes
# ===========================
-keep class com.jiomosa.webview.** { *; }

# Keep Activity classes
-keep public class * extends android.app.Activity
-keep public class * extends androidx.appcompat.app.AppCompatActivity

# ===========================
# Optimization
# ===========================
# Enable optimization
-optimizations !code/simplification/arithmetic,!code/simplification/cast,!field/*,!class/merging/*
-optimizationpasses 5
-allowaccessmodification
-dontpreverify

# ===========================
# Attributes
# ===========================
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes InnerClasses
-keepattributes EnclosingMethod
-keepattributes SourceFile,LineNumberTable

# ===========================
# Remove Logging
# ===========================
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# ===========================
# Material Components
# ===========================
-keep class com.google.android.material.** { *; }
-dontwarn com.google.android.material.**

# ===========================
# Stealth WebView Activity
# ===========================
-keep class com.jiomosa.webview.StealthWebViewActivity { *; }
-keepclassmembers class com.jiomosa.webview.StealthWebViewActivity$* { *; }
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# Keep WebView JavaScript interface methods
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebView related classes
-keep class android.webkit.** { *; }
-keep class androidx.webkit.** { *; }

# Keep Kotlin metadata
-keep class kotlin.Metadata { *; }

# Keep application class
-keep class com.jiomosa.webview.** { *; }
