from common import *
for v in ['type_fix','dual_token','hybrid']:
 for mode in ['audit','account']:
  dst=ROOT/'src'/(v+'_'+mode)
  def edit(n,old,new):
   p=dst/n;s=p.read_text();assert s.count(old)==1,(v,mode,n,old[:100],s.count(old));p.write_text(s.replace(old,new))
  if v!='type_fix':
   owner='top_owner' if v=='hybrid' else 'boundary_owner';expr='cdef_sync->top_slots * sizeof(int)' if v=='hybrid' else '(cdef_sync->top_slots+cdef_sync->bottom_slots)*sizeof(int)'
   p=dst/'av1/common/alloccommon.c';s=p.read_text().replace('req,use,'+expr+',','req,use,(cdef_sync->'+owner+'?'+expr+':0),');p.write_text(s)
  if mode=='account':continue
  cc='av1/common/cdef.c';tc='av1/common/thread_common.c'
  edit(cc,'    fb_info->top_linebuf[plane] =\n        &linebuf[plane][(!ping_pong) * CDEF_VBORDER * stride];','    if(fbr!=nvfb-1)h1_copy(fbr,plane,0,top_linebuf,(size_t)CDEF_VBORDER*stride);\n    fb_info->top_linebuf[plane] =\n        &linebuf[plane][(!ping_pong) * CDEF_VBORDER * stride];')
  edit(cc,'                           xd->plane[plane].dst.stride, CDEF_VBORDER, stride);\n  }\n}', '                           xd->plane[plane].dst.stride, CDEF_VBORDER, stride);\n    if(fbr!=nvfb-1)h1_copy(fbr,plane,1,fb_info->bot_linebuf[plane],(size_t)CDEF_VBORDER*stride);\n  }\n}')
  edit(cc,'  for (int fbr = 0; fbr < nvfb; fbr++)\n    av1_cdef_fb_row', '  fprintf(stderr,"{\\"h1\\":\\"frame_begin\\",\\"rows\\":%d,\\"workers\\":1,\\"width\\":%d,\\"height\\":%d}\\n",nvfb,cm->width,cm->height);\n  for (int fbr = 0; fbr < nvfb; fbr++)\n    av1_cdef_fb_row')
  edit(cc,'                    xd->error_info);\n}', '                    xd->error_info);\n  fprintf(stderr,"{\\"h1\\":\\"frame_end\\"}\\n");\n}')
  if v!='type_fix':
   owner='top_owner' if v=='hybrid' else 'boundary_owner'
   edit(tc,'    assert(slot >= 0 && slot < sync->top_slots);','    if(slot<0||slot>=sync->top_slots||sync->'+owner+'[slot]!=row)h1_violation("top_invalid_release_owner_index",row);\n    assert(slot >= 0 && slot < sync->top_slots);')
   inspect='''    for(int r=0;r<nvfb;r++)if(cdef_sync->cdef_row_mt[r].gate_active && r>0){
      int t=cdef_sync->cdef_row_mt[r].top_slot;
      if(t<0||t>=cdef_sync->top_slots||cdef_sync->OWNER[t]!=r)h1_violation("top_collision_owner_index",r);
    }
'''.replace('OWNER',owner)
   edit(tc,'    cdef_sync->cdef_row_mt[*cur_fbr].gate_active=1;', '    cdef_sync->cdef_row_mt[*cur_fbr].gate_active=1;\n'+inspect)
   if v=='dual_token':edit(tc,'    assert(slot >= 0 && slot < sync->bottom_slots);','    if(slot<0||slot>=sync->bottom_slots||sync->boundary_owner[sync->top_slots+slot]!=row)h1_violation("bottom_invalid_release_owner_index",row);\n    assert(slot >= 0 && slot < sync->bottom_slots);')
print('Observer completion: serial copies, explicit Release owner checks, NULL-owner accounting')
