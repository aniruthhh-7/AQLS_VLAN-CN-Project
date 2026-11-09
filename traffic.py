"""Glue: Layer 1 verdict -> classification -> Layer 2 routing."""
from acl import is_permitted, vlan_name, classify_traffic, HOSTS
from topology import key, path_delay


def resolve_flow(links, protocol_module, src_site, src_vlan, dst_site, dst_vlan):
    src_name, dst_name = vlan_name(src_site, src_vlan), vlan_name(dst_site, dst_vlan)
    result = {"src": f"{src_site}:{src_name}", "dst": f"{dst_site}:{dst_name}",
              "permitted": False, "class": None, "path": None, "delay_ms": None}
    if not is_permitted(src_site, src_vlan, dst_site, dst_vlan):
        return result                       # blocked here, routing never sees it
    result["permitted"] = True
    tclass = classify_traffic(src_name, dst_name)
    result["class"] = tclass
    if src_site == dst_site:
        result["path"], result["delay_ms"] = [src_site], 0.0
        return result
    route_class = "best_effort" if tclass == "fixed" else tclass
    path, _ = protocol_module.route(links, src_site, dst_site, route_class)
    result["path"] = path
    result["delay_ms"] = round(path_delay(links, path), 2) if path else None
    return result


def flow_from_hosts(src_host, dst_host):
    (ss, sv), (ds, dv) = HOSTS[src_host], HOSTS[dst_host]
    return ss, sv, ds, dv


# (source system, destination system)
SAMPLE_FLOWS = [
    ("SRV-DB01", "DR-SRV01"),     # replication        -> allowed, bulk
    ("IT-ADM-01", "BR-PC-01"),    # admin session      -> allowed, latency_sensitive
    ("BR-PC-01", "SRV-FILE01"),   # branch file access -> allowed, bulk
    ("GUEST-AP", "FIN-PC-01"),    # guest -> finance   -> BLOCKED
    ("FIN-PC-01", "HR-PC-01"),    # finance -> hr      -> BLOCKED
]
