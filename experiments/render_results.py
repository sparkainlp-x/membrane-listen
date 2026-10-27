"""Render docs/RESULTS.md from the committed JSON summaries.

    python -m experiments.render_results            # write docs/RESULTS.md
    python -m experiments.render_results --check    # fail if it differs

Tables are generated; interpretation is hand-written in
docs/interpretation.md and appended unchanged.
"""

import argparse
import json
import os
import sys

from .common import (COH_SIGMAS, DIR_SIGMAS, GAP_SIGMAS, LOCK_AMPS, OMEGAS,
                     PITCH_SIGMAS, RING_SIZES, SEPARATIONS, SPEEDS, tok)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")


def load(name):
    path = os.path.join(DOCS, "results", name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def num(x, nd):
    text = f"{x:.{nd}f}"
    return text[1:] if text.startswith("-") and float(text) == 0 else text


def ci(row, nd=3):
    return (f"{num(row['mean'], nd)} [{num(row['lo'], nd)}, "
            f"{num(row['hi'], nd)}]")


def table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def outcome(h):
    if h["id"] in ("H10", "H21"):
        return ("control retained (consistent with chance)" if h["supported"]
                else "control NOT retained")
    return "supported" if h["supported"] else "NOT supported"


def hyp_table(res):
    rows = []
    for h in res["hypotheses"]:
        rows.append([h["id"], h["statement"], f"`{h['key']}`", ci(h, 4),
                     f"{h['alternative']} {h['null']:g}",
                     f"{h['p_holm']:.4f}", outcome(h)])
    return table(["ID", "Statement", "Key", "Mean [95 % CI]", "Test vs null",
                  "Holm p", "Outcome"], rows)


def agreement(dev, conf):
    rows = []
    for hd, hc in zip(dev["hypotheses"], conf["hypotheses"]):
        rows.append([hc["id"], outcome(hd), outcome(hc),
                     "same" if hd["supported"] == hc["supported"]
                     else "DIFFERENT"])
    return table(["ID", "Development set", "Confirmation set", "Agreement"],
                 rows)


def study_a(r):
    rows = r["rows"]
    t1 = table(["Omega", "True Hz", "pv rel. error", "fft rel. error",
                "pv aided rel. error (diagnostic)", "wave-order"],
               [[tok(om), f"{om * 0.05 * 8000 / 6.283185307179586:.2f}",
                 ci(rows[f"A/om{tok(om)}/pv_relerr"], 4),
                 ci(rows[f"A/om{tok(om)}/fft_relerr"], 4),
                 ci(rows[f"A/om{tok(om)}/pv_aided_relerr"], 4),
                 ci(rows[f"A/om{tok(om)}/wave_order"])] for om in OMEGAS])
    t2 = table(["Ring size n", "pv rel. error", "fft rel. error",
                "wave-order"],
               [[n, ci(rows[f"A/n{n}/pv_relerr"], 4),
                 ci(rows[f"A/n{n}/fft_relerr"], 4),
                 ci(rows[f"A/n{n}/wave_order"])] for n in RING_SIZES])
    t3 = table(["Noise sigma", "pv rel. error", "fft rel. error",
                "fft minus pv", "pv aided rel. error (diagnostic)",
                "wave-order"],
               [[tok(s), ci(rows[f"A/sig{tok(s)}/pv_relerr"], 4),
                 ci(rows[f"A/sig{tok(s)}/fft_relerr"], 4),
                 ci(rows[f"A/sig{tok(s)}/diff_fft_minus_pv"], 4),
                 ci(rows[f"A/sig{tok(s)}/pv_aided_relerr"], 4),
                 ci(rows[f"A/sig{tok(s)}/wave_order"])] for s in PITCH_SIGMAS])
    return ("### Study A: pitch accuracy\n\n"
            "Drive frequency sweep (n = 64, A = 1.5 max(1, Omega), no noise):\n\n"
            + t1 + "\n\nRing size (Omega 1):\n\n" + t2
            + "\n\nNoise (Omega 1, n = 64):\n\n" + t3)


def study_b(r):
    rows = r["rows"]
    t1 = table(["Noise sigma", "single-reading accuracy",
                "long-window accuracy", "window minus single", "wave-order"],
               [[tok(s), ci(rows[f"B/s{tok(s)}/last_acc"]),
                 ci(rows[f"B/s{tok(s)}/win_acc"]),
                 ci(rows[f"B/s{tok(s)}/diff_win_minus_last"]),
                 ci(rows[f"B/s{tok(s)}/wave_order"])] for s in DIR_SIGMAS])
    other = [("coupling 0, noise 0.5", "B/c0_s0.5")] + [
        (f"lock loss, A = {tok(a)} (Omega 1)", f"B/lockloss_a{tok(a)}")
        for a in LOCK_AMPS]
    t2 = table(["Condition", "single-reading accuracy",
                "long-window accuracy", "wave-order"],
               [[name, ci(rows[f"{k}/last_acc"]), ci(rows[f"{k}/win_acc"]),
                 ci(rows[f"{k}/wave_order"])] for name, k in other])
    out = ["### Study B: direction recovery and stereo gap\n",
           "Direction accuracy (fraction of k = +1 and k = -1 runs with the "
           "right sign):\n", t1, "\nOther conditions:\n", t2]
    for sg in GAP_SIGMAS:
        suffix = "" if sg == 0.0 else f"_s{tok(sg)}"
        t = table(["Separation d (nodes)", "expected gap (rad)",
                   "gap error (rad)", "gap sign accuracy"],
                  [[d, f"{6.283185307179586 * d / 64:.4f}",
                    ci(rows[f"B/d{d}{suffix}/gap_err"], 4),
                    ci(rows[f"B/d{d}{suffix}/sign_acc"])]
                   for d in SEPARATIONS])
        out += [f"\nStereo phase gap, noise {tok(sg)}:\n", t]
    out += ["\nAudio-only direction (two audio channels from sensors 10 and "
            "26, no access to phases):\n",
            table(["Measure", "Mean [95 % CI]"],
                  [["lag sign accuracy", ci(rows["B/audio_lag/sign_acc"])],
                   ["lag error against +-31.42 samples",
                    ci(rows["B/audio_lag/err_samples"], 4)],
                   ["time-reversed audio flips the lag sign",
                    ci(rows["B/audio_lag_reversed/flip_acc"])]])]
    return "\n".join(out)


def study_c(r):
    rows = r["rows"]
    t1 = table(["Noise sigma", "coherence", "audio RMS", "wave-order"],
               [[tok(s), ci(rows[f"C/s{tok(s)}/coherence"]),
                 ci(rows[f"C/s{tok(s)}/rms"]),
                 ci(rows[f"C/s{tok(s)}/wave_order"])] for s in COH_SIGMAS])
    names = (("driven, no noise (reference)", "C/s0"),
             ("undriven, coupled (A = 0)", "C/undriven_coupled"),
             ("undriven, uncoupled (A = 0, coupling 0)",
              "C/undriven_uncoupled"),
             ("drive weaker than its frequency (A = 0.5)", "C/lockloss_a0.5"))
    t2 = table(["Case", "coherence", "audio RMS", "wave-order"],
               [[n, ci(rows[f"{k}/coherence"]), ci(rows[f"{k}/rms"]),
                 ci(rows[f"{k}/wave_order"])] for n, k in names])
    t3 = table(["Per-replicate correlation across the six noise levels",
                "Mean [95 % CI]"],
               [["Pearson(coherence, audio RMS)", ci(rows["C/corr_coh_rms"])],
                ["Pearson(coherence, wave-order)",
                 ci(rows["C/corr_coh_wave_order"])]])
    t4 = table(["Winding number of the final undriven coupled ring",
                "Fraction of replicates [95 % CI]"],
               [["0", ci(rows["C/undriven_coupled/winding0"])],
                ["+1", ci(rows["C/undriven_coupled/winding_plus1"])],
                ["any other", ci(rows["C/undriven_coupled/winding_other"])]])
    return ("### Study C: coherence, loudness and null controls\n\n" + t1
            + "\n\nControls:\n\n" + t2 + "\n\n" + t3
            + "\n\nWinding numbers (amendment A1, diagnostic):\n\n" + t4)


def study_d(r):
    rows = r["rows"]
    t1 = table(["Sensor speed v (nodes per time unit)", "expected omega "
                "(-1 + 2 pi k v / 64)", "abs. error (rad per time unit)"],
               [[tok(v), f"-1 + {6.283185307179586 * v / 64:+.4f} k",
                 ci(rows[f"D1/v{tok(v)}/abs_err"], 5)] for v in SPEEDS]
               + [["frozen-phase speed 10.186 k", "0",
                   ci(rows["D1/frozen/abs_err"], 5)],
                  ["20 k", "-1 + 1.9635 k",
                   ci(rows["D1/v20/abs_err"], 5)]])
    t2 = table(["Measure", "Mean [95 % CI]"],
               [["low speeds, mean abs. error (rad per time unit)",
                 ci(rows["D1/low_speeds/abs_err"], 5)],
                ["pitch at the frozen-phase speed (Hz)",
                 ci(rows["D1/frozen/hz"], 4)],
                ["pitch at speed 20 (Hz), measured",
                 ci(rows["D1/v20/hz"], 3)],
                ["pitch at speed 20 (Hz), expected",
                 ci(rows["D1/v20/hz_want"], 3)]])
    t3 = table(["Measure", "Mean [95 % CI]"],
               [["both wave-vector signs recovered from 3 sensors "
                 "(4 quadrants)", ci(rows["D2/sign_acc"])],
                ["x-pair gap difference between ky = +1 and ky = -1 (rad)",
                 ci(rows["D2/xpair_ky_leak"], 5)]])
    t4 = table(["Measure at noise 0.5 (amendment A1, exploratory)",
                "Mean [95 % CI]"],
               [["low speeds, mean abs. error (rad per time unit)",
                 ci(rows["D1n/low_speeds/abs_err"], 5)],
                ["pitch at the frozen-phase speed (Hz)",
                 ci(rows["D1n/frozen/hz"], 4)],
                ["pitch at speed 20 (Hz), measured",
                 ci(rows["D1n/v20/hz"], 3)],
                ["pitch at speed 20 (Hz), expected",
                 ci(rows["D1n/v20/hz_want"], 3)]])
    return ("### Study D: the two open questions\n\n"
            "D1, a moving sensor (Doppler-like shift); a kinematic effect "
            "of the sensor's motion, not a wave in a medium:\n\n"
            + t1 + "\n\n" + t2 + "\n\nD1 repeated with noise:\n\n" + t4
            + "\n\nD2, a 12 x 12 torus as a second spatial axis "
            "(EXPERIMENTAL):\n\n" + t3)


def study_f(r):
    rows = r["rows"]
    return ("### Study F: negative controls\n\n"
            + table(["Control", "Mean [95 % CI]"],
                    [["shuffled-phase sensor, direction accuracy (chance 0.5)",
                      ci(rows["F1/shuffle_acc"])],
                     ["unshuffled sensor, direction accuracy",
                      ci(rows["F1/unshuffled_acc"])],
                     ["attached sensors leave the trajectory identical "
                      "(fraction of replicates)",
                      ci(rows["F2/readonly_identical"])],
                     ["deliberately mutating sensor is detected "
                      "(fraction of replicates)",
                      ci(rows["F2/mutant_detected"])]]))


def study_e(w):
    if w is None:
        return "### Study E: WAV checks\n\n(no wav_checks.json)"
    out = ["### Study E: checks on the committed WAV files\n",
           "Deterministic, no seeds; pass or fail against the stated "
           f"tolerance. {w['n_checks']} checks, all pass: "
           f"{'yes' if w['all_pass'] else 'NO'}.\n"]
    for section, checks in w["checks"].items():
        out.append(f"\n{section}:\n")
        out.append(table(["Check", "Measured", "Expected", "Tolerance",
                          "Unit", "Pass"],
                         [[c["name"], c["measured"], c["expected"],
                           c["tolerance"], c["unit"],
                           "yes" if c["pass"] else "NO"] for c in checks]))
    out.append("\nAliasing of audio tones through the FFT pitch "
               "estimator (8000 Hz sampling, Nyquist 4000 Hz):\n")
    out.append(table(["True Hz", "Expected Hz (folded)", "Measured Hz"],
                     [[r["true_hz"], r["expected_hz"], r["measured_hz"]]
                      for r in w["aliasing_tones"]]))
    out.append("\nAliasing of a phase ramp through the pv estimator "
               "(per-sample step beyond pi folds):\n")
    out.append(table(["omega", "Per-sample step (rad)", "Expected omega",
                      "Measured omega"],
                     [[r["omega"], r["per_sample_step"], r["expected_omega"],
                       r["measured_omega"]] for r in w["aliasing_phase"]]))
    return "\n".join(out)


HEADER = """# Results

SYNTHETIC. Every number below comes from committed scripts
(`experiments/`) run on a classical simulation of coupled phase
oscillators. Nothing here is a recording, a measurement of anything
real, a listening test or a clinical result. The protocol that fixed
the hypotheses, seeds and tests before any result existed is
`docs/PROTOCOL.md`.

Regenerate: `python -m experiments.run_all --set confirm --out
docs/results/confirm.json`, `python -m experiments.wav_checks --out
docs/results/wav_checks.json`, then `python -m experiments.render_results`.
"""

LIMITS = """## Limitations

- SYNTHETIC classical simulation of a ring (and one torus) of phase
  oscillators with an explicit Euler integrator. Conclusions about the
  integrator (for example the stability limit) are conclusions about this
  code at dt = 0.05.
- No listening test was run. Nothing here says what anyone hears, finds
  clear, or can tell apart. "Pitch" means the frequency of the rendered
  audio signal, "loudness" means its RMS level, "clarity" means the
  sensor's local coherence; these are properties of numbers.
- The heart and brain scenes are pulse-arrival toys sonified as decaying
  thumps. They are checked in Study E only for internal consistency with
  their own labels. They are not anatomy, not electrophysiology, not an
  ECG or EEG, and not a medical device.
- Confidence intervals are percentile bootstrap intervals over 200
  replicate seeds. They describe seed-to-seed variation of this
  simulation, not uncertainty about any physical system.
- The brain scene's right-sensor delay is 0.59 s as supplied while its
  own label arithmetic gives 0.60 s; this is documented in DESIGN.md and
  left unchanged so the committed WAV is byte-identical to the supplied
  one.
- The development set was used for debugging and was looked at; the
  confirmation set was run once after the code was frozen.
"""


def render(dev, conf, wavc, interpretation):
    parts = [HEADER]
    parts.append("## Confirmatory hypotheses (confirmation set, seeds "
                 f"{conf['meta']['seeds'][0]} to {conf['meta']['seeds'][1]},"
                 f" {conf['meta']['replicates']} replicates)\n")
    n_ok = sum(1 for h in conf["hypotheses"] if h["supported"])
    parts.append(f"Holm correction over {len(conf['hypotheses'])} "
                 f"hypotheses. {n_ok} of {len(conf['hypotheses'])} came out "
                 "supported (or, for the two controls, retained).\n")
    parts.append(hyp_table(conf))
    parts.append("\n## Agreement with the development set (seeds "
                 f"{dev['meta']['seeds'][0]} to {dev['meta']['seeds'][1]})\n")
    parts.append(agreement(dev, conf))
    parts.append("\n## All studies (confirmation set; mean [95 % bootstrap "
                 "CI] over replicates)\n")
    for fn in (study_a, study_b, study_c, study_d):
        parts.append(fn(conf) + "\n")
    parts.append(study_e(wavc) + "\n")
    parts.append(study_f(conf) + "\n")
    parts.append(LIMITS)
    parts.append(interpretation.rstrip() + "\n")
    return "\n".join(parts)


def build(dev_name="dev.json", conf_name="confirm.json",
          wav_name="wav_checks.json"):
    dev, conf, wavc = load(dev_name), load(conf_name), load(wav_name)
    if dev is None or conf is None:
        raise SystemExit("missing docs/results/dev.json or confirm.json")
    path = os.path.join(DOCS, "interpretation.md")
    with open(path, encoding="utf-8") as fh:
        interpretation = fh.read()
    return render(dev, conf, wavc, interpretation)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = build()
    target = os.path.join(DOCS, "RESULTS.md")
    if args.check:
        with open(target, encoding="utf-8") as fh:
            same = fh.read() == text
        print("RESULTS.md is up to date" if same
              else "RESULTS.md differs from the committed JSON")
        return 0 if same else 1
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
