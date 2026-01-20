[app]
title = Tourismo
package.name = tourismo
package.domain = org.tourismo

source.dir = .
source.include_exts = py,kv,png,jpg,txt,md,json
version = 0.1.0

requirements = python3,kivy==2.3.0,kivymd,plyer,pillow,requests,androidstorage4kivy


orientation = portrait
icon.filename = assets/icon.png
fullscreen = 0

# <<< TU NAJWAŻNIEJSZE >>>
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.allow_cleartext_traffic = 1

[buildozer]
log_level = 2
warn_on_root = 1
android.accept_sdk_license = True
