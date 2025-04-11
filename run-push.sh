#!/bin/sh
cd "$(dirname "$0")";
CWD="$(pwd)"
echo $CWD
/home/jovan-cvetkovic/Workspace/projects/carelink-python-client/myenv/bin/python3 carelink_client2_push.py