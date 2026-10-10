#include "generated.hpp"
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <array>
#include <fcntl.h>
#include <sstream>
#include <string>
#include <thread>
#include <unistd.h>
int main(int argc,char**argv){
 long remaining=-1;bool realtime=false;int capture_fd=-1;uint64_t sample_index=0;
 for(int i=1;i<argc;i++){if(std::string(argv[i])=="--samples"&&i+1<argc)remaining=std::stol(argv[++i]);else if(std::string(argv[i])=="--realtime")realtime=true;else if(std::string(argv[i])=="--capture-fd"&&i+1<argc)capture_fd=std::stoi(argv[++i]);}
 if(capture_fd>=0)fcntl(capture_fd,F_SETFL,fcntl(capture_fd,F_GETFL)|O_NONBLOCK);
 fcntl(STDIN_FILENO,F_SETFL,fcntl(STDIN_FILENO,F_GETFL)|O_NONBLOCK);
 std::setvbuf(stdout,nullptr,_IONBF,0);
 LiveDSP dsp;if(realtime)dsp.target.level=0;std::string pending;char incoming[1024];float audio[256];
 auto deadline=std::chrono::steady_clock::now();
 while(remaining!=0){
  if(realtime){std::this_thread::sleep_until(deadline);auto now=std::chrono::steady_clock::now();if(now-deadline>std::chrono::milliseconds(30))deadline=now;}
  ssize_t got;while((got=read(STDIN_FILENO,incoming,sizeof(incoming)))>0){pending.append(incoming,got);if(pending.size()>8192)pending.clear();}
  size_t end;while((end=pending.find('\n'))!=std::string::npos){
   auto line=pending.substr(0,end);pending.erase(0,end+1);
   if(line=="quit")return 0;
   Parameters p=dsp.target;std::istringstream values(line);
   if(read_parameters(values,p))dsp.set(p);
  }
  int count=remaining<0?256:int(std::min<long>(256,remaining));
  // Fixed-size side-channel packets fit PIPE_BUF; a full pipe drops a
  // packet rather than delaying playback. The reader detects sample gaps.
  std::array<unsigned char,1276> packet{};size_t offset=0;
  auto append=[&](const auto& value){std::memcpy(packet.data()+offset,&value,sizeof(value));offset+=sizeof(value);};
  if(capture_fd>=0){
   append(sample_index);uint32_t frames=count;append(frames);
   auto parameters=[&](const Parameters& p){
    for(double v:{double(p.frequency),double(p.mod_rate),double(p.mod_depth),double(p.delay_ms),double(p.dry),double(p.echo),double(p.level),double(p.drive),double(p.mix),double(p.phase_frequency_1),double(p.phase_frequency_2),double(p.phase_depth),p.phase_offset})append(v);
   };
   parameters(dsp.target);parameters(dsp.current);
   for(double v:{dsp.phase,dsp.mod_phase,dsp.phase_control.first,dsp.phase_control.second})append(v);
  }
  for(int n=0;n<count;n++)audio[n]=dsp.tick();
  if(std::fwrite(audio,sizeof(float),count,stdout)!=size_t(count))return 2;
  if(capture_fd>=0){
   std::memcpy(packet.data()+offset,audio,count*sizeof(float));
   // Ignore EAGAIN: the audio pipe remains the authoritative playback path.
   if(write(capture_fd,packet.data(),packet.size())<0&&errno!=EAGAIN&&errno!=EINTR)capture_fd=-1;
  }
  sample_index+=count;
  if(remaining>0)remaining-=count;
  deadline+=std::chrono::nanoseconds(static_cast<long long>(double(count)/LiveDSP::sample_rate*1e9));
 }
}
