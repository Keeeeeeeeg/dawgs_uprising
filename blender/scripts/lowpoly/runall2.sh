#!/bin/sh
cd /home/claude/lp
B="RES=1024 BS=2"
env TYPE=rifle SEED=51 RES=1024 BS=2 python3 lp1.py > log_rifle.txt 2>&1
env TYPE=mg KIND=mg SEED=33 GEAR=ammo RES=1024 BS=2 python3 lp1.py > log_mg.txt 2>&1
env TYPE=loaderM KIND=can SEED=57 GEAR=ammorack RES=1024 BS=2 python3 lp1.py > log_loaderM.txt 2>&1
env TYPE=at KIND=rocket SEED=34 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_at.txt 2>&1
env TYPE=loaderR KIND=spare SEED=58 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_loaderR.txt 2>&1
echo DONE > done_a.txt
env TYPE=rifleL SEED=20 HEAD=leader GEAR=radio SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleL.txt 2>&1
env TYPE=rifleB SEED=52 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleB.txt 2>&1
env TYPE=rifleC SEED=53 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleC.txt 2>&1
env TYPE=rifleD SEED=54 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleD.txt 2>&1
env TYPE=rifleE SEED=56 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleE.txt 2>&1
echo DONE > done.txt
