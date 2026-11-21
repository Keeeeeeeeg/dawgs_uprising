#!/bin/sh
cd /home/claude/lp
while [ ! -f done.txt ]; do sleep 20; done
TYPE=mg KIND=mg SEED=33 GEAR=ammo RES=1024 BS=4 python3 lp1.py > log_mg.txt 2>&1
TYPE=loaderM SEED=57 GEAR=ammo SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_loaderM.txt 2>&1
echo DONE > done_mg.txt
