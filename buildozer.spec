[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

version = 1.0

requirements = python3,kivy,requests

orientation = portrait

android.permissions = INTERNET

android.api = 33
android.minapi = 24

[buildozer]
log_level = 2
warn_on_root = 1
