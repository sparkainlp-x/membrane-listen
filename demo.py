"""membrane-listen demo: build all four WAV files and print the numbers."""

import os

from membrane_listen import (Ring, Sensor, brain_signals, heart_signal,
                             record_ring, write_wav_mono, write_wav_stereo)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "wav")
os.makedirs(OUT, exist_ok=True)


def main():
    print("membrane-listen demo (seed 42, sample rate 8000 Hz)")
    print()
    # 1. Travelling wave, forward and reverse.
    for label, k in (("forward  k=+1", 1), ("reverse  k=-1", -1)):
        ring, sensor, readings = record_ring(drive_k=k)
        last = readings[-1]
        path = os.path.join(OUT, "wave_%s.wav" % ("forward" if k == 1 else "reverse"))
        n = write_wav_mono(path, [r["signal"] for r in readings])
        print(f"  wave {label}: k_est {last['k_est']:+.2f}  omega {last['omega']:+.3f}  "
              f"coherence {last['coherence']:.3f}  wave-order {ring.wave_order():.3f}  "
              f"{n} frames = {n / 8000:.1f} s -> {os.path.basename(path)}")
    # Stereo wave: two sensors a quarter-ring apart; their phase
    # difference is +pi/2 for k=+1, -pi/2 for k=-1.
    for label, k in (("forward", 1), ("reverse", -1)):
        ring = Ring(drive_k=k)
        for _ in range(200):
            ring.step()
        sa, sb = Sensor(ring, position=10.0), Sensor(ring, position=26.0)
        left, right = [], []
        for _ in range(16000):
            ring.step()
            left.append(sa.sample()["signal"])
            right.append(sb.sample()["signal"])
        path = os.path.join(OUT, "wave_stereo_%s.wav" % label)
        write_wav_stereo(path, left, right)
        print(f"  wave stereo {label}: sensors 10 and 26, phase gap "
              f"{'+' if k == 1 else '-'}pi/2 by construction -> {os.path.basename(path)}")
    # 2. Heart beat.
    heart = heart_signal()
    n = write_wav_mono(os.path.join(OUT, "heart.wav"), heart)
    print(f"  heart: pacemaker every 0.80 s, sensor delay 0.32 s, "
          f"5 thumps in {n / 8000:.1f} s -> heart.wav")
    # 3. Brain spread, stereo.
    left, right = brain_signals()
    n = write_wav_stereo(os.path.join(OUT, "brain_stereo.wav"), left, right)
    print(f"  brain: left sensor 0.16 s, right sensor 0.59 s, "
          f"spread delay 0.43 s, {n / 8000:.1f} s stereo -> brain_stereo.wav")
    print()
    print("Listen in order: wave_forward, wave_reverse (same pitch,")
    print("opposite gradient), heart (thumps), brain_stereo (left,")
    print("then right). Synthetic sonification only, not a recording.")


if __name__ == "__main__":
    main()
