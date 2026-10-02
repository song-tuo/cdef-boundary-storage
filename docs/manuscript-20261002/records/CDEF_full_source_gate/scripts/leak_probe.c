#include <stdlib.h>
#include <string.h>
#include <pthread.h>
__attribute__((noinline)) static void *lose(void *unused) {
  (void)unused;
  void *p = malloc(31337);
  memset(p, 17, 31337);
  __asm__ volatile("" : : "r"(p) : "memory");
  return NULL;
}
int main(void) { pthread_t t; pthread_create(&t,NULL,lose,NULL); pthread_join(t,NULL); return 0; }
