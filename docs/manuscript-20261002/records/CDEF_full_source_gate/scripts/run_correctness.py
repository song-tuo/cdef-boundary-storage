from pathlib import Path
import os, json, subprocess, csv, sys
root=Path(__file__).resolve().parents[1]
profile=sys.argv[1] if len(sys.argv)>1 else 'release'
variants=['baseline','type_fix','token'] if profile=='release' else ['token']
records=[]
env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1')
references={}
if profile!='release':
    for x in json.loads((root/'results/correctness_release.json').read_text()):
        if x['variant']=='baseline':references[(x['workload'],x['threads'],x['row_mt'])]=x['output']
for spec in json.loads((root/'results/correctness_workloads.json').read_text()):
    assert spec['status']==0, 'Failed encoding is not a test input'
    for threads in [1,2,4,8,16]:
        for rowmt in [0,1]:
            outputs=[]
            for v in variants:
                tag=f'{profile}_{spec["id"]}_{threads}_{rowmt}_{v}'
                cmd=[str(root/'builds'/f'{v}_{profile}'/'ivf_gate'),str(root/'testdata/generated'/(spec['id']+'.ivf')),str(threads),str(rowmt)]
                p=subprocess.run(cmd,capture_output=True,text=True,timeout=90,env=env)
                (root/'logs'/f'{tag}.log').write_text(p.stdout+p.stderr)
                out=json.loads(p.stdout) if p.stdout.strip().startswith('{') else {}
                records.append(dict(workload=spec['id'],threads=threads,row_mt=rowmt,variant=v,profile=profile,exit=p.returncode,output=out))
                outputs.append(out)
                if p.returncode: raise RuntimeError(f'{tag}: exit {p.returncode}; see log')
            ref=outputs[0] if profile=='release' else references[(spec['id'],threads,rowmt)]
            for out in outputs:
                assert out['pixel_sha256']==ref['pixel_sha256'],(spec,threads,rowmt,outputs)
                assert out['output_frames']==ref['output_frames']==spec['frames']
                assert out['bit_depth']==spec['depth']
                if spec['chroma']=='mono': assert out['monochrome']==1
                else:
                    assert (out['subsampling_x'],out['subsampling_y'])=={'420':(1,1),'422':(1,0),'444':(0,0)}[spec['chroma']]
            (root/'results'/f'correctness_{profile}.json').write_text(json.dumps(records,indent=2)+'\n')
    print(profile,spec['id'],'PASS',flush=True)
with (root/'results'/f'output_hash_comparison_{profile}.csv').open('w') as f:
    fields=['workload','threads','row_mt','variant','profile','exit','pixel_sha256','output_frames','peak_rss_bytes']
    w=csv.DictWriter(f,fields);w.writeheader()
    for x in records:w.writerow({k:x.get(k,x['output'].get(k)) for k in fields})
print('PASS',len(records),'runs',flush=True)
