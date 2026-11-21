cd /home/claude/lp
export SHELL_BODY=1
env TYPE=loaderM KIND=can SEED=57 GEAR=ammorack RES=1024 BS=2 python3 lp1.py > log_loaderM.txt 2>&1
env TYPE=at KIND=rocket SEED=34 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_at.txt 2>&1
env TYPE=loaderR KIND=spare SEED=58 GEAR=rocket RES=1024 BS=2 python3 lp1.py > log_loaderR.txt 2>&1
env TYPE=sniper KIND=sniper HEAD=sniper GEAR=light SEED=21 RES=1024 BS=2 python3 lp1.py > log_sniper.txt 2>&1
env TYPE=spotter KIND=binos HEAD=spotter GEAR=comms SEED=22 RES=1024 BS=2 python3 lp1.py > log_spotter.txt 2>&1
env TYPE=flagb2 KIND=flag GEAR=std SEED=41 NOBANNER=1 RES=1024 BS=2 python3 lp1.py > log_flagb2.txt 2>&1
env TYPE=officer KIND=pistol HEAD=officer GEAR=light SEED=42 RES=1024 BS=2 python3 lp1.py > log_officer.txt 2>&1
echo DONE > done_shell.txt
