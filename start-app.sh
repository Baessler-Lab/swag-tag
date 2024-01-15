#!/bin/bash

python -m streamlit run "./swagtag/main.py" \
--server.fileWatcherType none \
--server.port 8510 \
--server.enableCORS false \
--server.enableXsrfProtection false \
--server.enableWebsocketCompression false \
--server.baseUrlPath "/swag-tag"
