"""4-site partial mesh and the live state of every link."""
import networkx as nx

SITES = ["HQ", "BRANCH", "DR", "CLOUD"]

# (a, b): (bandwidth Mbps, base latency ms, base loss)
LINKS = {
    ("HQ", "BRANCH"): (100, 4, 0.001), ("HQ", "DR"): (200, 6, 0.001),
    ("HQ", "CLOUD"): (50, 2, 0.001),   ("BRANCH", "DR"): (100, 5, 0.001),
    ("BRANCH", "CLOUD"): (50, 3, 0.001), ("DR", "CLOUD"): (100, 4, 0.001),
}


class Link:
    def __init__(self, a, b, bw, lat, loss):
        self.a, self.b = a, b
        self.base_bw, self.base_latency, self.base_loss = bw, lat, loss
        self.utilization = 0.05          # events.py changes this
        self.down = False                # events.py changes this
        self.smoothed_bw, self.smoothed_latency, self.smoothed_loss = bw, lat, loss
        self.advertised_bw, self.advertised_latency, self.advertised_loss = bw, lat, loss
        self.adv_down = False            # failure state the network has been told about
        self.last_change_tick = -999     # last real change advertised (hold-down timer)
        self.last_refresh_tick = 0       # last advertisement of any kind

    def measure(self):
        """Queueing model: delay explodes as utilisation approaches 1."""
        u = min(self.utilization, 0.95)
        return self.base_bw * (1 - u), self.base_latency / (1 - u), self.base_loss + u * 0.05

    def update_smoothed(self, alpha=0.3):
        bw, lat, loss = self.measure()
        self.smoothed_bw = (1 - alpha) * self.smoothed_bw + alpha * bw
        self.smoothed_latency = (1 - alpha) * self.smoothed_latency + alpha * lat
        self.smoothed_loss = (1 - alpha) * self.smoothed_loss + alpha * loss


def key(a, b):
    return tuple(sorted((a, b)))


def build_topology():
    return {key(a, b): Link(a, b, *v) for (a, b), v in LINKS.items()}


def to_networkx(links, weight_fn):
    G = nx.Graph()
    G.add_nodes_from(SITES)
    for lk in links.values():
        if not lk.down:                  # dead links are not usable by anyone
            G.add_edge(lk.a, lk.b, weight=weight_fn(lk), link=lk)
    return G


def path_delay(links, path):
    """End-to-end delay of a path using what the links currently measure (smoothed)."""
    return sum(links[key(a, b)].smoothed_latency for a, b in zip(path, path[1:]))
