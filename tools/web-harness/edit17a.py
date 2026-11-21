p='/home/claude/vu/v17.html';s=open(p).read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(s.count(a),a[:70]);s=s.replace(a,b)
# ---------------- markup ----------------
i=s.index('<div id="right" class="panel">');j=s.index('<div id="city" class="panel" hidden></div>')
s=s[:i]+'''<div id="right" class="panel">
  <div id="facList"></div>
</div>

<div id="log" class="panel"></div>

<!-- classic RTS command bar: minimap | selection | command card -->
<div id="cmd" class="panel">
  <div id="mapBox"><canvas id="mini" width="300" height="200" aria-label="Minimap"></canvas></div>
  <div id="selBox">
    <div id="selHead"></div>
    <div id="selBody"></div>
  </div>
  <div id="card">
    <div id="cardTabs" role="tablist"></div>
    <div id="cardTop"></div>
    <div id="cardGrid"></div>
    <div id="cardHint"></div>
    <div class="gstrip">
      <button id="bMissile" title="Launch a ballistic missile from your HQ (Q). Each HQ you hold builds one every 2 minutes.">Missile <b id="mslN" class="num">0</b><small id="mslT" class="num"></small><kbd>Q</kbd></button>
      <label class="tog" title="Fire missiles automatically at the densest enemy target"><input type="checkbox" id="autoM"> Auto</label>
      <button id="bRallyG" title="Pick one rally point where every base sends its new troops">Rally all</button><button id="bRallyGx" title="Clear the global rally point" aria-label="Clear global rally">×</button>
      <button id="bAir" title="Select all your aircraft">Aircraft</button>
      <label class="tog" title="New troops fill each base's garrison before they gather outside"><input type="checkbox" id="autoG" checked> Garrison</label>
    </div>
  </div>
</div>

'''+s[j:]
rep('<div id="city" class="panel" hidden></div>\n','')

# ---------------- CSS ----------------
i=s.index('/* right column */');j=s.index('/* log */')
s=s[:i]+'''/* right column: armies */
#right{top:calc(10px + env(safe-area-inset-top,0px));right:max(10px,env(safe-area-inset-right,0px));width:270px;padding:4px 8px;display:flex;flex-direction:column;gap:0}
#right:has(#facList:empty){display:none}
.fac{display:grid;grid-template-columns:8px 1fr auto;gap:2px 8px;align-items:center;padding:5px 2px;border-top:1px solid var(--line)}
.fac:first-child{border-top:0}
.fac .sw{width:8px;height:22px;grid-row:span 2}
.fac .nm{font-family:var(--f-display);font-weight:600;font-size:12.5px;letter-spacing:.04em}
.fac .ct{font-family:var(--f-mono);font-size:11px;color:var(--dim);text-align:right}
.fac .sub{grid-column:2 / 4;display:flex;align-items:center;gap:6px;font-size:11px;color:var(--dim)}
.heat{flex:1;height:4px;background:#1a2a31;position:relative;overflow:hidden}
.heat i{position:absolute;inset:0 auto 0 0;background:currentColor}
.fac.dead{opacity:.4}

/* bottom command bar: minimap | selection | command card */
#cmd{left:50%;transform:translateX(-50%);bottom:calc(8px + env(safe-area-inset-bottom,0px));display:grid;grid-template-columns:auto minmax(260px,1fr) auto;
  width:min(1260px,calc(100% - 16px));height:206px}
#mapBox{padding:8px;border-right:1px solid var(--line);display:flex;align-items:center}
#mini{display:block;height:100%;max-height:188px;width:auto;max-width:300px;background:#1d4b5c;border:1px solid var(--line);cursor:pointer}
#selBox{padding:8px 12px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:6px;min-width:0;overflow:hidden}
#selHead{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-size:12.5px;line-height:1.3}
#selHead b{font-family:var(--f-display);font-weight:600;color:var(--militia);font-size:15px}
#selHead .dim{color:var(--dim)}
#selBody{flex:1;min-height:0;overflow:auto;font-size:12.5px;line-height:1.35;color:var(--text)}
#selBody .hint{color:var(--dim);margin:0 0 6px}
#selBody .tips{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:12px;color:var(--dim)}
#selBody .tips kbd{font-family:var(--f-mono);font-size:10.5px;color:var(--militia)}
/* unit portraits */
.ports{display:grid;grid-template-columns:repeat(auto-fill,minmax(46px,1fr));gap:4px}
.pt{position:relative;height:40px;border:1px solid var(--line-hi);background:var(--panel-hi);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;color:var(--militia)}
.pt:hover{border-color:var(--militia)}
.pt svg{width:24px;height:15px}
.pt .cnt{position:absolute;top:1px;right:3px;font-family:var(--f-mono);font-size:10px;color:var(--text)}
.pt .gar{position:absolute;top:1px;left:3px;font-family:var(--f-mono);font-size:9px;color:var(--warn)}
.pt .hp{position:absolute;left:3px;right:3px;bottom:3px;height:3px;background:rgba(0,0,0,.6)}
.pt .hp i{display:block;height:100%;background:var(--good)}
.pt .st{position:absolute;bottom:6px;right:3px;font-family:var(--f-mono);font-size:8.5px;color:var(--dim)}
/* base info in the selection box */
.ztag{font-size:11px;color:var(--dim);margin-left:4px}
.zhp{display:inline-block;width:90px;height:5px;background:rgba(0,0,0,.55);vertical-align:middle;margin-left:6px}
.zhp i{display:block;height:100%;background:var(--good)}.zhp.low i{background:var(--warn)}.zhp.gone i{background:var(--bad)}
.zrow{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12px;color:var(--dim)}.zrow b{color:var(--text)}
.plotGrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(66px,1fr));gap:4px;margin-top:6px}
/* command card */
#card{width:372px;padding:6px 10px 8px;display:flex;flex-direction:column;gap:5px;min-width:0}
#cardTabs{display:flex;gap:2px;border-bottom:1px solid var(--line)}
#cardTabs button{font-family:var(--f-display);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;padding:4px 10px 5px;color:var(--dim);border-bottom:2px solid transparent;margin-bottom:-1px}
#cardTabs button[aria-selected="true"]{color:var(--text);border-bottom-color:var(--militia)}
#cardTop{display:flex;align-items:center;gap:6px;font-size:12px;min-height:0}
#cardTop:empty{display:none}
#cardTop b{font-family:var(--f-display);font-weight:600;color:var(--text)}
#cardTop button{font-family:var(--f-display);font-size:11px;padding:1px 7px;border:1px solid var(--line-hi)}
#cardGrid{display:grid;grid-template-columns:repeat(5,1fr);grid-auto-rows:52px;gap:4px;flex:1;min-height:0;overflow:auto;align-content:start}
.cb{position:relative;border:1px solid var(--line-hi);background:var(--panel-hi);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;padding:3px 2px;text-align:center;min-width:0}
.cb:hover:not(:disabled){border-color:var(--militia)}
.cb:disabled{opacity:.38;cursor:not-allowed}
.cb[aria-pressed="true"]{background:var(--militia);color:var(--ink);border-color:var(--militia)}
.cb[aria-pressed="true"] svg,.cb[aria-pressed="true"] .ic{color:var(--ink)}
.cb svg{width:24px;height:15px;color:var(--militia);flex:none}
.cb .ic{font-family:var(--f-display);font-weight:700;font-size:14px;color:var(--militia);line-height:1}
.cb .n{font-family:var(--f-display);font-weight:600;font-size:10.5px;line-height:1.05;letter-spacing:.02em;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cb .c{font-family:var(--f-mono);font-size:9.5px;color:var(--dim)}
.cb[aria-pressed="true"] .c{color:var(--ink)}
.cb kbd{position:absolute;top:2px;right:4px;font-family:var(--f-mono);font-size:9.5px;color:var(--militia)}
.cb .pb{position:absolute;left:0;bottom:0;height:3px;background:var(--warn);width:0}
#cardHint{font-size:11.5px;color:var(--dim);line-height:1.3;min-height:15px;max-height:46px;overflow:hidden}
#cardHint b{color:var(--text);font-weight:600}#cardHint .why{color:var(--warn)}
.gstrip{display:flex;gap:4px;align-items:center;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:5px}
.gstrip button{font-family:var(--f-display);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;padding:3px 7px;border:1px solid var(--line-hi);color:var(--text)}
.gstrip button kbd{font-family:var(--f-mono);font-size:9.5px;color:var(--militia);margin-left:4px}
.gstrip button:disabled{opacity:.35;cursor:default}
.gstrip button[aria-pressed="true"]{background:var(--militia);color:var(--ink)}
.gstrip .tog{font-size:11px}
#bMissile b{color:var(--dim);margin-left:4px}#bMissile small{font-size:9.5px;color:var(--dim);margin-left:5px;letter-spacing:0}
#bMissile.ready{border-color:#ff6a50}#bMissile.ready b{color:#ff8a70}
.tog{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--dim);cursor:pointer}
.tog input{accent-color:var(--militia)}
.fogtog{font-size:13px;color:var(--text);margin-top:4px}.fogtog input{width:16px;height:16px}.fogtog small{font-size:11.5px}
/* aircraft list */
.airall{display:inline-flex;gap:3px;margin-left:6px}.airall button,.airrow .tg button{font-family:var(--f-display);font-size:10px;padding:1px 6px;border:1px solid var(--line-hi);text-transform:uppercase}
.airlist{display:flex;flex-direction:column;gap:2px;margin-top:4px}
.airrow{position:relative;display:grid;grid-template-columns:78px 1fr auto;gap:6px;align-items:center;font-size:11.5px;padding-bottom:3px}
.airrow .as{color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.airrow .tg button[aria-pressed="true"]{background:var(--militia);color:var(--ink)}
.airrow .hb{position:absolute;left:0;bottom:0;height:2px;background:var(--good)}

'''+s[j:]
# log sits above the bar
rep("#log{left:max(10px,env(safe-area-inset-left,0px));bottom:calc(214px + env(safe-area-inset-bottom,0px));","#log{left:max(10px,env(safe-area-inset-left,0px));bottom:calc(222px + env(safe-area-inset-bottom,0px));")
# old zone-view panel css → keep plot / bopt classes, drop #city box
rep("#city{left:max(10px,env(safe-area-inset-left,0px));top:calc(78px + env(safe-area-inset-top,0px));width:340px;max-width:calc(100% - 20px);max-height:calc(100% - 100px);overflow:auto;padding:12px 14px;display:flex;flex-direction:column;gap:10px}\n","")
rep(".plotGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}\n","")
rep("body.inmenu #top,body.inmenu #right,body.inmenu #log,body.inmenu #cmd,body.inmenu #city,body.inmenu #tut{display:none}","body.inmenu #top,body.inmenu #right,body.inmenu #log,body.inmenu #cmd,body.inmenu #tut{display:none}")
rep("#tut.shift{left:calc(max(10px,env(safe-area-inset-left,0px)) + 350px)}\n","")
rep("""@media (max-width:760px){
  #right{width:170px}
  #cmd{flex-direction:column;left:10px;right:10px;transform:none}
  #sel{width:auto;border-right:0;border-bottom:1px solid var(--line)}
  #recBtns{grid-template-columns:repeat(4,1fr)}.rb{width:auto}""","""@media (max-width:1000px){#card{width:320px}#mini{max-width:200px}}
@media (max-width:760px){
  #right{width:170px}
  #cmd{grid-template-columns:1fr;height:auto;max-height:60vh;overflow:auto}
  #mapBox{display:none}
  #selBox{border-right:0;border-bottom:1px solid var(--line);max-height:120px}
  #card{width:auto}""")
open(p,'w').write(s)
