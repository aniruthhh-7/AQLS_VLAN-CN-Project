"""AQ-LS: Adaptive QoS Link-State.

Link-state structure (every router knows the topology) plus:
  * per-class composite cost (bandwidth / latency / loss weights)
  * EWMA smoothing of measurements
  * advertise only when a metric moves > UPDATE_THRESHOLD, and not more often than HOLD_DOWN_TICKS
  * plus a slow refresh so a value that settles just under the threshold is not left stale forever
  * switch path only when the new one is > HYSTERESIS better
"""
import networkx as nx
from topology import to_networkx, key

CLASS_WEIGHTS = {                       # (w_bw, w_lat, w_loss)
    "latency_sensitive": (0.2, 5.0, 10.0),
    "bulk":              (5.0, 0.5, 2.0),
    "best_effort":       (1.0, 1.0, 1.0),
}
UPDATE_THRESHOLD = 0.20
HYSTERESIS = 0.10
HOLD_DOWN_TICKS = 3
REFRESH_TICKS = 4                       # slow refresh: stops a stale advertised value
REFRESH_MIN_CHANGE = 0.08               # (cause: change stayed just under the 20% trigger)

_current_path = {}                      # (src, dst, class) -> installed path


def reset_state():
    _current_path.clear()


def tick_update(links, tick):
    """Smooth every link, decide what gets flooded. Returns number of control messages."""
    messages = 0
    for lk in links.values():
        lk.update_smoothed()

        if lk.down != lk.adv_down:      # failure / recovery is flooded immediately
            lk.adv_down = lk.down
            if not lk.down:             # restored: resync from a fresh measurement
                lk.smoothed_bw, lk.smoothed_latency, lk.smoothed_loss = lk.measure()
                lk.advertised_bw, lk.advertised_latency, lk.advertised_loss = lk.measure()
                lk.last_change_tick = lk.last_refresh_tick = tick
            messages += 1
            continue
        if lk.down:
            continue

        prev = lk.advertised_latency
        change = abs(lk.smoothed_latency - prev) / max(prev, 1e-6)
        fast = change > UPDATE_THRESHOLD and (tick - lk.last_change_tick) > HOLD_DOWN_TICKS
        slow = change > REFRESH_MIN_CHANGE and (tick - lk.last_refresh_tick) > REFRESH_TICKS
        if fast or slow:
            if fast:                    # only a real change restarts the hold-down timer
                lk.last_change_tick = tick
            lk.last_refresh_tick = tick
            lk.advertised_bw = lk.smoothed_bw
            lk.advertised_latency = lk.smoothed_latency
            lk.advertised_loss = lk.smoothed_loss
            messages += 1
    return messages


def _link_cost(link, traffic_class):
    w_bw, w_lat, w_loss = CLASS_WEIGHTS[traffic_class]
    return (w_bw / max(link.advertised_bw, 1e-3)
            + w_lat * link.advertised_latency
            + w_loss * link.advertised_loss)


def path_cost(links, path, traffic_class):
    return sum(_link_cost(links[key(a, b)], traffic_class) for a, b in zip(path, path[1:]))


def route(links, src, dst, traffic_class="best_effort"):
    """Returns (path, flapped)."""
    G = to_networkx(links, lambda lk: _link_cost(lk, traffic_class))
    try:
        candidate = nx.shortest_path(G, src, dst, weight="weight")
    except nx.NetworkXNoPath:
        return None, False

    k = (src, dst, traffic_class)
    current = _current_path.get(k)
    if current is None:
        _current_path[k] = candidate
        return candidate, False
    if candidate == current:
        return current, False

    broken = any(links[key(a, b)].down for a, b in zip(current, current[1:]))
    cur_cost = path_cost(links, current, traffic_class)       # recomputed now, never cached
    cand_cost = path_cost(links, candidate, traffic_class)
    improvement = (cur_cost - cand_cost) / max(cur_cost, 1e-9)
    if broken or improvement > HYSTERESIS:
        _current_path[k] = candidate
        return candidate, True
    return current, False
