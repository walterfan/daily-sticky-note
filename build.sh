#!/bin/bash -e
pyinstaller --onefile --console --windowed --clean --upx-dir=/opt/homebrew/bin/upx  --add-data "etc:etc" app/sticky_note.py
#pyinstaller --onefile --console --debug all --add-data "etc:etc" app/sticky_note.py
