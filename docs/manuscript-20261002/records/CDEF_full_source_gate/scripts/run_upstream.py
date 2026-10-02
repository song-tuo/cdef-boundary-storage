from pathlib import Path
import json, subprocess, os, sys, time
root=Path(__file__).resolve().parents[1];variant=sys.argv[1];profile=sys.argv[2]
groups={
 'core':'*CDEF*:*CommonInt*:*AomMemTest*:*BlockdTest*:*Av1Config*:*DecodeAPI*:-*Speed*',
 'conformance':'*TestVectorTest*:*InvalidFileTest*:*ExternalFrameBuffer*:*DecodeScalabilityTest*',
 'row_tiles':'*DecodeMultiThreaded*:*ExtTileTest*:*TileIndependence*:*TileGroup*:*UniformTileConfig*',
 'resize_error':'*Resize*:*Superres*:*FrameSize*:*ErrorResilience*',
}
if len(sys.argv)>3:groups={k:v for k,v in groups.items() if k in sys.argv[3].split(',')}
results=[]
env=dict(os.environ,LIBAOM_TEST_DATA_PATH=str(root/'testdata'),ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1')
for name,filter in groups.items():
    stem=f'{variant}_{profile}_upstream_{name}'
    cmd=[str(root/'builds'/f'{variant}_{profile}'/'test_libaom'),'--gtest_filter='+filter,'--gtest_output=xml:'+str(root/'results'/(stem+'.xml'))]
    start=time.time()
    with (root/'logs'/(stem+'.log')).open('w') as log:
        try: p=subprocess.run(cmd,stdout=log,stderr=log,env=env,timeout=3600);code=p.returncode
        except subprocess.TimeoutExpired:code='TIMEOUT_3600s'
    results.append(dict(group=name,command=cmd,exit=code,seconds=time.time()-start))
    (root/'results'/f'{variant}_{profile}_upstream_status.json').write_text(json.dumps(results,indent=2)+'\n')
    print(stem,code,flush=True)
