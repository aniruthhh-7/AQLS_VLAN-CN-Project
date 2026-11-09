"""Baseline: static cost = reference bandwidth / configured bandwidth. Blind to load."""
import networkx as nx
from topology import to_networkx

REFERENCE_BW = 10000


def static_cost(link):
    return max(REFERENCE_BW / link.base_bw, 1)


def route(links, src, dst, traffic_class=None):
    G = to_networkx(links, static_cost)
    try:
        return nx.shortest_path(G, src, dst, weight="weight"), 0
    except nx.NetworkXNoPath:
        return None, 0
