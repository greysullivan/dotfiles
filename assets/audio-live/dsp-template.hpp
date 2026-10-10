#pragma once
#include <algorithm>
#include <cmath>
#include <istream>
#include <limits>
#include <vector>
#include "relations.hpp"
struct Parameters {
 float frequency=@FREQUENCY@,mod_rate=@MOD_RATE@,mod_depth=@MOD_DEPTH@,delay_ms=@DELAY_MS@,dry=@DRY@,echo=@ECHO@,level=@LEVEL@;
 float drive=@DRIVE@,mix=@MIX@;
 float phase_frequency_1=@PHASE_FREQUENCY_1@,phase_frequency_2=@PHASE_FREQUENCY_2@,phase_depth=@PHASE_DEPTH@;
 double phase_offset=@PHASE_OFFSET@;
};
inline bool read_parameters(std::istream& values, Parameters& p) {
 if (!(values >> p.frequency >> p.mod_rate >> p.mod_depth >> p.delay_ms >> p.dry >> p.echo >> p.level)) return false;
 values >> std::ws;
 if (!values.eof()) {
  if (!(values >> p.drive >> p.mix)) return false;
  values >> std::ws;
  if (!values.eof()) {
   if (!(values >> p.phase_frequency_1 >> p.phase_frequency_2 >> p.phase_depth >> p.phase_offset)) return false;
   values >> std::ws;
  }
 }
 return values.eof() && std::isfinite(p.frequency) && std::isfinite(p.mod_rate) && std::isfinite(p.mod_depth)
  && std::isfinite(p.delay_ms) && std::isfinite(p.dry) && std::isfinite(p.echo) && std::isfinite(p.level)
  && std::isfinite(p.drive) && std::isfinite(p.mix) && std::isfinite(p.phase_frequency_1)
  && std::isfinite(p.phase_frequency_2) && std::isfinite(p.phase_depth) && std::isfinite(p.phase_offset);
}
struct LiveDSP {
 static constexpr int sample_rate=@SR@;
 static constexpr unsigned capacity=@CAPACITY@;
 static constexpr float max_delay_ms=@MAX_DELAY_MS@;
 static constexpr bool shaping_enabled=@SHAPING_ENABLED@;
 static constexpr int shape_kind=@SHAPE_KIND@;
 static constexpr bool phase_enabled=@PHASE_ENABLED@,shared_clock=@SHARED_CLOCK@;
 std::vector<float> history=std::vector<float>(capacity,0);
 unsigned position=0;
 double phase=0,mod_phase=0;
 PhaseRelationship phase_control;
 Parameters target,current;
 LiveDSP(){current.level=0;}
 void set(Parameters p){
  if (!(std::isfinite(p.frequency) && std::isfinite(p.mod_rate) && std::isfinite(p.mod_depth)
   && std::isfinite(p.delay_ms) && std::isfinite(p.dry) && std::isfinite(p.echo) && std::isfinite(p.level)
   && std::isfinite(p.drive) && std::isfinite(p.mix) && std::isfinite(p.phase_frequency_1)
   && std::isfinite(p.phase_frequency_2) && std::isfinite(p.phase_depth) && std::isfinite(p.phase_offset))) return;
  target.frequency=std::clamp(p.frequency,40.f,2000.f);
  target.mod_rate=std::clamp(p.mod_rate,0.1f,20.f);
  target.mod_depth=std::clamp(p.mod_depth,0.f,500.f);
  target.delay_ms=std::clamp(p.delay_ms,10.f,max_delay_ms);
  target.dry=std::clamp(p.dry,0.f,1.f);target.echo=std::clamp(p.echo,0.f,1.f);
  target.level=std::clamp(p.level,0.f,0.3f);
  target.drive=std::clamp(p.drive,0.f,16.f);target.mix=std::clamp(p.mix,0.f,1.f);
  target.phase_frequency_1=std::clamp(p.phase_frequency_1,0.f,10000.f);
  target.phase_frequency_2=shared_clock ? target.phase_frequency_1 : std::clamp(p.phase_frequency_2,0.f,10000.f);
  target.phase_depth=std::clamp(p.phase_depth,0.f,std::min(target.drive,16.f-target.drive));
  target.phase_offset=std::clamp(p.phase_offset,-signal_tau/2,signal_tau/2);
 }
 double effective_drive() const {
  if constexpr (phase_enabled) {
   double amplitude=std::min(double(current.phase_depth),std::min(double(current.drive),16.-current.drive));
   return std::clamp(current.drive+amplitude*phase_control.alignment(current.phase_offset),0.,16.);
  }
  return current.drive;
 }
 float tick(){
  // A 10-ms exponential time constant for controls (approximately).
  constexpr float smoothing=@SMOOTH@;
  current.frequency+=smoothing*(target.frequency-current.frequency);
  current.mod_rate+=smoothing*(target.mod_rate-current.mod_rate);
  current.mod_depth+=smoothing*(target.mod_depth-current.mod_depth);
  current.delay_ms+=smoothing*(target.delay_ms-current.delay_ms);
  current.dry+=smoothing*(target.dry-current.dry);
  current.echo+=smoothing*(target.echo-current.echo);
  current.level+=smoothing*(target.level-current.level);
  if constexpr (shaping_enabled) {
   // Zero BASE drive is an explicit bypass. Fade out before clearing drive;
   // while enabling, establish a positive drive before raising the wet mix.
   float wet_target=target.drive==0 ? 0 : target.mix;
   if (target.drive>0) {
    if (current.drive==0) current.drive=target.drive;
    else current.drive+=smoothing*(target.drive-current.drive);
   }
   current.mix+=smoothing*(wet_target-current.mix);
   if (std::abs(current.mix-wet_target)<=std::numeric_limits<float>::epsilon()) current.mix=wet_target;
   if (target.drive==0 && current.mix==0) current.drive=0;
  }
  if constexpr (phase_enabled) {
   current.phase_frequency_1+=smoothing*(target.phase_frequency_1-current.phase_frequency_1);
   current.phase_frequency_2+=smoothing*(target.phase_frequency_2-current.phase_frequency_2);
   current.phase_depth+=smoothing*(target.phase_depth-current.phase_depth);
   // Smooth angular offsets along the shortest wrapped arc.
   current.phase_offset+=smoothing*wrapped_difference(target.phase_offset-current.phase_offset);
   current.phase_offset=wrapped_difference(current.phase_offset);
   phase_control.advance(current.phase_frequency_1,current.phase_frequency_2,sample_rate,shared_clock);
  }
  double frequency=std::clamp(double(current.frequency)+current.mod_depth*std::sin(mod_phase),1.,10000.);
  constexpr double tau=6.2831853071795864769;
  phase+=tau*frequency/sample_rate;if(phase>=tau)phase-=tau;
  mod_phase+=tau*current.mod_rate/sample_rate;if(mod_phase>=tau)mod_phase-=tau;
  float input=float(std::sin(phase));
  float read=float(position)-current.delay_ms*(sample_rate/1000.f);
  if(read<0)read+=capacity;
  unsigned i=unsigned(read);float fraction=read-i;
  float delayed=history[i]*(1-fraction)+history[(i+1)&(capacity-1)]*fraction;
  float output=current.level*(current.dry*input+current.echo*delayed);
  if constexpr (shaping_enabled) {
   if (current.drive>0 && current.mix>0) {
    float signal=current.dry*input+current.echo*delayed;
    output=current.level*float((1.-current.mix)*signal+current.mix*waveshape(signal,effective_drive(),shape_kind));
   }
  }
  history[position]=input;position=(position+1)&(capacity-1);
  return output;
 }
};
