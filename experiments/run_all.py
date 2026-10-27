"""Run every study over a seed set and write a JSON summary.

    python -m experiments.run_all --set dev --out docs/results/dev.json
    python -m experiments.run_all --set confirm --out docs/results/confirm.json

Outputs are deterministic given the code and the seed set (values are
rounded to 6 decimals). Hypotheses are the 23 listed in docs/PROTOCOL.md.
"""

import argparse
import json
import multiprocessing
import platform
import sys

from membrane_listen import __version__
from membrane_listen.stats import bootstrap_ci, bootstrap_p, holm, rng_for

from .common import SEED_SETS
from .studies import replicate

# (id, key, null, alternative, statement)
HYPOTHESES = [
    ("H1", "A/om1/pv_relerr", 0.01, "less",
     "at Omega 1 the pv pitch error is below 1 %"),
    ("H2", "A/om32/pv_relerr", 0.01, "less",
     "at Omega 32 (inside the Euler limit) the pv error is below 1 %"),
    ("H3", "A/om48/pv_relerr", 0.05, "greater",
     "at Omega 48 (beyond the Euler limit, below Nyquist) the pv error "
     "exceeds 5 %"),
    ("H4", "A/sig1/pv_relerr", 0.05, "less",
     "at noise 1 the pv pitch error is below 5 %"),
    ("H5", "A/sig1/diff_fft_minus_pv", 0.0, "greater",
     "at noise 1 the pv estimator is more accurate than the fft estimator"),
    ("H6", "B/s0/win_acc", 0.99, "greater",
     "direction accuracy of the long-window estimator exceeds 0.99 "
     "without noise"),
    ("H7", "B/s1/last_acc", 0.75, "less",
     "with noise 1 the single-reading direction accuracy is below 0.75"),
    ("H8", "B/s1/diff_win_minus_last", 0.0, "greater",
     "with noise 1 the long-window estimator beats the single-reading one"),
    ("H9", "B/lockloss_a0.5/win_acc", 0.99, "less",
     "with the drive weaker than its frequency (A 0.5) direction is not "
     "recovered reliably"),
    ("H10", "B/d32/sign_acc", 0.5, "two-sided",
     "at d = n/2 the gap sign is at chance (equivalence rule)"),
    ("H11", "B/d16/gap_err", 0.01, "less",
     "at d = 16 and no noise the mean gap error is below 0.01 rad"),
    ("H12", "C/undriven_coupled/coherence", 0.9, "greater",
     "the undriven coupled ring still shows local coherence above 0.9"),
    ("H13", "C/undriven_uncoupled/coherence", 0.6, "less",
     "the undriven uncoupled ring has coherence below 0.6"),
    ("H14", "C/undriven_coupled/wave_order", 0.3, "less",
     "the undriven ring has wave-order below 0.3"),
    ("H15", "C/corr_coh_rms", 0.9, "greater",
     "audio RMS tracks coherence across noise levels (Pearson above 0.9)"),
    ("H16", "C/s0/coherence", 0.98, "greater",
     "driven, no noise: coherence above 0.98 (the README says 0.990)"),
    ("H17", "D1/low_speeds/abs_err", 0.01, "less",
     "moving-sensor shift agrees with the derivation within 0.01 rad per "
     "time unit"),
    ("H18", "D1/frozen/hz", 1.0, "less",
     "at the frozen-phase speed the pitch is below 1 Hz"),
    ("H19", "D2/sign_acc", 0.99, "greater",
     "three sensors on the torus recover both wave-vector signs"),
    ("H20", "D2/xpair_ky_leak", 0.01, "less",
     "the x pair's gap does not depend on ky (difference below 0.01 rad)"),
    ("H21", "F1/shuffle_acc", 0.5, "two-sided",
     "a shuffled-phase sensor gives no direction (equivalence rule)"),
    ("H22", "B/audio_lag/sign_acc", 0.99, "greater",
     "the audio-only lag gets the direction right"),
    ("H23", "B/audio_lag_reversed/flip_acc", 0.99, "greater",
     "time-reversed audio gives the opposite lag sign, as the design says"),
]

EQUIVALENCE = {"H10": (0.40, 0.60), "H21": (0.45, 0.55)}


def _summ(args):
    key, vals, resamples = args
    m, lo, hi = bootstrap_ci(vals, rng_for("boot", key), resamples)
    return key, {"mean": round(m, 6), "lo": round(lo, 6), "hi": round(hi, 6)}


def _test(args):
    hid, key, null, alt, vals, resamples = args
    return hid, bootstrap_p(vals, null, rng_for("boot", "test", hid),
                            resamples, alt)


def supported(hid, p_holm, row):
    """Protocol rule; H10 and H21 are equivalence-type controls."""
    if hid in EQUIVALENCE:
        lo, hi = EQUIVALENCE[hid]
        return p_holm >= 0.05 and row["lo"] >= lo and row["hi"] <= hi
    return p_holm < 0.05


def run(set_name, jobs, ci_resamples, test_resamples):
    seeds = SEED_SETS[set_name]
    ctx = multiprocessing.get_context("fork") if jobs > 1 else None
    if jobs > 1:
        with ctx.Pool(jobs) as pool:
            reps = pool.map(replicate, seeds, chunksize=1)
    else:
        reps = [replicate(s) for s in seeds]
    keys = sorted(reps[0])
    assert all(sorted(r) == keys for r in reps), "replicates disagree on keys"
    series = {k: [r[k] for r in reps] for k in keys}
    work = [(k, series[k], ci_resamples) for k in keys]
    rows = dict(map(_summ, work))
    tests = [(hid, key, null, alt, series[key], test_resamples)
             for hid, key, null, alt, _ in HYPOTHESES]
    pvals = dict(map(_test, tests))
    adj = holm([pvals[h[0]] for h in HYPOTHESES])
    hyps = []
    for (hid, key, null, alt, text), a in zip(HYPOTHESES, adj):
        row = rows[key]
        hyps.append({
            "id": hid, "key": key, "null": null, "alternative": alt,
            "statement": text, "mean": row["mean"], "lo": row["lo"],
            "hi": row["hi"], "p": round(pvals[hid], 6),
            "p_holm": round(a, 6), "supported": supported(hid, a, row),
        })
    return {
        "meta": {
            "set": set_name, "seeds": [seeds[0], seeds[-1]],
            "replicates": len(seeds), "version": __version__,
            "ci_resamples": ci_resamples, "test_resamples": test_resamples,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "protocol": "docs/PROTOCOL.md", "synthetic": True,
        },
        "hypotheses": hyps,
        "rows": {k: rows[k] for k in keys},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=sorted(SEED_SETS), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args(argv)
    smoke = args.set == "smoke"
    result = run(args.set, 1 if smoke else args.jobs,
                 200 if smoke else 5000, 500 if smoke else 10000)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {args.out}: {len(result['rows'])} rows, "
          f"{result['meta']['replicates']} replicates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
