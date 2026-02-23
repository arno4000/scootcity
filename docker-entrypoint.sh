#!/bin/bash
set -e
python scripts/init_db.py
exec "$@"
