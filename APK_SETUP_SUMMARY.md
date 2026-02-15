# APK Build Setup - Quick Start

## What Was Done

✅ **1. API Integration**
- Added `/api/products` endpoints to Flask (web_app.py)
- Mobile app now fetches products from backend server instead of hardcoded data

✅ **2. Updated Kivy App** (main.py)
- Integrated HTTP requests to fetch products from API
- Added error handling for network issues
- Loads products asynchronously (non-blocking UI)
- Configurable backend URL: `BACKEND_URL = 'http://192.168.1.100:5000'`

✅ **3. Dependencies Updated** (requirements.txt)
- Added `kivy==2.1.0` and `requests==2.31.0`

✅ **4. APK Configuration** (buildozer.spec)
- Ready to build for Android
- Includes all required permissions (INTERNET, ACCESS_NETWORK_STATE)
- Targets Android 5.0+ (minapi 21)

✅ **5. Build Guide** (BUILD_APK_GUIDE.md)
- Complete instructions for building the APK
- Troubleshooting tips

## Quick Build Steps

### Windows Setup

1. **Install Java JDK 11+** (required for Android build)
   - Download from oracle.com or use OpenJDK

2. **Install Buildozer**
   ```powershell
   pip install buildozer cython
   ```

3. **Build the APK** (from your project directory)
   ```powershell
   buildozer android debug
   ```
   This will:
   - Download Android SDK (first time takes 5-10 minutes)
   - Compile your app
   - Generate APK at `bin/shoppingapp-0.1-debug.apk`

### Before Building
Edit the backend URL in **main.py** line 13:
```python
BACKEND_URL = 'http://YOUR_COMPUTER_IP:5000'
```
Find your IP: 
- Windows: Open Command Prompt, run `ipconfig`
- Use the Default Gateway or IPv4 Address

## Running the App

**1. Start Flask server:**
```bash
python web_app.py
```
Server runs on `http://YOUR_IP:5000`

**2. Install APK on Android phone:**
- Enable "Unknown Sources" in Settings → Security
- Copy `bin/shoppingapp-0.1-debug.apk` to phone
- Or use: `adb install bin/shoppingapp-0.1-debug.apk`

**3. Both phone and server must be on the same network**

## File Changes Summary

| File | Changes |
|------|---------|
| `main.py` | Added API calls, async loading, error handling |
| `web_app.py` | Added `/api/products` endpoints with jsonify |
| `requirements.txt` | Added kivy, requests |
| `buildozer.spec` | New - Android build configuration |
| `BUILD_APK_GUIDE.md` | New - Comprehensive build guide |

## Testing Locally First

Before building APK, test the API locally:
```bash
python web_app.py
# In another terminal:
curl http://localhost:5000/api/products
```

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Connection refused | Check Flask server is running on correct IP |
| Module not found (kivy, requests) | Run `pip install -r requirements.txt` |
| Java not found | Install JDK and add to System PATH |
| Buildozer not found | Run `pip install buildozer cython` |

## Next Steps

1. Read `BUILD_APK_GUIDE.md` for detailed instructions
2. Set up Java and Buildozer 
3. Update `BACKEND_URL` in main.py with your server IP
4. Run `buildozer android debug`
5. Test on Android device

## Support

Refer to:
- `BUILD_APK_GUIDE.md` - Detailed build instructions
- Buildozer docs: https://buildozer.readthedocs.io/
- Kivy docs: https://kivy.org/doc/
