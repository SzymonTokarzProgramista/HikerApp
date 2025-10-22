[app]
title = Tourismo
package.name = tourismo
package.domain = org.tourismo
source.dir = .
source.include_exts = py,kv,png,jpg,txt,md,json
version = 0.1.0

# Biblioteki Pythona (kivy + mobilne utilsy)
requirements = python3,kivy==2.3.0,kivymd,plyer,pillow,requests

orientation = portrait
icon.filename = assets/icon.png
fullscreen = 0

# Uprawnienia
android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Zezwól na HTTP (cleartext) do lokalnego backendu podczas dev
android.allow_cleartext_traffic = 1

# (opcjonalnie)
# android.api = 33
# android.minapi = 24

[buildozer]
log_level = 2
warn_on_root = 1
