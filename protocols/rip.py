"""Baseline: hop count only."""
import networkx as nx
from topology import to_networkx


def route(links, src, dst, traffic_class=None):
    G = to_networkx(links, lambda lk: 1)
    try:
        return nx.shortest_path(G, src, dst, weight="weight"), 0
    except nx.NetworkXNoPath:
        return None, 0
