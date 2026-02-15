# Building an APK for the Shopping App

## Prerequisites

You need to install the following tools:

1. **Java Development Kit (JDK)** - Java 11 or later
   - Download from: https://www.oracle.com/java/technologies/downloads/
   - Or use OpenJDK from: https://jdk.java.net/

2. **Android SDK** 
   - Install Android Studio from: https://developer.android.com/studio
   - Or download command-line tools only

3. **Python** (already have it)

4. **Buildozer** - Install with:
   ```bash
   pip install buildozer cython
   ```

## Key Changes Made

### 1. **Flask API Endpoints** (web_app.py)
Added JSON API endpoints for the mobile app to communicate with:
- `GET /api/products` - Returns all products as JSON
- `GET /api/products/<id>` - Returns specific product details

### 2. **Updated Kivy App** (main.py)
Modified to:
- Fetch products from Flask backend instead of local sample data
- Make async HTTP requests to avoid blocking UI
- Handle network errors gracefully
- Configurable backend URL via `SHOPPING_API_URL` environment variable

Default backend URL: `http://192.168.1.100:5000`
- Change the `BACKEND_URL` in main.py to match your server's IP/domain

### 3. **Updated Requirements** (requirements.txt)
Added `requests` library for HTTP calls

## Configuration

### Important: Backend URL

Before building, update the backend URL in `main.py` line 13:
```python
BACKEND_URL = os.getenv('SHOPPING_API_URL', 'http://YOUR_SERVER_IP:5000')
```

Replace `YOUR_SERVER_IP` with:
- Your computer's local network IP (e.g., `192.168.0.5`)
- Or your public domain name if deploying online

## Building the APK

### Option 1: Using Buildozer (Recommended)

```bash
# Navigate to your project directory
cd c:\Users\ADMIN\Project\shopping

# Create initial buildozer.spec
buildozer android debug

# Wait for first build (downloads Android SDK, takes 5-10 minutes)

# Find your APK at: bin/shoppingapp-0.1-debug.apk
```

### Option 2: Manual setup with buildozer.spec

The project already includes a `buildozer.spec` file configured for basic Android building.

Key settings in buildozer.spec:
- `requirements = python3,kivy,requests` - Includes all needed packages
- `android.permissions = INTERNET,ACCESS_NETWORK_STATE` - Network permissions
- `android.api = 31` - Target Android 12
- `android.minapi = 21` - Minimum Android 5.0

## Running the App

1. **Start the Flask backend:**
   ```bash
   python web_app.py
   # Runs on http://192.168.1.100:5000 (adjust IP as needed)
   ```

2. **Transfer APK to phone and install:**
   - Enable "Unknown Sources" in Android settings
   - Install the APK from `bin/shoppingapp-0.1-debug.apk`

3. **Configure app connection:**
   - On the phone, set `SHOPPING_API_URL` or modify the hardcoded URL
   - Make sure both phone and server are on same network

## Troubleshooting

### Build Issues
- **"java not found"** - Install JDK and add to PATH
- **"Android SDK not found"** - Run `buildozer android debug` again, it will download SDK

### Connection Issues
- Verify Flask server is running and accessible
- Check phone and server are on same network
- Try pinging your server IP from phone
- Update `BACKEND_URL` in main.py to match your server's actual IP

### App Crashes
- Check logcat for errors: `adb logcat | grep python`
- Ensure all imports work (kivy, requests, etc.)

## Next Steps for Production

For a production APK:
1. Create a release key: `keytool -genkey -alias myapp -keystore my-key.keystore`
2. Build release: `buildozer android release`
3. Sign the APK with your key
4. Deploy to Google Play Store

## Resources

- Buildozer docs: https://buildozer.readthedocs.io/
- Kivy docs: https://kivy.org/doc/stable/
- Python for Android: https://python-for-android.readthedocs.io/
