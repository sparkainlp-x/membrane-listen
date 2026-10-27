"""membrane-listen: hear inside the membrane (synthetic sonification).

What this is: a sensor inside a phase-oscillator membrane reads the
local vibration, and that reading is turned into sound. The mapping
is stated plainly, because it is a choice, not a discovery:

  - audio sample  = cos(sensor phase) * local coherence
  - pitch         = local phase velocity (omega), measured, not set
  - direction     = phase gradient sign (k_est), reported numerically
                    and, in the stereo wave file, as the phase
                    difference between two sensors a quarter-ring apart
  - clarity       = local coherence (locked ~0.99 = loud, noisy = quiet)

Scenes
------
1. Travelling wave (Kuramoto ring, same dynamics as
   membrane-propulsion): sensor at position 10, k=+1 vs k=-1.
   Both tones have the same pitch (omega = -drive_omega in both
   cases); what flips is the gradient sign.
2. Heart beat (pulse chain, NOT an ECG): a pacemaker fires every
   0.80 s, the pulse travels one node per 0.01 s, a sensor at node 32
   hears it 0.32 s later as a decaying 55 Hz thump. Five thumps in
   4 s. Labels are toy labels, not anatomy.
3. Brain spread (two pulse chains, stereo, NOT neural recording):
   left chain 32 nodes, right chain 32 nodes, cross delay 0.12 s.
   Left sensor (node 16) hears the pulse 0.16 s after firing; right
   sensor (node 16 of the right chain) hears it 0.59 s after firing.
   The stereo file puts left sensor on the left channel and right
   sensor on the right channel, so the wave is heard moving
   left -> right, 0.43 s apart.

Honest limits, kept in README and DESIGN: no sound pressure exists
in any of these models; the audio is a sonification of phase, not a
recording. Nothing here is a heart, a brain, an ECG, or a diagnosis.
Standard library only (wave, struct, math). AGPL-3.0-only.
"""

import cmath
import math
import struct
import wave

TWO_PI = 2.0 * math.pi
SAMPLE_RATE = 8000


def wrap(angle):
    while angle > math.pi:
        angle -= TWO_PI
    while angle <= -math.pi:
        angle += TWO_PI
    return angle


# ---------------------------------------------------------------- ring
class Ring:
    """Kuramoto ring with a travelling drive (propulsion dynamics)."""

    def __init__(self, n=64, coupling=2.0, drive_amp=1.5, drive_k=1,
                 drive_omega=1.0, dt=0.05, seed=42):
        import random
        self.n = n
        self.coupling = coupling
        self.drive_amp = drive_amp
        self.drive_k = drive_k
        self.drive_omega = drive_omega
        self.dt = dt
        self.t = 0.0
        rng = random.Random(seed)
        self.theta = [rng.uniform(-math.pi, math.pi) for _ in range(n)]

    def _drive_phase(self, i):
        return self.drive_k * TWO_PI * i / self.n - self.drive_omega * self.t

    def wave_order(self):
        re = sum(math.cos(self.theta[i] - self._drive_phase(i))
                 for i in range(self.n)) / self.n
        im = sum(math.sin(self.theta[i] - self._drive_phase(i))
                 for i in range(self.n)) / self.n
        return math.hypot(re, im)

    def step(self):
        n, dt = self.n, self.dt
        new = []
        for i in range(n):
            coupling_term = (math.sin(self.theta[(i - 1) % n] - self.theta[i])
                             + math.sin(self.theta[(i + 1) % n] - self.theta[i])) / 2.0
            drive_term = self.drive_amp * math.sin(self._drive_phase(i) - self.theta[i])
            new.append(self.theta[i] + dt * (self.coupling * coupling_term + drive_term))
        self.theta = [wrap(th) for th in new]
        self.t += dt


# ---------------------------------------------------------------- sensor
class Sensor:
    """Passive, read-only vibration sensor (propulsion v0.2.0 logic)."""

    def __init__(self, ring, position=0.0, window=2):
        self.ring = ring
        self.position = position % ring.n
        self.window = window
        self._prev_phase = None
        self._prev_t = None

    def sample(self):
        n = self.ring.n
        i = int(self.position) % n
        j = (i + 1) % n
        f = self.position - int(self.position)
        z = (1.0 - f) * cmath.exp(1j * self.ring.theta[i]) \
            + f * cmath.exp(1j * self.ring.theta[j])
        phase = cmath.phase(z)
        gradient = wrap(self.ring.theta[j] - self.ring.theta[i])
        total = sum(cmath.exp(1j * self.ring.theta[(i + d) % n])
                    for d in range(-self.window, self.window + 1))
        coherence = abs(total) / (2 * self.window + 1)
        if self._prev_phase is None:
            omega = 0.0
        else:
            dt = self.ring.t - self._prev_t
            omega = wrap(phase - self._prev_phase) / dt if dt else 0.0
        reading = {"t": self.ring.t, "phase": phase, "omega": omega,
                   "gradient": gradient, "k_est": gradient * n / TWO_PI,
                   "coherence": coherence,
                   "signal": math.cos(phase) * coherence}
        self._prev_phase = phase
        self._prev_t = self.ring.t
        return reading


def record_ring(drive_k, warmup=200, steps=16000, position=10.0, seed=42):
    """Warm up, then record sensor readings, one per step."""
    ring = Ring(drive_k=drive_k, seed=seed)
    for _ in range(warmup):
        ring.step()
    sensor = Sensor(ring, position=position)
    readings = []
    for _ in range(steps):
        ring.step()
        readings.append(sensor.sample())
    return ring, sensor, readings


# ---------------------------------------------------------------- pulses
def pulse_train(duration, period, delay, tau=640, freq_hz=55.0,
                sample_rate=SAMPLE_RATE):
    """Decaying thump train: pacemaker fires every `period` samples,
    the pulse reaches the sensor `delay` samples after each firing.
    All units are audio samples unless named otherwise."""
    out = [0.0] * duration
    arrival = delay
    while arrival < duration:
        for s in range(arrival, min(duration, arrival + 6 * tau)):
            age = s - arrival
            out[s] += math.exp(-age / tau) * math.sin(
                TWO_PI * freq_hz * age / sample_rate)
        arrival += period
    return out


def heart_signal(duration=32000, period=6400, delay=2560):
    """Pacemaker every 0.80 s, sensor hears it 0.32 s later."""
    return pulse_train(duration, period, delay)


def brain_signals(duration=38400, period=9600):
    """Left sensor delay 0.16 s, right sensor delay 0.59 s.
    Returns (left, right); the 0.43 s gap is the spread delay."""
    left = pulse_train(duration, period, delay=1280)
    right = pulse_train(duration, period, delay=4720)
    return left, right


# ---------------------------------------------------------------- wav io
def _to_int16(samples):
    return [max(-32767, min(32767, int(round(s * 32767)))) for s in samples]


def write_wav_mono(path, samples, sample_rate=SAMPLE_RATE):
    frames = _to_int16(samples)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    return len(frames)


def write_wav_stereo(path, left, right, sample_rate=SAMPLE_RATE):
    li, ri = _to_int16(left), _to_int16(right)
    frames = [v for pair in zip(li, ri) for v in pair]
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    return len(li)


def read_wav(path):
    with wave.open(path, "rb") as w:
        return w.getnchannels(), w.getframerate(), w.getnframes()
