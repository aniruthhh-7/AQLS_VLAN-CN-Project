def summarize(records):
    by = {}
    for r in records:
        by.setdefault(r["protocol"], []).append(r)
    out = {}
    for proto, rows in by.items():
        d = [x["delay_ms"] for x in rows if x["delay_ms"] is not None]
        out[proto] = {
            "avg_delay_ms": round(sum(d) / len(d), 2),
            "max_delay_ms": round(max(d), 2),
            "total_messages": sum(x["messages"] for x in rows),
            "path_changes": sum(1 for a, b in zip(rows, rows[1:]) if a["path"] != b["path"]),
            "flap_count": sum(1 for x in rows if x["flap"]),
        }
    return out


def table(summary):
    head = f"{'protocol':<8}{'avg ms':>9}{'max ms':>9}{'ctrl msgs':>11}{'path chg':>10}{'flaps':>7}"
    lines = [head, "-" * len(head)]
    for p, s in summary.items():
        lines.append(f"{p.upper():<8}{s['avg_delay_ms']:>9}{s['max_delay_ms']:>9}"
                     f"{s['total_messages']:>11}{s['path_changes']:>10}{s['flap_count']:>7}")
    return "\n".join(lines)
