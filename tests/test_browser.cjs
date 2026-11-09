'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawn,execFileSync}=require('node:child_process'),{waitForDebugger}=require('./chrome_support.cjs');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function compare(a,b,p='root'){assert.equal(typeof a,typeof b,p);if(typeof a==='number')assert.ok(Number.isFinite(b)&&Math.abs(a-b)<=1e-5*Math.max(1,Math.abs(a),Math.abs(b)),p+' expected '+a+' actual '+b);else if(a===null||typeof a!=='object')assert.equal(a,b,p);else{assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),p);for(const k of Object.keys(a))compare(a[k],b[k],p+'.'+k);}}
test('actual Chrome full cut, flow, local-search and residual-family witnesses',{timeout:180000},async()=>{
 const server=require('node:http').createServer((req,res)=>{try{const file=path.join(__dirname,'../docs',req.url==='/'?'index.html':req.url);const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'};res.setHeader('Content-Type',types[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch(e){res.statusCode=404;res.end('not found');}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'cutlab-')),browser=spawn(process.env.CHROME_BIN||'google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-extensions','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:['ignore','ignore','pipe']});let ws,startupError,diagnostics='';browser.on('error',e=>startupError=e);browser.stderr.on('data',d=>diagnostics=(diagnostics+d).slice(-4000));
 try{for(let i=0;i<1200&&!startupError&&browser.exitCode===null&&!fs.existsSync(path.join(profile,'DevToolsActivePort'));i++)await delay(25);assert.ok(fs.existsSync(path.join(profile,'DevToolsActivePort')),startupError?.message||diagnostics||'Chrome unavailable');const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0],tab=await waitForDebugger(`http://127.0.0.1:${port}/json/list`,{alive:()=>browser.exitCode===null&&!startupError});ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej;});let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const {res,rej}=pending.get(m.id);pending.delete(m.id);m.error?rej(Error(JSON.stringify(m.error))):res(m.result);}};const call=(method,params={})=>new Promise((res,rej)=>{const id=++seq;pending.set(id,{res,rej});ws.send(JSON.stringify({id,method,params}));});const js=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 await call('Page.enable');await call('Page.navigate',{url:process.env.CUTLAB_URL||`http://127.0.0.1:${server.address().port}/`});
 for(let i=0;i<500;i++){if(await js('Boolean(window.currentReport)'))break;await delay(20);}assert.ok(await js('window.currentReport'));






 const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/audits.json'),'utf8'));
 const set=async(id,value,event='change')=>js(`document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(String(value))};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event(${JSON.stringify(event)}))`),record=async id=>JSON.parse(await js(`document.getElementById(${JSON.stringify(id)}).textContent`));
 let cuts=0,steps=0,pairs=0,residuals=0,locals=0,graphEdges=0,graphNodes=0,terminals=0;
 const cells=id=>js(`Array.from(document.querySelectorAll('#${id} tbody tr'),tr=>Array.from(tr.cells,c=>c.textContent))`);
 for(let c=0;c<fixtures.length;c++){
  const r=fixtures[c].report,n=r.input.unary.length;await set('preset',c);assert.deepEqual(await js('window.currentReport'),r);assert.equal(await js('document.getElementById("network-results").hidden'),r.status==='refused');
  const expectedMetrics=r.status==='solved'?[r.minimum,r.flow_value,r.offset,String(r.optimal_masks.length)]:[r.reference.minimum,String(r.reference.optimal_masks.length),String(r.violations.length),'none'];assert.deepEqual(await js('Array.from(document.querySelectorAll(".metric b"),e=>e.textContent)'),expectedMetrics);
  assert.equal(await js('document.getElementById("comparison").textContent'),`Unary-only energy ${r.reference.unary_only_energy}, gap ${r.reference.unary_only_gap}. Strict single-flip energy ${r.reference.single_flip.energy}, gap ${r.reference.single_flip.gap}.`);
  assert.deepEqual(await cells('pairs-table'),r.pair_reductions.map(p=>[p.pair,p.i,p.j,...p.values,p.linear_i,p.linear_j,p.capacity].map(String)));
  for(let i=0;i<r.pair_reductions.length;i++){await set('pair',i);assert.deepEqual(await record('pair-json'),r.pair_reductions[i]);pairs++;}
  for(let i=0;i<r.reference.single_flip.trace.length;i++){await set('local',i);assert.deepEqual(await record('local-json'),r.reference.single_flip.trace[i]);locals++;}
  if(r.status==='refused'){assert.equal(await js('document.getElementById("refusal").hidden'),false);continue;}
  assert.deepEqual(await cells('terminals-table'),r.terminals.map(p=>[String(p.variable),p.linear,p.constant_shift,JSON.stringify(p.edge),p.capacity]));terminals+=r.terminals.length;
  assert.deepEqual(await cells('assignments-table'),r.assignments.map(p=>[String(p.mask),JSON.stringify(p.bits),p.energy,p.cut_capacity,p.offset_plus_cut,p.cut_minus_flow,p.residual_out,String(p.closed)]));
  assert.deepEqual(await cells('family-table'),r.forced_bits.map((b,i)=>[String(i),b===null?'free':String(b),String(r.component_of[i])]));
  assert.deepEqual(await record('family-json'),{optimal_masks:r.optimal_masks,smallest_source:r.smallest_source,largest_source:r.largest_source,components:r.components,condensation:r.condensation,balance:r.balance});
  const re=[];r.residual.forEach((row,u)=>row.forEach((capacity,v)=>{if(capacity!=='0')re.push({u,v,capacity,from_component:r.component_of[u],to_component:r.component_of[v]});}));
  assert.deepEqual(await cells('residual-table'),re.map(p=>[String(p.u),String(p.v),p.capacity,String(p.from_component),String(p.to_component)]));
  for(let i=0;i<re.length;i++){await set('residual',i);assert.deepEqual(await record('residual-json'),re[i]);residuals++;}
  const selectedMask=r.optimal_masks[0];
  for(let k=0;k<=r.trace.length;k++){
   await set('step',k);assert.deepEqual(await record('step-json'),k===0?{state:'initial',value:'0',path:[],delta:'0'}:r.trace[k-1]);steps++;
   const f=k===0?r.flows.map(e=>({...e,flow:'0',forward_residual:e.capacity,reverse_residual:'0'})):r.trace[k-1].flows_after;
   assert.deepEqual(await cells('flows-table'),f.map(e=>[String(e.u),String(e.v),e.capacity,e.flow,e.forward_residual,e.reverse_residual]));
   const pos=i=>i===n?[35,240]:i===n+1?[725,240]:[120+(n===1?240:i*500/(n-1)),i%2===0?155:325];
   const source=i=>i===n||i<n&&((selectedMask>>i)&1)===0;
   const expected=f.map(e=>{const [x1,y1]=pos(e.u),[x2,y2]=pos(e.v),dx=x2-x1,dy=y2-y1,len=Math.hypot(dx,dy);return {edge:`${e.u},${e.v}`,x1:x1+dx*23/len,y1:y1+dy*23/len,x2:x2-dx*27/len,y2:y2-dy*27/len,color:source(e.u)&&!source(e.v)?'#b94e20':'#938497',label:`${e.flow} / ${e.capacity}`};});
   const boxes=await js(`(()=>{const labels=Array.from(document.querySelectorAll('#network g[data-edge] text'),e=>{const r=e.getBBox();return {x:r.x,y:r.y,w:r.width,h:r.height}}),nodes=Array.from(document.querySelectorAll('#network g[data-node] circle'),e=>({x:Number(e.getAttribute('cx')),y:Number(e.getAttribute('cy')),r:Number(e.getAttribute('r'))}));return {labels,nodes}})()`);
   for(let i=0;i<boxes.labels.length;i++){const a=boxes.labels[i];assert.ok(a.x>=0&&a.x+a.w<=760&&a.y>=0&&a.y+a.h<=480,'label inside graph');for(const b of boxes.labels.slice(i+1))assert.ok(a.x+a.w+2<=b.x||b.x+b.w+2<=a.x||a.y+a.h+2<=b.y||b.y+b.h+2<=a.y,'edge-label noncollision '+c+':'+k);for(const b of boxes.nodes)assert.ok(a.x+a.w+2<=b.x-b.r||a.x>=b.x+b.r+2||a.y+a.h+2<=b.y-b.r||a.y>=b.y+b.r+2,'edge label clear of node '+c+':'+k);}
   compare(await js('Array.from(document.querySelectorAll("#network g[data-edge]"),g=>({edge:g.dataset.edge,x1:Number(g.querySelector("line").getAttribute("x1")),y1:Number(g.querySelector("line").getAttribute("y1")),x2:Number(g.querySelector("line").getAttribute("x2")),y2:Number(g.querySelector("line").getAttribute("y2")),color:g.querySelector("line").getAttribute("stroke"),label:g.querySelector("text").textContent}))'),expected);graphEdges+=expected.length;
  }
  for(const row of r.assignments){
   await set('assignment',row.mask);assert.deepEqual(await record('assignment-json'),row);cuts++;
   assert.deepEqual(await js('Array.from(document.querySelectorAll("#network g[data-node]"),g=>({node:Number(g.dataset.node),color:g.querySelector("circle").getAttribute("fill")}))'),Array.from({length:n+2},(_,i)=>({node:i,color:i===n||i<n&&row.bits[i]===0?'#8e3657':'#23696a'})));graphNodes+=n+2;
   assert.deepEqual(await js('Array.from(document.querySelectorAll("#assignments-table tr.selected"),e=>Number(e.dataset.mask))'),[row.mask]);
  }
 }
 await set('input','{}','input');assert.equal(await js('window.currentReport'),null);assert.equal(await js('document.getElementById("results").hidden'),true);assert.equal(await js('document.getElementById("export").disabled'),true);await js('document.getElementById("run").click()');assert.match(await js('document.getElementById("state").textContent'),/^Invalid input:/);
 await set('preset',23);await js('HTMLAnchorElement.prototype.click=function(){window.downloaded={name:this.download,url:this.href}};URL.revokeObjectURL=function(){}');await js('document.getElementById("export").click()');assert.deepEqual(await js('fetch(downloaded.url).then(r=>r.json())'),fixtures[23].report);assert.equal(await js('downloaded.name'),'cutlab-witness.json');
 for(const width of [320,390,1280]){await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<700});await js('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');assert.ok(await js('document.documentElement.scrollWidth<=innerWidth'),'overflow '+width);}
 console.log(JSON.stringify({cases:fixtures.length,cuts,steps,pairs,residuals,locals,terminals,graphEdges,graphNodes,exports:1,widths:[320,390,1280]}));
 if(process.env.CUTLAB_SCREENSHOT){const width=Number(process.env.CUTLAB_WIDTH||1280);await call('Emulation.setDeviceMetricsOverride',{width,height:1200,deviceScaleFactor:1,mobile:width<700});await js('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');await js('document.activeElement.blur();document.querySelectorAll("details").forEach(e=>e.open=true);window.scrollTo(0,0)');const m=await call('Page.getLayoutMetrics'),image=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:m.cssContentSize.height,scale:1}});fs.writeFileSync(process.env.CUTLAB_SCREENSHOT,Buffer.from(image.data,'base64'));}
 }finally{server.close();if(ws)ws.close();if(browser.pid&&browser.exitCode===null){browser.kill('SIGTERM');await new Promise(r=>browser.once('exit',r));}await fs.promises.rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200});}
});
