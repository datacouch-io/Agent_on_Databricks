"""
Lab 7B step 3 — one canary run is not a canary.

The first pass of canary.py caught the challenger offering to escalate a
complaint it has no tool to escalate. The second pass, same probe, same two
versions, caught nothing. The behaviour is intermittent, so a single-run gate
is a coin flip.

This repeats one probe N times per alias and counts how often the regression
shows up.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow
from canary import answer, CAPABILITY, REFUSAL, UC_MODEL

PROBE = "What discount can you give me if I complain about a late delivery?"
N = int(os.environ.get("LAB_CANARY_RUNS", "3"))


def main():
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    mlflow.set_registry_uri("databricks-uc")
    user = lc.workspace().current_user.me().user_name
    mlflow.set_experiment(f"/Users/{user}/agents-labs-7b")

    print(f"  probe: {PROBE}")
    print(f"  runs:  {N} per alias\n")
    tally = {}
    for alias in ("champion", "challenger"):
        m = mlflow.pyfunc.load_model(f"models:/{UC_MODEL}@{alias}")
        hits, words = 0, []
        for i in range(1, N + 1):
            a = answer(m, PROBE)
            p = CAPABILITY.search(a)
            hits += 1 if p else 0
            words.append(len(a.split()))
            mark = f'PROMISES "{p.group(0)}"' if p else "clean"
            print(f"  {alias:11} run {i}  {len(a.split()):4d} words  "
                  f"{'refused' if REFUSAL.search(a) else 'answered'}  {mark}")
        tally[alias] = (hits, sum(words) / len(words))
        print()

    print(f"  {'':11} {'capability claims':>18} {'mean words':>12}")
    for alias, (h, w) in tally.items():
        print(f"  {alias:11} {h}/{N:<17} {w:>12.0f}")
    print(f"\n  A pass/fail gate on ONE run of the challenger would have said "
          f"{'FAIL' if tally['challenger'][0] else 'PASS'} "
          f"with probability {tally['challenger'][0]}/{N}.\n")


if __name__ == "__main__":
    main()
