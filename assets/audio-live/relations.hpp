#pragma once
#include <algorithm>
#include <cmath>

// Memoryless nonlinear relationship, before wet mixing and master gain.
// Its caller owns parameter validation and the base-drive-zero bypass policy.
inline double waveshape(double signal, double drive, int kind) {
    return kind == 0 ? std::tanh(drive * signal)
                     : std::clamp(drive * signal, -1.0, 1.0);
}

constexpr double signal_tau = 6.2831853071795864769;
inline double wrapped_difference(double angle) {
    double result = std::fmod(angle + signal_tau/2, signal_tau);
    if (result < 0) result += signal_tau;
    return result - signal_tau/2;
}

struct PhaseRelationship {
    double first = 0, second = 0;
    // Call once per emitted sample, independently of block boundaries.
    // Frequencies are finite and in [0, Fs/2) after declaration/control bounds.
    void advance(double frequency1, double frequency2, double rate, bool shared) {
        first += signal_tau*frequency1/rate;
        if (first >= signal_tau) first -= signal_tau;
        if (shared) second = first;
        else {
            second += signal_tau*frequency2/rate;
            if (second >= signal_tau) second -= signal_tau;
        }
    }
    double difference(double offset) const { return wrapped_difference(first-second-offset); }
    double alignment(double offset) const { return std::cos(difference(offset)); }
};
