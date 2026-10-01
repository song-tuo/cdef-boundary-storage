from pathlib import Path
import json,subprocess,csv
root=Path(__file__).resolve().parents[1];rows=[]
for spec in json.loads((root/'results/timing_workloads.json').read_text()):
    for threads in [1,2,4,8,16]:
        for v in ['baseline','type_fix','token']:
            stem=f'memory_{spec["id"]}_{threads}_{v}'
            cmd=[str(root/'builds'/f'{v}_audit_release'/'ivf_gate'),str(root/'testdata/generated'/(spec['id']+'.ivf')),str(threads),'1']
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
            (root/'logs'/(stem+'.log')).write_text(p.stdout+p.stderr)
            assert p.returncode==0,stem
            out=json.loads(p.stdout);events=[json.loads(l) for l in p.stderr.splitlines() if l.startswith('{')]
            frames=[e for e in events if e['event']=='cdef_frame'];assert frames,stem+' lacks CDEF activity'
            row=dict(workload=spec['id'],width=spec['width'],height=spec['height'],requested_threads=threads,variant=v,active_workers=max(e['workers'] for e in frames),rows=max(e['rows'] for e in frames),cdef_frames=len(frames),requested_bytes=max(e['requested_bytes'] for e in frames),usable_bytes=max(e['usable_bytes'] for e in frames),stage_ns=sum(e['stage_ns'] for e in frames),row_sync_wait_ns=sum(e['row_sync_wait_ns'] for e in frames),pool_wait_count=sum(e['pool_wait_count'] for e in frames),peak_rss_bytes=out['peak_rss_bytes'],pixel_sha256=out['pixel_sha256'],output_frames=out['output_frames'])
            rows.append(row);(root/'results/memory_results.json').write_text(json.dumps(rows,indent=2)+'\n')
        triple=rows[-3:];assert len({x['pixel_sha256'] for x in triple})==1
        if spec['width']==3840 and threads in [8,16]:
            assert 1-triple[2]['requested_bytes']/triple[1]['requested_bytes']>=0.25
    print(spec['id'],'PASS',flush=True)
with (root/'results/memory_results.csv').open('w') as f:
    w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
