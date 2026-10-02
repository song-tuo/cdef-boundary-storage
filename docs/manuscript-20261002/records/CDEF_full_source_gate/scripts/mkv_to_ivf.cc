// Lossless packet extraction using the release's bundled Matroska parser.
#include "mkvparser/mkvparser.h"
#include "mkvparser/mkvreader.h"
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <vector>
static void le(FILE *f,uint64_t n,int bytes) { for(int i=0;i<bytes;++i){fputc(n&255,f);n>>=8;} }
int main(int argc,char **argv) {
  if(argc!=3)return 2;
  mkvparser::MkvReader reader;assert(reader.Open(argv[1])==0);
  long long pos=0;mkvparser::EBMLHeader head;assert(head.Parse(&reader,pos)>=0);
  mkvparser::Segment *seg=nullptr;assert(!mkvparser::Segment::CreateInstance(&reader,pos,seg));assert(seg->Load()>=0);
  const mkvparser::Tracks *tracks=seg->GetTracks();const mkvparser::VideoTrack *video=nullptr;
  for(unsigned long i=0;i<tracks->GetTracksCount();++i) {
    const mkvparser::Track *t=tracks->GetTrackByIndex(i);
    if(t->GetType()==mkvparser::Track::kVideo){video=static_cast<const mkvparser::VideoTrack*>(t);break;}
  }
  assert(video && !strcmp(video->GetCodecId(),"V_AV1"));
  FILE *out=fopen(argv[2],"wb");assert(out);fwrite("DKIF",1,4,out);le(out,0,2);le(out,32,2);fwrite("AV01",1,4,out);
  le(out,video->GetWidth(),2);le(out,video->GetHeight(),2);le(out,30,4);le(out,1,4);le(out,0,4);le(out,0,4);
  uint64_t count=0;
  for(const mkvparser::Cluster *c=seg->GetFirst();c && !c->EOS();c=seg->GetNext(c)) {
    const mkvparser::BlockEntry *entry=nullptr;assert(!c->GetFirst(entry));
    while(entry && !entry->EOS()) {
      const mkvparser::Block *b=entry->GetBlock();assert(b);
      if(b->GetTrackNumber()==video->GetNumber())for(int i=0;i<b->GetFrameCount();++i) {
        const auto &frame=b->GetFrame(i);std::vector<unsigned char> data(frame.len);assert(!frame.Read(&reader,data.data()));
        le(out,data.size(),4);le(out,count++,8);assert(fwrite(data.data(),1,data.size(),out)==data.size());
      }
      const mkvparser::BlockEntry *next=nullptr;assert(!c->GetNext(entry,next));entry=next;
    }
  }
  fseek(out,24,SEEK_SET);le(out,count,4);fclose(out);delete seg;reader.Close();
  printf("%llu packets extracted unchanged\n",(unsigned long long)count);return 0;
}
