#!/bin/sh
cd /home/claude/lp
while [ ! -f done3.txt ]; do sleep 20; done
env TYPE=sniper KIND=sniper HEAD=sniper GEAR=light SEED=21 RES=1024 BS=2 python3 lp1.py > log_sniper2.txt 2>&1
echo DONE > done4.txt
