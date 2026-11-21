p='/home/claude/vu/v16.html';s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,a[:80];s=s.replace(a,b)

# ---- 1. airbase drawn like an airport diagram
i=s.index("  }else if(z.type==='airbase'){\n    // runway across the base")
j=s.index("  }else if(z.type==='hq'){\n    // a walled fortress town")
s=s[:i]+r"""  }else if(z.type==='airbase'){
    // drawn like an airport diagram (runway coordinates: x along the runway, z across it; taxiway z=5.5, stands z=11, terminal z=16.5):
    // runway with threshold bars, numbers, aiming marks and blast-pad chevrons; a parallel taxiway with three links and hold-short bars;
    // the apron with lead-in lines, the terminal and tower behind it, a hangar at each end of the apron and the fuel farm
    const A=z.air,rg=new THREE.Group();rg.position.set(A.cx-z.x,0,A.cz-z.z);rg.rotation.y=-A.ang;g.add(rg);
    const L=A.L,E=L/2+3,flat=(w,d,m,x,zz,yy)=>add(rg,new THREE.PlaneGeometry(w,d).rotateX(-HALF),m,x,y+yy,zz);
    flat(2*E,5.4,M.asphalt,0,0,.09);
    for(const e of [-1,1]){flat(3,5.4,M.concDark,e*(E+1.5),0,.088);
      for(let k=0;k<3;k++){for(const sd of [-1,1])add(rg,new THREE.PlaneGeometry(1.5,.22).rotateX(-HALF),M.yellow,e*(E+.6+k*.9),y+.1,sd*1.1,0,-e*sd*.65,0);}
      for(let k=-3;k<=3;k++)if(k)flat(2.2,.36,M.white,e*(E-1.4),k*.66,.11);              // threshold bars
      for(const sd of [-1,1])flat(3.2,.55,M.white,e*(E-11),sd*1.15,.11);                   // aiming point
      for(const sd of [-1,1])for(const k of [0,1])flat(1.4,.25,M.white,e*(E-6-k*9.5),sd*1.4,.11);  // touchdown zone
    }
    for(let k=-Math.floor((E-13)/3);k<=Math.floor((E-13)/3);k++)flat(1.6,.2,M.white,k*3,0,.11);
    for(const sd of [-1,1])flat(2*E,.14,M.white,0,sd*2.5,.11);
    // runway numbers: the magnetic-style heading each way, readable on approach
    const hdg=Math.round(((Math.atan2(A.ux,-A.uz)*180/Math.PI)+360)%360/10)%36||36;
    for(const e of [-1,1]){const n=e<0?hdg:((hdg+17)%36)+1;
      add(rg,new THREE.PlaneGeometry(2.6,3.4).rotateX(-HALF),numMat(n),e*(E-4.6),y+.11,0,0,e<0?-HALF:HALF,0);}
    // edge lights
    for(let k=-E;k<=E+.1;k+=5)for(const sd of [-1,1])add(rg,B(.18,.18,.18),M.white,k,y+.18,sd*2.95);
    // parallel taxiway and its links
    flat(L+2.6,2.6,M.asphalt,0,5.5,.088);flat(L+.4,.14,M.yellow,0,5.5,.105);
    for(const s0 of [-L/2,0,L/2]){flat(2.6,3.2,M.asphalt,s0,4,.087);flat(.14,3.2,M.yellow,s0,4,.105);
      for(const k of [0,1])flat(2.6,.1,M.yellow,s0,3.15+k*.25,.107);}
    // apron, lead-in lines and stands
    flat(46,7.6,M.conc,0,10.9,.08);
    A.terms.forEach((t,k)=>{const o=(k-(A.terms.length-1)/2)*6.5;
      add(rg,new THREE.RingGeometry(1.6,1.82,24).rotateX(-HALF),M.yellow,o,y+.11,11);
      flat(.14,6,M.yellow,o,9.6,.105);flat(1.6,.14,M.yellow,o,13.2,.105);
      add(rg,B(1.4,.8,.8),M.olive,o+2.6,y+.5,13.4);add(rg,Cy(.32,1.2,8),M.olive,o+2.6,y+1,12.6,0,0,HALF);});
    // terminal with glass front and a covered walkway, control tower beside it
    const TW=A.terms.length*6.5+4;
    add(rg,B(TW,2.6,3),M.house,0,y+1.3,16.6);add(rg,B(TW+.4,.3,3.4),M.concDark,0,y+2.75,16.6);
    add(rg,B(TW-1.2,.9,.06),M.glass,0,y+1.6,15.07);add(rg,B(5,1.2,2),M.house,0,y+3.4,16.8);
    add(rg,B(1.7,7,1.7),M.conc,TW/2+2.4,y+3.5,16.4);add(rg,new THREE.CylinderGeometry(1.7,1.3,1.5,8),M.glass,TW/2+2.4,y+7.7,16.4);
    add(rg,new THREE.CylinderGeometry(1.9,1.9,.25,8),M.concDark,TW/2+2.4,y+8.55,16.4);add(rg,Cy(.05,2,6),M.metal,TW/2+2.7,y+9.6,16.2);
    // hangars at both ends of the apron, doors to the taxiway
    for(const sx of [-19,19]){add(rg,new THREE.CylinderGeometry(2.8,2.8,5.6,16,1,true,0,Math.PI).rotateZ(HALF).rotateY(HALF),M.corr,sx,y,10.8);
      add(rg,new THREE.CircleGeometry(2.8,16,0,Math.PI),M.concDark,sx,y,10.8-2.8,0,Math.PI,0);add(rg,new THREE.CircleGeometry(2.8,16,0,Math.PI),M.olive,sx,y,10.8+2.8,0,0,0);
      flat(.14,2,M.yellow,sx,7.2,.105);}
    // fuel farm and stores
    for(let k=0;k<3;k++)add(rg,new THREE.CylinderGeometry(1,1,1.7,16),M.tank,-23.6+k*2.3,y+.85,16.2);
    drums(rg,-25,13.6,y,3);crates(rg,23.4,15.8,y,0);
    // windsock on the far side
    add(rg,Cy(.05,2.6,6),M.metal,E-6,y+1.3,-4.6);add(rg,new THREE.CylinderGeometry(.22,.1,.9,8),mat(0xd9682a),E-5.6,y+2.4,-4.6,0,.4,HALF);
"""+s[j:]

# runway number materials (cached)
rep("function buildZone(z){\n","""const _numMats={};
function numMat(n){if(_numMats[n])return _numMats[n];
  const t=canvasTex(64,84,(c,w,h)=>{c.fillStyle='#fff';c.font='700 46px "Arial Narrow",Arial,sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(String(n).padStart(2,'0'),w/2,h/2+2);});
  return _numMats[n]=new THREE.MeshLambertMaterial({map:t,transparent:true,depthWrite:false});}
function buildZone(z){
""")
open(p,'w').write(s)
