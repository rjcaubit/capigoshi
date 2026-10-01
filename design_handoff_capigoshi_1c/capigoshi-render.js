// Renderizador de referência do Capigoshi. Só usa o que o framebuf da placa tem:
// rect, ellipse (cheia / contorno / metade), poly (triângulo), pixel, hline e texto 8x8.
// Toda cor passa por q565 (quantização RGB565). Sem gradiente, sem transparência.
export const W=240,H=284,GROUND=196,FEET=205;
export function q565(c){const [r,g,b]=c,R=r>>3,G=g>>2,B=b>>3;return [R<<3|R>>2,G<<2|G>>4,B<<3|B>>2];}
export function hex565(c){const [r,g,b]=c;return '0x'+((r>>3)<<11|(g>>2)<<5|(b>>3)).toString(16).toUpperCase().padStart(4,'0');}
export const css=c=>typeof c==='string'?c:`rgb(${q565(c).join(',')})`;
export const hexcss=c=>'#'+q565(c).map(v=>v.toString(16).padStart(2,'0')).join('');
export const dark=(c,f=.55)=>c.map(v=>Math.round(v*f));
export const light=(c,f=.3)=>c.map(v=>Math.round(v+(255-v)*f));
export const mix=(a,b,f=.5)=>a.map((v,i)=>Math.round(v+(b[i]-v)*f));

export const INK=[40,30,40],CREME=[255,247,232],TEXTO=[58,42,16],BRANCO=[255,255,255],VERMELHO=[226,75,74],AMARELO=[255,200,32],TRACK=[228,212,190],MUTED=[150,130,110];
export const STAT={fome:[255,138,42],alegria:[226,80,138],energia:[58,138,232],saude:[46,176,96]};
export const UI={tray:[52,42,54],trayBtn:[86,72,92],trayBar:[96,84,100],madeira:[130,88,44],madeiraCl:[190,140,90]};
export const CP={MARROM:[168,112,70],ESCURO:[122,79,46],MASCARA:[186,128,89],CREME:[230,192,154],ROSA:[224,158,134],BOCHECHA:[214,140,118],ENJOADA:[160,190,120],OLHO:[34,21,11],BOCA:[110,40,30],
 PATO:[255,200,40],PATO_ESC:[205,145,20],LARANJA:[255,140,30],LARANJA_CL:[255,170,90],ROXO:[128,40,128],LILAS:[190,165,230],OLHO_PATO:[60,40,30],
 CINZA:[205,205,214],CINZA_ESC:[125,125,138],ROSA_EL:[245,165,185],PRETO:[20,16,20]};

export const PHASES=[
 {id:'madrugada',nome:'Madrugada',ini:0,fim:5,sky:[[14,18,52],[22,28,70],[34,42,92]],grass:[24,74,52],grassD:[16,52,38],lake:[36,64,120],hillF:[26,32,78],hillN:[22,60,48],stars:true},
 {id:'amanhecer',nome:'Amanhecer',ini:5,fim:7.5,sky:[[236,150,130],[250,176,130],[255,214,170]],grass:[70,160,90],grassD:[44,116,66],lake:[130,180,220],hillF:[196,134,150],hillN:[60,140,80]},
 {id:'dia',nome:'Dia',ini:7.5,fim:17,sky:[[92,178,248],[130,200,250],[170,222,252]],grass:[46,176,96],grassD:[30,124,66],lake:[90,170,235],hillF:[110,180,210],hillN:[40,150,84]},
 {id:'pordosol',nome:'Por do sol',ini:17,fim:19.5,sky:[[236,110,96],[250,150,90],[255,204,130]],grass:[60,150,86],grassD:[36,106,60],lake:[240,160,120],hillF:[186,104,120],hillN:[50,130,74]},
 {id:'crepusculo',nome:'Crepusculo',ini:19.5,fim:21,sky:[[52,44,104],[90,68,132],[160,104,140]],grass:[36,100,66],grassD:[24,70,48],lake:[84,80,150],hillF:[72,58,120],hillN:[30,84,58],stars:true},
 {id:'noite',nome:'Noite',ini:21,fim:24,sky:[[14,18,52],[18,24,62],[28,34,80]],grass:[20,70,45],grassD:[14,50,34],lake:[30,60,110],hillF:[20,26,68],hillN:[18,56,42],stars:true},
];
export const phaseOf=h=>PHASES.find(p=>h>=p.ini&&h<p.fim)||PHASES[5];
export const ROTINA=[[0,'dormindo'],[6.5,'espreguicando'],[7,'comendo'],[9,'passeando'],[12,'comendo'],[13,'banho'],[15.5,'passeando'],[18,'por do sol'],[19.5,'passeando'],[21.5,'dormindo']];
export const TEXTOS={dormindo:'dormindo',espreguicando:'acordou',comendo:'comendo capim',passeando:'passeando',banho:'nadando no lago','por do sol':'vendo o por do sol'};
export function activityOf(h){let a='dormindo';for(const [i,n] of ROTINA)if(h>=i)a=n;return a;}

export const STYLES={
 a:{id:'a',nome:'Pocket',outline:()=>INK,dither:true,bands:3,relevo:'pinheiros',hud:'pips',upper:true,caption:true,shadow:false},
 b:{id:'b',nome:'Macio',outline:null,dither:false,bands:3,relevo:'colinas',hud:'chips',upper:false,caption:false,shadow:true},
 c:{id:'c',nome:'Diorama',outline:c=>dark(c,.5),dither:false,bands:4,relevo:'montanhas',hud:'tray',upper:false,caption:false,shadow:true},
};
const up=(st,s)=>st.upper?s.toUpperCase():s;

export function makeG(ctx){
  const C=css,g={ctx};
  g.fill=c=>{ctx.fillStyle=C(c);ctx.fillRect(0,0,W,H);};
  g.rect=(x,y,w,h,c)=>{ctx.fillStyle=C(c);ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
  g.box=(x,y,w,h,c)=>{ctx.strokeStyle=C(c);ctx.lineWidth=1;ctx.strokeRect(Math.round(x)+.5,Math.round(y)+.5,Math.round(w)-1,Math.round(h)-1);};
  g.px=(x,y,c)=>g.rect(x,y,1,1,c);
  g.hl=(x,y,w,c)=>g.rect(x,y,w,1,c);
  g.vl=(x,y,h,c)=>g.rect(x,y,1,h,c);
  g.line=(x1,y1,x2,y2,c)=>{ctx.strokeStyle=C(c);ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(x1+.5,y1+.5);ctx.lineTo(x2+.5,y2+.5);ctx.stroke();};
  g.ell=(x,y,rx,ry,c,filled=true,mask=0)=>{let a0=0,a1=Math.PI*2;if(mask===1){a0=Math.PI;a1=2*Math.PI;}else if(mask===2){a0=0;a1=Math.PI;}
    ctx.beginPath();ctx.ellipse(Math.round(x),Math.round(y),Math.max(.5,rx),Math.max(.5,ry),0,a0,a1);
    if(filled){ctx.fillStyle=C(c);ctx.fill();}else{ctx.strokeStyle=C(c);ctx.lineWidth=1;ctx.stroke();}};
  g.arc=(x,y,rx,ry,c,mask,th=2)=>{for(let i=0;i<th;i++)g.ell(x,y,rx-i,ry-i,c,false,mask);};
  g.poly=(x,y,pts,c)=>{ctx.fillStyle=C(c);ctx.beginPath();ctx.moveTo(x+pts[0],y+pts[1]);for(let i=2;i<pts.length;i+=2)ctx.lineTo(x+pts[i],y+pts[i+1]);ctx.closePath();ctx.fill();};
  g.text=(s,x,y,c,sc=1)=>{ctx.fillStyle=C(c);ctx.font=`${8*sc}px "Press Start 2P", monospace`;ctx.textBaseline='top';ctx.fillText(s,Math.round(x),Math.round(y));};
  g.center=(s,y,c,sc=1)=>g.text(s,(W-s.length*8*sc)/2,y,c,sc);
  g.dither=(x,y,w,h,c)=>{ctx.fillStyle=C(c);for(let j=0;j<h;j++)for(let i=j&1;i<w;i+=2)ctx.fillRect(x+i,y+j,1,1);};
  g.rrect=(x,y,w,h,r,c)=>{r=Math.min(r,w/2,h/2);g.rect(x+r,y,w-2*r,h,c);g.rect(x,y+r,w,h-2*r,c);g.ell(x+r,y+r,r,r,c);g.ell(x+w-r,y+r,r,r,c);g.ell(x+r,y+h-r,r,r,c);g.ell(x+w-r,y+h-r,r,r,c);};
  return g;
}

export function parseSpec(s){const o={};for(const kv of s.split(';')){const i=kv.indexOf('=');if(i>0)o[kv.slice(0,i).trim()]=kv.slice(i+1).trim();}return o;}

// ── personagens ───────────────────────────────────────────────────────
function termometro(g,tx,ty){g.rect(tx,ty,3,12,BRANCO);g.ell(tx+1,ty+12,3,3,VERMELHO);g.rect(tx+1,ty+5,1,7,VERMELHO);}
function rel(g,cx,pe,s,ol,ring){
  const E=(dx,dy,rx,ry,c,out)=>{const x=cx+dx*s,y=pe+dy*s,RX=Math.max(1,rx*s),RY=Math.max(1,ry*s);const oc=ol?ol(c):(out&&ring&&ring(c));if(oc&&out)g.ell(x,y,RX+1,RY+1,oc);g.ell(x,y,RX,RY,c);};
  const P=(dx,dy,pts,c)=>g.poly(cx+dx*s,pe+dy*s,pts.map(v=>v*s),c);
  const R=(dx,dy,w,h,c)=>g.rect(cx+dx*s,pe+dy*s,w*s,Math.max(1,h*s),c);
  const A=(dx,dy,rx,ry,c,m,th)=>g.arc(cx+dx*s,pe+dy*s,rx*s,ry*s,c,m,th);
  return {E,P,R,A};
}
function capi(g,cx,pe,o){
  const K=0.078*o.s,ol=o.ol;
  const X=v=>cx+(v-965)*K,Y=v=>pe+(v-1810)*K,R=v=>Math.max(1,v*K);
  const E=(x,y,rx,ry,c,out)=>{if(ol&&out)g.ell(X(x),Y(y),R(rx)+1,R(ry)+1,ol(c));g.ell(X(x),Y(y),R(rx),R(ry),c);};
  E(965,1390,495,330,CP.MARROM,1);E(965,1530,330,240,CP.CREME);
  E(760,1330,100,75,CP.MARROM,1);E(1170,1330,100,75,CP.MARROM,1);
  E(750,1760,90,52,CP.ESCURO,1);E(1180,1760,90,52,CP.ESCURO,1);
  E(678,560,90,72,CP.ESCURO,1);E(678,560,45,38,CP.ROSA);E(1253,560,90,72,CP.ESCURO,1);E(1253,560,45,38,CP.ROSA);
  E(965,835,432,382,CP.MARROM,1);E(965,940,330,250,CP.MASCARA);E(965,1050,197,145,CP.CREME);
  const bc=o.sick?CP.ENJOADA:CP.BOCHECHA;E(710,1000,57,32,bc);E(1220,1000,57,32,bc);
  const eyes=[];
  for(const ox of [808,1122]){eyes.push([X(ox),Y(845)]);
    if(o.eyes==='fechados')g.rect(X(ox-48),Y(845),R(96),2,CP.OLHO);
    else if(o.eyes==='feliz')g.arc(X(ox),Y(880),R(52),R(48),CP.OLHO,1);
    else if(o.eyes==='susto'){E(ox,845,80,85,BRANCO);E(ox,845,30,32,CP.OLHO);}
    else if(o.eyes==='sono'){E(ox,845,57,63,CP.OLHO);g.rect(X(ox-60),Y(780),R(120),R(70),CP.MASCARA);}
    else{E(ox,845,57,63,CP.OLHO);E(ox+17,818,17,17,BRANCO);}
  }
  E(965,1003,45,28,CP.OLHO);
  const bx=X(965),by=Y(1092),m=o.mouth;
  if(m==='sorriso'){g.arc(bx,by,R(70),R(48),CP.OLHO,2);g.rect(bx-3,by+R(40),2,3,BRANCO);g.rect(bx+1,by+R(40),2,3,BRANCO);}
  else if(m==='triste')g.arc(bx,Y(1150),R(60),R(40),CP.OLHO,1);
  else if(m==='aberta')E(965,1105,45,55,CP.BOCA);
  else if(m==='meia')E(965,1105,40,18,CP.BOCA);
  else if(m==='o')E(965,1110,32,40,CP.BOCA);
  else E(965,1100,16,16,CP.OLHO);
  if(o.fones!==false){g.arc(X(965),Y(700),R(355),R(300),CP.OLHO,1,3);for(const x0 of [548,1278]){g.rect(X(x0),Y(610),R(104),R(138),CP.OLHO);g.rect(X(x0+22),Y(632),R(60),R(94),AMARELO);}}
  if(o.sick)termometro(g,X(1300),Y(1040));
  return {eyes,head:Y(835),top:Y(480),half:R(495)};
}
function pato(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===CP.PATO?CP.PATO_ESC:null);
  E(0,-44,35,46,CP.PATO,1);
  E(-30,-38,8,15,CP.PATO_ESC);E(30,-38,8,15,CP.PATO_ESC);
  E(-12,-2,10,4,CP.LARANJA,1);E(12,-2,10,4,CP.LARANJA,1);
  E(-36,-70,9,16,CP.ROXO,1);E(36,-70,9,16,CP.ROXO,1);
  const bc=o.sick?CP.ENJOADA:CP.LARANJA_CL;E(-23,-50,5,3,bc);E(23,-50,5,3,bc);
  const eyes=[];
  for(const ox of [-13,13]){const oy=-62;eyes.push([cx+ox*s,pe+oy*s]);
    if(o.eyes==='fechados')R(ox-7,oy,14,2,CP.OLHO_PATO);
    else if(o.eyes==='feliz')A(ox,oy+4,7,6,CP.OLHO_PATO,1);
    else if(o.eyes==='susto'){E(ox,oy,10,10,BRANCO,1);E(ox,oy,4,4,CP.OLHO_PATO);}
    else if(o.eyes==='sono'){E(ox,oy,8,8,CP.OLHO_PATO);R(ox-9,oy-9,18,9,CP.PATO);}
    else{E(ox,oy,8,8,CP.OLHO_PATO);E(ox-3,oy-3,2,2,BRANCO);}
  }
  const by=-50,m=o.mouth;
  if(m==='aberta'){P(0,by,[-8,-3,8,-3,0,11],CP.BOCA);P(0,by,[-8,-3,8,-3,0,3],CP.LARANJA);}
  else if(m==='meia'){P(0,by,[-8,-3,8,-3,0,8],CP.BOCA);P(0,by,[-8,-3,8,-3,0,4],CP.LARANJA);}
  else if(m==='o'){P(0,by,[-8,-3,8,-3,0,7],CP.LARANJA);E(0,by+9,3,3,CP.BOCA);}
  else if(m==='triste'){P(0,by,[-8,-3,8,-3,0,7],CP.LARANJA);A(0,by+14,6,4,CP.OLHO_PATO,1);}
  else if(m==='dormindo')P(0,by,[-6,-2,6,-2,0,5],CP.LARANJA);
  else{P(0,by,[-8,-3,8,-3,0,7],CP.LARANJA);A(0,by+8,7,4,CP.OLHO_PATO,2);}
  E(0,-82,42,12,CP.ROXO,1);R(-24,-91,48,7,CP.LILAS);
  if(o.ol)P(0,-85,[-26,1,26,1,7,-44],o.ol(CP.ROXO));P(0,-85,[-24,0,24,0,6,-42],CP.ROXO);
  if(o.sick)termometro(g,cx+30*s,pe-58*s);
  return {eyes,head:pe-62*s,top:pe-128*s,half:35*s};
}
function elefante(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===CP.CINZA?CP.CINZA_ESC:null);
  for(const sg of [-1,1]){E(sg*32,-80,15,17,CP.CINZA,1);E(sg*33,-80,9,11,CP.ROSA_EL);}
  E(0,-38,34,42,CP.CINZA,1);
  E(-14,-2,10,4,CP.CINZA_ESC,1);E(14,-2,10,4,CP.CINZA_ESC,1);
  E(0,-72,30,28,CP.CINZA,1);
  const bc=o.sick?CP.ENJOADA:CP.ROSA_EL;E(-23,-60,5,3,bc);E(23,-60,5,3,bc);
  const eyes=[];
  for(const ox of [-12,12]){const oy=-74;eyes.push([cx+ox*s,pe+oy*s]);
    if(o.eyes==='fechados')R(ox-8,oy,16,2,CP.PRETO);
    else if(o.eyes==='feliz')A(ox,oy+4,8,7,CP.PRETO,1);
    else if(o.eyes==='susto'){E(ox,oy,10,10,BRANCO,1);E(ox,oy,3,3,CP.PRETO);}
    else if(o.eyes==='sono'){E(ox,oy,10,10,BRANCO,1);E(ox+1,oy+1,5,5,CP.PRETO);R(ox-11,oy-11,22,11,CP.CINZA);}
    else{E(ox,oy,10,10,BRANCO,1);E(ox+1,oy+1,5,5,CP.PRETO);E(ox-2,oy-3,2,2,BRANCO);}
  }
  const mx=-13,my=-52,m=o.mouth;
  if(m==='sorriso')A(mx,my,5,3,CP.PRETO,2);
  else if(m==='triste')A(mx,my+3,5,3,CP.PRETO,1);
  else if(m==='aberta')E(mx,my+1,4,5,CP.BOCA);
  else if(m==='meia')E(mx,my+1,4,2,CP.BOCA);
  else if(m==='o')E(mx,my+1,3,3,CP.BOCA);
  const sobe=m==='aberta'||o.eyes==='feliz';
  const segs=sobe?[[0,-58,8,9],[1,-48,8,9],[4,-39,7,8],[10,-33,7,6],[17,-38,5,5]]:[[0,-58,8,9],[1,-48,8,9],[3,-38,7,8],[9,-30,7,6],[16,-28,5,4]];
  for(const [dx,dy,rx,ry] of segs)E(dx,dy,rx,ry,CP.CINZA,1);
  if(o.sick)termometro(g,cx+30*s,pe-62*s);
  return {eyes,head:pe-72*s,top:pe-102*s,half:34*s};
}
// ── olhos e bocas genéricos (personagens novos) ──────────────────────
function eyesG(o,cx,pe,E,R,A,pts,kind,ink,lid,iris){
  const s=o.s,out=[];
  for(const [ox,oy,k] of pts){out.push([cx+ox*s,pe+oy*s]);const e=o.eyes;
    const base=()=>{if(kind==='cat'){E(ox,oy,k*.85,k,iris);R(ox-.9,oy-k*.7,1.8,k*1.4,CP.PRETO);E(ox+k*.3,oy-k*.42,k*.24,k*.24,BRANCO);}
      else{E(ox,oy,k*.8,k,CP.PRETO);E(ox+k*.28,oy-k*.4,k*.32,k*.32,BRANCO);}};
    if(e==='fechados')R(ox-k,oy,2*k,2.4,ink);
    else if(e==='feliz')A(ox,oy+k*.5,k*.85,k*.75,ink,1,2);
    else if(e==='susto'){E(ox,oy,k*1.15+1,k*1.2+1,CP.PRETO);E(ox,oy,k*1.15,k*1.2,BRANCO);E(ox,oy,k*.4,k*.45,CP.PRETO);}
    else if(e==='sono'){base();R(ox-k-1.5,oy-k-1.5,2*k+3,k+1.5,lid);}
    else base();}
  return out;
}
function mouthG(o,E,A,mx,my,k,ink,w){
  const m=o.mouth;
  if(m==='sorriso'){if(w){A(mx-2.6*k,my,2.6*k,2.2*k,ink,2,2);A(mx+2.6*k,my,2.6*k,2.2*k,ink,2,2);}else A(mx,my,4*k,3*k,ink,2,2);}
  else if(m==='triste')A(mx,my+3*k,4*k,3*k,ink,1,2);
  else if(m==='aberta')E(mx,my+2*k,3.6*k,4.2*k,CP.BOCA);
  else if(m==='meia')E(mx,my+1*k,3.6*k,1.8*k,CP.BOCA);
  else if(m==='o')E(mx,my+1.2*k,2.3*k,2.7*k,CP.BOCA);
  else E(mx,my,1.4*k,1.4*k,ink);
}
function beak(o,E,P,A,by,k,col,ink){
  const m=o.mouth,b=[-6*k,-2*k,6*k,-2*k,0,6*k];
  if(m==='aberta'){P(0,by,[-6*k,-2*k,6*k,-2*k,0,10*k],CP.BOCA);P(0,by,[-6*k,-2*k,6*k,-2*k,0,2.5*k],col);}
  else if(m==='meia'){P(0,by,[-6*k,-2*k,6*k,-2*k,0,8*k],CP.BOCA);P(0,by,[-6*k,-2*k,6*k,-2*k,0,4*k],col);}
  else if(m==='o'){P(0,by,b,col);E(0,by+8*k,2.5*k,2.5*k,CP.BOCA);}
  else if(m==='triste'){P(0,by,b,col);A(0,by+12*k,5*k,3*k,ink,1,2);}
  else if(m==='dormindo')P(0,by,[-4.5*k,-1.5*k,4.5*k,-1.5*k,0,4*k],col);
  else{P(0,by,b,col);A(0,by+6.5*k,6*k,3.5*k,ink,2,2);}
}
const NP={POLVO:[150,108,214],POLVO_ESC:[104,70,168],POLVO_CL:[196,168,240],ROSA:[244,150,190],
 CAL:[252,212,84],CAL_ESC:[214,166,44],CAL_CL:[255,236,160],CAL_BOCH:[238,92,66],CAL_BICO:[236,126,70],
 CAR:[214,148,78],CAR_ESC:[160,98,44],CAR_CL:[252,224,182],CAR_ORELHA:[136,82,38],
 GATO:[58,54,70],GATO_ESC:[32,30,40],GATO_CL:[226,222,234],GATO_IRIS:[200,232,90],
 ET:[112,200,92],ET_ESC:[58,138,62],ET_CL:[190,240,120],
 SAPO:[150,200,56],SAPO_ESC:[96,146,36],SAPO_CL:[214,232,140]};
function polvo(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===NP.POLVO?NP.POLVO_ESC:null);
  for(const [dx,dy,rx,ry] of [[-27,-13,11,12],[27,-13,11,12],[-14,-9,10,10],[14,-9,10,10],[0,-8,10,10]])E(dx,dy,rx,ry,NP.POLVO,1);
  for(const dx of [-27,-14,0,14,27])E(dx,-4,4,2.5,NP.POLVO_CL);
  E(0,-56,38,40,NP.POLVO,1);E(-18,-80,9,5,NP.POLVO_CL);
  const bc=o.sick?CP.ENJOADA:NP.ROSA;E(-25,-45,6,3.5,bc);E(25,-45,6,3.5,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-13,-58,8],[13,-58,8]],'solid',CP.PRETO,NP.POLVO);
  mouthG(o,E,A,0,-44,1,CP.PRETO,false);
  if(o.sick)termometro(g,cx+32*s,pe-58*s);
  return {eyes,head:pe-56*s,top:pe-96*s,half:38*s};
}
function calopsita(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===NP.CAL?NP.CAL_ESC:null);
  if(o.ol)P(0,0,[8,-34,38,-2,26,3],o.ol(NP.CAL_ESC));P(0,0,[10,-36,36,-4,24,1],NP.CAL_ESC);
  E(-9,-2,7,3,NP.CAL_BICO,1);E(9,-2,7,3,NP.CAL_BICO,1);
  E(0,-38,27,37,NP.CAL,1);E(0,-28,17,22,NP.CAL_CL);
  E(-22,-38,7,17,NP.CAL_ESC);E(22,-38,7,17,NP.CAL_ESC);
  if(o.ol){P(-2,-94,[-6,6,6,6,3,-22],o.ol(NP.CAL));P(5,-92,[-4,5,5,5,13,-15],o.ol(NP.CAL));}
  P(-2,-94,[-5,6,5,6,3,-20],NP.CAL);P(5,-92,[-3,5,4,5,12,-14],NP.CAL_ESC);
  E(0,-77,22,21,NP.CAL,1);
  const bc=o.sick?CP.ENJOADA:NP.CAL_BOCH;E(-14,-70,6.5,6.5,bc);E(14,-70,6.5,6.5,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-9,-81,5],[9,-81,5]],'solid',CP.PRETO,NP.CAL);
  beak(o,E,P,A,-73,.8,NP.CAL_BICO,CP.PRETO);
  if(o.sick)termometro(g,cx+26*s,pe-60*s);
  return {eyes,head:pe-77*s,top:pe-114*s,half:28*s};
}
function cachorro(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===NP.CAR?NP.CAR_ESC:null);
  E(28,-36,6,11,NP.CAR,1);E(31,-46,4,4,NP.CAR_CL);
  E(-11,-2,8,4,NP.CAR_ESC,1);E(11,-2,8,4,NP.CAR_ESC,1);
  E(0,-32,27,32,NP.CAR,1);E(0,-24,16,20,NP.CAR_CL);
  E(-19,-36,6,10,NP.CAR_ESC);E(19,-36,6,10,NP.CAR_ESC);
  E(0,-74,30,27,NP.CAR,1);
  E(-29,-70,9,17,NP.CAR_ORELHA,1);E(29,-70,9,17,NP.CAR_ORELHA,1);
  E(0,-62,13,9,NP.CAR_CL);
  const bc=o.sick?CP.ENJOADA:[240,150,150];E(-20,-63,5,3,bc);E(20,-63,5,3,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-12,-78,7],[12,-78,7]],'solid',CP.PRETO,NP.CAR);
  E(0,-67,4,3,CP.PRETO);
  mouthG(o,E,A,0,-61,.8,CP.PRETO,true);
  if(o.sick)termometro(g,cx+34*s,pe-60*s);
  return {eyes,head:pe-74*s,top:pe-101*s,half:30*s};
}
function gato(g,cx,pe,o){
  const s=o.s,ol=o.ol?(c=>c===NP.GATO?[110,104,128]:o.ol(c)):null,{E,P,R,A}=rel(g,cx,pe,s,ol,c=>c===NP.GATO?[96,90,112]:null);
  E(28,-42,5,14,NP.GATO,1);E(33,-58,5,5,NP.GATO,1);
  E(-10,-2,8,4,NP.GATO,1);E(10,-2,8,4,NP.GATO,1);
  E(0,-32,25,32,NP.GATO,1);E(0,-34,8,10,NP.GATO_CL);
  const ring=ol?ol(NP.GATO):[96,90,112];
  P(-18,-88,[-12,14,10,14,-6,-14],ring);P(18,-88,[12,14,-10,14,6,-14],ring);
  P(-18,-88,[-10,13,8,13,-6,-12],NP.GATO);P(18,-88,[10,13,-8,13,6,-12],NP.GATO);
  P(-18,-86,[-5,10,4,10,-4,-5],NP.ROSA);P(18,-86,[5,10,-4,10,4,-5],NP.ROSA);
  E(0,-72,29,25,NP.GATO,1);
  const bc=o.sick?CP.ENJOADA:NP.ROSA;E(-20,-63,5,3,bc);E(20,-63,5,3,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-12,-75,8],[12,-75,8]],'cat',NP.GATO_CL,NP.GATO,NP.GATO_IRIS);
  P(0,-67,[-3,0,3,0,0,3],NP.ROSA);
  for(const dy of [-65,-61]){R(-33,dy,9,1,NP.GATO_CL);R(24,dy,9,1,NP.GATO_CL);}
  mouthG(o,E,A,0,-61,.8,NP.GATO_CL,true);
  if(o.sick)termometro(g,cx+32*s,pe-60*s);
  return {eyes,head:pe-72*s,top:pe-102*s,half:29*s};
}
function et(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===NP.ET?NP.ET_ESC:null),olc=o.ol?o.ol(NP.ET):NP.ET_ESC;
  P(0,-50,[-15,-1,15,-1,32,49,-32,49],olc);P(-12,-45,[1,-1,-28,18,-21,26],olc);P(12,-45,[-1,-1,28,18,21,26],olc);
  P(-12,-44,[0,0,-26,18,-20,24],NP.ET);P(12,-44,[0,0,26,18,20,24],NP.ET);
  P(0,-50,[-14,0,14,0,30,48,-30,48],NP.ET);
  for(const dx of [-19,0,19])E(dx,-2,11,3,NP.ET);
  R(-17,-22,11,2,NP.ET_ESC);R(5,-28,11,2,NP.ET_ESC);R(-6,-12,13,2,NP.ET_ESC);
  R(-14,-104,2,18,NP.ET_ESC);R(12,-104,2,18,NP.ET_ESC);E(-13,-106,4.5,4.5,NP.ET_CL,1);E(13,-106,4.5,4.5,NP.ET_CL,1);
  E(0,-70,26,24,NP.ET,1);
  const bc=o.sick?CP.ENJOADA:[250,166,170];E(-18,-61,4,2.5,bc);E(18,-61,4,2.5,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-11,-71,5.5],[11,-71,5.5],[0,-83,4.5]],'solid',CP.PRETO,NP.ET);
  mouthG(o,E,A,0,-58,.75,CP.PRETO,false);
  if(o.sick)termometro(g,cx+28*s,pe-62*s);
  return {eyes,head:pe-70*s,top:pe-110*s,half:30*s};
}
function sapinho(g,cx,pe,o){
  const s=o.s,{E,P,R,A}=rel(g,cx,pe,s,o.ol,c=>c===NP.SAPO?NP.SAPO_ESC:null);
  E(-22,-4,11,5,NP.SAPO_ESC,1);E(22,-4,11,5,NP.SAPO_ESC,1);
  E(-15,-74,13,13,NP.SAPO,1);E(15,-74,13,13,NP.SAPO,1);
  E(0,-38,35,34,NP.SAPO,1);E(0,-24,21,17,NP.SAPO_CL);
  E(-11,-6,7,4,NP.SAPO_ESC,1);E(11,-6,7,4,NP.SAPO_ESC,1);
  const bc=o.sick?CP.ENJOADA:[240,150,90];E(-24,-46,6,3.5,bc);E(24,-46,6,3.5,bc);
  const eyes=eyesG(o,cx,pe,E,R,A,[[-15,-74,9.5],[15,-74,9.5]],'solid',CP.PRETO,NP.SAPO);
  if(o.eyes==='normal'||!o.eyes){E(-18,-70,1.8,1.8,BRANCO);E(12,-70,1.8,1.8,BRANCO);}
  E(-3,-56,1.2,1.2,CP.PRETO);E(3,-56,1.2,1.2,CP.PRETO);
  mouthG(o,E,A,0,-49,1.5,CP.PRETO,false);
  if(o.sick)termometro(g,cx+34*s,pe-56*s);
  return {eyes,head:pe-46*s,top:pe-88*s,half:35*s};
}
export const CHAR_SCALE=0.74;
function egg(g,cx,pe,o){
  const c=[250,240,222];
  g.ell(cx,pe-1,30,6,dark(o.grass||[46,176,96],.7));
  if(o.ol)g.ell(cx,pe-26,25,32,o.ol(c));g.ell(cx,pe-26,24,31,c);
  for(const [dx,dy,r] of [[-8,-38,4],[9,-30,3],[-3,-16,3],[12,-14,2]])g.ell(cx+dx,pe+dy,r,r,[214,190,160]);
  if(o.crack){const p=[[-8,-30],[-3,-26],[-7,-22],[0,-18],[-4,-14]];for(let i=0;i<p.length-1;i++)g.line(cx+p[i][0],pe+p[i][1],cx+p[i+1][0],pe+p[i+1][1],INK);}
  return {eyes:[],head:pe-30,top:pe-58,half:24};
}
export const CHARS={capi,pato,elefante,polvo,calopsita,cachorro,gato,et,sapinho};
export const NOMES={capi:'Capi',pato:'Pato',elefante:'Elefante',polvo:'Polvo',calopsita:'Calopsita',cachorro:'Caramelo',gato:'Gato',et:'ET',sapinho:'Sapinho'};
export const PALS={capi:[CP.MARROM,CP.ESCURO,CP.MASCARA,CP.CREME,AMARELO],pato:[CP.PATO,CP.PATO_ESC,CP.ROXO,CP.LILAS,CP.LARANJA],elefante:[CP.CINZA,CP.CINZA_ESC,CP.ROSA_EL,CP.PRETO,BRANCO],
 polvo:[NP.POLVO,NP.POLVO_ESC,NP.POLVO_CL,NP.ROSA,CP.PRETO],calopsita:[NP.CAL,NP.CAL_ESC,NP.CAL_CL,NP.CAL_BOCH,NP.CAL_BICO],cachorro:[NP.CAR,NP.CAR_ESC,NP.CAR_CL,NP.CAR_ORELHA,CP.PRETO],
 gato:[NP.GATO,NP.GATO_ESC,NP.GATO_CL,NP.GATO_IRIS,NP.ROSA],et:[NP.ET,NP.ET_ESC,NP.ET_CL,[250,166,170],CP.PRETO],sapinho:[NP.SAPO,NP.SAPO_ESC,NP.SAPO_CL,[240,150,90],CP.PRETO]};
export function drawChar(g,id,cx,pe,o){
  o=Object.assign({eyes:'normal',mouth:'sorriso',s:1},o);
  if(o.stage==='ovo')return egg(g,cx,pe,o);
  if(!o.raw)o.s*=CHAR_SCALE;
  if(o.stage==='filhote')o.s*=0.62;
  const r=(CHARS[id]||capi)(g,cx,pe,o);
  if(o.stage==='idoso'){for(const [ex,ey] of r.eyes)g.rect(ex-5,ey-11,10,2,BRANCO);const bx=cx+r.half+4;g.rect(bx,pe-38,3,38,UI.madeira);g.ell(bx+1,pe-40,4,3,UI.madeira);}
  return r;
}

// ── visitantes, objetos, eventos ──────────────────────────────────────
const V={
 passarinho(g,x,y,t){const az=[70,140,230];g.ell(x,y,7,5,az);g.ell(x+6,y-4,4,4,az);g.px(x+7,y-5,INK);g.poly(x+9,y-4,[0,0,4,1,0,2],AMARELO);const asa=(Math.floor(t/120)%2)?-4:2;g.ell(x-1,y+asa/2,5,2,[40,100,190]);},
 tartaruga(g,x,y,t){const p=(Math.floor(t/250)%2)?1:0,v=[120,180,90];g.ell(x-7,y+p,3,2,v);g.ell(x+7,y+1-p,3,2,v);g.ell(x-13,y-3,4,3,v);g.px(x-15,y-4,INK);g.ell(x,y-2,11,8,[60,130,60],true,1);g.ell(x,y-4,5,3,[90,160,80]);},
 borboleta(g,x,y,t){const ab=2+Math.floor(3*Math.abs(Math.sin(t/90))),r=[240,110,170];g.ell(x-ab,y-2,ab,4,r);g.ell(x+ab,y-2,ab,4,r);g.ell(x-ab,y+3,ab-1,3,[250,180,60]);g.ell(x+ab,y+3,ab-1,3,[250,180,60]);g.vl(x,y-4,9,INK);},
 sapo(g,x,y,t){y-=Math.floor(Math.abs(Math.sin(t/200))*6);const v=[80,170,60];g.ell(x,y,8,5,v);g.ell(x-4,y-5,3,3,v);g.ell(x+4,y-5,3,3,v);g.px(x-4,y-5,INK);g.px(x+4,y-5,INK);},
 vagalumes(g,t){for(let i=0;i<7;i++){if((Math.floor(t/300)+i)%3)g.rect(Math.round(30+i*30+10*Math.sin(t/700+i)),Math.round(120+30*Math.sin(t/900+i*2)),2,2,[255,250,120]);}},
};
function fogueira(g,ph,t){const x=60,y=204;g.rect(x-10,y-2,20,3,UI.madeira);g.rect(x-8,y-5,16,3,UI.madeiraCl);
  const f=Math.floor(Math.abs(Math.sin(t/140))*4);g.poly(x,y-5,[-7,0,7,0,0,-14-f],[255,140,30]);g.poly(x,y-5,[-3,0,3,0,0,-8-f],AMARELO);
  if(ph.stars)for(let i=0;i<4;i++)g.px(x-14+i*9,y-20-((Math.floor(t/200)+i*3)%12),AMARELO);}
function barquinho(g,t){const x=202,y=210+Math.round(Math.sin(t/800)*1.5);g.poly(x,y,[-14,0,14,0,10,5,-10,5],[150,100,50]);g.vl(x,y-14,14,UI.madeira);g.poly(x+1,y-13,[0,0,10,10,0,10],BRANCO);}
function cabana(g,ph){const x=38,y=GROUND+8;g.rect(x-18,y-26,36,26,UI.madeiraCl);g.poly(x,y-26,[-22,0,22,0,0,-16],[160,70,60]);g.rect(x-4,y-14,8,14,UI.madeira);g.rect(x+7,y-20,6,6,ph.stars?AMARELO:[130,200,250]);}
const BUILDS={fogueira:(g,ph,t)=>fogueira(g,ph,t),barquinho:(g,ph,t)=>barquinho(g,t),cabana:(g,ph)=>cabana(g,ph)};
function balao(g,t){const x=Math.round(((t/250)%330)-45),y=64+Math.round(Math.sin(t/900)*4);g.ell(x,y,11,13,VERMELHO);g.rect(x-3,y-13,6,26,AMARELO);g.vl(x-6,y+12,7,INK);g.vl(x+5,y+12,7,INK);g.rect(x-5,y+19,10,6,UI.madeira);}
function cometa(g,t){const c=(t%9000)/9000;if(c>.2)return;const x=Math.round(20+c*1000),y=Math.round(30+c*400);for(let i=0;i<8;i++)g.px(x-i*3,y-i*1.2,i<2?BRANCO:[200,210,255]);}
function chuva(g,t){for(const [x,y] of [[70,46],[160,38]]){const c=[118,122,148];g.ell(x,y,16,8,c);g.ell(x-11,y+3,10,6,c);g.ell(x+12,y+3,10,6,c);}
  for(let i=0;i<16;i++){const x=16+i*14,y=56+((t/6+i*23)%130);g.vl(x,y,4,[150,190,240]);}}
function nuvem(g,x,y,c){g.ell(x,y,12,6,c);g.ell(x-8,y+2,8,5,c);g.ell(x+9,y+2,8,5,c);}
function capim(g,x,y,c,h=1){for(const [dx,alt] of [[-4,8*h],[0,11*h],[4,8*h]]){g.line(x+Math.trunc(dx/2),y,x+dx,y-alt,c);g.line(x+Math.trunc(dx/2)+1,y,x+dx+1,y-alt,c);}}
function tree(g,x,y,c,size,ol){g.rect(x-2,y-size,4,size,UI.madeira);if(ol)g.ell(x,y-size-6,size*.8+1,size*.7+1,ol(c));g.ell(x,y-size-6,size*.8,size*.7,c);}

// ── cena ──────────────────────────────────────────────────────────────
function sky(g,st,ph){
  const b=ph.sky,bands=st.bands===4?[b[0],b[1],mix(b[1],b[2]),b[2]]:b,cuts=st.bands===4?[0,60,110,150,GROUND]:[0,70,135,GROUND];
  for(let i=0;i<bands.length;i++){g.rect(0,cuts[i],W,cuts[i+1]-cuts[i],bands[i]);
    if(st.dither&&i<bands.length-1){g.dither(0,cuts[i+1]-3,W,3,bands[i+1]);g.dither(0,cuts[i+1],W,3,bands[i]);}}
}
function stars(g,t){for(let i=0;i<30;i++){const f=(Math.floor(t/(380+i*61))+i*7)%(3+i%3);if(f){const sx=(i*53+11)%W,sy=34+(i*37)%120;g.px(sx,sy,BRANCO);if(i%4===0&&f>1){g.px(sx+1,sy,BRANCO);g.px(sx,sy+1,BRANCO);}}}}
function sunMoon(g,st,ph,hour){
  if(hour>=6&&hour<19.5){const a=(hour-6)/13.5*Math.PI,x=Math.round(120-100*Math.cos(a)),y=Math.round(170-105*Math.sin(a));if(st.outline)g.ell(x,y,12,12,st.outline([255,220,60]));g.ell(x,y,11,11,[255,220,60]);if(!st.outline)g.ell(x-3,y-3,4,4,[255,240,150]);}
  else{const a=(((hour-19.5)%24)+24)%24/10.5*Math.PI,x=Math.round(120-100*Math.cos(a)),y=Math.round(170-105*Math.sin(a));g.ell(x,y,15,15,light(ph.sky[0],.12));g.ell(x,y,9,9,[240,240,220]);g.ell(x+4,y-3,8,8,ph.sky[0]);}
}
function relevo(g,st,ph){
  if(st.relevo==='pinheiros'){g.ell(60,GROUND+4,90,28,ph.hillF);g.ell(180,GROUND+6,90,22,ph.hillF);
    for(let x=4;x<W;x+=20){const h=14+((x/20)%3)*5;g.poly(x,GROUND,[-6,0,6,0,0,-h],ph.hillN);}}
  else if(st.relevo==='colinas'){g.ell(70,GROUND+16,120,46,ph.hillF);g.ell(190,GROUND+18,100,38,ph.hillF);g.ell(30,GROUND+10,80,22,ph.hillN);g.ell(150,GROUND+12,70,16,ph.hillN);}
  else{g.poly(0,GROUND,[-10,0,40,-52,90,0],ph.hillF);g.poly(70,GROUND,[0,0,55,-66,110,0],ph.hillF);g.poly(150,GROUND,[0,0,48,-44,100,0],ph.hillF);
    const sn=light(ph.hillF,.5);g.poly(125,GROUND-66,[0,0,-7,9,7,9],sn);g.poly(40,GROUND-52,[0,0,-6,7,6,7],sn);
    g.ell(40,GROUND+8,90,24,ph.hillN);g.ell(200,GROUND+10,80,20,ph.hillN);}
}
function ground(g,st,ph){
  g.rect(0,GROUND,W,H-GROUND,ph.grass);
  if(st.dither){g.dither(0,GROUND,W,3,ph.grassD);g.hl(0,GROUND,W,dark(ph.grass,.6));}
  if(st.id==='c')g.rect(0,240,W,H-240,ph.grassD);
  if(st.id==='b'){g.ell(22,GROUND+3,12,6,ph.grassD);g.ell(150,GROUND+2,9,5,ph.grassD);}
}
function lake(g,st,ph,t){
  if(st.outline)g.ell(202,214,35,10,st.outline(ph.lake));g.ell(202,214,34,9,ph.lake);
  if(!st.outline){g.ell(194,212,12,2,light(ph.lake,.35));}
  const r=Math.floor(t/500)%3;g.ell(214+r*3,216,3+r,1.5,light(ph.lake,.4),false);
}
function foreground(g,st,ph){
  const c=ph.grassD;for(const x of [18,44,96,150])capim(g,x,200,c);
  if(st.id==='c')for(const x of [12,60,118,176,226])capim(g,x,258,ph.grass,1.4);
}
function tag(g,st,x,y,s,sc=1,center=false){const w=s.length*8*sc+12,h=8*sc+8;if(center)x=Math.round((W-w)/2);
  if(st.id==='a'){g.rrect(x,y,w,h,3,INK);g.rrect(x+1,y+1,w-2,h-2,2,CREME);g.text(s,x+6,y+4,INK,sc);}
  else if(st.id==='b'){g.rrect(x,y,w,h,Math.floor(h/2),CREME);g.text(s,x+6,y+4,TEXTO,sc);}
  else{g.text(s,x+7,y+5,dark(CREME,.25),sc);g.text(s,x+6,y+4,CREME,sc);}
  return w;}
function balaoFala(g,s,x,y){const w=s.length*8+10;x=Math.max(2,Math.min(W-w-2,x-w/2));g.rrect(x,y,w,14,3,BRANCO);g.text(s,x+5,y+3,TEXTO);g.poly(x+w/2,y+14,[-3,0,3,0,0,4],BRANCO);}
// ── balões ────────────────────────────────────────────────────────────
const bolOl=st=>st.id==='b'?null:(st.id==='a'?INK:[128,104,86]);
export function say(g,st,s,cx,top){
  const L=s.split('|'),w=Math.max(...L.map(l=>l.length))*8+12,h=L.length*10+6,ol=bolOl(st);
  const x=Math.round(Math.max(8,Math.min(W-8-w,cx-w/2))),y=Math.round(top-h-8),tx=Math.round(Math.max(x+8,Math.min(x+w-8,cx)));
  if(ol){g.rrect(x-1,y-1,w+2,h+2,4,ol);g.poly(tx,y+h,[-5,0,5,0,0,7],ol);}
  g.rrect(x,y,w,h,3,CREME);g.poly(tx,y+h-1,[-4,0,4,0,0,6],CREME);
  L.forEach((l,i)=>g.text(l,x+6+Math.floor((w-12-l.length*8)/2),y+4+i*10,TEXTO));
  return {x,y,w,h};
}
function thinkIcon(g,k,x,y){
  if(k==='capim')capim(g,x,y+7,[30,124,66],1.1);
  else if(k==='zzz'){g.text('z',x-7,y-1,STAT.energia);g.text('z',x,y-6,STAT.energia);}
  else if(k==='coracao'){const c=STAT.alegria;g.ell(x-3,y-2,3.5,3.5,c);g.ell(x+3,y-2,3.5,3.5,c);g.poly(x,y-1,[-6.5,0,6.5,0,0,7],c);}
  else if(k==='bola')btnIcon(g,1,x,y,null);
  else if(k==='banho')btnIcon(g,2,x,y,null);
  else if(k==='remedio')btnIcon(g,3,x,y,null);
  else if(k==='peixe'){const c=[240,140,90];g.ell(x-2,y,7,4,c);g.poly(x+4,y,[0,0,6,-5,6,5],c);g.px(x-6,y-1,INK);}
  else if(k==='nota'){g.ell(x-2,y+4,3,2.5,INK);g.vl(x,y-6,10,INK);g.rect(x,y-6,5,2,INK);}
}
function think(g,st,k,cx,top,t){
  const ol=bolOl(st),bx=Math.min(W-26,cx+30),by=top-22+Math.round(Math.sin(t/500));
  const dot=(x,y,r)=>{if(ol)g.ell(x,y,r+1,r+1,ol);g.ell(x,y,r,r,CREME);};
  dot(cx+12,top-2,2);dot(cx+19,top-8,3);
  if(ol)g.rrect(bx-17,by-14,34,28,11,ol);g.rrect(bx-16,by-13,32,26,10,CREME);thinkIcon(g,k,bx,by);
}
function shout(g,st,s,cx,top,t){
  const w=s.length*16+22,h=30,x=Math.round(Math.max(10+w/2,Math.min(W-10-w/2,cx))),y=Math.round(top-18),j=Math.floor(t/140)%2,pts=[];
  for(let i=0;i<18;i++){const a=i/18*2*Math.PI+j*.17,r=i%2?1:1.3;pts.push(Math.cos(a)*w/2*r*.82,Math.sin(a)*h/2*r);}
  const ol=bolOl(st);if(ol)g.poly(x,y,pts.map(v=>v*1.08),ol);g.poly(x,y,pts,AMARELO);g.text(s,x-s.length*8,y-7,TEXTO,2);
}
function need(g,st,k,cx,top,half,t){
  const urg=k.endsWith('!'),key=k.replace('!',''),x=Math.round(Math.min(W-24,cx+half+4)),y=Math.round(top+8+(Math.floor(t/400)%2)),ol=urg?VERMELHO:bolOl(st);
  if(ol){g.ell(x,y,14,13,ol);g.poly(x-6,y+8,[0,0,8,0,-6,9],ol);}
  g.ell(x,y,13,12,CREME);g.poly(x-5,y+7,[0,0,6,0,-5,7],CREME);thinkIcon(g,key,x,y);
  if(urg){g.ell(x+11,y-10,5,5,VERMELHO);g.text('!',x+8,y-14,BRANCO);}
}
function sysMsg(g,st,s){const w=s.length*8+20,x=Math.round((W-w)/2),y=36;g.rrect(x,y,w,18,9,UI.tray);g.text(s,x+10,y+5,CREME);}
function icon(g,k,x,y,c){
  if(k==='fome'){g.rect(x+1,y+2,1,6,c);g.rect(x+3,y,2,8,c);g.rect(x+6,y+2,1,6,c);}
  else if(k==='alegria'){g.ell(x+2,y+2,2,2,c);g.ell(x+6,y+2,2,2,c);g.poly(x,y,[0,3,8,3,4,8],c);}
  else if(k==='energia')g.poly(x,y,[4,0,8,0,5,3,8,3,2,8,3,4,0,4],c);
  else{g.rect(x+3,y,2,8,c);g.rect(x,y+3,8,2,c);}
}
function btnIcon(g,i,cx,cy,ol,mono){
  if(i===0)capim(g,cx,cy+7,mono||[30,124,66],1.2);
  else if(i===1){if(ol)g.ell(cx,cy,9,9,ol);g.ell(cx,cy,8,8,mono||[255,154,31]);g.arc(cx,cy,8,8,mono?dark(mono,.6):[210,90,30],2,2);g.ell(cx-3,cy-3,2,2,BRANCO);}
  else if(i===2){const a=mono||[90,170,235];if(ol){g.ell(cx,cy+3,7,7,ol);g.poly(cx,cy,[-7,4,7,4,0,-10],ol);}g.ell(cx,cy+3,6,6,a);g.poly(cx,cy,[-6,3,6,3,0,-9],a);g.ell(cx-2,cy+3,1.5,1.5,BRANCO);}
  else{if(ol){g.ell(cx-3,cy,5,4,ol);g.ell(cx+3,cy,5,4,ol);}g.ell(cx-3,cy,4,3,mono||VERMELHO);g.ell(cx+3,cy,4,3,BRANCO);}
}
function hudPet(g,st,sp,ph){
  const raw=(sp.hud||'80,65,50,90').split(',').map(Number),keys=['fome','alegria','energia','saude'],v={};keys.forEach((k,i)=>v[k]=raw[i]??80);
  const col=k=>v[k]<25?VERMELHO:STAT[k];
  if(st.hud==='pips'){g.rrect(28,6,184,20,4,INK);g.rrect(29,7,182,18,3,CREME);
    keys.forEach((k,i)=>{const x=34+i*45,y=12;icon(g,k,x,y,INK);for(let p=0;p<4;p++){const on=v[k]>p*25+12;g.rect(x+11+p*7,y+1,6,6,on?col(k):TRACK);}});}
  else if(st.hud==='chips'){keys.forEach((k,i)=>{const x=30+i*46,y=8;g.rrect(x,y,42,16,5,CREME);icon(g,k,x+4,y+4,STAT[k]);g.rrect(x+15,y+5,24,6,3,TRACK);g.rrect(x+15,y+5,Math.max(6,Math.round(24*v[k]/100)),6,3,col(k));});}
  else{g.rect(0,224,W,H-224,UI.tray);keys.forEach((k,i)=>{const x=30+i*46;icon(g,k,x,229,CREME);g.rect(x+11,231,29,4,UI.trayBar);g.rect(x+11,231,Math.round(29*v[k]/100),4,col(k));});}
}
function buttons(g,st,ph){
  if(st.id==='a')for(let i=0;i<4;i++){const x=28+i*48,y=238;g.rect(x,y+2,40,36,INK);g.rect(x,y,40,34,CREME);g.box(x,y,40,34,INK);btnIcon(g,i,x+20,y+17,INK);}
  else if(st.id==='b'){const f=[[255,190,120],[255,160,190],[150,205,250],[170,230,170]];for(let i=0;i<4;i++){const cx=48+i*48,cy=257;g.ell(cx,cy+2,17,17,dark(f[i],.78));g.ell(cx,cy,17,17,f[i]);btnIcon(g,i,cx,cy,null);}}
  else for(let i=0;i<4;i++){const x=28+i*46,y=244;g.rrect(x,y,42,30,7,UI.trayBtn);btnIcon(g,i,x+21,y+15,null,i===0?[170,230,170]:null);}
}
function pose(sp,act,t){
  let cx=+(sp.x||110),pe=FEET,eyes='normal',mouth='sorriso',zz=false,eating=false,water=false;
  if(sp.hour==='cycle'){if(act==='banho'){cx=200;water=true;}else if(act==='comendo')cx=60;else if(act==='passeando')cx=Math.round(120+64*Math.sin(t/5000));else cx=110;}
  else if(act==='banho'||act==='nadando'){cx=200;water=true;}
  if(act==='dormindo'){eyes='fechados';mouth='dormindo';zz=true;pe+=Math.trunc(Math.sin(t/900));}
  else if(water){eyes='feliz';pe=211+Math.round(Math.sin(t/700)*4);}
  else if(act==='comendo'){eating=true;mouth=(Math.floor(t/220)%2)?'aberta':'meia';pe+=Math.trunc(Math.sin(t/300)*1.5);}
  else if(act==='espreguicando'){eyes='sono';mouth='o';}
  else if(act==='por do sol'){eyes='feliz';}
  else if(act==='pular'){eyes='feliz';pe-=Math.trunc(Math.abs(Math.sin(t/260))*20);}
  else if(act==='correndo'){eyes='feliz';pe-=Math.trunc(Math.abs(Math.sin(t/72))*6);}
  else pe+=Math.trunc(Math.sin(t/300)*1.5);
  if(sp.sick==='1'&&!sp.eyes){eyes='sono';mouth='triste';}
  if(sp.eyes)eyes=sp.eyes;if(sp.mouth)mouth=sp.mouth;
  if(eyes==='normal'&&(t%3800)<150&&!sp.eyes)eyes='fechados';
  return {cx,pe,eyes,mouth,zz,eating,water};
}
function explore(g,st,ph,sp,t){
  const off=Math.floor(t/40),ol=st.outline,wrap=(x,per)=>((x%per)+per)%per;
  for(let i=0;i<6;i++)tree(g,wrap(i*60-off/2,W+60)-30,GROUND,ph.hillF,10,null);
  g.rect(0,GROUND,W,H-GROUND,ph.grass);if(st.dither)g.hl(0,GROUND,W,dark(ph.grass,.6));
  for(let x=-wrap(off,16);x<W;x+=16)g.rect(x,GROUND+16,8,6,ph.grassD);
  if(st.id==='c')g.rect(0,240,W,H-240,ph.grassD);
  for(let i=0;i<4;i++)tree(g,wrap(i*90-off,W+80)-40,GROUND,ph.hillN,16,ol);
  const sx=wrap(200-off,W+80)-40;g.rect(sx,GROUND-26,3,26,UI.madeira);g.rect(sx-9,GROUND-30,21,10,UI.madeiraCl);if(ol)g.box(sx-9,GROUND-30,21,10,ol(UI.madeiraCl));
  for(let i=0;i<3;i++){const x=wrap(60+i*22-off,W+80)-40,y=GROUND-34-Math.abs(Math.sin(t/300+i))*4;if(ol)g.ell(x,y,4,4,ol(AMARELO));g.ell(x,y,3,3,AMARELO);}
  const pe=FEET-Math.trunc(Math.abs(Math.sin(t/90))*6);
  if(st.shadow)g.ell(110,FEET+1,26,4,ph.grassD);
  drawChar(g,sp.char||'capi',110,pe,{eyes:'feliz',mouth:'sorriso',ol});
  tag(g,st,30,8,up(st,'campo 2'));const w=up(st,'x3');tag(g,st,W-30-(w.length*8+24),8,'  '+w);
  const cx=W-30-(w.length*8+24)+12,cy=16;if(ol)g.ell(cx,cy,4,4,ol(AMARELO));g.ell(cx,cy,3,3,AMARELO);
  g.poly(10,140,[0,0,8,-6,8,6],CREME);g.poly(230,140,[0,0,-8,-6,-8,6],CREME);
}
function iconScene(g,x,y,k){
  g.rect(x,y,36,36,[130,200,250]);
  if(k==='praia'){g.rect(x,y+22,36,14,[240,220,160]);g.ell(x+18,y+22,20,5,[90,170,235]);g.ell(x+28,y+8,4,4,[255,220,60]);}
  else if(k==='floresta'){g.rect(x,y+26,36,10,[46,176,96]);tree(g,x+12,y+26,[40,150,84],12,null);tree(g,x+26,y+26,[40,150,84],8,null);}
  else{g.rect(x,y+30,36,6,[46,176,96]);g.ell(x+18,y+18,8,6,INK);g.ell(x+25,y+13,5,5,INK);g.poly(x+29,y+13,[0,-2,9,0,0,3],[255,140,30]);g.px(x+26,y+12,BRANCO);}
}
function novidades(g,sp){
  const st=STYLES[sp.style]||STYLES.b,ol=st.outline;
  g.fill(CREME);g.center(up(st,'Novidades'),12,TEXTO,2);
  const rows=[['Praia','cenario','praia'],['Floresta','cenario','floresta'],['Tucano','visitante','tucano']];
  rows.forEach((r,i)=>{const y=44+i*58;if(ol)g.rrect(23,y-1,194,52,7,INK);g.rrect(24,y,192,50,6,BRANCO);iconScene(g,32,y+7,r[2]);
    g.text(up(st,r[0]),76,y+12,TEXTO);g.text(up(st,r[1]),76,y+28,MUTED);
    if(ol)g.rrect(159,y+15,50,20,6,INK);g.rrect(160,y+16,48,18,5,STAT.saude);g.text(up(st,'baixar'),160,y+21,BRANCO);});
  g.hl(24,224,192,TRACK);g.text(up(st,'sistema v1.2'),32,236,MUTED);g.text(up(st,'atualizar'),136,236,STAT.energia);
}
function portrait(g,sp){
  const st=STYLES[sp.style]||STYLES.b,ph=PHASES[2];
  g.rect(0,0,80,130,ph.sky[1]);g.rect(0,120,80,10,ph.grass);
  drawChar(g,sp.char,40,125,{eyes:sp.eyes||'normal',mouth:sp.mouth||'sorriso',sick:sp.sick==='1',ol:st.outline,raw:true,s:sp.char==='pato'||sp.char==='calopsita'?.94:1});
}
function guides(g){const c=g.ctx;c.save();
  c.fillStyle='rgba(255,40,40,.45)';c.beginPath();c.rect(0,0,W,H);c.roundRect(0,0,W,H,30);c.fill('evenodd');
  c.strokeStyle='rgba(255,255,255,.14)';c.lineWidth=1;for(let x=8;x<W;x+=8){c.beginPath();c.moveTo(x+.5,0);c.lineTo(x+.5,H);c.stroke();}for(let y=8;y<H;y+=8){c.beginPath();c.moveTo(0,y+.5);c.lineTo(W,y+.5);c.stroke();}
  const zone=(x,y,w,h,lab)=>{c.strokeStyle='#fff';c.setLineDash([2,2]);c.strokeRect(x+.5,y+.5,w-1,h-1);c.setLineDash([]);g.text(lab,x+3,y+3,'#fff');};
  if(g.zones!==false){zone(28,6,184,20,'HUD');zone(70,75,80,130,'80x130');zone(28,238,184,38,'BOTOES');zone(168,205,70,18,'LAGO');}
  c.strokeStyle='#ff0';c.beginPath();c.moveTo(0,FEET+.5);c.lineTo(W,FEET+.5);c.stroke();g.text('Y=205',2,FEET+3,'#ff0');
  c.restore();}

export function draw(g,sp,t){
  drawScene(g,sp,t);
  if(sp.menu!==undefined&&sp.mode!=='portrait'&&sp.mode!=='novidades'){
    const b=sp.menu==='open'?MENU.bottom:+sp.menu;
    if(b>0)drawMenu(g,{mode:sp.mmode||sp.mode,char:sp.mchar||sp.char||'capi',time:sp.mtime||'real',speed:+(sp.mspeed||2),clock:sp.mclock||'14:32'},b);
    else g.rrect(106,3,28,4,2,CREME);
  }
}
// ── menu de ajustes (puxar de cima) ───────────────────────────────────────────
export const MENU={bottom:272,modeY:40,modeH:30,carY:88,carH:62,timeY:182,timeH:26,speedY:214,speedH:22,handleY:256};
export const MODES=[['pet','Cuidar'],['companion','Olhar'],['explore','Passear']];
export const CHAR_ORDER=['capi','elefante','pato','polvo','calopsita','cachorro','gato','et','sapinho'];
export const SPEED_MIN={1:30,2:15,3:10};
const ACC=[242,140,90],MUTEDM=[176,156,176];
function segBtn(g,x,y,w,h,label,on){g.rrect(x,y,w,h,6,on?ACC:UI.trayBtn);g.text(label,x+Math.round((w-label.length*8)/2),y+Math.round((h-8)/2),on?INK:CREME);}
export function drawMenu(g,cfg,bottom){
  const c=g.ctx,off=bottom-MENU.bottom;c.save();c.beginPath();c.rect(0,0,W,bottom);c.clip();c.translate(0,off);
  g.rect(0,0,W,MENU.bottom-10,UI.tray);g.rrect(0,MENU.bottom-22,W,22,10,UI.tray);
  g.center('Ajustes',12,CREME);
  g.rect(196,13,3,5,CREME);g.poly(198,15,[0,-1,6,-5,6,8,0,4],CREME);g.rect(206,13,1,5,CREME);g.rect(209,11,1,9,CREME);
  for(let i=0;i<3;i++)g.rect(36+i*4,19-i*3,3,3+i*3,i<2?CREME:MUTEDM);
  g.text('modo',20,29,MUTEDM);
  MODES.forEach(([id,l],i)=>segBtn(g,20+i*68,MENU.modeY,64,MENU.modeH,l,cfg.mode===id));
  g.text('personagem',20,78,MUTEDM);
  const idx=Math.max(0,CHAR_ORDER.indexOf(cfg.char)),n=CHAR_ORDER.length,at=k=>CHAR_ORDER[(idx+k+n)%n];
  for(const [k,x] of [[-1,56],[1,184]])drawChar(g,at(k),x,MENU.carY+MENU.carH-8,{raw:true,s:.3,eyes:'normal',mouth:'sorriso'});
  g.rrect(83,MENU.carY-1,74,MENU.carH+2,9,ACC);g.rrect(85,MENU.carY+1,70,MENU.carH-2,8,UI.trayBtn);
  drawChar(g,at(0),120,MENU.carY+MENU.carH-6,{raw:true,s:cfg.char==='pato'||cfg.char==='calopsita'?.4:.45,eyes:'feliz',mouth:'sorriso'});
  g.poly(14,MENU.carY+31,[0,0,8,-7,8,7],CREME);g.poly(226,MENU.carY+31,[0,0,-8,-7,-8,7],CREME);
  g.center(NOMES[at(0)],MENU.carY+MENU.carH+6,CREME);
  g.text('hora',20,MENU.timeY-11,MUTEDM);
  segBtn(g,20,MENU.timeY,98,MENU.timeH,'Real',cfg.time==='real');segBtn(g,122,MENU.timeY,98,MENU.timeH,'Simulada',cfg.time==='sim');
  if(cfg.time==='sim'){[1,2,3].forEach((v,i)=>segBtn(g,20+i*68,MENU.speedY,64,MENU.speedH,v+'x',cfg.speed===v));g.center('dia em '+SPEED_MIN[cfg.speed]+' min',MENU.speedY+30,MUTEDM);}
  else{g.center('agora '+cfg.clock,MENU.speedY+4,CREME);g.center('segue o relogio',MENU.speedY+20,MUTEDM);}
  g.rrect(100,MENU.handleY,40,4,2,MUTEDM);
  c.restore();
  if(bottom<H)g.hl(0,bottom,W,[24,18,26]);
}
export function menuHit(x,y,cfg){
  if(y>=MENU.modeY&&y<MENU.modeY+MENU.modeH){const i=Math.floor((x-20)/68);if(i>=0&&i<3)return {k:'mode',v:MODES[i][0]};}
  if(y>=MENU.carY&&y<MENU.carY+MENU.carH+14){if(x<82)return {k:'char',v:-1};if(x>158)return {k:'char',v:1};}
  if(y>=MENU.timeY&&y<MENU.timeY+MENU.timeH)return {k:'time',v:x<120?'real':'sim'};
  if(cfg.time==='sim'&&y>=MENU.speedY&&y<MENU.speedY+MENU.speedH){const i=Math.floor((x-20)/68);if(i>=0&&i<3)return {k:'speed',v:i+1};}
  if(y>=MENU.handleY-14)return {k:'close'};
  return null;
}
function drawScene(g,sp,t){
  if(sp.mode==='portrait')return portrait(g,sp);
  if(sp.mode==='novidades')return novidades(g,sp);
  const st=STYLES[sp.style]||STYLES.b,ol=st.outline;
  const hour=sp.hour==='cycle'?((t/60000)*24)%24:parseFloat(sp.hour||10);
  const ph=phaseOf(hour);
  const act=sp.act||(sp.mode==='companion'?(sp.hour==='cycle'?activityOf(hour):'passeando'):'');
  sky(g,st,ph);
  if(ph.stars)stars(g,t);
  if(sp.weather==='chuva')chuva(g,t);else sunMoon(g,st,ph,hour);
  if(!ph.stars&&st.id!=='a'&&sp.weather!=='chuva'){const c=light(ph.sky[1],.6);nuvem(g,Math.round(((t/220)%(W+80))-40),46,c);nuvem(g,Math.round(((t/300+150)%(W+80))-40),72,c);}
  if(sp.event==='balao')balao(g,t);if(sp.event==='cometa'&&ph.stars)cometa(g,t);
  relevo(g,st,ph);
  if(sp.mode==='explore')return explore(g,st,ph,sp,t);
  ground(g,st,ph);lake(g,st,ph,t);foreground(g,st,ph);
  if(sp.build&&BUILDS[sp.build])BUILDS[sp.build](g,ph,t);
  const p=pose(sp,act,t);
  const name=NOMES[sp.char]||'Capi';
  let r=null;
  if(sp.stage!=='none'){
    if(st.shadow&&!p.water&&sp.stage!=='ovo')g.ell(p.cx,FEET+1,sp.stage==='filhote'?12:20,3,ph.grassD);
    r=drawChar(g,sp.char||'capi',p.cx,p.pe,{eyes:p.eyes,mouth:p.mouth,sick:sp.sick==='1',ol,stage:sp.stage,crack:sp.crack==='1',grass:ph.grass});
    if(p.water){g.ell(p.cx,214,r.half+8,8,ph.lake);for(let i=0;i<4;i++){const a=t/210+i*1.4,ox=Math.round(p.cx+Math.cos(a)*(12+i*3)),oy=Math.round(213+Math.sin(a*1.5)*3);if(ox>168&&ox<238)g.ell(ox,oy,3+i,2,light(ph.lake,.4),false);}}
    if(p.eating)for(let i=0;i<3;i++)capim(g,p.cx+r.half+2+i*6,FEET-4,ph.grassD);
    if(p.zz){const z=Math.floor(t/450)%3;g.text('z',p.cx+r.half+z*4,r.top-4-z*7,CREME,2);}
    if(sp.poop)for(let i=0;i<+sp.poop;i++){const x=24+i*16;g.ell(x,211,5,4,[90,58,26]);g.ell(x,206,3,3,[90,58,26]);}
  }
  const vis=ph.stars&&sp.hour==='cycle'?'vagalumes':sp.visitor;
  if(vis&&r){
    if(vis==='passarinho')V.passarinho(g,p.cx,r.top-6,t);
    else if(vis==='tartaruga')V.tartaruga(g,Math.round(230-((t/50)%300)),208,t);
    else if(vis==='borboleta')V.borboleta(g,Math.round(p.cx+45*Math.sin(t/900)),Math.round(r.top+8+15*Math.sin(t/450)),t);
    else if(vis==='sapo'&&!p.water)V.sapo(g,196,208,t);
    else if(vis==='vagalumes'&&ph.stars)V.vagalumes(g,t);
    else if(CHARS[vis]){const vx=p.cx>110?52:172;if(st.shadow)g.ell(vx,FEET+1,16,3,ph.grassD);
      const talking=sp.alt==='1'?Math.floor(t/2600)%2===1:true;
      const vr=drawChar(g,vis,vx,FEET+Math.trunc(Math.sin(t/260+1)*1.5),{s:.9,eyes:'feliz',mouth:talking&&(Math.floor(t/180)%2)?'aberta':'sorriso',ol});
      const line=sp.vsay!==undefined?sp.vsay:(sp.say?'':'oi, '+name+'!');
      if(line&&talking)say(g,st,up(st,line),vx,vr.top);}
  }
  if(sp.fala&&r)balaoFala(g,up(st,sp.fala),p.cx,r.top-22);
  if(r){const mainTalk=sp.alt==='1'&&sp.vsay?Math.floor(t/2600)%2===0:true;
    if(sp.say&&mainTalk)say(g,st,up(st,sp.say),p.cx,r.top);
    if(sp.think)think(g,st,sp.think,p.cx,r.top,t);
    if(sp.shout)shout(g,st,sp.shout,p.cx,r.top,t);
    if(sp.need)need(g,st,sp.need,p.cx,r.top,r.half,t);}
  if(sp.sys)sysMsg(g,st,up(st,sp.sys));
  if(sp.star){g.poly(120,66,[0,-9,2,-2,9,0,2,2,0,9,-2,2,-9,0,-2,-2],AMARELO);g.px(112,58,BRANCO);g.px(129,75,BRANCO);g.text(up(st,sp.star),120-sp.star.length*4,82,CREME);}
  if(sp.mode==='pet'){hudPet(g,st,sp,ph);buttons(g,st,ph);}
  else if(sp.mode==='companion'){const hh=String(Math.floor(hour)).padStart(2,'0'),mm=String(Math.floor(hour*60)%60).padStart(2,'0');tag(g,st,0,8,hh+':'+mm,2,true);
    if(st.caption&&act&&sp.live!=='0')tag(g,st,0,258,up(st,name+' '+(TEXTOS[act]||act)),1,true);}
  if(sp.text)tag(g,st,0,256,up(st,sp.text),1,true);
  if(sp.msg){const w=sp.msg.length*16+16;g.rrect((W-w)/2,50,w,24,6,BRANCO);g.center(up(st,sp.msg),54,TEXTO,2);}
  if(sp.guides==='1'||sp.guides==='2'){g.zones=sp.guides==='1';guides(g);}
}
