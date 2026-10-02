from common import *
import shutil
header=r'''#ifndef H1_AUDIT_H
#define H1_AUDIT_H
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <malloc/malloc.h>
#include "aom_mem/aom_mem.h"
static inline size_t h1_usable(void *p){return p?malloc_size((void*)(((size_t*)p)[-1])):0;}
static inline int h1_env(const char*n,int f){const char*s=getenv(n);return s?atoi(s):f;}
static inline void*h1_record(void*p,size_t n,int site){fprintf(stderr,"{\"h1\":\"alloc\",\"ptr\":\"%p\",\"requested\":%zu,\"usable\":%zu,\"site\":%d}\n",p,n,h1_usable(p),site);return p;}
static inline void h1_free(void*p){if(p)fprintf(stderr,"{\"h1\":\"free\",\"ptr\":\"%p\"}\n",p);aom_free(p);}
#define h1_malloc(n) h1_record(aom_malloc(n),(n),__LINE__)
#define h1_calloc(n,s) h1_record(aom_calloc(n,s),(size_t)(n)*(s),__LINE__)
#define h1_memalign(a,n) h1_record(aom_memalign(a,n),(n),__LINE__)
static inline uint64_t h1_hash(const uint16_t*p,size_t n){uint64_t h=14695981039346656037ull;for(size_t i=0;i<n;i++){h=(h^(p[i]&255))*1099511628211ull;h=(h^(p[i]>>8))*1099511628211ull;}return h;}
static inline void h1_copy(int row,int plane,int kind,const uint16_t*p,size_t n){fprintf(stderr,"{\"h1\":\"copy\",\"row\":%d,\"plane\":%d,\"kind\":%d,\"samples\":%zu,\"hash\":\"%016llx\"}\n",row,plane,kind,n,(unsigned long long)h1_hash(p,n));}
static inline void h1_violation(const char*kind,int row){fprintf(stderr,"{\"h1\":\"violation\",\"kind\":\"%s\",\"row\":%d}\n",kind,row);abort();}
#endif
'''
for v in ['type_fix','dual_token','hybrid']:
 for mode in ['account','audit']:
  dst=ROOT/'src'/(v+'_'+mode);shutil.copytree(ROOT/'src'/v,dst)
  def edit(name,old,new):
   p=dst/name;s=p.read_text();assert s.count(old)==1,(v,mode,name,old[:100],s.count(old));p.write_text(s.replace(old,new))
  (dst/'av1/common/h1_audit.h').write_text(header)
  ac='av1/common/alloccommon.c';tc='av1/common/thread_common.c';th='av1/common/thread_common.h';cc='av1/common/cdef.c'
  for n in [ac,tc,cc]:
   p=dst/n;s=p.read_text();s=s.replace('#include "config/aom_config.h"','#include "config/aom_config.h"\n#include "av1/common/h1_audit.h"',1);p.write_text(s)
  p=dst/ac;s=p.read_text();start=s.index('static inline void free_cdef_linebuf_conditional');end=s.index('#if !CONFIG_REALTIME_ONLY || CONFIG_AV1_DECODER',start);part=s[start:end]
  for op in ['malloc','calloc','memalign','free']:part=part.replace('aom_'+op+'(','h1_'+op+'(')
  s=s[:start]+part+s[end:];p.write_text(s)
  owner='top_owner' if v=='hybrid' else 'boundary_owner'
  own_request='cdef_sync->top_slots * sizeof(int)' if v=='hybrid' else '(cdef_sync->top_slots+cdef_sync->bottom_slots)*sizeof(int)'
  snapshot='''
  {
    size_t req=0,use=0;for(int p=0;p<num_planes;p++){req+=cdef_info->allocated_linebuf_size[p];use+=h1_usable(cdef_info->linebuf[p]);}
    fprintf(stderr,"{\\"h1\\":\\"account\\",\\"rows\\":%d,\\"workers\\":%d,\\"enabled\\":%d,\\"width\\":%d,\\"height\\":%d,\\"pixel_requested\\":%zu,\\"pixel_usable\\":%zu,\\"owner_requested\\":%zu,\\"owner_usable\\":%zu,\\"row_struct_requested\\":%zu,\\"row_struct_usable\\":%zu,\\"worker_requested\\":%zu,\\"worker_usable\\":%zu,\\"sync_struct_bytes\\":%zu,\\"top_slots\\":%d,\\"bottom_slots\\":%d}\\n",
        num_mi_rows,num_workers,is_cdef_enabled,cm->width,cm->height,req,use,OWNER_REQ,OWNER_USE,
        cdef_sync->cdef_row_mt?(size_t)num_mi_rows*sizeof(*cdef_sync->cdef_row_mt):0,h1_usable(cdef_sync->cdef_row_mt),
        *cdef_worker?(size_t)num_workers*sizeof(**cdef_worker):0,h1_usable(*cdef_worker),sizeof(*cdef_sync),TOP,BOTTOM);
  }
'''
  snapshot=snapshot.replace('OWNER_REQ',own_request if v!='type_fix' else '(size_t)0').replace('OWNER_USE',f'h1_usable(cdef_sync->{owner})' if v!='type_fix' else '(size_t)0').replace('TOP','cdef_sync->top_slots' if v!='type_fix' else 'num_bufs').replace('BOTTOM','cdef_sync->bottom_slots' if v!='type_fix' else 'num_bufs')
  edit(ac,'''  alloc_cdef_row_sync(cm, &cdef_sync->cdef_row_mt,
                      cdef_info->allocated_mi_rows);''','''  alloc_cdef_row_sync(cm, &cdef_sync->cdef_row_mt,
                      cdef_info->allocated_mi_rows);'''+snapshot)
  # Serial/disabled accounting still reports its explicitly unmodified path.
  edit(ac,'  if (!is_cdef_enabled) return;','  if (!is_cdef_enabled) {\n'+snapshot+'    return;\n  }')
  edit(ac,'  if (num_workers < 2) return;','  if (num_workers < 2) {\n'+snapshot+'    return;\n  }')
  if mode=='account':continue
  edit(th,'  int is_row_done;','  int gate_active;\n  struct aom_internal_error_info *gate_error;\n  int is_row_done;')
  edit(th,'  bool cdef_mt_exit;','  int gate_fault_fired;\n  bool cdef_mt_exit;')
  # Diagnostic owner/collision inspection uses active rows, not a bottom-owner pool.
  top='cdef_sync->cdef_row_mt[*cur_fbr+1].top_slot' if v!='type_fix' else '*cur_fbr+1'
  bottom='cdef_sync->cdef_row_mt[*cur_fbr].bottom_slot' if v!='type_fix' else '*cur_fbr'
  other='cdef_sync->cdef_row_mt[r].bottom_slot' if v!='type_fix' else 'r'
  reserve='''    if(cdef_sync->cdef_row_mt[*cur_fbr].gate_active)h1_violation("double_dispatch",*cur_fbr);
    if (*cur_fbr<nvfb-1) {
      const int b=BOTTOM;
      for(int r=0;r<nvfb-1;r++)if(cdef_sync->cdef_row_mt[r].gate_active && OTHER==b)h1_violation("bottom_collision",*cur_fbr);
    }
    cdef_sync->cdef_row_mt[*cur_fbr].gate_active=1;
    fprintf(stderr,"{\\"h1\\":\\"dispatch\\",\\"row\\":%d}\\n",*cur_fbr);
'''.replace('BOTTOM',bottom).replace('OTHER',other)
  edit(tc,'    update_cdef_row_next_job_info(cdef_sync, nvfb);',reserve+'    update_cdef_row_next_job_info(cdef_sync, nvfb);')
  fault='''static void h1_fault(AV1CdefSync*s,int row,int stage){
  if(h1_env("H1_FAULT_STAGE",0)!=stage || h1_env("H1_FAULT_ROW",1)!=row)return;
#if CONFIG_MULTITHREAD
  pthread_mutex_lock(s->mutex_);
#endif
  int fire=!s->gate_fault_fired;s->gate_fault_fired=1;
#if CONFIG_MULTITHREAD
  pthread_mutex_unlock(s->mutex_);
#endif
  if(fire){fprintf(stderr,"{\\"h1\\":\\"fault\\",\\"row\\":%d,\\"stage\\":%d}\\n",row,stage);aom_internal_error(s->cdef_row_mt[row].gate_error,AOM_CODEC_ERROR,"H1 injected copy/worker fault %d",stage);}
}
static void h1_row_finish(AV1CdefSync*s,int row){
#if CONFIG_MULTITHREAD
 pthread_mutex_lock(s->mutex_);
#endif
 if(!s->cdef_row_mt[row].gate_active)h1_violation("double_release",row);
 s->cdef_row_mt[row].gate_active=0;
 fprintf(stderr,"{\\"h1\\":\\"release\\",\\"row\\":%d}\\n",row);
#if CONFIG_MULTITHREAD
 pthread_mutex_unlock(s->mutex_);
#endif
}

'''
  edit(tc,'// Hook function for each thread in CDEF multi-threading.',fault+'// Hook function for each thread in CDEF multi-threading.')
  edit(tc,'    MACROBLOCKD *xd = cdef_worker->xd;','''    cdef_sync->cdef_row_mt[cur_fbr].gate_error=error_info;
    h1_fault(cdef_sync,cur_fbr,1);
    MACROBLOCKD *xd = cdef_worker->xd;''')
  anchor='                    cdef_worker->cdef_init_fb_row_fn, cdef_sync, error_info);'
  edit(tc,anchor,anchor+'''\n    fprintf(stderr,"{\\"h1\\":\\"filter_done\\",\\"row\\":%d}\\n",(int)cur_fbr);
    h1_fault(cdef_sync,cur_fbr,4);''')
  if v!='type_fix':
   edit(tc,'    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);','    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);\n    h1_row_finish(cdef_sync,cur_fbr);\n    h1_fault(cdef_sync,cur_fbr,5);')
  else:edit(tc,'    if (cdef_worker->do_extend_border) {','    h1_row_finish(cdef_sync,cur_fbr);\n    h1_fault(cdef_sync,cur_fbr,5);\n    if (cdef_worker->do_extend_border) {')
  edit(tc,'  reset_cdef_job_info(cdef_sync);','''  for(int r=0;r<cm->cdef_info.allocated_mi_rows;r++)cdef_sync->cdef_row_mt[r].gate_active=0;
  fprintf(stderr,"{\\"h1\\":\\"frame_begin\\",\\"rows\\":%d,\\"workers\\":%d,\\"width\\":%d,\\"height\\":%d}\\n",cm->cdef_info.allocated_mi_rows,num_workers,cm->width,cm->height);
  reset_cdef_job_info(cdef_sync);''')
  edit(tc,'  sync_cdef_workers(workers, cm, num_workers);','''  sync_cdef_workers(workers, cm, num_workers);
  for(int r=0;r<cm->cdef_info.allocated_mi_rows;r++)if(cdef_sync->cdef_row_mt[r].gate_active)h1_violation("unreleased_row",r);
  fprintf(stderr,"{\\"h1\\":\\"frame_end\\"}\\n");''')
  # Copy audit is canonicalized per row/plane, but program order is retained in raw logs.
  edit(tc,'      if (fbr != nvfb - 1)  // if (fbr != 0)  // top line buffer copy','      h1_fault(cdef_sync,fbr,7);\n      if (fbr != nvfb - 1)  // if (fbr != 0)  // top line buffer copy')
  top_ptr='&top_linebuf[(fbr + 1) * CDEF_VBORDER * stride]' if v=='type_fix' else '&top_linebuf[outgoing * strip]'
  bottom_ptr='&bot_linebuf[fbr * CDEF_VBORDER * stride]' if v=='type_fix' else '&bot_linebuf[bottom * strip]'
  edit(tc,'      if (fbr != nvfb - 1)  // bottom line buffer copy',f'      if(fbr!=nvfb-1)h1_copy(fbr,plane,0,{top_ptr},(size_t)CDEF_VBORDER*stride);\n      h1_fault(cdef_sync,fbr,6);\n      if (fbr != nvfb - 1)  // bottom line buffer copy')
  marker='xd->plane[plane].dst.stride, CDEF_VBORDER, stride);\n    }'
  edit(tc,marker,marker[:-5]+f'      if(fbr!=nvfb-1)h1_copy(fbr,plane,1,{bottom_ptr},(size_t)CDEF_VBORDER*stride);\n    }}')
  edit(tc,'''  cdef_row_mt_sync_write(cdef_sync, fbr);
  cdef_row_mt_sync_read(cdef_sync, fbr);''','''  h1_fault(cdef_sync,fbr,2);
  fprintf(stderr,"{\\"h1\\":\\"signal\\",\\"row\\":%d}\\n",fbr);
  cdef_row_mt_sync_write(cdef_sync, fbr);
  h1_fault(cdef_sync,fbr,3);
  cdef_row_mt_sync_read(cdef_sync, fbr);
  fprintf(stderr,"{\\"h1\\":\\"wait_done\\",\\"row\\":%d}\\n",fbr);''')
  # Source-level allocation failures at the actual linebuf/owner allocations.
  edit(ac,'h1_malloc(cdef_info->allocated_linebuf_size[plane])','(h1_env("H1_ALLOC_PLANE",-1)==plane ? NULL : h1_malloc(cdef_info->allocated_linebuf_size[plane]))')
  if v!='type_fix':
   num='top_slots' if v=='hybrid' else 'strips';old=f'h1_calloc({num}, sizeof(*cdef_sync->{owner}))'
   edit(ac,old,f'(h1_env("H1_ALLOC_OWNER",0)?NULL:{old})')
  # Measure CDEF activation at the existing arithmetic boundary, without changing it.
  edit(cc,'    cdef_init_fb_col(xd, fb_info, level, sec_strength, fbc, fbr, plane);','''    fprintf(stderr,"{\\"h1\\":\\"activation\\",\\"row\\":%d,\\"col\\":%d,\\"plane\\":%d,\\"blocks\\":%d,\\"primary\\":%d,\\"secondary\\":%d}\\n",fbr,fbc,plane,fb_info->cdef_count,level[get_plane_type(plane)],sec_strength[get_plane_type(plane)]);
    cdef_init_fb_col(xd, fb_info, level, sec_strength, fbc, fbr, plane);''')
  print('Prepared',v,mode,flush=True)
