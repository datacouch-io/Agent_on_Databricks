"""
Lab 7B step 4 — promote and roll back by moving an alias.

    python rollout.py status
    python rollout.py promote     # champion -> the current challenger
    python rollout.py rollback    # champion -> the previous champion

Nothing about the caller changes. It loads models:/<model>@champion before and
after. That is the entire value of the alias: the rollback is a pointer move,
not a redeploy, and it does not depend on anyone remembering a version number.

The previous champion is recorded as a third alias, @previous, at promotion
time. Without it, "roll back" means "ask someone what was running before".
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow
from mlflow import MlflowClient

UC_MODEL = "agents_labs.retail.support_agent"


def client() -> MlflowClient:
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    mlflow.set_registry_uri("databricks-uc")
    return MlflowClient()


def resolve(c: MlflowClient, alias: str):
    try:
        return c.get_model_version_by_alias(UC_MODEL, alias).version
    except Exception:
        return None


def status(c: MlflowClient):
    print(f"  {UC_MODEL}")
    for alias in ("champion", "challenger", "previous"):
        v = resolve(c, alias)
        print(f"    @{alias:11} -> {'v' + v if v else '(unset)'}")
    print(f"\n    caller URI (never changes): models:/{UC_MODEL}@champion")


def promote(c: MlflowClient):
    ch, cl = resolve(c, "champion"), resolve(c, "challenger")
    if not cl:
        sys.exit("  no @challenger set")
    if ch:
        c.set_registered_model_alias(UC_MODEL, "previous", ch)
        print(f"  recorded @previous  -> v{ch}")
    c.set_registered_model_alias(UC_MODEL, "champion", cl)
    print(f"  promoted @champion  -> v{cl}\n")
    status(c)


def rollback(c: MlflowClient):
    prev, ch = resolve(c, "previous"), resolve(c, "champion")
    if not prev:
        sys.exit("  no @previous recorded — nothing to roll back to")
    if prev == ch:
        print(f"  @champion is already v{prev}")
    c.set_registered_model_alias(UC_MODEL, "champion", prev)
    print(f"  rolled back @champion  v{ch} -> v{prev}\n")
    status(c)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    c = client()
    {"status": status, "promote": promote, "rollback": rollback}[cmd](c)
