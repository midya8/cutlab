import copy,json,random,unittest
from fractions import Fraction as Q
from cutlab.path import response_path,loads_path
from cutlab.core import energy

class PathTests(unittest.TestCase):
    @staticmethod
    def random(r,n=3):
        return {'base':{'unary':[[str(r.randint(-4,4)),str(r.randint(-4,4))] for _ in range(n)],'pairs':[{'i':i,'j':j,'values':['0',str(r.randint(0,3)),str(r.randint(0,3)),'0']} for i in range(n) for j in range(i+1,n)]},'slopes':[[str(r.randint(-3,3)),str(r.randint(-3,3))] for _ in range(n)],'domain':['-3','3']}
    def oracle(self,s,x):
        n=len(s['base']['unary']);values=[]
        for mask in range(1<<n):
            bits=[(mask>>i)&1 for i in range(n)];values.append(energy(s['base'],bits)+x*sum((Q(s['slopes'][i][b]) for i,b in enumerate(bits)),Q(0)))
        return min(values),[i for i,v in enumerate(values) if v==min(values)]
    def test_all_pair_intersection_oracle(self):
        r=random.Random(52218)
        for k in range(120):
            s=self.random(r);p=response_path(s);cuts={Q(s['domain'][0]),Q(s['domain'][1])}
            for a in p['lines']:
                for b in p['lines']:
                    if a['slope']!=b['slope']:
                        x=(Q(b['intercept'])-Q(a['intercept']))/(Q(a['slope'])-Q(b['slope']))
                        if Q(s['domain'][0])<=x<=Q(s['domain'][1]):cuts.add(x)
            xs=sorted(cuts);xs+= [(a+b)/2 for a,b in zip(xs,xs[1:])]
            for x in xs:
                value,masks=self.oracle(s,x);active=[l['mask'] for l in p['lines'] if l['region'] and Q(l['region'][0])<=x<=Q(l['region'][1])];self.assertEqual(active,masks)
            for w in p['cells']+p['points']:
                v,m=self.oracle(s,Q(w['lambda']));self.assertEqual((w['minimum'],w['optimal_masks']),(str(v),m));self.assertEqual(w['graph']['minimum'],str(v));self.assertEqual(w['graph']['optimal_masks'],m)
    def test_interval_inequalities_and_binding(self):
        r=random.Random(31)
        for k in range(50):
            p=response_path(self.random(r))
            for l in p['lines']:
                if not l['region']:continue
                for x in map(Q,l['region']):
                    for c in l['constraints']:self.assertLessEqual(Q(c['a'])*x,Q(c['b']))
                self.assertLessEqual(Q(l['region'][0]),Q(l['region'][1]))
    def test_positive_objective_transform(self):
        r=random.Random(841)
        for k in range(40):
            s=self.random(r,2);p=response_path(s);t=copy.deepcopy(s)
            t['base']['unary']=[[str(2*Q(x)-1) for x in row] for row in t['base']['unary']]
            for pair in t['base']['pairs']:pair['values']=[str(2*Q(x)) for x in pair['values']]
            t['slopes']=[[str(2*Q(x)) for x in row] for row in t['slopes']];z=response_path(t)
            self.assertEqual(p['knots'],z['knots']);self.assertEqual([l['region'] for l in p['lines']],[l['region'] for l in z['lines']])
            for a,b in zip(p['cells']+p['points'],z['cells']+z['points']):self.assertEqual(b['minimum'],str(2*Q(a['minimum'])-2))
    def test_lambda_reversal(self):
        r=random.Random(19)
        for k in range(40):
            s=self.random(r,2);p=response_path(s);t=copy.deepcopy(s);t['slopes']=[[str(-Q(x)) for x in row] for row in t['slopes']];z=response_path(t)
            self.assertEqual(p['knots'],[str(-Q(x)) for x in reversed(z['knots'])])
            self.assertEqual([c['optimal_masks'] for c in p['cells']],[c['optimal_masks'] for c in reversed(z['cells'])])
    def test_point_only_and_persistent_ties(self):
        s={'base':{'unary':[['0','0'],['0','0']],'pairs':[]},'slopes':[['0','1'],['0','-1']],'domain':['-2','2']};p=response_path(s)
        self.assertEqual(p['knots'],['-2','0','2']);self.assertEqual(p['points'][1]['optimal_masks'],[0,1,2,3]);self.assertEqual(p['lines'][0]['region'],['0','0']);self.assertEqual(p['lines'][3]['region'],['0','0'])
        s['slopes']=[['0','0'],['0','0']];p=response_path(s);self.assertEqual(p['cells'][0]['optimal_masks'],[0,1,2,3])
    def test_saved_controls_and_nonmonotone(self):
        from pathlib import Path
        rows=json.loads((Path(__file__).resolve().parents[1]/'docs/path-audits.json').read_text())
        for row in rows:self.assertEqual(response_path(row['input']),row['report'])
        self.assertEqual([c['optimal_masks'] for c in rows[0]['report']['cells']],[[7],[0],[1]])
        self.assertEqual(rows[6]['report']['points'][-1]['optimal_masks'],[0,1])
    def test_validation_no_mutation(self):
        s=self.random(random.Random(4));before=copy.deepcopy(s);response_path(s);self.assertEqual(s,before)
        for changes in [{'domain':['0','0']},{'domain':['1','-1']},{'slopes':[]},{'extra':1},{'slopes':[['0',1]]*3}]:
            t={**s,**changes}
            with self.assertRaises(ValueError):response_path(t)
        with self.assertRaises(ValueError):loads_path('{"base":1,"base":2}')
        t=copy.deepcopy(s);t['base']['pairs'][0]['values']=['2','0','0','2']
        with self.assertRaises(ValueError):response_path(t)
    def test_concave_slope_order(self):
        r=random.Random(77)
        for k in range(60):
            p=response_path(self.random(r));slopes=[Q(p['lines'][c['optimal_masks'][0]]['slope']) for c in p['cells']];self.assertEqual(slopes,sorted(slopes,reverse=True))

    def test_cli_path_and_invalid_output_preservation(self):
        import subprocess,sys,tempfile
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        expected=response_path(json.loads((root/'examples/path.json').read_text()))
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.json'
            p=subprocess.run([sys.executable,'-m','cutlab',str(root/'examples/path.json'),'--path','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(out.read_text()),expected)
            bad=Path(d)/'bad.json';bad.write_text('{}');before=out.read_bytes()
            p=subprocess.run([sys.executable,'-m','cutlab',str(bad),'--path','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2);self.assertEqual(out.read_bytes(),before)
