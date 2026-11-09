"""Exact tiny affine unary response, by all-line halfspace intersection."""
from fractions import Fraction as Q
import copy
import json
from .core import validate, _q, energy, _audit_exact


def validate_path(raw):
    if not isinstance(raw, dict) or set(raw) != {'base', 'slopes', 'domain'}:
        raise ValueError('exact path keys: base,slopes,domain')
    base = validate(raw['base'])
    if not isinstance(raw['slopes'],list) or len(raw['slopes']) != len(base['unary']):
        raise ValueError('one slope row per variable')
    for row in raw['slopes']:
        if not isinstance(row,list) or len(row)!=2: raise ValueError('slope row needs two rational strings')
        for x in row: _q(x)
    domain=raw['domain']
    if not isinstance(domain,list) or len(domain)!=2 or _q(domain[0])>=_q(domain[1]):
        raise ValueError('strictly increasing two-rational domain required')
    for p in base['pairs']:
        a,b,c,d=map(Q,p['values'])
        if b+c-a-d<0: raise ValueError('path requires submodular fixed pairs; no clipping')
    return copy.deepcopy(raw)


def loads_path(text):
    if len(text.encode('utf8'))>32768: raise ValueError('path input exceeds 32KiB UTF-8')
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d: raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    return validate_path(json.loads(text,object_pairs_hook=pairs))


def response_path(raw):
    spec=validate_path(raw);base=spec['base'];n=len(base['unary']);lo,hi=map(Q,spec['domain'])
    lines=[]
    for mask in range(1<<n):
        bits=[(mask>>i)&1 for i in range(n)]
        lines.append({'mask':mask,'bits':bits,'intercept':energy(base,bits),'slope':sum((Q(spec['slopes'][i][b]) for i,b in enumerate(bits)),Q(0))})
    endpoints={lo,hi}
    for line in lines:
        left,right=lo,hi;possible=True;constraints=[]
        for other in lines:
            a=line['slope']-other['slope'];b=other['intercept']-line['intercept']
            if a>0: bound=b/a;sense='<=';right=min(right,bound)
            elif a<0: bound=b/a;sense='>=';left=max(left,bound)
            else: bound=None;sense='always' if b>=0 else 'impossible';possible &= b>=0
            constraints.append({'other_mask':other['mask'],'a':str(a),'b':str(b),'sense':sense,'bound':None if bound is None else str(bound)})
        region=[str(left),str(right)] if possible and left<=right else None
        line['region']=region;line['constraints']=constraints
        if region: endpoints.update((left,right))
    knots=sorted(endpoints)
    def at(x,kind,left=None,right=None):
        values=[l['intercept']+x*l['slope'] for l in lines];value=min(values);masks=[i for i,v in enumerate(values) if v==value]
        derived=copy.deepcopy(base);derived['unary']=[[str(Q(c)+x*Q(spec['slopes'][i][b])) for b,c in enumerate(row)] for i,row in enumerate(base['unary'])]
        graph=_audit_exact(derived)
        if graph['minimum']!=str(value) or graph['optimal_masks']!=masks: raise ArithmeticError('independent graph response mismatch')
        return {'kind':kind,'lambda':str(x),'left':None if left is None else str(left),'right':None if right is None else str(right),'minimum':str(value),'optimal_masks':masks,'energies':list(map(str,values)),'graph':graph}
    points=[at(x,'point') for x in knots]
    cells=[at((a+b)/2,'open',a,b) for a,b in zip(knots,knots[1:])]
    # Every active line is globally <= every other line throughout its closed region.
    out=[]
    for l in lines:out.append({**l,'intercept':str(l['intercept']),'slope':str(l['slope'])})
    return {'schema':'cutlab-path/1','input':spec,'lines':out,'knots':list(map(str,knots)),'points':points,'cells':cells}
