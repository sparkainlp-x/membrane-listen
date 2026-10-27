"""membrane-listen: SYNTHETIC sonification of a phase-oscillator membrane.

Classical, standard-library-only simulation. Not a recording, not a
medical model.
"""

from .core import SAMPLE_RATE, TWO_PI, Ring, Sensor, record_ring, wrap
from .pulses import brain_signals, heart_signal, pulse_train
from .wavio import (_to_int16, read_wav, write_wav_mono,
                    write_wav_stereo)

__version__ = "0.1.0"
