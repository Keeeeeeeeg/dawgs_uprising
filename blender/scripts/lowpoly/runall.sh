#!/bin/sh
cd /home/claude/lp
TYPE=rifle SEED=51 RES=1024 BS=4 python3 lp1.py > log_rifle.txt 2>&1
TYPE=rifleB SEED=52 SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_rifleB.txt 2>&1
TYPE=rifleC SEED=53 SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_rifleC.txt 2>&1
TYPE=rifleD SEED=54 SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_rifleD.txt 2>&1
TYPE=rifleE SEED=56 SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_rifleE.txt 2>&1
TYPE=rifleL SEED=20 HEAD=leader GEAR=radio SHAREW=1 RES=1024 BS=4 python3 lp1.py > log_rifleL.txt 2>&1
echo DONE > done.txt
