#!/bin/sh


echo "Delete old pyc files"
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

echo "restart HW-API (Nginx Unit)"
curl http://127.0.0.1:8443/control/applications/hw-ctrl-fastapi/restart
