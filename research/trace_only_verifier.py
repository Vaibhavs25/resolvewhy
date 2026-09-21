import copy, json, os, subprocess, sys, tempfile

OPS = {'==':lambda a,b:a==b,'!=':lambda a,b:a!=b,'<':lambda a,b:a<b,'<=':lambda a,b:a<=b,'>':lambda a,b:a>b,'>=':lambda a,b:a>=b}
def ver(v): return tuple(int(x) for x in v.split('.'))
def satv(v, op, rhs): return OPS[op](ver(v),ver(rhs))

def structural(t):
    required=['schema','trace_scope','requirements','candidates','artifacts','dependencies','runtime_contexts','evaluation_domain','resolution_policy','candidate_domains','semantic_constraints','provenance','evidence_state']
    missing=[x for x in required if x not in t]
    if missing: return False,'missing required fields: '+','.join(missing)
    if t['trace_scope'] not in {'existential','universal','branch'}: return False,'invalid trace scope'
    if not isinstance(t['evaluation_domain'],list) or not t['evaluation_domain']: return False,'invalid evaluation domain'
    ids=[c.get('id') for c in t['candidates']]
    if any(x is None for x in ids) or len(ids)!=len(set(ids)): return False,'invalid candidate IDs'
    aids=[a.get('id') for a in t['artifacts']]
    if any(x is None for x in aids) or len(aids)!=len(set(aids)): return False,'invalid artifact IDs'
    eids=[e.get('id') for e in t['dependencies']]
    if any(x is None for x in eids) or len(eids)!=len(set(eids)): return False,'invalid dependency IDs'
    cids=[e.get('id') for e in t['semantic_constraints']]
    if any(x is None for x in cids) or len(cids)!=len(set(cids)): return False,'invalid constraint IDs'
    for e in t['dependencies']:
        if e.get('parent_candidate') not in ids: return False,'dangling dependency parent'
        if 'requirement' not in e: return False,'missing dependency requirement'
    for a in t['artifacts']:
        if a.get('candidate_ref') not in ids: return False,'dangling artifact candidate'
    for q in t['candidate_domains']:
        cov=q.get('coverage',{})
        if cov.get('status')=='complete' and not isinstance(cov.get('attestation'),dict): return False,'complete coverage lacks attestation'
        if any(x not in ids for x in q.get('candidate_ids',[])): return False,'dangling coverage candidate'
    if not t['provenance']: return False,'missing provenance'
    return True,'ok'

def candidate_usable(c,t,env):
    rp=c.get('requires_python')
    if rp=='>=3.10' and env['id']=='py3.9-linux': return False
    return True

def branch_sat(t,env):
    candidates=[c for c in t['candidates'] if candidate_usable(c,t,env)]
    # Enumerate assignments for the finite fixture fragment. Every requirement is checked.
    packages=sorted({c['package'] for c in candidates})
    choices=[]
    for p in packages:
        choices.append([c for c in candidates if c['package']==p])
    if not choices:return False
    import itertools
    for assignment in itertools.product(*choices):
        chosen={c['package']:c for c in assignment}
        root_ok=all(r['package'] in chosen and satv(chosen[r['package']]['version'],r['op'],r['version']) for r in t['requirements'])
        if not root_ok: continue
        ok=True
        for e in t['dependencies']:
            if e.get('active',True) is False: continue
            parent=chosen.get(next(c['package'] for c in candidates if c['id']==e['parent_candidate']))
            if parent is None: continue
            r=e['requirement']
            target=chosen.get(r['package'])
            if target is None or not satv(target['version'],r['op'],r['version']): ok=False; break
        if ok:return True
    return False

def verify(t):
    ok,why=structural(t)
    if not ok:return 'INVALID_TRACE',why
    if t['evidence_state'].get('overall') in {'missing','incomplete','unknown'}: return 'INSUFFICIENT_EVIDENCE','evidence incomplete'
    if any(q.get('coverage',{}).get('status')!='complete' for q in t['candidate_domains']): return 'INSUFFICIENT_EVIDENCE','candidate coverage incomplete'
    results=[branch_sat(t,e) for e in t['evaluation_domain'] if isinstance(e,dict) and 'id' in e]
    if len(results)!=len(t['evaluation_domain']): return 'INVALID_TRACE','malformed evaluation domain entry'
    if t['trace_scope']=='universal':
        if all(not x for x in results): return 'VERIFIED_UNSAT',results
        if all(x for x in results): return 'VERIFIED_SAT',results
        return 'INSUFFICIENT_EVIDENCE',results
    if t['trace_scope']=='existential':
        return ('VERIFIED_SAT',results) if any(results) else ('VERIFIED_UNSAT',results)
    return 'INSUFFICIENT_EVIDENCE','branch scope requires explicit branch selector'

def base_trace():
    return {
      'schema':'resolvewhy-trace/research-2026', 'trace_scope':'universal',
      'requirements':[{'id':'root:a','package':'a','op':'==','version':'1.0'}],
      'candidates':[{'id':'a@1','package':'a','version':'1.0'},{'id':'x@1','package':'x','version':'1.0'},{'id':'x@2','package':'x','version':'2.0'}],
      'artifacts':[{'id':'art:a1','candidate_ref':'a@1'}],
      'dependencies':[{'id':'dep:a-x','parent_candidate':'a@1','requirement':{'package':'x','op':'>=','version':'2.0'},'active':True}],
      'runtime_contexts':[{'id':'env:py3.13-linux','python':'3.13','platform':'linux'}],
      'evaluation_domain':[{'id':'py3.13-linux'}],
      'resolution_policy':{'prerelease':'disallow','source_selection':'fixed'},
      'candidate_domains':[{'id':'domain:x','candidate_ids':['x@1','x@2'],'scope':{'sources':['index:A']},'coverage':{'status':'complete','attestation':{'kind':'authoritative_finite_domain','evidence_refs':['obs:x']}}}],
      'semantic_constraints':[{'id':'c:root','kind':'requirement','source_ref':'root:a'},{'id':'c:dep','kind':'dependency','source_ref':'dep:a-x'}],
      'provenance':[{'id':'p:root','premise_refs':['root:a'],'claim':'root requirement'},{'id':'p:dep','premise_refs':['dep:a-x'],'claim':'dependency metadata'},{'id':'p:domain','premise_refs':['obs:x'],'claim':'candidate domain complete'}],
      'evidence_state':{'overall':'known'},
      'claimed_core':['c:root','c:dep']
    }

def clone(t): return json.loads(json.dumps(t,sort_keys=True))
def mutate(t,name):
    x=clone(t)
    if name=='coverage_attestation': x['candidate_domains'][0]['coverage'].pop('attestation',None)
    elif name=='evaluation_domain': x.pop('evaluation_domain',None)
    elif name=='resolution_policy': x.pop('resolution_policy',None)
    elif name=='candidate_identity': x['candidates'][0].pop('id',None)
    elif name=='provenance': x['provenance']=[]
    elif name=='dependency_semantics': x['dependencies'][0]['requirement'].pop('version',None)
    elif name=='candidate_coverage': x['candidate_domains'][0]['coverage']['status']='partial'
    elif name=='dangling_ref': x['dependencies'][0]['parent_candidate']='missing@1'
    elif name=='evidence_state': x['evidence_state']['overall']='unknown'
    return x

def minimality(t):
    base=verify(t)[0]=='VERIFIED_UNSAT'; checks=[]
    for name in ('drop_dependency','drop_root_constraint','drop_candidate'):
        x=clone(t)
        if name=='drop_dependency': x['dependencies']=[]
        elif name=='drop_root_constraint': x['requirements']=[]
        else: x['candidate_domains'][0]['candidate_ids']=['x@2']
        checks.append((name,verify(x)[0]))
    return base,checks

def main():
    t=base_trace(); d=Path(tempfile.mkdtemp(prefix='resolvewhy-trace-only-')); p=d/'trace.json'
    p.write_text(json.dumps(t,sort_keys=True)); rt=json.loads(p.read_text())
    print('TRACE_ONLY',verify(rt)); print('SERIALIZATION_STABLE',verify(t)==verify(rt)); print('MINIMALITY',minimality(t))
    for n in ['coverage_attestation','evaluation_domain','resolution_policy','candidate_identity','provenance','dependency_semantics','candidate_coverage','dangling_ref','evidence_state']: print('MUTATION',n,verify(mutate(t,n)))
    isolated=d/'isolated.py'; isolated.write_text(Path(__file__).read_text())
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'}}
    out=subprocess.run([sys.executable,str(isolated)],cwd=d,env=env,capture_output=True,text=True)
    print('HERMETIC_RC',out.returncode); print(out.stdout.split('HERMETIC_RC',1)[0])

if __name__=='__main__': main()