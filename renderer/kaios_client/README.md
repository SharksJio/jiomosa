# KaiOS Cloud Browser Client

A Puffin-like cloud browser client for KaiOS devices (Gecko 48).

## Features

- **Video Streaming**: Real-time MJPEG streaming from cloud-rendered browser
- **Audio Streaming**: Web Audio API-based audio from cloud browser
- **D-Pad Navigation**: Number key cursor control (2/4/6/8 for up/left/right/down)
- **Gecko 48 Compatible**: ES5 JavaScript, -moz- CSS prefixes

## Controls

| Key | Action |
|-----|--------|
| 2 | Move cursor up |
| 4 | Move cursor left |
| 6 | Move cursor right |
| 8 | Move cursor down |
| 5 / Enter | Click |
| 1 | Back (previous page) |
| 3 | Scroll up |
| 9 | Scroll down |
| 0 | Home (launcher) |
| * | Toggle audio |
| # | Settings |

## Architecture

```
KaiOS Device (240x320)          Cloud Server
┌─────────────────────┐         ┌─────────────────────┐
│                     │         │                     │
│  kaios_client/      │◄───────►│  renderer/          │
│   launcher.html     │ WebSocket│   app.py           │
│   browser.html      │         │   audio_handler.py │
│   styles.css        │         │                     │
│   client.js         │         │  Chrome Container   │
│                     │         │   (with audio)      │
└─────────────────────┘         └─────────────────────┘
```

## Files

- `launcher.html` - App launcher with shortcuts
- `browser.html` - Main browser viewer
- `styles.css` - Gecko 48 compatible styles
- `client.js` - ES5 JavaScript client logic

## Deployment

1. Push files to KaiOS device via ADB:
   ```bash
   adb push kaios_client/ /data/local/tmp/jiomosa/
   ```

2. Access via device browser:
   ```
   file:///data/local/tmp/jiomosa/launcher.html
   ```

Or serve via HTTP and access:
   ```
   http://<server-ip>:5000/kaios/
   ```
