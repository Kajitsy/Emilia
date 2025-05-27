# How to Fix the Issue

[![ru](https://img.shields.io/badge/FIX_ERROR-ru-red.svg)](../ru/FIX_ERROR.md)

## EXE Version or Winget Installation
The EXE version is officially supported on **Windows 10 x64** and **Windows 11**.
Other platforms have not been tested and are **not officially supported**.

### Emilia Doesn't Start
- If you're launching the app for the first time without saved login data, try setting the following environment variable: `QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer"`