from checks import *
shim=ROOT/'scripts/tarball_version';shim.mkdir(exist_ok=True);p=shim/'git';p.write_text('#!/bin/sh\n# Only source_version() lookup: use the CMake-generated tarball version.\nexit 127\n');p.chmod(0o755)
b=ROOT/'builds/hybrid_release';d=ROOT/'results/shell_work';d.mkdir(exist_ok=True)
cmd=['sh',ROOT/'src/hybrid/test/aomdec.sh','--bin-path',b,'--config-path',b,'--test-data-path','${WORKSPACE}/CDEF_full_source_gate/testdata','--show-program-output','--verbose'];r=run('shell_aomdec_hybrid',cmd,cwd=d,env={'PATH':str(shim)+':'+os.environ['PATH']},timeout=600)
writecsv('results/shell_safety.csv',[{'category':'upstream_decoder_shell','profile':'release','exit_code':r['exit_code'],'status':'PASS' if r['exit_code']==0 else 'FAIL','command_log':'shell_aomdec_hybrid','source_version_note':'tarball source has no .git; helper disables git version query only'}])
