#!/usr/bin/env python3
"""Generate an MT5 headless backtest launcher .ini with the REQUIRED UTF-16 LE + BOM
encoding. Without the BOM, MT5 silently ignores the file and falls back to cached
terminal.ini dates (FromDate/ToDate get ignored -> re-runs the old range).

Usage:
  python make_backtest_ini.py --expert SafeGrid_NR_v1.ex5 --from 2026.08.05 --to 2026.08.06 --out C:/Users/user/gh_lab/SG.ini
  python make_backtest_ini.py --expert SafeGrid_NR_v1.ex5 --from 2026.07.07 --to 2026.08.06 --out C:/Users/user/gh_lab/SG_30d.ini
"""
import argparse

# EA inputs are inlined under [TesterInputs] (more reliable than ExpertParameters=SET_FILE.set).
# Format per line: Name=value||default||min||max||N
TPL = """[Tester]
Expert={expert}
Symbol=XAUUSDm
Period=M5
Optimization=0
Model=4
FromDate={frm}
ToDate={to}
ForwardMode=0
Deposit=500
Currency=USD
ProfitInPips=0
Leverage=2000
ExecutionMode=0
OptimizationCriterion=0
Visual=0
Report={report}
ReplaceReport=1
ShutdownTerminal=1
[TesterInputs]
; === Grid geometry ===
InpOrdersPerSide=2||2||1||20||N
InpMaxOrdersTotal=5.0||5.0||0.500000||50.000000||N
InpGridStepMode=1||1||1||10||N
InpGridStepPoints=300.0||300.0||30.000000||3000.000000||N
InpAtrPeriod=14||14||1||140||N
InpGridStepAtrMult=0.4||0.4||0.040000||4.000000||N
InpMinStepPoints=200.0||200.0||20.000000||2000.000000||N
; === Exit / harvest (NO SL) ===
InpHarvestPts=100.0||100.0||10.000000||2000.000000||N
InpRiskPercent=0.5||0.5||0.050000||5.000000||N
InpFixedLot=0.0||0.0||0.000000||0.000000||N
InpMaxLot=0.1||0.1||0.010000||1.000000||N
; === Account protection ===
InpMaxDDPct=20.0||20.0||2.000000||200.000000||N
InpMaxDailyLossPct=4.0||4.0||0.400000||40.000000||N
InpNetTargetPct=3.0||3.0||0.300000||30.000000||N
InpUseSession=true||false||0||true||N
InpSessionStart=9||9||1||90||N
InpSessionEnd=17||17||1||170||N
InpReconHour=22||22||1||220||N
InpMaxSpreadPts=500.0||500.0||50.000000||5000.000000||N
; === Misc ===
InpMagic=880822||880822||1||8808220||N
InpSlippagePts=50||50||1||500||N
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expert", default="SafeGrid_NR_v1.ex5")
    ap.add_argument("--from", dest="frm", default="2026.08.05")
    ap.add_argument("--to", dest="to", default="2026.08.06")
    ap.add_argument("--report", default=r"C:\Users\user\rep_RUN")
    ap.add_argument("--out", default=r"C:\Users\user\gh_lab\backtest.ini")
    a = ap.parse_args()
    content = TPL.format(expert=a.expert, frm=a.frm, to=a.to, report=a.report)
    with open(a.out, "wb") as f:
        f.write(b"\xff\xfe")          # UTF-16 LE BOM -- MANDATORY
        f.write(content.encode("utf-16-le"))
    print("wrote", a.out, "with UTF-16 BOM; FromDate=%s ToDate=%s" % (a.frm, a.to))

if __name__ == "__main__":
    main()
