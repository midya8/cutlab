"""Original synthetic affine-cost controls, all exact response witnesses."""
import json,random
from pathlib import Path
from cutlab.path import response_path
ROOT=Path(__file__).resolve().parents[1]

def fixtures():
    def one(name,u,s,d):return {'name':name,'input':{'base':{'unary':[u],'pairs':[]},'slopes':[s],'domain':d}}
    out=[{'name':'Mixed slopes: one label leaves and returns','input':{'base':{'unary':[['0','-5'],['0','0'],['0','4']],'pairs':[{'i':0,'j':1,'values':['0','4','4','0']},{'i':0,'j':2,'values':['0','0','5','0']},{'i':1,'j':2,'values':['0','3','5','0']}]},'slopes':[['0','-2'],['0','5'],['0','1']],'domain':['-4','4']}},
    {'name':'Four ties at a single breakpoint','input':{'base':{'unary':[['0','0'],['0','0']],'pairs':[]},'slopes':[['0','1'],['0','-1']],'domain':['-2','2']}},
    {'name':'Persistent free labels across both cells','input':{'base':{'unary':[['0','0']]*3,'pairs':[]},'slopes':[['0','1'],['0','0'],['0','0']],'domain':['-2','2']}},
    {'name':'64 persistent optima, zero slope','input':{'base':{'unary':[['0','0']]*6,'pairs':[]},'slopes':[['0','0']]*6,'domain':['-3','5']}},
    one('Rational 2/3 breakpoint',['0','2/3'],['0','-1'],['-1','2']),
    one('Intersection outside the domain',['0','5'],['0','-1'],['-1','1']),
    one('Tie at the right endpoint only',['0','1'],['0','-1'],['0','1']),
    one('Common slope changes values, not labels',['-2','3'],['2','2'],['-3','3']),
    {'name':'Parallel lines and persistent duplicated winners','input':{'base':{'unary':[['0','0'],['0','3']],'pairs':[]},'slopes':[['0','0'],['0','0']],'domain':['-1','1']}},
    {'name':'Asymmetric rational coupling','input':{'base':{'unary':[['-1/3','2/7'],['1/5','-2/9']],'pairs':[{'i':0,'j':1,'values':['-1/2','2/3','3/7','-1/5']}]},'slopes':[['1/3','-2/7'],['-1/5','3/11']],'domain':['-7/3','5/2']}},
    {'name':'Disconnected agreement pairs','input':{'base':{'unary':[['0','0']]*4,'pairs':[{'i':0,'j':1,'values':['0','2','2','0']},{'i':2,'j':3,'values':['0','1','1','0']}]},'slopes':[['0','1'],['0','2'],['0','-1'],['0','-2']],'domain':['-2','2']}},
    one('Fixed unique optimum with negative offset',['-3','-1'],['0','0'],['-5','5'])]
    r=random.Random(91317)
    for k in range(6):
        n=4;out.append({'name':'Seeded signed affine graph '+str(k),'input':{'base':{'unary':[[str(r.randint(-4,4)),str(r.randint(-4,4))] for _ in range(n)],'pairs':[{'i':i,'j':j,'values':['0',str(r.randint(0,4)),str(r.randint(0,4)),'0']} for i in range(n) for j in range(i+1,n) if r.random()<.7]},'slopes':[[str(r.randint(-3,3)),str(r.randint(-3,3))] for _ in range(n)],'domain':['-3','3']}})
    return out

if __name__=='__main__':
    rows=[{**r,'report':response_path(r['input'])} for r in fixtures()]
    (ROOT/'docs/path-audits.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
    (ROOT/'examples/path.json').write_text(json.dumps(rows[0]['input'],indent=2)+'\n')
    print(len(rows),'paths',sum(len(r['report']['cells']) for r in rows),'cells',sum(len(r['report']['points']) for r in rows),'points')
