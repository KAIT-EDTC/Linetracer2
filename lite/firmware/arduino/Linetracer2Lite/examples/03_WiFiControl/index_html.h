// The page the phone gets (one file, no internet needed).  The phone calls /api about 10 times a second:
// that is the "signal" of the watchdog in 03_WiFiControl.ino.
#pragma once

const char INDEX_HTML[] PROGMEM = R"HTML(<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Linetracer2</title>
<style>
:root{--bg:#10141a;--card:#1b222c;--fg:#e8edf3;--dim:#8a96a6;--acc:#2fb5ff;--ok:#3ddc84;--ng:#ff5a5a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif;user-select:none;-webkit-user-select:none}
main{max-width:480px;margin:0 auto;padding:12px 16px 24px}
h1{font-size:20px;margin:4px 0 8px;display:flex;justify-content:space-between;align-items:center}
#st{font-size:13px;padding:3px 10px;border-radius:99px;background:var(--ng);color:#000}
#st.ok{background:var(--ok)}
.card{background:var(--card);border-radius:14px;padding:12px;margin:10px 0}
#pad{position:relative;width:min(80vw,300px);aspect-ratio:1;margin:6px auto;border-radius:50%;
 background:radial-gradient(circle,#26303d 0 60%,#1f2732 61%);touch-action:none}
#knob{position:absolute;width:30%;height:30%;left:35%;top:35%;border-radius:50%;background:var(--acc);
 box-shadow:0 4px 14px #0008;pointer-events:none}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
label{color:var(--dim);font-size:14px}
input[type=range]{flex:1}
button{flex:1;min-height:44px;border:0;border-radius:10px;background:#2a3442;color:var(--fg);font-size:16px}
button:active{filter:brightness(1.4)}
button.go{background:var(--ok);color:#000}button.stop{background:var(--ng);color:#000}
#cols{gap:4px;justify-content:space-between;flex-wrap:nowrap}
.c{flex:0 0 32px;height:32px;min-height:0;border-radius:50%;border:3px solid transparent}
.c.sel{border-color:#fff}
.bars{display:flex;gap:10px}
.bar{flex:1;text-align:center;font-size:12px;color:var(--dim)}
.bar div{height:60px;background:#0c1015;border-radius:6px;position:relative;overflow:hidden;margin-bottom:4px}
.bar span{position:absolute;bottom:0;left:0;right:0;background:#dfe6ee}
select{min-height:44px;border-radius:10px;background:#2a3442;color:var(--fg);border:0;font-size:16px;padding:0 8px}
#msg{color:var(--dim);font-size:13px;min-height:1em;margin-top:6px}
</style></head><body><main>
<h1>Linetracer2 <span id="st">つないでいます…</span></h1>

<div class="card">
 <div id="pad"><div id="knob"></div></div>
 <div class="row"><label>はやさ</label><input id="spd" type="range" min="20" max="100" value="60"><span id="spdv">60</span>%</div>
</div>

<div class="card">
 <div class="row"><button id="beep">♪ ブザー</button><button id="melo">♫ メロディ</button></div>
 <div class="row" id="cols" style="margin-top:10px"></div>
</div>

<div class="card">
 <div class="row" style="margin-bottom:8px"><label>センサー（白いほど 長い）</label></div>
 <div class="bars"><div class="bar"><div><span id="b0"></span></div>S1 左</div>
  <div class="bar"><div><span id="b1"></span></div>S2 まん中</div>
  <div class="bar"><div><span id="b2"></span></div>S3 右</div></div>
</div>

<div class="card">
 <div class="row"><label>ライントレース</label>
  <select id="lv"><option value="1">ゆっくり</option><option value="2">ふつう</option><option value="3">はやい</option></select></div>
 <div class="row" style="margin-top:8px"><button id="cal">① 白黒を おぼえる</button><button id="trace" class="go">② スタート</button></div>
 <div id="msg">黒い 線の 上に おいて ① → ②</div>
</div>
</main>
<script>
const $=id=>document.getElementById(id);
let L=0,R=0,mode="drive",busy=false;
const pad=$("pad"),knob=$("knob");

// joystick: up = forward, sideways = turn
function setKnob(x,y){knob.style.left=(35+x*35)+"%";knob.style.top=(35+y*35)+"%"}
function drive(e){
 const b=pad.getBoundingClientRect();
 let x=(e.clientX-b.left)/b.width*2-1,y=(e.clientY-b.top)/b.height*2-1;
 const d=Math.hypot(x,y);if(d>1){x/=d;y/=d}
 setKnob(x,y);
 const s=+$("spd").value,f=-y,t=x*0.6;
 L=Math.round(Math.max(-1,Math.min(1,f+t))*s);R=Math.round(Math.max(-1,Math.min(1,f-t))*s);
}
pad.addEventListener("pointerdown",e=>{pad.setPointerCapture(e.pointerId);drive(e)});
pad.addEventListener("pointermove",e=>{if(pad.hasPointerCapture(e.pointerId))drive(e)});
const release=()=>{L=R=0;setKnob(0,0)};
pad.addEventListener("pointerup",release);pad.addEventListener("pointercancel",release);
$("spd").oninput=()=>$("spdv").textContent=$("spd").value;

async function get(u,ms=1500){
 const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);
 try{const r=await fetch(u,{signal:c.signal,cache:"no-store"});return r}finally{clearTimeout(t)}
}

// ~10 times a second: send the speeds, get the sensors.  (no answer for 1 s -> the robot stops by itself)
async function tick(){
 if(!busy){
  try{
   const r=await get(mode=="trace"?"/api":`/api?l=${L}&r=${R}`,800);
   const j=await r.json();
   $("st").textContent="つながっています";$("st").className="ok";
   for(let i=0;i<3;i++)$("b"+i).style.height=Math.min(100,j.s[i]/30)+"%";
   if(mode=="trace"&&j.mode!="trace"){$("msg").textContent="止まりました";}
   mode=j.mode;
   $("trace").textContent=mode=="trace"?"ストップ":"② スタート";
   $("trace").className=mode=="trace"?"stop":"go";
  }catch(e){$("st").textContent="きれています";$("st").className="";}
 }
 setTimeout(tick,100);
}
tick();

$("beep").onclick=()=>get("/beep?f=4000&ms=150");
$("melo").onclick=async()=>{for(const[f,ms]of[[1047,150],[1319,150],[1568,150],[2093,300]])await get(`/beep?f=${f}&ms=${ms}`)};

const COLS=["2fb5ff","00ff00","ff0000","ffc800","b400ff","ff3c96","ffffff","000000"];
COLS.forEach((c,i)=>{const b=document.createElement("button");b.className="c"+(i==0?" sel":"");
 b.style.background="#"+(c=="000000"?"333":c);b.title=c;
 b.onclick=()=>{document.querySelectorAll(".c").forEach(x=>x.classList.remove("sel"));b.classList.add("sel");get("/led?c="+c)};
 $("cols").appendChild(b)});
get("/led?c="+COLS[0]);

$("cal").onclick=async()=>{
 busy=true;$("msg").textContent="白と 黒を おぼえています… ロボットが まわります";
 try{const j=await(await get("/cal",8000)).json();
  $("msg").textContent=j.ok?"OK! ② スタートを おしてね":"しっぱい: 黒い 線の 上に おいて もう一度";
 }catch(e){$("msg").textContent="へんじが ありません"}
 busy=false;
};
$("trace").onclick=async()=>{
 const on=mode!="trace";
 const r=await get(`/trace?on=${on?1:0}&level=${$("lv").value}`);
 if(r.status==409){$("msg").textContent="さきに ① 白黒を おぼえる";return}
 $("msg").textContent=on?"走っています（START か ストップで 止まる）":"止めました";
 mode=on?"trace":"drive";
};
</script></body></html>)HTML";
