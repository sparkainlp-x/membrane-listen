"""One replicate of every study, as a flat {key: float} dict.

``replicate(seed)`` is deterministic given the seed. Keys are the names
used in docs/PROTOCOL.md and in the result files.
"""

import math

from membrane_listen import Ring, Sensor, TWO_PI, wrap
from membrane_listen import estimators as est
from membrane_listen.experimental import Torus
from membrane_listen.stats import pearson, rng_for

from .common import (COH_SIGMAS, DIR_SIGMAS, FAST_SPEED, GAP_SIGMAS,
                     LOCK_AMPS, OMEGAS, PITCH_SIGMAS, RING_SIZES, SEPARATIONS,
                     SENSOR_POS, SHUFFLES, SPEEDS, WARMUP, finite_or, mean,
                     record, sign_ok, tok)

HZ_1 = est.omega_to_hz(1.0)


def _pitch_errors(ring, true_hz):
    """(pv_relerr, fft_relerr, wave_order) for one recorded ring."""
    sensor = Sensor(ring, position=SENSOR_POS)
    (rd,) = record(ring, [sensor])
    pv = est.omega_to_hz(est.phase_velocity([r["phase"] for r in rd]))
    ff = est.peak_frequency_hz([r["signal"] for r in rd])
    pv_err = abs(finite_or(pv, 0.0) - true_hz) / true_hz
    ff_err = abs(finite_or(ff, 0.0) - true_hz) / true_hz
    # Amendment A1 (diagnostic only; it uses the true drive frequency):
    # unwrap each step around the expected step -Omega dt, which removes
    # step aliasing from the sum.
    expect = -ring.drive_omega * ring.dt
    phases = [r["phase"] for r in rd]
    drift = math.fsum(wrap(b - a - expect) for a, b in zip(phases, phases[1:]))
    om_aided = expect / ring.dt + drift / (ring.dt * (len(phases) - 1))
    aided_err = abs(est.omega_to_hz(om_aided) - true_hz) / true_hz
    return pv_err, ff_err, ring.wave_order(), aided_err


def study_a(seed):
    out = {}
    for om in OMEGAS:
        ring = Ring(seed=seed, drive_omega=om, drive_amp=1.5 * max(1.0, om))
        pv, ff, wo, aided = _pitch_errors(ring, est.omega_to_hz(om))
        k = f"A/om{tok(om)}"
        out[f"{k}/pv_relerr"], out[f"{k}/fft_relerr"] = pv, ff
        out[f"{k}/wave_order"] = wo
        out[f"{k}/pv_aided_relerr"] = aided
    for n in RING_SIZES:
        pv, ff, wo, _ = _pitch_errors(Ring(seed=seed, n=n), HZ_1)
        k = f"A/n{n}"
        out[f"{k}/pv_relerr"], out[f"{k}/fft_relerr"] = pv, ff
        out[f"{k}/wave_order"] = wo
    for sg in PITCH_SIGMAS:
        pv, ff, wo, aided = _pitch_errors(Ring(seed=seed, noise=sg), HZ_1)
        k = f"A/sig{tok(sg)}"
        out[f"{k}/pv_aided_relerr"] = aided
        out[f"{k}/pv_relerr"], out[f"{k}/fft_relerr"] = pv, ff
        out[f"{k}/diff_fft_minus_pv"] = ff - pv
        out[f"{k}/wave_order"] = wo
    return out


def _direction(seed, k, **ring_kw):
    """(last correct, window correct, wave_order) for one ring."""
    ring = Ring(seed=seed, drive_k=k, **ring_kw)
    sensor = Sensor(ring, position=SENSOR_POS)
    (rd,) = record(ring, [sensor])
    kw, _ = est.window_k([r["gradient"] for r in rd], ring.n)
    return (float(sign_ok(rd[-1]["k_est"], k)), float(sign_ok(kw, k)),
            ring.wave_order())


def _direction_pair(seed, prefix, out, **ring_kw):
    res = [_direction(seed, k, **ring_kw) for k in (1, -1)]
    last = mean(r[0] for r in res)
    win = mean(r[1] for r in res)
    out[f"{prefix}/last_acc"] = last
    out[f"{prefix}/win_acc"] = win
    out[f"{prefix}/diff_win_minus_last"] = win - last
    out[f"{prefix}/wave_order"] = mean(r[2] for r in res)


def study_b(seed):
    out = {}
    for sg in DIR_SIGMAS:
        _direction_pair(seed, f"B/s{tok(sg)}", out, noise=sg)
    _direction_pair(seed, "B/c0_s0.5", out, noise=0.5, coupling=0.0)
    for amp in LOCK_AMPS:
        _direction_pair(seed, f"B/lockloss_a{tok(amp)}", out, drive_amp=amp)
    # stereo gap vs separation
    for sg in GAP_SIGMAS:
        suffix = "" if sg == 0.0 else f"_s{tok(sg)}"
        errs = {d: [] for d in SEPARATIONS}
        oks = {d: [] for d in SEPARATIONS}
        for k in (1, -1):
            ring = Ring(seed=seed, drive_k=k, noise=sg)
            sensors = [Sensor(ring, position=SENSOR_POS)] + [
                Sensor(ring, position=SENSOR_POS + d) for d in SEPARATIONS]
            data = record(ring, sensors)
            pa = [r["phase"] for r in data[0]]
            for d, rd in zip(SEPARATIONS, data[1:]):
                gap, _ = est.phase_gap(pa, [r["phase"] for r in rd])
                want = wrap(TWO_PI * k * d / ring.n)
                errs[d].append(abs(wrap(gap - want)))
                oks[d].append(float(sign_ok(gap, k)))
        for d in SEPARATIONS:
            out[f"B/d{d}{suffix}/gap_err"] = mean(errs[d])
            out[f"B/d{d}{suffix}/sign_acc"] = mean(oks[d])
    # audio-only direction from the stereo pair 10 and 26
    ok, flip, err = [], [], []
    for k in (1, -1):
        ring = Ring(seed=seed, drive_k=k)
        sa = Sensor(ring, position=SENSOR_POS)
        sb = Sensor(ring, position=SENSOR_POS + 16)
        ra, rb = record(ring, [sa, sb])
        left = [r["signal"] for r in ra]
        right = [r["signal"] for r in rb]
        lag = est.stereo_lag(left, right, 39)
        lag_r = est.stereo_lag(left[::-1], right[::-1], 39)
        expected = k * (TWO_PI / 4) / (1.0 * 0.05)
        ok.append(float(sign_ok(finite_or(lag, 0.0), k)))
        flip.append(float(finite_or(lag_r, 0.0) * k < 0))
        err.append(abs(finite_or(lag, 1e9) - expected))
    out["B/audio_lag/sign_acc"] = mean(ok)
    out["B/audio_lag/err_samples"] = mean(err)
    out["B/audio_lag_reversed/flip_acc"] = mean(flip)
    return out


def study_c(seed):
    out = {}
    cohs, rmss, wos = [], [], []
    for sg in COH_SIGMAS:
        ring = Ring(seed=seed, noise=sg)
        (rd,) = record(ring, [Sensor(ring, position=SENSOR_POS)])
        coh = mean(r["coherence"] for r in rd)
        rms = math.sqrt(mean(r["signal"] ** 2 for r in rd))
        wo = ring.wave_order()
        k = f"C/s{tok(sg)}"
        out[f"{k}/coherence"], out[f"{k}/rms"] = coh, rms
        out[f"{k}/wave_order"] = wo
        cohs.append(coh)
        rmss.append(rms)
        wos.append(wo)
    out["C/corr_coh_rms"] = pearson(cohs, rmss)
    out["C/corr_coh_wave_order"] = pearson(cohs, wos)
    cases = (("undriven_coupled", {"drive_amp": 0.0}),
             ("undriven_uncoupled", {"drive_amp": 0.0, "coupling": 0.0}),
             ("lockloss_a0.5", {"drive_amp": 0.5}))
    for name, kw in cases:
        ring = Ring(seed=seed, **kw)
        (rd,) = record(ring, [Sensor(ring, position=SENSOR_POS)])
        out[f"C/{name}/coherence"] = mean(r["coherence"] for r in rd)
        out[f"C/{name}/rms"] = math.sqrt(mean(r["signal"] ** 2 for r in rd))
        out[f"C/{name}/wave_order"] = ring.wave_order()
        if name == "undriven_coupled":  # Amendment A1 (diagnostic)
            w = round(math.fsum(wrap(ring.theta[(i + 1) % ring.n]
                                     - ring.theta[i])
                                for i in range(ring.n)) / TWO_PI)
            out["C/undriven_coupled/winding0"] = float(w == 0)
            out["C/undriven_coupled/winding_plus1"] = float(w == 1)
            out["C/undriven_coupled/winding_other"] = float(w not in (0, 1))
    return out


def _doppler(seed, prefix, noise):
    """Moving-sensor rows for one noise level (k = +1 and -1)."""
    out = {}
    v_frozen = 1.0 * 64 / TWO_PI  # nodes per time unit, times k below
    abs_err = {}
    hz = {}
    for k in (1, -1):
        speeds = [(f"{tok(v)}", v) for v in SPEEDS]
        speeds.append(("frozen", v_frozen * k))
        speeds.append(("v20", FAST_SPEED * k))
        ring = Ring(seed=seed, drive_k=k, noise=noise)
        sensors = []
        for _, v in speeds:
            s = Sensor(ring, position=SENSOR_POS)
            s.follow_probe(v)
            sensors.append(s)
        data = record(ring, sensors)
        for (name, v), rd in zip(speeds, data):
            om = est.phase_velocity([r["phase"] for r in rd])
            want = -1.0 + TWO_PI * k * v / ring.n
            abs_err.setdefault(name, []).append(abs(om - want))
            hz.setdefault(name, []).append(est.omega_to_hz(om))
            if name == "v20":
                hz.setdefault("v20_want", []).append(est.omega_to_hz(want))
    for name in abs_err:
        label = "v" + name if name[0] in "-0123456789" else name
        out[f"{prefix}/{label}/abs_err"] = mean(abs_err[name])
    out[f"{prefix}/low_speeds/abs_err"] = mean(
        v for name, vals in abs_err.items()
        if name not in ("frozen", "v20") for v in vals)
    out[f"{prefix}/frozen/hz"] = mean(hz["frozen"])
    out[f"{prefix}/v20/hz"] = mean(hz["v20"])
    out[f"{prefix}/v20/hz_want"] = mean(hz["v20_want"])
    return out


def study_d(seed):
    out = _doppler(seed, "D1", 0.0)
    out.update(_doppler(seed, "D1n", 0.5))  # Amendment A1 (exploratory)
    # D2: torus, three sensors
    oks, gx_by = [], {}
    for kx in (1, -1):
        for ky in (1, -1):
            torus = Torus(seed=seed, kx=kx, ky=ky)
            for _ in range(300):
                torus.step()
            p0, px, py = [], [], []
            for _ in range(300):
                torus.step()
                p0.append(torus.phase_at(0, 0))
                px.append(torus.phase_at(3, 0))
                py.append(torus.phase_at(0, 3))
            gx, _ = est.phase_gap(p0, px)
            gy, _ = est.phase_gap(p0, py)
            oks.append(float(sign_ok(gx, kx) and sign_ok(gy, ky)))
            gx_by[(kx, ky)] = gx
    out["D2/sign_acc"] = mean(oks)
    out["D2/xpair_ky_leak"] = mean(
        abs(wrap(gx_by[(kx, 1)] - gx_by[(kx, -1)])) for kx in (1, -1))
    return out


class _Mutant(Sensor):
    """A deliberately wrong sensor: it nudges the ring it reads."""

    def sample(self):
        reading = super().sample()
        self.ring.theta[0] += 1e-9
        return reading


def study_f(seed):
    out = {}
    oks = []
    base_ok = []
    for k in (1, -1):
        ring = Ring(seed=seed, drive_k=k)
        for _ in range(WARMUP):
            ring.step()
        theta = list(ring.theta)
        i = int(SENSOR_POS)
        j = i + 1
        base_ok.append(float(sign_ok(wrap(theta[j] - theta[i]), k)))
        for trial in range(SHUFFLES):
            rng = rng_for("shuffle", seed, k, trial)
            perm = list(theta)
            rng.shuffle(perm)
            oks.append(float(sign_ok(wrap(perm[j] - perm[i]), k)))
    out["F1/shuffle_acc"] = mean(oks)
    out["F1/unshuffled_acc"] = mean(base_ok)
    # sensor mutation tests
    a, b = Ring(seed=seed), Ring(seed=seed)
    sensors = [Sensor(b, position=p) for p in (1.0, 20.25, 40.0)]
    moving = Sensor(b, position=5.0)
    moving.follow_probe(1.5)
    sensors.append(moving)
    for _ in range(300):
        a.step()
        b.step()
        for s in sensors:
            s.sample()
    out["F2/readonly_identical"] = float(a.theta == b.theta and a.t == b.t)
    c, d = Ring(seed=seed), Ring(seed=seed)
    bad = _Mutant(d, position=1.0)
    for _ in range(300):
        c.step()
        d.step()
        bad.sample()
    out["F2/mutant_detected"] = float(c.theta != d.theta)
    return out


def replicate(seed):
    out = {}
    for study in (study_a, study_b, study_c, study_d, study_f):
        out.update(study(seed))
    return out
