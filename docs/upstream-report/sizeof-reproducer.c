#include <stdint.h>
#include <stdio.h>

/* Minimal reproduction of the upstream CdefInfo member and sizeof operand. */
struct cdef_info_excerpt {
  uint16_t *linebuf[3];
};

int main(void) {
  struct cdef_info_excerpt info = { { 0 } };
  struct cdef_info_excerpt *cdef_info = &info;
  const size_t rows = 34;
  const size_t two_vertical_borders = 4;
  const size_t sum_plane_strides = 3840 + 1920 + 1920;
  const size_t samples = rows * two_vertical_borders * sum_plane_strides;
  printf("upstream operand bytes: %zu\n", sizeof(*cdef_info->linebuf));
  printf("sample element bytes: %zu\n", sizeof(**cdef_info->linebuf));
  printf("4K row-indexed requested bytes: %zu\n",
         samples * sizeof(*cdef_info->linebuf));
  printf("4K type-corrected requested bytes: %zu\n",
         samples * sizeof(**cdef_info->linebuf));
  return 0;
}
