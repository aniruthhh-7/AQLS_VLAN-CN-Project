# Zero-Trust Multi-Site Network + AQ-LS

Layer 1: VLAN default-deny ACL (`acl.py`). Layer 2: RIP vs OSPF vs AQ-LS over a 4-site mesh.

    pip install networkx matplotlib
    python3 main.py              # Part A (ACL) + 4 routing scenarios, plots in output/
    python3 main.py latency      # one scenario: congestion | failure | cascade | latency
    python3 sweep.py             # threshold / hysteresis stability sweep
    python3 custom.py BR-PC-01 SRV-DB01 --fault congestion --link HQ-BRANCH --load 0.9
                                 # your own flow + optional fault (case 5 of the demo)

Open `zt_aqls_sim.html` for the visual demo (same algorithms in JS).

| file | role |
|---|---|
| acl.py | VLANs, host list, ACL matrix, traffic classes |
| topology.py | mesh, link state (measured / smoothed / advertised) |
| protocols/rip.py, ospf.py | baselines |
| protocols/aqls.py | custom protocol |
| events.py | congestion, failure, recovery |
| traffic.py | ACL verdict -> class -> route |
| metrics.py | delay, messages, flaps |
| custom.py | any source/destination system, optional congestion or failure |
| sweep.py | threshold / hysteresis stability sweep |
| zt_aqls_sim.html | visual demo, 5 cases, algorithm tabs |

Deviation from the original guide: AQ-LS adds a slow refresh (`REFRESH_TICKS`, `REFRESH_MIN_CHANGE`).
Without it a link whose metric settles just under the 20% trigger stays advertised at a stale value and
AQ-LS can sit on a detour that is worse than the recovered direct link.
