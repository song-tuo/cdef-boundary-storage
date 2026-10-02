#include <aom/aom_decoder.h>
#include <aom/aomdx.h>
#include <CommonCrypto/CommonDigest.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>

typedef struct { unsigned char *p; size_t n; } Packet;
static uint32_t le32(const unsigned char *p) {
  return p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static uint64_t now(void) {
  struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return (uint64_t)t.tv_sec*1000000000 + t.tv_nsec;
}
static void image_hash(CC_SHA256_CTX *hash, const aom_image_t *im, uint64_t *bytes) {
  int bps=(im->fmt&AOM_IMG_FMT_HIGHBITDEPTH)?2:1;
  for (int p=0;p<(im->monochrome?1:3);++p) {
    unsigned w=im->d_w, h=im->d_h;
    if (p) { w=(w+(1u<<im->x_chroma_shift)-1)>>im->x_chroma_shift;
             h=(h+(1u<<im->y_chroma_shift)-1)>>im->y_chroma_shift; }
    for (unsigned y=0;y<h;++y) {
      CC_SHA256_Update(hash,im->planes[p]+(size_t)y*im->stride[p],w*bps);
      *bytes+=(uint64_t)w*bps;
    }
  }
}
int main(int argc,char **argv) {
  if(argc!=4) { fprintf(stderr,"usage: ivf_gate input.ivf threads row_mt\n"); return 2; }
  FILE *f=fopen(argv[1],"rb"); if(!f)return 2;
  unsigned char hdr[32]; if(fread(hdr,1,32,f)!=32 || memcmp(hdr,"DKIF",4))return 2;
  Packet *packets=NULL; size_t count=0; int truncated=0;
  for(;;) {
    unsigned char ph[12]; size_t n=fread(ph,1,12,f); if(!n)break;
    if(n!=12){truncated=1;break;}
    uint32_t size=le32(ph); if(size>268435456){truncated=1;break;}
    unsigned char *data=malloc(size?size:1); if(!data)return 2;
    n=fread(data,1,size,f);
    Packet *next=realloc(packets,(count+1)*sizeof(*packets)); if(!next)return 2;
    packets=next; packets[count++]=(Packet){data,n};
    if(n!=size){truncated=1;break;}
  }
  fclose(f);
  aom_codec_ctx_t ctx={0}; aom_codec_dec_cfg_t cfg={0}; cfg.threads=atoi(argv[2]); cfg.allow_lowbitdepth=1;
  int status=aom_codec_dec_init(&ctx,aom_codec_av1_dx(),&cfg,0);
  if(status)return 3;
  status=aom_codec_control(&ctx,AV1D_SET_ROW_MT,atoi(argv[3]));
  CC_SHA256_CTX hash; CC_SHA256_Init(&hash);
  uint64_t decode_ns=0,frames=0,bytes=0,decoded_packets=0;
  unsigned depth=0,ssx=0,ssy=0,mono=0;
  const char *delay_s=getenv("CDEF_GATE_DELAY_NS"); uint64_t delay=delay_s?strtoull(delay_s,NULL,10):0;
  uint64_t begin=now();
  for(size_t i=0;!status && i<=count;++i) {
    uint64_t start=now();
    status=aom_codec_decode(&ctx,i<count?packets[i].p:NULL,i<count?packets[i].n:0,NULL);
    if(delay && i<count) {
      struct timespec req={(time_t)(delay/1000000000),(long)(delay%1000000000)};
      while(nanosleep(&req,&req)){}
    }
    decode_ns+=now()-start;
    if(status) { fprintf(stderr,"codec_error=%d detail=%s\n",status,aom_codec_error_detail(&ctx)?aom_codec_error_detail(&ctx):aom_codec_error(&ctx)); break; }
    if(i<count)++decoded_packets;
    aom_codec_iter_t it=NULL; aom_image_t *im;
    while((im=aom_codec_get_frame(&ctx,&it))) {
      depth=im->bit_depth;ssx=im->x_chroma_shift;ssy=im->y_chroma_shift;mono=im->monochrome;
      CC_SHA256_CTX one;CC_SHA256_Init(&one);uint64_t onebytes=0;image_hash(&one,im,&onebytes);
      unsigned char od[32];char oh[65];CC_SHA256_Final(od,&one);for(int z=0;z<32;z++)sprintf(oh+2*z,"%02x",od[z]);oh[64]=0;
      fprintf(stderr,"{\"h1\":\"visible_frame\",\"index\":%llu,\"width\":%u,\"height\":%u,\"sha256\":\"%s\"}\n",(unsigned long long)frames,im->d_w,im->d_h,oh);
      image_hash(&hash,im,&bytes); ++frames;
    }
  }
  uint64_t elapsed=now()-begin;
  int destroyed=getenv("CDEF_GATE_SKIP_DESTROY") ? -1 : aom_codec_destroy(&ctx);
  for(size_t i=0;i<count;++i)free(packets[i].p); free(packets);
  unsigned char digest[32]; CC_SHA256_Final(digest,&hash); char hex[65];
  for(int i=0;i<32;++i)sprintf(hex+i*2,"%02x",digest[i]);hex[64]=0;
  struct rusage usage; getrusage(RUSAGE_SELF,&usage);
  printf("{\"status\":%d,\"destroy_status\":%d,\"input_packets\":%zu,\"decoded_packets\":%"PRIu64",\"output_frames\":%"PRIu64",\"output_bytes\":%"PRIu64",\"pixel_sha256\":\"%s\",\"decode_ns\":%"PRIu64",\"elapsed_with_hash_ns\":%"PRIu64",\"peak_rss_bytes\":%ld,\"truncated_input\":%d,\"bit_depth\":%u,\"subsampling_x\":%u,\"subsampling_y\":%u,\"monochrome\":%u}\n",status,destroyed,count,decoded_packets,frames,bytes,hex,decode_ns,elapsed,usage.ru_maxrss,truncated,depth,ssx,ssy,mono);
  return status||destroyed?3:truncated?4:0;
}
