#! /bin/sh

mkfifo /tmp/pipe
python3 /opt/mash-o-matic/core/core.py < /tmp/pipe | /opt/mash-o-matic/gui > /tmp/pipe

