const SIM=require('./load.js')(process.argv[2]);const m=SIM.MAPS[process.argv[3]];
const T=SIM.__terrain(m,20261017,[]);const {pass,GW,GH}=T;
const lab=new Int32Array(GW*GH).fill(-1);let L=0;const sizes=[];
for(let k=0;k<GW*GH;k++){if(!pass[k]||lab[k]>=0)continue;const st=[k];lab[k]=L;let s=0;while(st.length){const c=st.pop();s++;const i=c%GW,j=(c-i)/GW;
 for(const [a,b] of [[1,0],[-1,0],[0,1],[0,-1]]){const ni=i+a,nj=j+b;if(ni<0||nj<0||ni>=GW||nj>=GH)continue;const nk=nj*GW+ni;if(pass[nk]&&lab[nk]<0){lab[nk]=L;st.push(nk);}}}sizes.push(s);L++;}
console.log(sizes.map((s,i)=>[i,s]).filter(a=>a[1]>200));
// print coarse map of labels
for(let j=0;j<GH;j+=4){let r='';for(let i=0;i<GW;i+=2){const l=lab[j*GW+i];r+=l<0?'.':sizes[l]>200?String.fromCharCode(65+l%26):'-';}console.log(r);}
