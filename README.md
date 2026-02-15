# Shopping App (Kivy)

Minimal Python mobile shopping app built with Kivy. This is a starter scaffold with a product catalog, cart, and mock checkout.

Files added:
- [main.py](main.py)
- [shopping.kv](shopping.kv)
- [models.py](models.py)
- [requirements.txt](requirements.txt)

Run locally (Windows):

```bash
python -m pip install -r requirements.txt
python main.py
```

Notes for building Android APK:
- Buildozer runs on Linux; use WSL2 or a Linux builder.
- Typical flow (on Linux):

```bash
pip install buildozer
buildozer init
# edit buildozer.spec to set app name, package, requirements
buildozer android debug
```

Need help packaging the app for Android/iOS? I can add a `buildozer.spec` or a Toga/briefcase scaffold.
