#!/usr/bin/env bash
#TODO:
# This should be able to determine the correct version of twistd on the system
# I don't know enough about the various linux twistd setups to implement this.
# How can we get twistd to tell us what version of python it's invoking? 
# On my box twistd is invoking python 2.7 and not python 3
twistd3 -v  >/dev/null 2>&1 || { echo >&2 "I require twistd3 but it's not installed.  Aborting."; exit 1; }
twistd3 --nodaemon --python bridge.py
#twistd  --nodaemon --python bridge.py
#twistd --python bridge.py
