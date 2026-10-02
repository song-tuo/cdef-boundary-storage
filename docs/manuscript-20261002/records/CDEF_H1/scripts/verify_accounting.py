from checks import *
rows=list(csv.DictReader((ROOT/'allocation_accounting.csv').open()));checks=[]
for r in rows:
 R=int(r['R']);W=int(r['actual_W']);width=int(r['width']);strips=2*R if r['variant']=='type_fix' else min(2*R-2,2*W+1);pixel_expected=strips*2*2*(width+width//2+width//2)
 checks.append({'variant':r['variant'],'width':width,'height':int(r['height']),'R':R,'W':W,'independent_strip_count':strips,'sample_bytes':2,'CDEF_VBORDER':2,'sum_plane_strides':width*2,'expected_pixel_bytes':pixel_expected,'observed_pixel_bytes':int(r['pixel_requested']),'pass':pixel_expected==int(r['pixel_requested'])})
save(ROOT/'results/allocation_formula_check.json',checks);assert all(r['pass'] for r in checks)
print(len(checks),'independent requested-byte formula checks PASS')
