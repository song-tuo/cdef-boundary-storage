from pathlib import Path
import subprocess,json,os,struct
root=Path(__file__).resolve().parents[1]
data=(root/'testdata/generated/odd_8_420.ivf').read_bytes()
bad=root/'testdata/generated/truncated_payload.ivf';bad.write_bytes(data[:-31])
mut=root/'testdata/generated/corrupt_payload.ivf';b=bytearray(data);b[44:56]=b'\xff'*12;mut.write_bytes(b)
files=sorted((root/'testdata').glob('invalid*.ivf'))+[bad,mut];rows=[]
for stream in files:
    for w in [1,4,16]:
        for mt in [0,1]:
            outs=[]
            for variant in ['baseline_release','type_fix_release','token_release','token_asan','token_tsan']:
                tag=f'invalid_{stream.name}_{w}_{mt}_{variant}'
                p=subprocess.run([str(root/'builds'/variant/'ivf_gate'),str(stream),str(w),str(mt)],capture_output=True,text=True,timeout=30,env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1'))
                (root/'logs'/(tag+'.log')).write_text(p.stdout+p.stderr)
                assert p.stdout.strip().startswith('{'),tag
                o=json.loads(p.stdout);assert o['destroy_status']==0,tag
                assert not any(x in p.stderr for x in ['ERROR: AddressSanitizer','runtime error:','WARNING: ThreadSanitizer']),tag
                key=(p.returncode,o['status'],o['pixel_sha256'],o['output_frames'])
                if outs: assert key==outs[0],(tag,outs[0],key)
                outs.append(key);rows.append(dict(workload=stream.name,threads=w,row_mt=mt,variant=variant,exit=p.returncode,output=o))
            (root/'results/invalid_input_comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(stream.name,'PASS',flush=True)
print('PASS',len(rows),'runs',flush=True)
