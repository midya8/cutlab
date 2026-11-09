// Independent BigInt arithmetic and finite graph-cut witness implementation.
const gcd=(a,b)=>{a=a<0n?-a:a;while(b){[a,b]=[b,a%b];}return a;};
class Rat{
 constructor(n,d=1n){if(!d)throw Error('zero denominator');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);this.n=n/g;this.d=d/g;}
 add(b){return new Rat(this.n*b.d+b.n*this.d,this.d*b.d);}sub(b){return new Rat(this.n*b.d-b.n*this.d,this.d*b.d);}neg(){return new Rat(-this.n,this.d);}cmp(b){const d=this.n*b.d-b.n*this.d;return d<0n?-1:d>0n?1:0;}
 toString(){return this.d===1n?String(this.n):`${this.n}/${this.d}`;}
}
const Z=()=>new Rat(0n), parse=x=>{
 if(typeof x!=='string'||x.length>12||! /^-?(?:0|[1-9][0-9]*)(?:\/[1-9][0-9]*)?$/.test(x))throw Error('costs must be bounded signed rational strings');
 const [n,d='1']=x.split('/'),q=new Rat(BigInt(n),BigInt(d));if(q.n>10000n||q.n< -10000n||q.d>10000n)throw Error('reduced numerator/denominator exceeds 10000');return q;
};
const sum=a=>a.reduce((v,x)=>v.add(x),Z()), serialize=x=>x instanceof Rat?x.toString():Array.isArray(x)?x.map(serialize):x!==null&&typeof x==='object'?Object.fromEntries(Object.entries(x).map(([k,v])=>[k,serialize(v)])):x;
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join(',')===[...keys].sort().join(',');
export function validate(raw){
 if(!exact(raw,['unary','pairs']))throw Error('exact keys required: unary,pairs');
 const {unary:u,pairs:ps}=raw;if(!Array.isArray(u)||u.length<1||u.length>6)throw Error('one to six unary rows required');
 u.forEach(row=>{if(!Array.isArray(row)||row.length!==2)throw Error('each unary is [cost0,cost1]');row.forEach(parse);});
 if(!Array.isArray(ps)||ps.length>15)throw Error('at most fifteen pair terms');const seen=new Set();
 ps.forEach(p=>{
  if(!exact(p,['i','j','values']))throw Error('pair exact keys i,j,values');
  if(!Number.isInteger(p.i)||!Number.isInteger(p.j)||p.i<0||p.j>=u.length||p.i>=p.j||seen.has(`${p.i},${p.j}`))throw Error('pairs require distinct integer i<j scopes in range');seen.add(`${p.i},${p.j}`);
  if(!Array.isArray(p.values)||p.values.length!==4)throw Error('pair values must be [00,01,10,11]');p.values.forEach(parse);
 });return JSON.parse(JSON.stringify(raw));
}
export function parseInput(text){if(text.length>32768)throw Error('input exceeds 32768 characters');return validate(JSON.parse(text));}
export function audit(raw){return auditDerived(validate(raw));}
// Internal path adapter: caller validates the base and every slope first.
export function auditDerived(spec){
 const parse=x=>{const [n,d]=x.split('/');return new Rat(BigInt(n),d===undefined?1n:BigInt(d));};
 const n=spec.unary.length,N=n+2,s=n,t=n+1,U=spec.unary.map(row=>row.map(parse));
 const reds=spec.pairs.map((p,k)=>{const [a,b,c,d]=p.values.map(parse),u=c.sub(a),v=d.sub(c),w=b.add(c).sub(a).sub(d);return {pair:k,i:p.i,j:p.j,values:[a,b,c,d],constant:a,linear_i:u,linear_j:v,capacity:w,reconstructed:[a,a.add(v).add(w),a.add(u),a.add(u).add(v)]};});
 const violations=reds.filter(p=>p.capacity.cmp(Z())<0).map(p=>({pair:p.pair,slack:p.capacity}));
 const e=bits=>sum(U.map((row,i)=>row[bits[i]])).add(sum(spec.pairs.map(p=>parse(p.values[2*bits[p.i]+bits[p.j]]))));
 const dense=Array.from({length:2**n},(_,mask)=>{const bits=Array.from({length:n},(_,i)=>(mask>>i)&1);return {mask,bits,energy:e(bits)};});
 let minimum=dense[0].energy;dense.forEach(r=>{if(r.energy.cmp(minimum)<0)minimum=r.energy;});
 const opts=dense.filter(r=>r.energy.cmp(minimum)===0).map(r=>r.mask),naive=U.map(([a,b])=>a.cmp(b)<=0?0:1);
 let localMask=0;const localTrace=[];
 for(;;){const current=dense[localMask].energy,candidates=Array.from({length:n},(_,i)=>({variable:i,mask:localMask^(1<<i),energy:dense[localMask^(1<<i)].energy})),best=[...candidates].sort((a,b)=>a.energy.cmp(b.energy)||a.variable-b.variable)[0],chosen=best.energy.cmp(current)<0?best.variable:null;localTrace.push({mask:localMask,energy:current,candidates,chosen_variable:chosen});if(chosen===null)break;localMask^=1<<chosen;}
 const local={start_mask:0,mask:localMask,energy:dense[localMask].energy,gap:dense[localMask].energy.sub(minimum),trace:localTrace};
 const reference={minimum,optimal_masks:opts,unary_only_bits:naive,unary_only_energy:e(naive),unary_only_gap:e(naive).sub(minimum),single_flip:local};
 if(violations.length)return serialize({schema:'cutlab/1',input:spec,status:'refused',violations,pair_reductions:reds,reference,assignments:dense});
 let offset=sum(U.map(row=>row[0]));const linear=U.map(([a,b])=>b.sub(a));
 reds.forEach(p=>{offset=offset.add(p.constant);linear[p.i]=linear[p.i].add(p.linear_i);linear[p.j]=linear[p.j].add(p.linear_j);});
 const C=Array.from({length:N},()=>Array.from({length:N},Z));reds.forEach(p=>{C[p.i][p.j]=C[p.i][p.j].add(p.capacity);});
 const terminals=linear.map((l,i)=>{const shift=l.cmp(Z())<0?l:Z(),edge=l.cmp(Z())>=0?[s,i]:[i,t],cap=l.cmp(Z())<0?l.neg():l;offset=offset.add(shift);C[edge[0]][edge[1]]=C[edge[0]][edge[1]].add(cap);return {variable:i,linear:l,constant_shift:shift,edge,capacity:cap};});
 const F=Array.from({length:N},()=>Array.from({length:N},Z)),edges=[];C.forEach((row,i)=>row.forEach((v,j)=>{if(v.cmp(Z())>0)edges.push([i,j]);}));
 const flows=()=>edges.map(([u,v])=>({u,v,capacity:C[u][v],flow:F[u][v],forward_residual:C[u][v].sub(F[u][v]),reverse_residual:F[u][v]})),trace=[];
 for(;;){
  const parent=Array(N).fill(null),q=[s];parent[s]=s;
  for(let h=0;h<q.length&&parent[t]===null;h++){const u=q[h];for(let v=0;v<N;v++){if(parent[v]===null&&C[u][v].sub(F[u][v]).cmp(Z())>0){parent[v]=u;q.push(v);}}}
  if(parent[t]===null)break;
  const path=[t];while(path.at(-1)!==s)path.push(parent[path.at(-1)]);path.reverse();
  const moves=path.slice(0,-1).map((u,k)=>({u,v:path[k+1],residual_before:C[u][path[k+1]].sub(F[u][path[k+1]]),reverse_original:C[u][path[k+1]].cmp(Z())===0}));let delta=moves[0].residual_before;
  moves.forEach(m=>{if(m.residual_before.cmp(delta)<0)delta=m.residual_before;});
  moves.forEach(({u,v})=>{F[u][v]=F[u][v].add(delta);F[v][u]=F[v][u].sub(delta);});
  trace.push({step:trace.length+1,path,moves,delta,value:sum(F[s]),flows_after:flows()});
 }
 const residual=C.map((row,i)=>row.map((v,j)=>v.sub(F[i][j]))),reach=residual.map((row,i)=>row.map((v,j)=>i===j||v.cmp(Z())>0));
 for(let k=0;k<N;k++)for(let i=0;i<N;i++)for(let j=0;j<N;j++)reach[i][j] ||= reach[i][k]&&reach[k][j];
 const components=[],seen=new Set();for(let i=0;i<N;i++){if(!seen.has(i)){const cc=[];for(let j=0;j<N;j++){if(reach[i][j]&&reach[j][i]){cc.push(j);seen.add(j);}}components.push(cc);}}
 const component_of=Array.from({length:N},(_,i)=>components.findIndex(c=>c.includes(i))),dag=new Map();
 residual.forEach((row,i)=>row.forEach((v,j)=>{if(v.cmp(Z())>0&&component_of[i]!==component_of[j])dag.set(`${component_of[i]},${component_of[j]}`,[component_of[i],component_of[j]]);}));
 const condensation=[...dag.values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]),value=sum(F[s]),family=[];
 dense.forEach(row=>{
  const source=[...row.bits.flatMap((b,i)=>b===0?[i]:[]),s].sort((a,b)=>a-b),S=new Set(source),crossing=edges.filter(([u,v])=>S.has(u)&&!S.has(v)).map(([u,v])=>({u,v,capacity:C[u][v]})),cap=sum(crossing.map(e=>e.capacity)),res=[];
  source.forEach(i=>{for(let j=0;j<N;j++)if(!S.has(j))res.push(residual[i][j]);});const slack=sum(res),closed=slack.cmp(Z())===0;
  Object.assign(row,{source,crossing,cut_capacity:cap,offset_plus_cut:offset.add(cap),cut_minus_flow:cap.sub(value),residual_out:slack,closed});if(closed)family.push(row.mask);
 });
 return serialize({schema:'cutlab/1',input:spec,status:'solved',pair_reductions:reds,offset,linear,terminals,capacity:C,trace,flows:flows(),flow_value:value,minimum:offset.add(value),residual,reachability:reach,components,component_of,condensation,smallest_source:Array.from({length:N},(_,i)=>i).filter(i=>reach[s][i]),largest_source:Array.from({length:N},(_,i)=>i).filter(i=>!reach[i][t]),forced_bits:Array.from({length:n},(_,i)=>reach[s][i]?0:reach[i][t]?1:null),optimal_masks:family,reference,assignments:dense,balance:F.map(sum)});
}
