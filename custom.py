"""Custom case (same as case 5 in the HTML demo).

  python3 custom.py BR-PC-01 SRV-DB01 --fault congestion --link HQ-BRANCH --load 0.9 --start 10 --end 30
  python3 custom.py SRV-DB01 DR-SRV01                      # no fault injected
"""
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from acl import HOSTS, is_permitted, vlan_name, classify_traffic
from traffic import flow_from_hosts
from metrics import summarize, table
from main import run_scenario, PROTOCOLS, COLORS, TICKS

ap = argparse.ArgumentParser()
ap.add_argument("src", choices=HOSTS)
ap.add_argument("dst", choices=HOSTS)
ap.add_argument("--fault", choices=["none", "congestion", "failure"], default="none")
ap.add_argument("--link", default="HQ-DR")
ap.add_argument("--load", type=float, default=0.92)
ap.add_argument("--start", type=int, default=10)
ap.add_argument("--end", type=int, default=30)
a = ap.parse_args()

ss, sv, ds, dv = flow_from_hosts(a.src, a.dst)
sn, dn = vlan_name(ss, sv), vlan_name(ds, dv)
if not is_permitted(ss, sv, ds, dv):
    raise SystemExit(f"BLOCKED by ACL: {ss}:{sn} -> {ds}:{dn}. Flow never reaches routing.")
if ss == ds:
    raise SystemExit("Same site: traffic stays local, nothing to route.")
cls = classify_traffic(sn, dn)
cls = "best_effort" if cls == "fixed" else cls

x, y = a.link.upper().split("-")
ev = []
if a.fault == "congestion":
    ev = [(a.start, "util", x, y, a.load)] + ([(a.end, "util", x, y, 0.05)] if a.start < a.end < TICKS else [])
elif a.fault == "failure":
    ev = [(a.start, "down", x, y, None)] + ([(a.end, "up", x, y, None)] if a.start < a.end < TICKS else [])

print(f"{a.src} ({ss}:{sn}) -> {a.dst} ({ds}:{dn})  class={cls}  fault={a.fault} {a.link if ev else ''}\n")
rows = []
for p in PROTOCOLS:
    rec, _ = run_scenario(p, ss, ds, cls, ev)
    rows += rec
    prev = None
    for r in rec:
        s = ">".join(r["path"]) if r["path"] else "NO PATH"
        if s != prev:
            print(f"  t={r['tick']:>2} {r['protocol']:<5} {s:<20} {r['delay_ms']} ms")
            prev = s
print("\n" + table(summarize(rows)))
plt.figure(figsize=(8, 4.5))
for p in COLORS:
    r = [q for q in rows if q["protocol"] == p]
    plt.plot([q["tick"] for q in r], [q["delay_ms"] for q in r], label=p.upper(), color=COLORS[p], lw=3 if p == "aqls" else 1.8)
plt.xlabel("Tick"); plt.ylabel("Delay (ms)"); plt.legend(); plt.tight_layout()
plt.savefig("output/delay_custom.png", dpi=130)
print("saved output/delay_custom.png")
