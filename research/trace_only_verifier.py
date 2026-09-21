import copy, json, os, subprocess, sys, tempfile
from pathlib import Path

OPS = {'==':lambda a,b:a==b,'!=':lambda a,b:a!=b,'<':lambda a,b:a<b,'<=':lambda a,b:a<=b,'>':lambda a,b:a>b,'>=':lambda a,b:a>=b}
def ver(v):
    try:
        parts=tuple(int(x) for x in v.split('.'))
        if len(parts)!=3:
            raise ValueError
        return parts
    except (ValueError, AttributeError):
        raise ValueError(f'unsupported version: {v!r}')

def satv(v, op, rhs):
    return OPS[op](ver(v),ver(rhs))

# EXECUTABLE BOUNDARY: this research verifier intentionally implements only the finite fixture fragment below.
# Unsupported marker grammars, artifact-selection/build semantics, lockfile semantics,
# and generic branch selectors are not inferred; unsupported policy values fail closed.

def structural(t):
    required=['schema','trace_scope','requirements','candidates','artifacts','dependencies','runtime_contexts','evaluation_domain','resolution_policy','candidate_domains','semantic_constraints','provenance','evidence_state','proof_claim']

    missing=[x for x in required if x not in t]
    if missing: return False,'missing required fields: '+','.join(missing)
    if t['trace_scope'] not in {'existential','universal','branch'}: return False,'invalid trace scope'
    if not isinstance(t['evaluation_domain'],list) or not t['evaluation_domain']: return False,'invalid evaluation domain'
    domain_ids=[e.get('id') for e in t['evaluation_domain'] if isinstance(e,dict)]
    if len(domain_ids)!=len(t['evaluation_domain']) or len(domain_ids)!=len(set(domain_ids)): return False,'invalid evaluation domain IDs'
    claim=t['proof_claim']
    if not isinstance(claim,dict): return False,'invalid proof claim'
    if claim.get('kind')!='satisfiability': return False,'invalid proof claim kind'
    if claim.get('quantifier') not in {'existential','universal','branch'}: return False,'invalid proof claim quantifier'
    if claim.get('evaluation_domain_ref')!='evaluation_domain': return False,'proof claim does not bind evaluation domain'
    if claim.get('status_claim') not in {'SAT','UNSAT'}: return False,'invalid proof claim result'
    if not isinstance(claim.get('premise_refs'),list) or not claim.get('premise_refs'): return False,'proof claim lacks premises'
    ids=[c.get('id') for c in t['candidates']]
    if any(x is None for x in ids) or len(ids)!=len(set(ids)): return False,'invalid candidate IDs'
    if t['trace_scope'] != claim.get('quantifier'): return False,'trace scope and proof quantifier disagree'
    aids=[a.get('id') for a in t['artifacts']]
    if any(x is None for x in aids) or len(aids)!=len(set(aids)): return False,'invalid artifact IDs'
    eids=[e.get('id') for e in t['dependencies']]
    if any(x is None for x in eids) or len(eids)!=len(set(eids)): return False,'invalid dependency IDs'
    cids=[e.get('id') for e in t['semantic_constraints']]
    if any(x is None for x in cids) or len(cids)!=len(set(cids)): return False,'invalid constraint IDs'
    req_ids={x.get('id') for x in t['requirements'] if isinstance(x,dict)}
    dep_ids={x.get('id') for x in t['dependencies'] if isinstance(x,dict)}
    sem_by_id={x.get('id'):x for x in t['semantic_constraints'] if isinstance(x,dict)}
    for s in t['semantic_constraints']:
        if not isinstance(s,dict): return False,'invalid semantic constraint'
        if s.get('kind')=='requirement' and s.get('source_ref') not in req_ids: return False,'dangling semantic requirement ref'
        if s.get('kind')=='dependency' and s.get('source_ref') not in dep_ids: return False,'dangling semantic dependency ref'
        if s.get('kind') not in {'requirement','dependency'}: return False,'unsupported semantic constraint kind'
    for e in t['dependencies']:
        if e.get('parent_candidate') not in ids: return False,'dangling dependency parent'
        if 'requirement' not in e: return False,'missing dependency requirement'
    for a in t['artifacts']:
        if a.get('candidate_ref') not in ids: return False,'dangling artifact candidate'
    for q in t['candidate_domains']:
        cov=q.get('coverage',{})
        if cov.get('status')=='complete' and not isinstance(cov.get('attestation'),dict): return False,'complete coverage lacks attestation'
        if any(x not in ids for x in q.get('candidate_ids',[])): return False,'dangling coverage candidate'
        att=cov.get('attestation')
        if isinstance(att,dict):
            refs=att.get('evidence_refs',[])
            if not isinstance(refs,list) or any(not isinstance(x,str) for x in refs) or not refs:
                return False,'invalid coverage evidence references'
    provenance_tokens=set()
    for p in t['provenance']:
        if isinstance(p,dict):
            provenance_tokens.update(p.get('premise_refs',[]))
            provenance_tokens.update(p.get('evidence_refs',[]))
            provenance_tokens.update(p.get('source_refs',[]))
    for q in t['candidate_domains']:
        att=q.get('coverage',{}).get('attestation')
        if isinstance(att,dict):
            if any(ref not in provenance_tokens for ref in att.get('evidence_refs',[])):
                return False,'coverage evidence is not provenance-backed'
    if not t['provenance']: return False,'missing provenance'
    prov_ids=[p.get('id') for p in t['provenance'] if isinstance(p,dict)]
    if len(prov_ids)!=len(t['provenance']) or any(x is None for x in prov_ids) or len(prov_ids)!=len(set(prov_ids)): return False,'invalid provenance IDs'
    evidence_refs=set()
    for q in t['candidate_domains']:
        a=q.get('coverage',{}).get('attestation',{})
        if isinstance(a,dict): evidence_refs.update(a.get('evidence_refs',[]))
    claimed=list(claim.get('premise_refs',[]))
    if not claimed or not claimed.issubset(sem_by_id): return False,'proof premise is not a declared semantic constraint'
    prov_by_id={p.get('id'):p for p in t['provenance'] if isinstance(p,dict)}
    visited=set()
    def reachable_from_premise(premise_id,trail=()):
        if premise_id in trail: return False
        for p in t['provenance']:
            if not isinstance(p,dict) or premise_id not in p.get('premise_refs',[]): continue
            pid=p.get('id')
            if pid in visited: return True
            refs=p.get('evidence_refs',[])
            raw_refs=p.get('source_refs',[])
            if isinstance(refs,list) and any(ref in evidence_refs for ref in refs):
                visited.add(pid); return True
            if isinstance(raw_refs,list) and any(ref in evidence_refs or ref in dep_ids or ref in req_ids for ref in raw_refs):
                visited.add(pid); return True
            for parent in p.get('premise_refs',[]):
                if parent != premise_id and reachable_from_premise(parent,trail+(premise_id,)):
                    visited.add(pid); return True
        return False
    for sid in claimed:
        if not reachable_from_premise(sid): return False,'proof premise provenance is not reachable'
    return True,'ok'

def candidate_usable(c,t,env):
    rp=c.get('requires_python')
    if rp=='>=3.10' and env['id'].startswith('py3.9-'): return False
    if rp is not None and rp != '>=3.10':
        return False
    for a in t.get('artifacts', []):
        if a.get('candidate_ref') == c.get('id'):
            if a.get('compatible') is False:
                return False
    return True

def branch_sat(t,env):
    candidates=[c for c in t['candidates'] if candidate_usable(c,t,env)]
    # The proof claim premises select the semantic constraints that participate
    # in the proposition. This executable fragment supports requirement and
    # dependency constraints only.
    premise_ids=set(t['proof_claim'].get('premise_refs',[]))
    selected=[s for s in t['semantic_constraints'] if s.get('id') in premise_ids]
    root_ids={s.get('source_ref') for s in selected if s.get('kind')=='requirement'}
    dep_ids={s.get('source_ref') for s in selected if s.get('kind')=='dependency'}
    requirements=[r for r in t['requirements'] if r.get('id') in root_ids]
    dependencies=[d for d in t['dependencies'] if d.get('id') in dep_ids]
    packages=sorted({c['package'] for c in candidates})
    choices=[]
    for p in packages:
        choices.append([c for c in candidates if c['package']==p])
    if not choices:return False
    import itertools
    for assignment in itertools.product(*choices):
        chosen={c['package']:c for c in assignment}
        root_ok=all(r['package'] in chosen and satv(chosen[r['package']]['version'],r['op'],r['version']) for r in requirements)
        if not root_ok: continue
        ok=True
        for e in dependencies:
            if e.get('active',True) is False: continue
            parents=[c for c in candidates if c['id']==e['parent_candidate']]
            if not parents: return False
            parent=chosen.get(parents[0]['package'])
            if parent is None: continue
            rr=e['requirement']
            target=chosen.get(rr['package'])
            if target is None or not satv(target['version'],rr['op'],rr['version']):
                ok=False
                break
        if ok:return True
    return False


def verify(t):
    try:
        ok, why = structural(t)
        if not ok:
            return 'INVALID_TRACE', why
        if t['evidence_state'].get('overall') in {'missing','incomplete','unknown'}:
            return 'INSUFFICIENT_EVIDENCE', 'evidence incomplete'

        policy = t['resolution_policy']
        if policy.get('prerelease') not in {'disallow'} or policy.get('source_selection') not in {'fixed'}:
            return 'INSUFFICIENT_EVIDENCE', 'unsupported executable policy semantics'
        if any(q.get('coverage',{}).get('status') != 'complete' for q in t['candidate_domains']):
            return 'INSUFFICIENT_EVIDENCE', 'candidate coverage incomplete'

        results = [branch_sat(t,e) for e in t['evaluation_domain'] if isinstance(e,dict) and 'id' in e]
        if len(results) != len(t['evaluation_domain']):
            return 'INVALID_TRACE', 'malformed evaluation domain entry'

        if t['trace_scope'] == 'universal':
            if all(not x for x in results):
                return 'VERIFIED_UNSAT', results
            if all(x for x in results):
                return 'VERIFIED_SAT', results
            return 'INSUFFICIENT_EVIDENCE', results

        if t['trace_scope'] == 'existential':
            return ('VERIFIED_SAT', results) if any(results) else ('VERIFIED_UNSAT', results)

        if t['trace_scope'] == 'branch':
            branch_ref = t['proof_claim'].get('branch_ref')
            domain_ids = {e.get('id') for e in t['evaluation_domain']}
            if not branch_ref or branch_ref not in domain_ids:
                return 'INVALID_TRACE', 'branch claim lacks valid branch_ref'
            selected = [e for e in t['evaluation_domain'] if e.get('id') == branch_ref]
            result = branch_sat(t, selected[0])
            return ('VERIFIED_SAT', [result]) if result else ('VERIFIED_UNSAT', [result])

        return 'INVALID_TRACE', 'unsupported trace scope'
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        return 'INVALID_TRACE', f'uninterpretable finite semantic data: {exc}'

def sat_fixture():
    t=base_trace()
    t['dependencies']=[]
    t['trace_scope']='existential'
    t['proof_claim']['quantifier']='existential'
    t['proof_claim']['status_claim']='SAT'
    t['claimed_core']=[]
    t['proof_claim']['premise_refs']=['c:root']
    return t
def base_trace():
    return {
      'schema':'resolvewhy-trace/research-2026', 'trace_scope':'universal',
      'requirements':[{'id':'root:a','package':'a','op':'==','version':'1.0'}],
      'candidates':[{'id':'a@1','package':'a','version':'1.0'},{'id':'x@1','package':'x','version':'1.0'},{'id':'x@2','package':'x','version':'2.0'}],
      'artifacts':[{'id':'art:a1','candidate_ref':'a@1','compatible':True}],
      'dependencies':[{'id':'dep:a-x','parent_candidate':'a@1','requirement':{'package':'x','op':'>=','version':'2.0'},'active':True}],
      'runtime_contexts':[{'id':'env:py3.13-linux','python':'3.13','platform':'linux'}],
      'evaluation_domain':[{'id':'py3.13-linux'}],
      'resolution_policy':{'prerelease':'disallow','source_selection':'fixed'},
      'candidate_domains':[{'id':'domain:x','candidate_ids':['x@1','x@2'],'scope':{'sources':['index:A']},'coverage':{'status':'complete','attestation':{'kind':'authoritative_finite_domain','evidence_refs':['obs:x']}}}],
      'semantic_constraints':[{'id':'c:root','kind':'requirement','source_ref':'root:a'},{'id':'c:dep','kind':'dependency','source_ref':'dep:a-x'}],
      'provenance':[{'id':'p:root','premise_refs':['c:root'],'source_refs':['root:a'],'evidence_refs':['obs:root'],'claim':'root requirement'},{'id':'p:dep','premise_refs':['c:dep'],'source_refs':['dep:a-x'],'evidence_refs':['obs:dep'],'claim':'dependency metadata'},{'id':'p:domain','premise_refs':['obs:x'],'evidence_refs':['obs:x'],'claim':'candidate domain complete'}],
      'evidence_state':{'overall':'known'},
      'proof_claim':{'id':'claim:1','kind':'satisfiability','quantifier':'universal','evaluation_domain_ref':'evaluation_domain','status_claim':'UNSAT','premise_refs':['c:root','c:dep']},
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
    if verify(t)[0] != 'VERIFIED_UNSAT':
        return False, []
    core_ids=list(t.get('claimed_core', []))
    if set(core_ids) != set(t['proof_claim'].get('premise_refs', [])):
        return False, []
    checks=[]
    for cid in core_ids:
        x=clone(t)
        x['semantic_constraints']=[z for z in x['semantic_constraints'] if z.get('id') != cid]
        # The proof claim is the proposition, so delete the core element from
        # its premises and independently recompute the resulting problem.
        x['proof_claim']['premise_refs']=[z for z in x['proof_claim']['premise_refs'] if z != cid]
        if not x['proof_claim']['premise_refs']:
            x['proof_claim']['premise_refs']=[z.get('id') for z in x['semantic_constraints']]
        checks.append((cid, verify(x)[0]))
    return True, checks

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