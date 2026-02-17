[app]
title = Shopping App
package.name = shoppingapp
package.domain = org.shoppingapp
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests,bin,instance,__pycache__

requirements = python3,kivy,requests

orientation = portrait
fullscreen = 1

android.api = 33
android.minapi = 21
android.ndk = 26b
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.enable_androidx = True
android.theme = "@android:style/Theme.NoTitleBar"
android.copy_libs = 1

p4a.branch = develop
p4a.use_sdl2 = 1

[buildozer]
log_level = 2
warn_on_root = 1
