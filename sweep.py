"""Stability trade-off: sweep AQ-LS UPDATE_THRESHOLD and HYSTERESIS on a noisy link."""
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from protocols import aqls
from main import run_scenario
from metrics import summarize


def noisy_events(seed=7, ticks=80):
    rng = random.Random(seed)
    ev = []
    for t in range(0, ticks, 2):                  # both direct and backup wobble in 20-75% load
        ev.append((t, "util", "HQ", "DR", round(rng.uniform(0.2, 0.75), 2)))
        ev.append((t, "util", "HQ", "CLOUD", round(rng.uniform(0.2, 0.75), 2)))
    return ev


if __name__ == "__main__":
    ev = noisy_events()
    thresholds = [0.05, 0.10, 0.20, 0.30, 0.40, 0.60]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for hyst in (0.0, 0.10, 0.25):
        flaps, avg = [], []
        for th in thresholds:
            aqls.UPDATE_THRESHOLD, aqls.HYSTERESIS = th, hyst
            rec, _ = run_scenario(aqls, "HQ", "DR", "bulk", ev, ticks=80)
            s = summarize(rec)["aqls"]
            flaps.append(s["flap_count"]); avg.append(s["avg_delay_ms"])
            print(f"threshold {th:.2f} hysteresis {hyst:.2f}  flaps {s['flap_count']:>3}  "
                  f"msgs {s['total_messages']:>3}  avg {s['avg_delay_ms']} ms")
        ax[0].plot(thresholds, flaps, marker="o", label=f"hysteresis {hyst}")
        ax[1].plot(thresholds, avg, marker="o", label=f"hysteresis {hyst}")
    ax[0].set(xlabel="UPDATE_THRESHOLD", ylabel="path flaps", title="Stability")
    ax[1].set(xlabel="UPDATE_THRESHOLD", ylabel="avg delay (ms)", title="Cost of being stable")
    ax[0].legend(); plt.tight_layout(); plt.savefig("output/sweep_flaps.png", dpi=130)
    print("saved output/sweep_flaps.png")
