import json,random
from pathlib import Path
from cutlab import audit
R=Path(__file__).resolve().parents[1]
def pair(i,j,vs):return {'i':i,'j':j,'values':[str(x) for x in vs]}
def case(name,u,p):return {'name':name,'input':{'unary':[[str(x) for x in v] for v in u],'pairs':p}}
cases=[
 case('A coupling overturns unary-only decisions',[[0,3],[3,0]],[pair(0,1,[0,5,5,0])]),
 case('Two tied constant-label minima',[[0,0],[0,0]],[pair(0,1,[0,4,4,0])]),
 case('An asymmetric directed implication',[[0,0],[0,0]],[pair(0,1,[0,3,0,0])]),
 case('Negative costs need the retained offset',[[-7,-4],[2,-3]],[pair(0,1,[-2,4,0,-1])]),
 case('All-zero graph, every labeling is optimal',[[0,0]]*6,[]),
 case('One forced variable and five free variables',[[0,2]]+[[0,0]]*5,[]),
 case('Disconnected tied pairs',[[0,0]]*4,[pair(0,1,[0,2,2,0]),pair(2,3,[0,1,1,0])]),
 case('Non-submodular pair: graph solve refused',[[0,0],[0,0]],[pair(0,1,[2,0,0,2])]),
 case('Zero-slack separable asymmetric table',[[0,1],[1,0]],[pair(0,1,[3,1,5,3])]),
 case('Rational capacities and offsets',[['-2/3','1/2'],['3/4','-1/3'],['0','1/5']],[pair(0,1,['1/3','5/4','2/3','0']),pair(1,2,['0','1/7','2/7','0'])]),
 case('Unary singleton with negative optimum',[[-3,-1]],[]),
 case('Six-site synthetic denoising chain',[[0,4],[3,0],[0,1],[4,0],[0,3],[0,2]],[pair(i,i+1,[0,2,2,0]) for i in range(5)]),
]
rng=random.Random(7741)
for seed in range(10):
 n=3+seed%4;u=[[rng.randint(-4,4) for _ in range(2)] for _ in range(n)];p=[]
 for i in range(n):
  for j in range(i+1,n):
   if rng.random()<.6:
    a,b,c=[rng.randint(-3,5) for _ in range(3)];w=rng.randint(0,6);d=b+c-a-w;p.append(pair(i,j,[a,b,c,d]))
 cases.append(case('Seeded signed submodular graph '+str(seed),u,p))
cases.append({'name':'Reverse residual arcs undo earlier routed flow','input':json.loads((R/'examples/reverse.json').read_text())})
cases.append(case('Strict single-flip search is trapped at a local minimum',[[1,0],[1,0]],[pair(0,1,[0,2,2,0])]))
out=[dict(c,report=audit(c['input'])) for c in cases]
(R/'docs/audits.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
(R/'examples/demo.json').write_text(json.dumps(cases[0]['input'],indent=2)+'\n')
print(len(out),'reports',sum(len(c['report'].get('trace',[])) for c in out),'augmentations')
