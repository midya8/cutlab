import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {audit,parseInput} from '../docs/engine.js';
const cases=JSON.parse(fs.readFileSync(new URL('../docs/audits.json',import.meta.url)));
function leaves(x){return x!==null&&typeof x==='object'?Object.values(x).reduce((s,v)=>s+leaves(v),0):1;}
test('all full Python/independent BigInt witnesses match',()=>{let total=0;for(const c of cases){assert.deepEqual(audit(c.input),c.report,c.name);total+=leaves(c.report);}console.log(JSON.stringify({cases:cases.length,exactLeaves:total}));});
test('strict shape, fractions and explicit browser parser semantics',()=>{for(const x of [{},{unary:[[0,1]],pairs:[]},{unary:[['1/0','0']],pairs:[]},{unary:[['0','0']],pairs:[{i:0,j:0,values:['0','0','0','0']}]},{unary:[['1e2','0']],pairs:[]}])assert.throws(()=>audit(x));assert.throws(()=>parseInput(' '.repeat(32769)));assert.equal(parseInput('{"unary":[["0","0"]],"pairs":null,"pairs":[]}').pairs.length,0);assert.equal(audit(cases[7].input).status,'refused');});
