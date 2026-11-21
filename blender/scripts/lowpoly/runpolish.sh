cd /home/claude/lp
export SHELL_BODY=1
env TYPE=rifle SEED=51 RES=1024 BS=2 python3 lp1.py > log_rifle.txt 2>&1
env TYPE=rifleB SEED=52 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleB.txt 2>&1
env TYPE=rifleC SEED=53 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleC.txt 2>&1
env TYPE=rifleD SEED=54 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleD.txt 2>&1
env TYPE=rifleE SEED=56 SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleE.txt 2>&1
env TYPE=rifleL SEED=20 HEAD=leader GEAR=radio SHAREW=1 RES=1024 BS=2 python3 lp1.py > log_rifleL.txt 2>&1
env TYPE=mg KIND=mg SEED=33 GEAR=ammo RES=1024 BS=2 python3 lp1.py > log_mg.txt 2>&1
env TYPE=loaderM KIND=can SEED=57 GEAR=ammorack RES=1024 BS=2 python3 lp1.py > log_loaderM.txt 2>&1
env TYPE=at KIND=rocket SEED=34 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_at.txt 2>&1
env TYPE=loaderR KIND=spare SEED=58 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_loaderR.txt 2>&1
env TYPE=sniper KIND=sniper HEAD=sniper GEAR=light SEED=21 RES=1024 BS=2 python3 lp1.py > log_sniper.txt 2>&1
env TYPE=spotter KIND=binos HEAD=spotter GEAR=comms SEED=22 RES=1024 BS=2 python3 lp1.py > log_spotter.txt 2>&1
env TYPE=flagb2 KIND=flag GEAR=std SEED=41 NOBANNER=1 RES=1024 BS=2 python3 lp1.py > log_flagb2.txt 2>&1
env TYPE=officer KIND=pistol HEAD=officer GEAR=light SEED=42 RES=1024 BS=2 python3 lp1.py > log_officer.txt 2>&1
export HPART=1 TH=2600 TW=1800
env TYPE=bmShot BOARD=shot KIND=rifle SEED=61 RES=1024 BS=2 python3 lp1.py > log_bmShot.txt 2>&1
env TYPE=bmShotB BOARD=shot KIND=rifle SEED=62 RES=1024 BS=2 python3 lp1.py > log_bmShotB.txt 2>&1
env TYPE=bmDemo BOARD=demo KIND=rifle SEED=63 RES=1024 BS=2 python3 lp1.py > log_bmDemo.txt 2>&1
env TYPE=bmBreach BOARD=shield KIND=can SEED=64 RES=1024 BS=2 python3 lp1.py > log_bmBreach.txt 2>&1
echo DONE > done_polish.txt
