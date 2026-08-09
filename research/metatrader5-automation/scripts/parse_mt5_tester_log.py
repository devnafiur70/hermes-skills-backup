#!/usr/bin/env python3
"""Parse an MT5 Strategy Tester log and print a full performance summary.

MT5 tester logs are UTF-16-LE; shell tools (cat/tail/grep) produce garbage on
them. This decodes properly and extracts the stats the HTML report often fails
to write.

Usage:
    python parse_mt5_tester_log.py <path-to-log> [--contract-size 100]

Typical log location:
    %APPDATA%\\MetaQuotes\\Terminal\\<HASH>\\Tester\\logs\\YYYYMMDD.log
"""
import argparse
import os
import re
import sys
from collections import Counter

DEAL_RE = re.compile(
    r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+deal #(\d+)\s+"
    r"(buy|sell) ([\d.]+) (\S+) at ([\d.]+) done"
)
TS_RE = re.compile(r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})")


def load_lines(path):
    """MT5 tester logs are UTF-16-LE. Fall back to utf-8 for odd encodings."""
    raw = open(path, "rb").read()
    txt = raw.decode("utf-16-le", errors="ignore")
    if txt.count("\x00") > len(txt) // 4 or "Tester" not in txt:
        alt = raw.decode("utf-8", errors="ignore")
        if "Tester" in alt or len(alt.strip()) > len(txt.strip()):
            txt = alt
    return [l.strip() for l in txt.splitlines() if l.strip()]


def first_ts(lines, needle):
    for l in lines:
        if needle in l:
            m = TS_RE.search(l)
            if m:
                return m.group(1)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--contract-size", type=float, default=100.0,
                    help="Units per lot (gold=100, most FX=100000)")
    args = ap.parse_args()

    if not os.path.exists(args.log):
        sys.exit(f"Not found: {args.log}")

    lines = load_lines(args.log)
    print(f"log lines: {len(lines)}\n")

    # --- Headline figures -------------------------------------------------
    deposit = final = None
    for l in lines:
        m = re.search(r"initial deposit ([\d.]+)", l)
        if m:
            deposit = float(m.group(1))
        m = re.search(r"final balance ([\d.]+)", l)
        if m:
            final = float(m.group(1))

    print("=== HEADLINE ===")
    print(f"  initial deposit : {deposit}")
    print(f"  final balance   : {final}")
    if deposit and final is not None:
        chg = final - deposit
        print(f"  net             : {chg:+.2f} ({100 * chg / deposit:+.1f}%)")
        if final <= deposit * 0.05:
            print("  *** ACCOUNT EFFECTIVELY BLOWN ***")

    for l in lines:
        if "ticks," in l and "bars generated" in l:
            print(f"  {l.split(chr(9))[-1]}")
            break

    # --- Deals / round trips ---------------------------------------------
    deals = []
    for l in lines:
        m = DEAL_RE.search(l)
        if m:
            deals.append({
                "time": m.group(1), "side": m.group(3),
                "vol": float(m.group(4)), "price": float(m.group(6)),
            })

    print(f"\n=== DEALS ===\n  executed deals: {len(deals)}")

    rts = []
    for i in range(0, len(deals) - 1, 2):
        e, x = deals[i], deals[i + 1]
        sign = 1 if e["side"] == "buy" else -1
        pl = sign * (x["price"] - e["price"]) * args.contract_size * e["vol"]
        rts.append({"open": e["time"], "side": e["side"], "pl": pl})

    if rts:
        wins = [t for t in rts if t["pl"] > 0]
        losses = [t for t in rts if t["pl"] <= 0]
        gp = sum(t["pl"] for t in wins)
        gl = sum(t["pl"] for t in losses)
        aw = gp / len(wins) if wins else 0.0
        al = gl / len(losses) if losses else 0.0

        print(f"  round trips   : {len(rts)}")
        print(f"  wins / losses : {len(wins)} / {len(losses)}")
        print(f"  win rate      : {100 * len(wins) / len(rts):.1f}%")
        print(f"  gross profit  : {gp:+.2f}")
        print(f"  gross loss    : {gl:+.2f}")
        print(f"  profit factor : {abs(gp / gl):.2f}" if gl else "  profit factor : n/a")
        print(f"  avg win       : {aw:+.3f}")
        print(f"  avg loss      : {al:+.3f}")
        if aw and al:
            need = abs(al) / (aw + abs(al)) * 100
            print(f"  breakeven win rate needed: {need:.1f}%")
        print("  (price-only: excludes spread/commission/swap)")

        hours = Counter(t["open"][11:13] for t in rts)
        print(f"  trades per hour: {dict(sorted(hours.items()))}")

    # --- Exit reasons & rejections ---------------------------------------
    sl = sum(1 for l in lines if "stop loss triggered" in l)
    tp = sum(1 for l in lines if "take profit triggered" in l)
    inv = sum(1 for l in lines if "Invalid price" in l)
    nem = [l for l in lines if "not enough money" in l]

    print("\n=== EXITS & REJECTIONS ===")
    print(f"  stop loss triggered : {sl}")
    print(f"  take profit triggered: {tp}")
    if sl and not tp:
        print("  *** ZERO TP HITS — structural problem, not variance ***")
    print(f"  'Invalid price' failures: {inv}")
    if inv > 50:
        print("  *** bulk rejections — EA likely violates broker min stop distance ***")
    print(f"  'not enough money'      : {len(nem)}")
    if nem:
        print(f"  collapse began at: {first_ts(nem, 'not enough money')}")

    print("\n=== ERROR CODES ===")
    codes = Counter(re.findall(r"Error:\s*(\d+)", "\n".join(lines)))
    for code, n in codes.most_common(10):
        note = " (invalid stops / too close to market)" if code == "4756" else ""
        print(f"  {code}: {n}{note}")
    if not codes:
        print("  none")


if __name__ == "__main__":
    main()
