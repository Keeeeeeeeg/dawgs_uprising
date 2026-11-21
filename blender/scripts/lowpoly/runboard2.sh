cd /home/claude/lp
export SHELL_BODY=1
export HPART=1 TH=3400 TW=1800
env TYPE=bmShot BOARD=shot KIND=rifle SEED=61 RES=1024 BS=2 python3 lp1.py > log_bmShot.txt 2>&1
env TYPE=bmShotB BOARD=shot KIND=rifle SEED=62 RES=1024 BS=2 python3 lp1.py > log_bmShotB.txt 2>&1
env TYPE=bmDemo BOARD=demo KIND=rifle SEED=63 RES=1024 BS=2 python3 lp1.py > log_bmDemo.txt 2>&1
env TYPE=bmBreach BOARD=shield KIND=can SEED=64 RES=1024 BS=2 python3 lp1.py > log_bmBreach.txt 2>&1
echo DONE > done_board2.txt
