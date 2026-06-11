#!/usr/bin/env bash
cd "$(dirname "$0")"
set -a; source ./bot.env; set +a
exec ./bin/python3.14 ./webexIncBot.py