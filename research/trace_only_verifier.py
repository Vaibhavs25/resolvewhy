from pathlib import Path
import copy, json, subprocess, sys, tempfile, os

OPS = {'==': lambda a,b:a==b, '<':lambda a,b:a<b, '<=':lambda a,b:a<=b, '>':lambda a,b:a>b, '>=':lambda a,b:a>=b}
def ver(v): return tuple(int(x) for x in v.split('.'))
def satv(v, op, rhs): return OPS[op](ver(v), ver(rhs))

def verify(t):
    required=['schema','requirements','candidates','dependencies','runtime_context','evaluation_domain','resolution_policy','candidate_domains','provenance','evidence_state','proof_scope']
    if any(k not in t for k in required): return ('INVALID_TRACE','missing required field')
    if not isinstance(t['evaluation_domain'],list) or not t['evaluation_domain']: return ('INVALID_TRACE','invalid evaluation_domain')
    ids={c.get('id') for c in t['candidates']}
    if None in ids: return ('INVALID_TRACE','missing candidate id')
    for e in t['dependencies']:
        if e.get('candidate_ref') not in ids: return ('INVALID_TRACE','dangling dependency reference')
        if 'requirement' not in e: return ('INVALID_TRACE','missing dependency requirement')
    for q in t['candidate_domains']:
        cov=q.get('coverage',{})
        if cov.get('status')=='complete' and not cov.get('attestation'): return ('INVALID_TRACE','complete coverage without attestation')
        if any(x not in ids for x in q.get('candidate_ids',[])): return ('INVALID_TRACE','dangling coverage reference')
    if not t['provenance']: return ('INVALID_TRACE','missing provenance')
    if t['evidence_state'].get('overall') in {'missing','incomplete','unknown'}: return ('INSUFFICIENT_EVIDENCE','incomplete evidence')
    if any(q.get('coverage',{}).get('status') != 'complete' for q in t['candidate_domains']): return ('INSUFFICIENT_EVIDENCE','non-complete candidate coverage')
    branches=[]
    for env in t['evaluation_domain']:
        en=env['id']; active=[]
        for c in t['candidates']:
            rp=c.get('requires_python')
            if rp=='>=3.10' and en=='py3.9-linux': continue
            active.append(c)
        roots=[]
        for root in t['requirements']:
            roots += [c for c in active if c['package']==root['package'] and satv(c['version'],root['op'],root['version'])]
        if not roots: branches.append(('UNSAT',en)); continue
        bad=False
        for c in roots:
            for e in t['dependencies']:
                if e['candidate_ref']==c['id'] and e.get('active',True):
                    req=e['requirement']
                    if not any(x['package']==req['package'] and satv(x['version'],req['op'],req['version']) for x in active): bad=True
        branches.append(('UNSAT' if bad else 'SAT',en))
    if t['proof_scope']=='universal':
        if all(x[0]=='UNSAT' for x in branches): return ('VERIFIED_UNSAT',branches)
        if all(x[0]=='SAT' for x in branches): return ('VERIFIED_SAT',branches)
        return ('INSUFFICIENT_EVIDENCE',branches)
    if t['proof_scope']=='existential':
        if any(x[0]=='SAT' for x in branches): return ('VERIFIED_SAT',branches)
        if all(x[0]=='UNSAT' for x in branches): return ('VERIFIED_UNSAT',branches)
        return ('INSUFFICIENT_EVIDENCE',branches)
    return ('INVALID_TRACE','unknown proof scope')

def base_trace():
    return {
      'schema':'resolvewhy-trace/v0-research',
      'requirements':[{'id':'root:appa','package':'appa','op':'==','version':'1.0'}],
      'candidates':[{'id':'appa@1','package':'appa','version':'1.0'},{'id':'leaf@1','package':'leaf','version':'1.0'}],
      'dependencies':[{'id':'edge1','candidate_ref':'appa@1','requirement':{'package':'leaf','op':'==','version':'2.0'},'active':True}],
      'runtime_context':{'python':'3.13','platform':'linux'},
      'evaluation_domain':[{'id':'py3.13-linux'}],
      'resolution_policy':{'prerelease':'disallow'},
      'candidate_domains':[{'id':'domain:leaf','candidate_ids':['leaf@1'],'coverage':{'status':'complete','attestation':{'kind':'authoritative_finite_domain','evidence_refs':['obs:1']}}}],
      'provenance':{'obs:1':{'source':'fixture','kind':'known_fact'},'edge1':{'premises':['obs:1'],'kind':'dependency'}},
      'evidence_state':{'overall':'known'},
      'proof_scope':'universal',
      'claimed_core':['root:appa','edge1']
    }

def mutate(t,name):
    x=copy.deepcopy(t)
    if name=='coverage_attestation': x['candidate_domains'][0]['coverage'].pop('attestation',None)
    elif name=='evaluation_domain': x.pop('evaluation_domain',None)
    elif name=='policy': x.pop('resolution_policy',None)
    elif name=='artifact_identity': x['candidates'][0].pop('id',None)
    elif name=='requires_python': x['candidates'][0]['requires_python']='>=3.10'
    elif name=='provenance': x['provenance'].pop('edge1',None)
    elif name=='source_scope': x['candidate_domains'][0].pop('scope',None)
    elif name=='active_marker': x['dependencies'][0].pop('active',None)
    elif name=='dangling_ref': x['dependencies'][0]['candidate_ref']='missing@1'
    return x

def minimality(t):
    full=verify(t)[0]=='VERIFIED_UNSAT'; checks=[]
    for kind in ('drop_dependency','drop_root'):
        x=copy.deepcopy(t)
        if kind=='drop_dependency': x['dependencies']=[]
        else: x['requirements']=[]
        checks.append((kind,verify(x)[0]))
    return full, checks

def main():
    t=base_trace(); root=Path(tempfile.mkdtemp(prefix='resolvewhy-trace-only-'))
    path=root/'trace.json'; path.write_text(json.dumps(t,sort_keys=True))
    roundtrip=json.loads(path.read_text())
    print('TRACE_ONLY',verify(roundtrip)); print('SERIALIZATION_STABLE',verify(t)==verify(roundtrip)); print('MINIMALITY',minimality(t))
    for name in ['coverage_attestation','evaluation_domain','policy','artifact_identity','requires_python','provenance','source_scope','active_marker','dangling_ref']:
        print('MUTATION',name,verify(mutate(t,name)))
    isolated=root/'verifier_copy.py'; isolated.write_text(Path(__file__).read_text())
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'}}
    p=subprocess.run([sys.executable,str(isolated)],cwd=root,env=env,capture_output=True,text=True)
    print('HERMETIC_RC',p.returncode); print(p.stdout); print(p.stderr if p.stderr else '')

if __name__=='__main__': main()