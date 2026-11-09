"""Scripted network events. An event is (tick, kind, site_a, site_b, value)."""
from topology import key


def apply_events(links, events, tick, event_log):
    for t, kind, a, b, value in events:
        if t != tick:
            continue
        lk = links[key(a, b)]
        if kind == "util":
            lk.utilization = value
            event_log.append((tick, f"Load {a}-{b} -> {int(value * 100)}%"))
        elif kind == "down":
            lk.down = True
            event_log.append((tick, f"Link {a}-{b} DOWN"))
        elif kind == "up":
            lk.down, lk.utilization = False, 0.05
            event_log.append((tick, f"Link {a}-{b} restored"))
