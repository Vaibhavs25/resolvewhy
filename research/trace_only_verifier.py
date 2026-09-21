from pathlib import Path
import copy, json, subprocess, sys, tempfile, os

def parse_ver(v): return tuple(map(int, v.split('.')))
def satisfies(v, op, rhs):
    a,b=parse_ver(v),parse_ver(rhs)
    return {'==':a==b,'<':a<b,'<=':a<=b,'>':a>b,'>=':a>=b}[op]

def verify(t):
    required=['requirements','candidates','dependencies','runtime_context','evaluation_domain','resolution_policy','candidate_domains','provenance','evidence_state']
    if any(k not in t for k in required): return 'INVALID_TRACE', 'missing required field'
    if not isinstance(t['evaluation_domain'], list) or not t['evaluation_domain']: return 'INVALID_TRACE', 'invalid evaluation domain'
    ids={c.get('id') for c in t['candidates']}
    if None in ids: return 'INVALID_TRACE', 'candidate identity missing'
    for e in t['dependencies']:
        if e.get('candidate_ref') not in ids: return 'INVALID_TRACE', 'dangling dependency reference'
    for q in t['candidate_domains']:
        cov=q.get('coverage',{})
        if cov.get('status')=='complete' and not cov.get('attestation'): return 'INVALID_TRACE', 'complete coverage lacks attestation'
        if any(x not in ids for x in q.get('candidate_ids',[])): return 'INVALID_TRACE', 'dangling coverage reference'
    if not t['provenance']: return 'INVALID_TRACE', 'proof-supporting trace lacks provenance'
    if t['evidence_state'].get('overall') in {'missing','incomplete','unknown'}: return 'INSUFFICIENT_EVIDENCE', 'evidence incomplete'
    results=[]
    for env in t['evaluation_domain']:
        en=env['id']; active=[]
        for c in t['candidates']:
            rp=c.get('requires_python')
            if rp=='>=3.10' and en=='py3.9-linux': continue
            active.append(c)
        okroots=[c for c in active if any(c['package']==r['package'] and satisfies(c['version'],r['op'],r['version']) for r in t['requirements'])]
        if not okroots: results.append('UNSAT'); continue
        bad=False
        for c in okroots:
            for e in t['dependencies']:
                if e['candidate_ref']==c['id'] and e.get('active',True):
                    req=e['requirement']
                    if not any(x['package']==req['package'] and satisfies(x['version'],req['op'],req['version']) for x in active): bad=True
        results.append('UNSAT' if bad else 'SAT')
    if t.get('proof_scope')=='universal' and all(x=='UNSAT' for x in results): return 'VERIFIED_UNSAT', results
    if t.get('proof_scope')=='existential' and any(x=='SAT' for x in results): return 'VERIFIED_SAT', results
    if all(x=='UNSAT' for x in results): return 'VERIFIED_UNSAT', results
    return 'INSUFFICIENT_EVIDENCE', results

def base_trace():
    return {
      'schema':'resolvewhy-trace/v0-research',
      'requirements':[{'id':'root:appa','package':'appa','op':'==','version':'1.0'}],
      'candidates':[
        {'id':'appa@1','package':'appa','version':'1.0'},
        {'id':'leaf@1','package':'leaf','version':'1.0'},
        {'id':'leaf@2','package':'leaf','version':'2.0'},
      ],
      'dependencies':[{'id':'e1','candidate_ref':'appa@1','requirement':{'package':'leaf','op':'==','version':'3.0'},'active':True}],
      'runtime_context':{'python':'3.13','platform':'linux'},
      'evaluation_domain':[{'id':'py3.13-linux'}],
      'resolution_policy':{'prerelease':'disallow'},
      'candidate_domains':[{'id':'leaf','candidate_ids':['leaf@1','leaf@2'],'coverage':{'status':'complete','attestation':{'kind':'authoritative_finite_domain','evidence_refs':['obs:1']}}}],
      'provenance':{'obs:1':{'source':'fixture','kind':'known_fact'}},
      'evidence_state':{'overall':'known'},
      'proof_scope':'existential',
      'claimed_core':['root:appa','appa->leaf']
    }

def mutate(t,name):
    x=copy.deepcopy(t)
    if name=='remove_coverage_attestation': x['candidate_domains'][0]['coverage'].pop('attestation',None)
    elif name=='remove_evaluation_domain': x.pop('evaluation_domain',None)
    elif name=='remove_policy': x.pop('resolution_policy',None)
    elif name=='remove_artifact_identity': x['candidates'][0].pop('id',None)
    elif name=='remove_provenance': x['provenance']={}
    elif name=='remove_dependency_fact': x['dependencies'][0].pop('requirement',None)
    elif name=='remove_marker_activation': x['dependencies'][0].pop('active',None)
    return x

def minimality_check(t):
    # Verify the contradiction and each single deletion of claimed core.
    full=verify(t)[0]=='VERIFIED_UNSAT'
    deletion_sat=[]
    for drop in range(len(t['dependencies'])):
        x=copy.deepcopy(t); x['dependencies'].pop(drop); deletion_sat.append(verify(x)[0])
    return full, deletion_sat

if __name__=='__main__':
    t=base_trace(); print('TRACE_ONLY',verify(t)); print('MINIMALITY',minimality_check(t))
    for name in ['remove_coverage_attestation','remove_evaluation_domain','remove_policy','remove_artifact_identity','remove_provenance','remove_dependency_fact','remove_marker_activation']:
        print(name, verify(mutate(t,name)))
    root=Path(tempfile.mkdtemp(prefix='resolvewhy-hermetic-')); (root/'trace.json').write_text(json.dumps(t))
    isolated=root/'verifier.py'; isolated.write_text(Path(__file__).read_text())
    env=os.environ.copy(); env['PYTHONPATH']=''; env['NO_PROXY']='*'; env['HTTP_PROXY']=''; env['HTTPS_PROXY']=''
    p=subprocess.run([sys.executable,str(isolated)],cwd=root,env=env,capture_output=True,text=True)
    print('HERMETIC_RETURN',p.returncode); print(p.stdout)
    if p.stderr: print('HERMETIC_STDERR',p.stderr)