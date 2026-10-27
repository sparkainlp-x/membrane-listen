"""Shim kept from the supplied package: builds the WAV files in ./wav.

Equivalent to ``python -m membrane_listen --out wav`` run from the
repository root.
"""

import os
import sys

from membrane_listen.__main__ import main

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main(["--out", os.path.join(here, "wav")]))
