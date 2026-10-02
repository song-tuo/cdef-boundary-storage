from common import *
from collections import Counter,defaultdict
import csv
SANENV={'ASAN_OPTIONS':'halt_on_error=1:abort_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1','TSAN_OPTIONS':'halt_on_error=1'}
def writecsv(name,rows,fields=None):
 with (ROOT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def parse(name):
 stdout=(ROOT/'logs'/(name+'.stdout')).read_text(errors='replace');stderr=(ROOT/'logs'/(name+'.stderr')).read_text(errors='replace');outputs=[];events=[]
 for line in stdout.splitlines():
  if line.startswith('{'):
   try:outputs.append(json.loads(line))
   except ValueError:pass
 for line in stderr.splitlines():
  if line.startswith('{'):
   try:events.append(json.loads(line))
   except ValueError:pass
 result=json.loads((ROOT/'logs'/(name+'.result.json')).read_text());o=outputs[-1] if outputs else {}
 sanitizer=any(t in stderr for t in ['ERROR: AddressSanitizer','SUMMARY: ThreadSanitizer','WARNING: ThreadSanitizer','runtime error:','Assertion failed'])
 alive={};double_alloc=double_free=0;copies=[];frame=None;frame_idx=-1;order_errors=0;exhaustion='CDEF token exhaustion' in stderr
 for e in events:
  kind=e.get('h1')
  if kind=='alloc' and e['ptr'] not in ('0x0','(nil)'):
   if e['ptr'] in alive:double_alloc+=1
   alive[e['ptr']]=e
  elif kind=='free':
   if e['ptr'] not in alive:double_free+=1
   else:del alive[e['ptr']]
  elif kind=='frame_begin':frame_idx+=1;frame=e|{'rows_seen':defaultdict(list),'copied':[]}
  elif kind in ['copy','dispatch','signal','wait_done','filter_done','release'] and frame is not None:
   row=e['row'];frame['rows_seen'][row].append(kind)
   if kind=='copy':frame['copied'].append((row,e['plane'],e['kind'],e['samples'],e['hash']))
   if kind=='wait_done' and row>0 and 'signal' not in frame['rows_seen'][row-1]:order_errors+=1
  elif kind=='frame_end' and frame is not None:
   if frame['workers']>1:
    for row in range(frame['rows']):
     seq=frame['rows_seen'][row]
     required=['dispatch','signal','wait_done','filter_done','release']
     if any(seq.count(v)!=1 for v in required):order_errors+=1
     elif [seq.index(v) for v in required]!=sorted(seq.index(v) for v in required):order_errors+=1
     if 'copy' in seq and (seq.index('copy')<seq.index('dispatch') or max(i for i,v in enumerate(seq) if v=='copy')>seq.index('signal')):order_errors+=1
   cp=sorted(frame['copied']);
   if len(cp)!=6*(frame['rows']-1):order_errors+=1
   copies.append({'index':frame_idx,'R':frame['rows'],'width':frame['width'],'height':frame['height'],'copies':cp});frame=None
 frames=[e for e in events if e.get('h1')=='visible_frame'];n=o.get('output_frames',0);frames=frames[-n:] if n else []
 canonical=json.dumps(copies,sort_keys=True,separators=(',',':'))
 return {'exit_code':result['exit_code'],'output':o,'outputs':outputs,'visible_hashes':[e['sha256'] for e in frames],'events':events,'copy_hash':hashlib.sha256(canonical.encode()).hexdigest(),'copy_frames':len(copies),'order_errors':order_errors,'double_allocation':double_alloc,'double_free':double_free,'unreleased_allocations':len(alive),'live_allocation_bytes':sum(x['requested'] for x in alive.values()),'slot_violations':sum(e.get('h1')=='violation' for e in events),'exhaustion':exhaustion,'sanitizer':sanitizer,'alive':alive}
def execute(tag,variant,profile,stream,w,mt,env=None,harness='ivf_gate',timeout=180):
 run(tag,[ROOT/'builds'/f'{variant}_{profile}'/harness,ROOT/'inputs'/(stream+'.ivf'),str(w),str(mt)],env=SANENV|(env or {}),timeout=timeout)
 return parse(tag)
def equality(a,b):
 return a['output'].get('output_frames')==b['output'].get('output_frames') and a['visible_hashes']==b['visible_hashes'] and a['output'].get('pixel_sha256')==b['output'].get('pixel_sha256')
def clean(x,audit=False):
 return not x['exit_code'] and x['output'].get('destroy_status')==0 and not x['sanitizer'] and not x['slot_violations'] and not x['exhaustion'] and (not audit or not (x['order_errors'] or x['double_allocation'] or x['double_free'] or x['unreleased_allocations']))
