"""
Lab 7A step 3 — why "each task must stand alone" is a hard constraint.

A worker is a separate LLM call with its own message list. It never sees the
supervisor's conversation. Send it a task that leans on context and it cannot
recover the missing fact; it can only guess or refuse.

Both calls below go to the same worker with the same tools. The only difference
is whether the task carries its own context.
"""
import os, sys, textwrap
sys.path.insert(0, os.path.dirname(__file__))
from supervisor import policy_worker

BAD  = "Would that customer pay a return shipping fee?"
GOOD = ("A 'plus' tier customer is returning 25 units of a single seating product. "
        "Would they pay a return shipping fee?")

for label, task in (("CONTEXT-DEPENDENT", BAD), ("STANDALONE", GOOD)):
    print(f"\n{'='*74}\n  {label}\n  task: {task}\n{'-'*74}")
    out = policy_worker(task)
    print(textwrap.fill(out["finding"], 72, initial_indent="  ",
                        subsequent_indent="  ")[:1400])
    print(f"\n  cited: {out['cited']}")
print()
