import copy,json,random,subprocess,sys,tempfile,unittest
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
from cutlab import audit,loads,validate
from cutlab.core import energy
R=Path(__file__).resolve().parents[1]


def random_case(rng,n):
    u=[[str(rng.randint(-6,6)) for _ in range(2)] for _ in range(n)];pairs=[]
    for i in range(n):
        for j in range(i+1,n):
            if rng.random()<.6:
                a,b,c=[Q(rng.randint(-6,6),rng.randint(1,5)) for _ in range(3)];w=Q(rng.randint(0,9),rng.randint(1,5));d=b+c-a-w
                pairs.append({'i':i,'j':j,'values':list(map(str,[a,b,c,d]))})
    return {'unary':u,'pairs':pairs}


def direct(spec):
    rows=[]
    for bits in product([0,1],repeat=len(spec['unary'])):
        total=Q(0)
        for i,b in enumerate(bits):total+=Q(spec['unary'][i][b])
        for p in spec['pairs']:
            table=[[Q(x) for x in p['values'][:2]],[Q(x) for x in p['values'][2:]]]
            total+=table[bits[p['i']]][bits[p['j']]]
        rows.append((sum(b<<i for i,b in enumerate(bits)),total))
    v=min(v for _,v in rows)
    return v,sorted(m for m,x in rows if x==v),dict(rows)


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=json.loads((R/'docs/audits.json').read_text())
    def test_saved_reports(self):
        for c in self.cases:self.assertEqual(audit(c['input']),c['report'])
    def test_250_independent_dense_energy_oracles(self):
        rng=random.Random(5534)
        for k in range(250):
            s=random_case(rng,1+k%6);r=audit(s);v,opts,rows=direct(s)
            self.assertEqual(Q(r['minimum']),v);self.assertEqual(r['optimal_masks'],opts)
            for row in r['assignments']:
                self.assertEqual(Q(row['energy']),rows[row['mask']]);self.assertEqual(Q(row['offset_plus_cut']),rows[row['mask']])
    def test_160_every_cut_dual_slack_identities(self):
        rng=random.Random(9833)
        for k in range(160):
            r=audit(random_case(rng,1+k%6));N=len(r['capacity']);C=[[Q(x) for x in a] for a in r['capacity']]
            F=[[Q(0)]*N for _ in range(N)]
            for e in r['flows']:F[e['u']][e['v']]=Q(e['flow']);F[e['v']][e['u']]=-Q(e['flow'])
            for row in r['assignments']:
                S=set(row['source']);cap=sum((C[i][j] for i in S for j in range(N) if j not in S),Q(0));slack=sum((C[i][j]-F[i][j] for i in S for j in range(N) if j not in S),Q(0))
                self.assertEqual(cap,Q(row['cut_capacity']));self.assertEqual(cap-Q(r['flow_value']),slack);self.assertEqual(slack,Q(row['residual_out']));self.assertGreaterEqual(slack,0)
                self.assertEqual(row['closed'],row['mask'] in r['optimal_masks'])
    def test_all_pair_reconstruction_entries(self):
        for c in self.cases:
            for p in c['report']['pair_reductions']:
                a,u,v,w=map(Q,[p['constant'],p['linear_i'],p['linear_j'],p['capacity']])
                for i,j in product([0,1],repeat=2):self.assertEqual(a+u*i+v*j+w*(1-i)*j,Q(p['values'][2*i+j]))
                self.assertEqual(p['values'],p['reconstructed'])
    def test_every_augmentation_replayed_and_shortest(self):
        for c in self.cases:
            r=c['report']
            if r['status']=='refused':continue
            C=[[Q(x) for x in row] for row in r['capacity']];N=len(C);n=N-2;s=n;t=n+1;F=[[Q(0)]*N for _ in range(N)]
            for step in r['trace']:
                dist={s:0};todo=[s]
                for u in todo:
                    for v in range(N):
                        if v not in dist and C[u][v]-F[u][v]>0:dist[v]=dist[u]+1;todo.append(v)
                path=step['path'];self.assertEqual((path[0],path[-1]),(s,t));self.assertEqual(len(path)-1,dist[t]);self.assertEqual(len(path),len(set(path)))
                before=[C[a][b]-F[a][b] for a,b in zip(path,path[1:])];self.assertEqual(list(map(Q,[x['residual_before'] for x in step['moves']])),before);self.assertEqual(min(before),Q(step['delta']))
                for a,b in zip(path,path[1:]):F[a][b]+=Q(step['delta']);F[b][a]-=Q(step['delta'])
                for i in range(n):self.assertEqual(sum(F[i]),0)
                self.assertEqual(sum(F[s]),Q(step['value']))
                for e in step['flows_after']:self.assertEqual(F[e['u']][e['v']],Q(e['flow']));self.assertTrue(0<=Q(e['flow'])<=Q(e['capacity']))
            self.assertEqual([sum(F[i]) for i in range(N)],list(map(Q,r['balance'])))
    def test_residual_reachability_independent_search(self):
        for c in self.cases:
            r=c['report']
            if r['status']=='refused':continue
            N=len(r['residual']);reach=[]
            for start in range(N):
                seen={start};q=[start]
                for i in q:
                    for j in range(N):
                        if Q(r['residual'][i][j])>0 and j not in seen:seen.add(j);q.append(j)
                reach.append([i in seen for i in range(N)])
            self.assertEqual(reach,r['reachability']);self.assertFalse(reach[N-2][N-1])
            for cc in r['components']:
                for i,j in product(cc,cc):self.assertTrue(reach[i][j])
            for i,j in product(range(N),repeat=2):self.assertEqual(r['component_of'][i]==r['component_of'][j],reach[i][j] and reach[j][i])
    def test_complete_family_and_forced_values(self):
        for c in self.cases:
            r=c['report']
            if r['status']=='refused':continue
            n=len(c['input']['unary']);opts=r['optimal_masks']
            for i,b in enumerate(r['forced_bits']):
                vals={(m>>i)&1 for m in opts};self.assertEqual(b,next(iter(vals)) if len(vals)==1 else None)
            for a,b in product(opts,opts):self.assertIn(a&b,opts);self.assertIn(a|b,opts)
            for key,mask in [('smallest_source',(1<<n)-1),('largest_source',0)]:
                if key=='smallest_source':
                    for m in opts:mask&=~m
                else:
                    for m in opts:mask|=((1<<n)-1)^m
                self.assertEqual([i for i in range(n) if (mask>>i)&1]+[n],r[key])
    def test_100_offset_shifts_and_positive_scaling(self):
        rng=random.Random(390)
        for k in range(100):
            s=random_case(rng,1+k%6);r=audit(s);z=copy.deepcopy(s);shift=Q(-7,3);scale=Q(5,4)
            for i,row in enumerate(z['unary']):z['unary'][i]=[str(scale*Q(x)+(shift if i==0 else 0)) for x in row]
            for p in z['pairs']:p['values']=[str(scale*Q(x)) for x in p['values']]
            q=audit(z);self.assertEqual(q['optimal_masks'],r['optimal_masks']);self.assertEqual(Q(q['minimum']),scale*Q(r['minimum'])+shift)
    def test_all_zero_has_64_ties_no_flow(self):
        r=self.cases[4]['report'];self.assertEqual(len(r['optimal_masks']),64);self.assertEqual(r['trace'],[]);self.assertEqual(r['forced_bits'],[None]*6)
    def test_coupling_overturns_unary_control(self):
        r=self.cases[0]['report'];self.assertEqual(r['minimum'],'3');self.assertEqual(r['optimal_masks'],[0,3]);self.assertEqual(r['reference']['unary_only_energy'],'5');self.assertEqual(r['reference']['unary_only_gap'],'2')
    def test_asymmetric_has_three_minima(self):self.assertEqual(self.cases[2]['report']['optimal_masks'],[0,1,3])
    def test_negative_offset_retained(self):self.assertLess(Q(self.cases[3]['report']['offset']),0)
    def test_non_submodular_not_clipped(self):
        r=self.cases[7]['report'];self.assertEqual(r['status'],'refused');self.assertEqual(r['violations'],[{'pair':0,'slack':'-4'}]);self.assertNotIn('flow_value',r);self.assertEqual(r['reference']['optimal_masks'],[1,2])
    def test_reverse_residual_control_present(self):
        r=self.cases[22]['report'];self.assertTrue(any(m['reverse_original'] for t in r['trace'] for m in t['moves']))
    def test_single_flip_local_not_global(self):
        r=self.cases[23]['report'];self.assertEqual(r['reference']['single_flip']['gap'],'2');self.assertEqual(r['reference']['single_flip']['mask'],0);self.assertEqual(r['optimal_masks'],[3])
        for c in self.cases:
            s=c['input'];r=c['report'];local=r['reference']['single_flip'];last=None
            for t in local['trace']:
                self.assertEqual(Q(t['energy']),energy(s,[(t['mask']>>i)&1 for i in range(len(s['unary']))]))
                if last is not None:self.assertLess(Q(t['energy']),last)
                last=Q(t['energy'])
                for p in t['candidates']:self.assertEqual(Q(p['energy']),energy(s,[(p['mask']>>i)&1 for i in range(len(s['unary']))]))
            self.assertIsNone(local['trace'][-1]['chosen_variable'])
    def test_80_relabeling_invariance(self):
        rng=random.Random(9004)
        for k in range(80):
            n=1+k%6;s=random_case(rng,n);r=audit(s);perm=list(range(n));rng.shuffle(perm);u=[None]*n
            for i,j in enumerate(perm):u[j]=s['unary'][i]
            ps=[]
            for p in s['pairs']:
                i,j=perm[p['i']],perm[p['j']];vs=p['values']
                if i>j:i,j=j,i;vs=[vs[0],vs[2],vs[1],vs[3]]
                ps.append({'i':i,'j':j,'values':vs})
            q=audit({'unary':u,'pairs':ps});self.assertEqual(r['minimum'],q['minimum']);self.assertEqual(sorted(sum(((m>>i)&1)<<j for i,j in enumerate(perm)) for m in r['optimal_masks']),q['optimal_masks'])
    def test_no_input_mutation(self):
        s=self.cases[0]['input'];b=copy.deepcopy(s);audit(s);self.assertEqual(s,b)
    def test_schema_invalid(self):
        s=self.cases[0]['input'];bad=[{},dict(s,extra=1),dict(s,unary=[]),dict(s,unary=[[0,1]]),dict(s,unary=[['0','1/0']]),dict(s,unary=[['nan','0']]),dict(s,unary=[['1e2','0']]),dict(s,unary=[['10001','0']]),dict(s,pairs=[dict(s['pairs'][0],i=True)]),dict(s,pairs=[dict(s['pairs'][0],j=0)]),dict(s,pairs=s['pairs']*2),dict(s,pairs=[dict(s['pairs'][0],values=['0'])])]
        for x in bad:
            with self.assertRaises(ValueError):audit(x)
    def test_duplicate_keys_and_utf8_size(self):
        for txt in ['{"unary":[["0","1"]],"pairs":[],"pairs":[]}', ' '*32769, '{"unary":[["0","1"]],"pairs":[{"i":0.0,"j":1,"values":["0","0","0","0"]}]}']:
            with self.assertRaises(ValueError):loads(txt)
    def test_cli_module_matches_saved(self):
        p=subprocess.run([sys.executable,'-m','cutlab',str(R/'examples/demo.json')],capture_output=True,text=True,check=True);self.assertEqual(json.loads(p.stdout),self.cases[0]['report'])
    def test_cli_invalid_preserves_output(self):
        with tempfile.TemporaryDirectory() as d:
            i=Path(d)/'bad.json';o=Path(d)/'result.json';i.write_text('{}');o.write_text('keep')
            p=subprocess.run([sys.executable,'-m','cutlab',str(i),'--output',str(o)],capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(o.read_text(),'keep')

if __name__=='__main__':unittest.main()
