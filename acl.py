"""Layer 1 - zero-trust gatekeeper. VLAN based, default deny."""

SITE_VLANS = {
    "HQ":     {10: "FINANCE", 20: "HR", 30: "IT_ADMIN", 40: "GUEST", 99: "SERVERS"},
    "BRANCH": {50: "BRANCH_STAFF", 40: "GUEST"},
    "DR":     {99: "SERVERS"},
    "CLOUD":  {0: "GATEWAY"},
}

# end systems that sit behind each site's switch: name -> (site, vlan id)
HOSTS = {
    "FIN-PC-01": ("HQ", 10), "FIN-PC-02": ("HQ", 10),
    "HR-PC-01": ("HQ", 20),
    "IT-ADM-01": ("HQ", 30),
    "GUEST-AP": ("HQ", 40),
    "SRV-DB01": ("HQ", 99), "SRV-FILE01": ("HQ", 99),
    "BR-PC-01": ("BRANCH", 50), "BR-PC-02": ("BRANCH", 50),
    "BR-GUEST": ("BRANCH", 40),
    "DR-SRV01": ("DR", 99), "DR-BACKUP": ("DR", 99),
    "CLOUD-GW": ("CLOUD", 0),
}

# explicit rules only; anything missing is denied
ACL_MATRIX = {
    ("FINANCE", "HR"): False, ("HR", "FINANCE"): False,
    ("GUEST", "FINANCE"): False, ("GUEST", "HR"): False,
    ("GUEST", "IT_ADMIN"): False, ("GUEST", "BRANCH_STAFF"): False,
    ("GUEST", "SERVERS"): False, ("GUEST", "GATEWAY"): True,
    ("IT_ADMIN", "FINANCE"): True, ("IT_ADMIN", "HR"): True,
    ("IT_ADMIN", "BRANCH_STAFF"): True, ("IT_ADMIN", "SERVERS"): True,
    ("IT_ADMIN", "GATEWAY"): True,
    ("FINANCE", "SERVERS"): True, ("HR", "SERVERS"): True,
    ("BRANCH_STAFF", "SERVERS"): True, ("SERVERS", "SERVERS"): True,
    ("BRANCH_STAFF", "IT_ADMIN"): True,
}


def vlan_name(site, vlan_id):
    return SITE_VLANS[site][vlan_id]


def is_permitted(src_site, src_vlan_id, dst_site, dst_vlan_id):
    src = vlan_name(src_site, src_vlan_id)
    dst = vlan_name(dst_site, dst_vlan_id)
    if src_site == dst_site and src == dst:
        return True
    return ACL_MATRIX.get((src, dst), False)


def classify_traffic(src_vlan_name, dst_vlan_name):
    if dst_vlan_name == "GATEWAY":
        return "fixed"              # internet breakout, AQ-LS not tuned for it
    if "SERVERS" in (src_vlan_name, dst_vlan_name):
        return "bulk"
    if "IT_ADMIN" in (src_vlan_name, dst_vlan_name):
        return "latency_sensitive"
    return "best_effort"
