"""Runs the ACL demo, then each routing scenario for RIP / OSPF / AQ-LS."""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from topology import build_topology, path_delay
from protocols import rip, ospf, aqls
from traffic import resolve_flow, flow_from_hosts, SAMPLE_FLOWS
from events import apply_events
from metrics import summarize, table

TICKS = 50
PROTOCOLS = (rip, ospf, aqls)
COLORS = {"rip": "#e5533d", "ospf": "#d9902b", "aqls": "#0f9d78"}

SCENARIOS = {
    "congestion": dict(
        title="HQ-DR congested 92% (bulk replication SRV-DB01 -> DR-SRV01)",
        flow=("SRV-DB01", "DR-SRV01"), cls="bulk",
        events=[(10, "util", "HQ", "DR", 0.92), (30, "util", "HQ", "DR", 0.05)]),
    "failure": dict(
        title="HQ-DR hard failure (bulk)",
        flow=("SRV-DB01", "DR-SRV01"), cls="bulk",
        events=[(10, "down", "HQ", "DR", None), (30, "up", "HQ", "DR", None)]),
    "cascade": dict(
        title="HQ-DR congests, then the backup HQ-CLOUD congests (bulk)",
        flow=("SRV-DB01", "DR-SRV01"), cls="bulk",
        events=[(8, "util", "HQ", "DR", 0.92), (18, "util", "HQ", "CLOUD", 0.90),
                (30, "util", "HQ", "DR", 0.05), (34, "util", "HQ", "CLOUD", 0.05)]),
    "latency": dict(
        title="HQ-BRANCH congested 70% (IT admin session, latency_sensitive)",
        flow=("IT-ADM-01", "BR-PC-01"), cls="latency_sensitive",
        events=[(10, "util", "HQ", "BRANCH", 0.70), (30, "util", "HQ", "BRANCH", 0.05)]),
}


def run_scenario(proto, src, dst, cls, events, ticks=TICKS):
    links = build_topology()
    if proto is aqls:
        aqls.reset_state()
    name = proto.__name__.split(".")[-1]
    records, event_log = [], []
    for tick in range(ticks):
        apply_events(links, events, tick, event_log)
        if proto is aqls:
            messages = aqls.tick_update(links, tick)
        else:
            messages = 0
            for lk in links.values():
                lk.update_smoothed()
        path, flap = proto.route(links, src, dst, cls)
        delay = path_delay(links, path) if path else None
        records.append({"tick": tick, "protocol": name, "path": path,
                        "delay_ms": None if delay is None else round(delay, 2),
                        "messages": messages, "flap": flap})
    return records, event_log


def part_a():
    print("=== Part A: zero-trust ACL (Layer 1) ===")
    links = build_topology()
    for s, d in SAMPLE_FLOWS:
        r = resolve_flow(links, ospf, *flow_from_hosts(s, d))
        if r["permitted"]:
            print(f"{s:<11} -> {d:<11} {r['src']:>14} -> {r['dst']:<14} ALLOWED  "
                  f"[{r['class']}] {'>'.join(r['path'])}  {r['delay_ms']} ms")
        else:
            print(f"{s:<11} -> {d:<11} {r['src']:>14} -> {r['dst']:<14} BLOCKED  (never reaches routing)")
    print()


def part_b(name):
    sc = SCENARIOS[name]
    src, dst = (flow_from_hosts(*sc["flow"])[i] for i in (0, 2))
    print(f"=== Part B [{name}]: {sc['title']} ===")
    all_rec = []
    for proto in PROTOCOLS:
        rec, ev = run_scenario(proto, src, dst, sc["cls"], sc["events"])
        all_rec += rec
        prev = None
        for r in rec:                    # show the exact moment each protocol changes path
            p = ">".join(r["path"]) if r["path"] else "NO PATH"
            if p != prev:
                print(f"  t={r['tick']:>2}  {r['protocol']:<5} path {p:<22} delay {r['delay_ms']} ms")
                prev = p
    print()
    print(table(summarize(all_rec)))
    print()

    plt.figure(figsize=(8, 4.5))
    for p in ("rip", "ospf", "aqls"):
        rows = [r for r in all_rec if r["protocol"] == p]
        plt.plot([r["tick"] for r in rows], [r["delay_ms"] for r in rows],
                 label=p.upper(), color=COLORS[p], lw=3 if p == "aqls" else 1.8)
    for t, kind, *_ in sc["events"]:
        plt.axvline(t, ls="--", color="red" if kind in ("down",) or t < 20 else "green", alpha=.5)
    plt.title(sc["title"], fontsize=10)
    plt.xlabel("Tick")
    plt.ylabel("Delay (ms)")
    plt.legend()
    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plt.savefig(f"output/delay_{name}.png", dpi=130)
    plt.close()


if __name__ == "__main__":
    part_a()
    for n in (sys.argv[1:] or SCENARIOS):
        part_b(n)
    print("plots saved in output/")
