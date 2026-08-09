#!/usr/bin/env python3
# Patch MT5 terminal.ini [Tester] DateFrom/DateTo to a YYYY.MM.DD -> YYYY.MM.DD window.
# WHY: MT5 headless backtest reads the test date window from
# config/terminal.ini -> [Tester] DateFrom/DateTo (Unix epoch SECONDS, UTC),
# NOT from the launcher .ini's FromDate/ToDate. A prior aborted run can zero
# these, giving a ~2s 00:00->00:00 zero-length window with no final balance.
# USAGE: python patch_terminal_ini_dates.py 2026.07.07 2026.08.06
# Then launch the BOM-encoded launcher .ini. Re-run before each launch if the
# window looks broken (ShutdownTerminal=1 rewrites terminal.ini on exit).
import sys, datetime, os

DATA = r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06"
INI = os.path.join(DATA, "config", "terminal.ini")

def epoch(y, m, d):
    return int(datetime.datetime(y, m, d, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp())

def main():
    if len(sys.argv) != 3:
        print("usage: patch_terminal_ini_dates.py FROM_YYYY.MM.DD TO_YYYY.MM.DD")
        sys.exit(2)
    def parse(s):
        y, m, d = (int(x) for x in s.split("."))
        return y, m, d
    fy, fm, fd = parse(sys.argv[1]); ty, tm, td = parse(sys.argv[2])
    ft, tt = epoch(fy, fm, fd), epoch(ty, tm, td)
    raw = open(INI, "rb").read()
    txt = raw.decode("utf-16")
    out = []
    for ln in txt.split("\n"):
        if ln.startswith("DateFrom="): out.append("DateFrom=%d" % ft)
        elif ln.startswith("DateTo="): out.append("DateTo=%d" % tt)
        else: out.append(ln)
    with open(INI, "wb") as f:
        f.write("\n".join(out).encode("utf-16"))
    v = open(INI, "rb").read().decode("utf-16")
    for ln in v.split("\n"):
        if ln.startswith(("DateFrom=", "DateTo=")):
            print("VERIFY:", ln)

if __name__ == "__main__":
    main()
