"""Exact small binary graph-cut energy inspector. Established graph-cut reduction."""
from collections import deque
from fractions import Fraction as Q
import copy
import json
import re


def _q(x):
    if not isinstance(x, str) or len(x) > 12 or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?', x):
        raise ValueError('costs must be bounded signed rational strings')
    z = Q(x)
    if abs(z.numerator) > 10000 or z.denominator > 10000:
        raise ValueError('reduced numerator/denominator exceeds 10000')
    return z


def _int(x, lo, hi):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError('index/count must be an integer in range')
    return x


def validate(spec):
    if not isinstance(spec, dict) or set(spec) != {'unary', 'pairs'}:
        raise ValueError('exact keys required: unary,pairs')
    u = spec['unary']
    if not isinstance(u, list) or not 1 <= len(u) <= 6:
        raise ValueError('one to six unary rows required')
    for row in u:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError('each unary is [cost0,cost1]')
        for x in row: _q(x)
    if not isinstance(spec['pairs'], list) or len(spec['pairs']) > 15:
        raise ValueError('at most fifteen pair terms')
    seen = set()
    for p in spec['pairs']:
        if not isinstance(p, dict) or set(p) != {'i', 'j', 'values'}:
            raise ValueError('pair exact keys i,j,values')
        i = _int(p['i'], 0, len(u)-1); j = _int(p['j'], 0, len(u)-1)
        if i >= j or (i,j) in seen:
            raise ValueError('pairs require i<j and no duplicate scopes')
        seen.add((i,j))
        if not isinstance(p['values'], list) or len(p['values']) != 4:
            raise ValueError('pair values must be [00,01,10,11]')
        for x in p['values']: _q(x)
    return copy.deepcopy(spec)


def loads(text):
    if len(text.encode('utf-8')) > 32768: raise ValueError('input exceeds 32KiB UTF-8')
    def pairs(kv):
        d = {}
        for k,v in kv:
            if k in d: raise ValueError('duplicate JSON key')
            d[k] = v
        return d
    return validate(json.loads(text, object_pairs_hook=pairs))


def energy(spec, bits):
    return sum((_q(row[bits[i]]) for i,row in enumerate(spec['unary'])), Q(0)) + sum((_q(p['values'][2*bits[p['i']]+bits[p['j']]]) for p in spec['pairs']),Q(0))


def _out(x):
    if isinstance(x,Q): return str(x)
    if isinstance(x,list): return [_out(a) for a in x]
    if isinstance(x,dict): return {k:_out(v) for k,v in x.items()}
    return x


def audit(raw):
    return _audit_exact(validate(raw))


def _audit_exact(spec):
    # Internal: a validated affine path can derive larger exact rationals.
    _q = Q
    n = len(spec['unary']); N=n+2; s=n; t=n+1
    unary = [[_q(x) for x in row] for row in spec['unary']]
    pair_reductions=[]; violations=[]
    for k,p in enumerate(spec['pairs']):
        a,b,c,d=map(_q,p['values']); w=b+c-a-d
        pair_reductions.append({'pair':k,'i':p['i'],'j':p['j'],'values':[a,b,c,d], 'constant':a,'linear_i':c-a,'linear_j':d-c,'capacity':w,
          'reconstructed':[a,a+(d-c)+w,a+(c-a),a+(c-a)+(d-c)]})
        if w<0: violations.append({'pair':k,'slack':w})
    # Exhaustive original-energy reference is independent of the graph reduction.
    dense=[]
    for mask in range(1<<n):
        bits=[(mask>>i)&1 for i in range(n)]
        dense.append({'mask':mask,'bits':bits,'energy':sum((Q(row[bits[i]]) for i,row in enumerate(spec['unary'])),Q(0))+sum((Q(p['values'][2*bits[p['i']]+bits[p['j']]]) for p in spec['pairs']),Q(0))})
    minimum=min(r['energy'] for r in dense)
    optimum=[r['mask'] for r in dense if r['energy']==minimum]
    naive=[0 if a<=b else 1 for a,b in unary]
    local_mask=0;local_trace=[]
    while True:
        current=dense[local_mask]['energy']
        candidates=[{'variable':i,'mask':local_mask^(1<<i),'energy':dense[local_mask^(1<<i)]['energy']} for i in range(n)]
        best=min(candidates,key=lambda c:(c['energy'],c['variable']))
        chosen=best['variable'] if best['energy']<current else None
        local_trace.append({'mask':local_mask,'energy':current,'candidates':candidates,'chosen_variable':chosen})
        if chosen is None:break
        local_mask^=1<<chosen
    local={'start_mask':0,'mask':local_mask,'energy':dense[local_mask]['energy'],'gap':dense[local_mask]['energy']-minimum,'trace':local_trace}
    reference={'minimum':minimum,'optimal_masks':optimum,'unary_only_bits':naive,'unary_only_energy':dense[sum(b<<i for i,b in enumerate(naive))]['energy'],'unary_only_gap':dense[sum(b<<i for i,b in enumerate(naive))]['energy']-minimum,'single_flip':local}
    if violations:
        return _out({'schema':'cutlab/1','input':spec,'status':'refused','violations':violations,'pair_reductions':pair_reductions,'reference':reference,'assignments':dense})
    offset=sum((row[0] for row in unary),Q(0)); linear=[b-a for a,b in unary]
    for p in pair_reductions:
        offset+=p['constant'];linear[p['i']]+=p['linear_i'];linear[p['j']]+=p['linear_j']
    C=[[Q(0) for _ in range(N)] for _ in range(N)]
    for p in pair_reductions: C[p['i']][p['j']]+=p['capacity']
    terminal=[]
    for i,l in enumerate(linear):
        shift=min(Q(0),l);offset+=shift
        if l>=0:C[s][i]+=l;edge=[s,i]
        else:C[i][t]+=-l;edge=[i,t]
        terminal.append({'variable':i,'linear':l,'constant_shift':shift,'edge':edge,'capacity':abs(l)})
    F=[[Q(0) for _ in range(N)] for _ in range(N)]
    edges=[(i,j) for i in range(N) for j in range(N) if C[i][j]>0]
    def flows():return [{'u':i,'v':j,'capacity':C[i][j],'flow':F[i][j],'forward_residual':C[i][j]-F[i][j],'reverse_residual':F[i][j]} for i,j in edges]
    trace=[]
    while True:
        parent=[None]*N;parent[s]=s;q=deque([s])
        while q and parent[t] is None:
            u=q.popleft()
            for v in range(N):
                if parent[v] is None and C[u][v]-F[u][v]>0:parent[v]=u;q.append(v)
        if parent[t] is None:break
        path=[t]
        while path[-1]!=s:path.append(parent[path[-1]])
        path.reverse(); before=[C[a][b]-F[a][b] for a,b in zip(path,path[1:])];delta=min(before)
        moves=[{'u':a,'v':b,'residual_before':z,'reverse_original':C[a][b]==0} for a,b,z in zip(path,path[1:],before)]
        for a,b in zip(path,path[1:]):F[a][b]+=delta;F[b][a]-=delta
        trace.append({'step':len(trace)+1,'path':path,'moves':moves,'delta':delta,'value':sum(F[s]),'flows_after':flows()})
    residual=[[C[i][j]-F[i][j] for j in range(N)] for i in range(N)]
    reach=[[i==j or residual[i][j]>0 for j in range(N)] for i in range(N)]
    for k in range(N):
        for i in range(N):
            for j in range(N):reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
    components=[];used=set()
    for i in range(N):
        if i not in used:
            cc=[j for j in range(N) if reach[i][j] and reach[j][i]];components.append(cc);used.update(cc)
    component_of=[next(k for k,c in enumerate(components) if i in c) for i in range(N)]
    dag=sorted({(component_of[i],component_of[j]) for i in range(N) for j in range(N) if residual[i][j]>0 and component_of[i]!=component_of[j]})
    value=sum(F[s]); family=[]
    for row in dense:
        source=[i for i,b in enumerate(row['bits']) if b==0]+[s];S=set(source)
        crossing=[{'u':i,'v':j,'capacity':C[i][j]} for i,j in edges if i in S and j not in S]
        cap=sum((e['capacity'] for e in crossing),Q(0));slack=sum((residual[i][j] for i in S for j in range(N) if j not in S),Q(0))
        closed=slack==0
        row.update({'source':sorted(source),'crossing':crossing,'cut_capacity':cap,'offset_plus_cut':offset+cap,'cut_minus_flow':cap-value,'residual_out':slack,'closed':closed})
        if closed:family.append(row['mask'])
    forced=[0 if reach[s][i] else 1 if reach[i][t] else None for i in range(n)]
    smallest=[i for i in range(N) if reach[s][i]];largest=[i for i in range(N) if not reach[i][t]]
    report={'schema':'cutlab/1','input':spec,'status':'solved','pair_reductions':pair_reductions,'offset':offset,'linear':linear,'terminals':terminal,'capacity':C,'trace':trace,'flows':flows(),'flow_value':value,'minimum':offset+value,'residual':residual,'reachability':reach,'components':components,'component_of':component_of,'condensation':[list(x) for x in dag],'smallest_source':smallest,'largest_source':largest,'forced_bits':forced,'optimal_masks':family,'reference':reference,'assignments':dense,'balance':[sum(F[i]) for i in range(N)]}
    return _out(report)
