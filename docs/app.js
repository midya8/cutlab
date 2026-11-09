import {audit,parseInput} from './engine.js';
const $=id=>document.getElementById(id),text=(id,v)=>{$(id).textContent=v;},pretty=(id,v)=>text(id,JSON.stringify(v,null,2)),opt=(el,value,label)=>{const o=document.createElement('option');o.value=value;o.textContent=label;el.append(o);};
const table=(id,headers,rows)=>{const t=$(id);t.replaceChildren();const h=document.createElement('tr');headers.forEach(v=>{const c=document.createElement('th');c.textContent=v;h.append(c);});const head=document.createElement('thead');head.append(h);t.append(head);const body=document.createElement('tbody');rows.forEach(row=>{const tr=document.createElement('tr');if(row.className)tr.className=row.className;if(row.mask!==undefined)tr.dataset.mask=row.mask;(row.cells||row).forEach(v=>{const td=document.createElement('td');td.textContent=Array.isArray(v)?JSON.stringify(v):v===null?'free':String(v);tr.append(td);});body.append(tr);});t.append(body);};
let current=null,cases=[];
const nodeName=(i,n)=>i===n?'s':i===n+1?'t':'x'+i;
function currentFlows(){if(!current||current.status!=='solved')return [];const k=Number($('step').value);return k===0?current.flows.map(e=>({...e,flow:'0',forward_residual:e.capacity,reverse_residual:'0'})):current.trace[k-1].flows_after;}
function graph(){if(!current||current.status!=='solved')return;const n=current.input.unary.length,N=n+2,mask=Number($('assignment').value),flows=currentFlows(),svg=$('network'),NS='http://www.w3.org/2000/svg';svg.replaceChildren();
 const make=(tag,attrs,txt)=>{const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(txt!==undefined)e.textContent=txt;return e;};
 const defs=make('defs',{}),marker=make('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});marker.append(make('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#645d6d'}));defs.append(marker);svg.append(defs);
 const pos=i=>i===n?[35,240]:i===n+1?[725,240]:[120+(n===1?240:i*500/(n-1)),i%2===0?155:325];
 const source=i=>i===n||i<n&&((mask>>i)&1)===0;
 // Place readable labels without covering variable nodes or other edge labels.
 // Geometry is decorative; exact capacities and flow remain in the full table.
 const occupied=[],nodes=Array.from({length:N},(_,i)=>pos(i));
 const offsets=[];for(let dy=-150;dy<=150;dy+=15)for(let dx=-180;dx<=180;dx+=15)offsets.push([dx,dy]);offsets.sort((a,b)=>(a[0]**2+a[1]**2)-(b[0]**2+b[1]**2)||a[1]-b[1]||a[0]-b[0]);
 function labelPosition(e){const a=pos(e.u),b=pos(e.v),mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2-6,label=`${e.flow} / ${e.capacity}`,half=label.length*3.65+4;
  for(const [dx,dy] of offsets){const x=mx+dx,y=my+dy,r={left:x-half,right:x+half,top:y-13,bottom:y+5};if(r.left<6||r.right>754||r.top<5||r.bottom>475)continue;
   if(nodes.some(([nx,ny])=>r.left<nx+29&&r.right>nx-29&&r.top<ny+29&&r.bottom>ny-29))continue;
   if(occupied.some(q=>r.left<q.right+5&&r.right>q.left-5&&r.top<q.bottom+5&&r.bottom>q.top-5))continue;
   occupied.push(r);return {x,y,label};
  }throw Error('No readable edge-label position within the bounded graph');
 }
 for(const e of flows){const [x1,y1]=pos(e.u),[x2,y2]=pos(e.v),dx=x2-x1,dy=y2-y1,len=Math.hypot(dx,dy),cross=source(e.u)&&!source(e.v),lp=labelPosition(e);const g=make('g',{'data-edge':`${e.u},${e.v}`});g.append(make('line',{x1:x1+dx*23/len,y1:y1+dy*23/len,x2:x2-dx*27/len,y2:y2-dy*27/len,stroke:cross?'#b94e20':'#938497','stroke-width':cross?3:1.5,'marker-end':'url(#arrow)'}));if(Math.abs(lp.x-(x1+x2)/2)>1||Math.abs(lp.y-((y1+y2)/2-6))>1)g.append(make('line',{x1:(x1+x2)/2,y1:(y1+y2)/2,x2:lp.x,y2:lp.y-5,stroke:'#938497','stroke-width':0.7,'stroke-dasharray':'2 3'}));g.append(make('text',{x:lp.x,y:lp.y,'text-anchor':'middle',fill:'#292033','font-family':'monospace','font-size':12,'paint-order':'stroke',stroke:'#e9e4e6','stroke-width':4},lp.label));svg.append(g);}
 for(let i=0;i<N;i++){const [x,y]=pos(i),g=make('g',{'data-node':i});g.append(make('circle',{cx:x,cy:y,r:23,fill:source(i)?'#8e3657':'#23696a'}));g.append(make('text',{x,y:y+5,'text-anchor':'middle',fill:'#fff','font-family':'monospace','font-size':14},nodeName(i,n)));svg.append(g);}
}
function selectedPair(){pretty('pair-json',current.pair_reductions[Number($('pair').value)]??{message:'No pair terms.'});}
function selectedStep(){if(current.status!=='solved')return;const k=Number($('step').value);pretty('step-json',k===0?{state:'initial',value:'0',path:[],delta:'0'}:current.trace[k-1]);table('flows-table',['u','v','capacity','flow','forward residual','reverse residual'],currentFlows().map(e=>[e.u,e.v,e.capacity,e.flow,e.forward_residual,e.reverse_residual]));graph();}
function selectedAssignment(){if(current.status!=='solved')return;const mask=Number($('assignment').value);pretty('assignment-json',current.assignments[mask]);document.querySelectorAll('#assignments-table tbody tr').forEach(tr=>tr.classList.toggle('selected',Number(tr.dataset.mask)===mask));graph();}
function residualEntries(){if(current.status!=='solved')return [];const out=[];current.residual.forEach((row,u)=>row.forEach((capacity,v)=>{if(capacity!=='0')out.push({u,v,capacity,from_component:current.component_of[u],to_component:current.component_of[v]});}));return out;}
function selectedResidual(){pretty('residual-json',residualEntries()[Number($('residual').value)]??{message:'No positive residual arcs.'});}
function selectedLocal(){pretty('local-json',current.reference.single_flip.trace[Number($('local').value)]);}
function render(r){current=r;window.currentReport=r;$('results').hidden=false;$('export').disabled=false;text('state','Current witness ready. No network or model call.');$('state').className='';
 const solved=r.status==='solved';$('network-results').hidden=!solved;$('solved-reduction').hidden=!solved;$('refusal').hidden=solved;text('headline',solved?'A matching lower and upper bound.':'Negative capacity. Graph solve refused.');
 $('metrics').replaceChildren();const metrics=solved?[[r.minimum,'minimum energy'],[r.flow_value,'maximum flow'],[r.offset,'retained offset'],[r.optimal_masks.length,'optimal assignments']]:[[r.reference.minimum,'enumerated minimum'],[r.reference.optimal_masks.length,'enumerated ties'],[r.violations.length,'negative pair slacks'],['none','graph certificate']];
 metrics.forEach(([v,label])=>{const d=document.createElement('div');d.className='metric';const b=document.createElement('b'),s=document.createElement('span');b.textContent=v;s.textContent=label;d.append(b,s);$('metrics').append(d);});
 text('comparison',`Unary-only energy ${r.reference.unary_only_energy}, gap ${r.reference.unary_only_gap}. Strict single-flip energy ${r.reference.single_flip.energy}, gap ${r.reference.single_flip.gap}.`);text('refusal','This supplied pair table violates submodularity. No negative edge is clipped, no flow/cut optimum is asserted. Only the original-energy exhaustive reference and local control are retained.');
 $('pair').replaceChildren();r.pair_reductions.forEach((p,k)=>opt($('pair'),k,`Pair ${k}: x${p.i}, x${p.j}; slack ${p.capacity}`));selectedPair();
 table('pairs-table',['pair','i','j','A','B','C','D','linear i','linear j','w'],r.pair_reductions.map(p=>[p.pair,p.i,p.j,...p.values,p.linear_i,p.linear_j,p.capacity]));
 if(solved){
  table('terminals-table',['variable','linear','offset shift','edge','capacity'],r.terminals.map(p=>[p.variable,p.linear,p.constant_shift,p.edge,p.capacity]));
  $('step').replaceChildren();opt($('step'),0,'Initial zero flow');r.trace.forEach((t,k)=>opt($('step'),k+1,`After augmentation ${k+1}: flow ${t.value}, delta ${t.delta}`));$('step').value=r.trace.length;
  $('assignment').replaceChildren();r.assignments.forEach(row=>opt($('assignment'),row.mask,`mask ${row.mask} / x=[${row.bits.join(',')}] / energy ${row.energy}${row.closed?' / optimal':''}`));$('assignment').value=r.optimal_masks[0];
  table('assignments-table',['mask','x0…','energy','cut','offset + cut','cut - flow','residual out','closed'],r.assignments.map(p=>({mask:p.mask,className:p.closed?'optimal':'',cells:[p.mask,p.bits,p.energy,p.cut_capacity,p.offset_plus_cut,p.cut_minus_flow,p.residual_out,p.closed]})));
  table('family-table',['variable','forced label','component'],r.forced_bits.map((v,i)=>[i,v,r.component_of[i]]));pretty('family-json',{optimal_masks:r.optimal_masks,smallest_source:r.smallest_source,largest_source:r.largest_source,components:r.components,condensation:r.condensation,balance:r.balance});
  $('residual').replaceChildren();residualEntries().forEach((p,k)=>opt($('residual'),k,`${nodeName(p.u,r.input.unary.length)} → ${nodeName(p.v,r.input.unary.length)} : ${p.capacity}`));table('residual-table',['u','v','residual','from SCC','to SCC'],residualEntries().map(p=>[p.u,p.v,p.capacity,p.from_component,p.to_component]));table('components-table',['SCC','nodes'],r.components.map((c,i)=>[i,c.map(n=>nodeName(n,r.input.unary.length))]));selectedStep();selectedAssignment();selectedResidual();
 }
 $('local').replaceChildren();r.reference.single_flip.trace.forEach((p,k)=>opt($('local'),k,`State ${k}: mask ${p.mask}, energy ${p.energy}${p.chosen_variable===null?' / stopped':` / flip x${p.chosen_variable}`}`));selectedLocal();
}
function run(){try{render(audit(parseInput($('input').value)));}catch(e){current=null;window.currentReport=null;$('results').hidden=true;$('export').disabled=true;text('state','Invalid input: '+e.message);$('state').className='error';}}
$('run').onclick=run;$('input').oninput=()=>{current=null;window.currentReport=null;$('results').hidden=true;$('export').disabled=true;text('state','Input changed. Rebuild before reading or exporting a witness.');};
$('preset').onchange=()=>{$('input').value=JSON.stringify(cases[Number($('preset').value)].input,null,2);run();};$('pair').onchange=selectedPair;$('step').onchange=selectedStep;$('assignment').onchange=selectedAssignment;$('residual').onchange=selectedResidual;$('local').onchange=selectedLocal;
$('export').onclick=()=>{if(!current)return;const blob=new Blob([JSON.stringify(current,null,2)+'\n'],{type:'application/json'}),a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download='cutlab-witness.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
try{cases=await fetch('audits.json').then(r=>{if(!r.ok)throw Error('failed to load controls');return r.json();});cases.forEach((c,k)=>opt($('preset'),k,c.name));$('preset').value=23;$('preset').onchange();window.cutlabReady=true;}catch(e){text('state','Load error: '+e.message);}
