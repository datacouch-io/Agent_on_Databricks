# Teardown

Everything created for building these labs, and how to remove it.
The labs themselves are parameterised — they do not depend on any of this.

## Azure (one command removes all of it)

```bash
az group delete -n rg-agents-on-databricks --yes --no-wait
```

That resource group contains:

| Resource | Name |
|---|---|
| Databricks workspace (trial SKU) | `dbx-agents-labs` |
| Managed resource group | `databricks-rg-dbx-agents-labs-1p1zpq0e4cjuy` |
| ADLS Gen2 storage account | `stagentslabs1588` |
| Databricks access connector | `ac-agents-labs` |

## Unity Catalog — IMPORTANT, this is a *shared* metastore

The workspace was attached to the **existing** `eastus` metastore
`79599d4f-1385-479a-9715-1021f2e7e329`, which already held the `dbacademy`
catalogs from other workspaces. Deleting the resource group does **not** remove
UC objects. Remove only what this course created:

```bash
databricks catalogs delete agents_labs --force -p agents-labs
databricks external-locations delete sc-agents-loc -p agents-labs
databricks storage-credentials delete sc-agents-labs -p agents-labs
databricks account metastore-assignments delete 7405616584960877 79599d4f-1385-479a-9715-1021f2e7e329 -p agents-account
```

Dropping the catalog with `--force` takes its schemas, tables, functions,
volumes, **registered models, model aliases and the MLflow trace tables** with
it. The full inventory inside `agents_labs.retail`, for the record:

| Kind | Objects |
|---|---|
| Tables | `customers`, `orders`, `support_docs`, `support_chunks` |
| Functions | `get_order_summary`, `revenue_by_region` |
| Vector index | `support_chunks_idx` |
| Registered models | `support_agent` (v1–v3, aliases `@champion` `@challenger` `@previous`), `returns_adjudicator` (v1, `@champion`) |
| Trace tables | `<experiment_id>_otel_{spans,logs,metrics,annotations}`, one set per traced experiment |

Nothing else in that metastore was touched.

## Objects that live outside the catalog

These are **not** removed by dropping the catalog, and are not in the resource
group either. Delete them before the workspace goes:

```bash
# Vector Search endpoint — billed while it exists, so remove it even if you
# keep the workspace
databricks vector-search-endpoints delete-endpoint agents-labs-vs -p agents-labs

# Genie space and SQL warehouse (workspace objects)
#   Genie space   01f1bc6b0a4f1c6d8269cc9c1ec2af08   — delete from the UI
databricks warehouses delete c8729519c456cb8e -p agents-labs

# Service principal created for Lab 5B least-privilege probes
databricks service-principals list -p agents-labs   # find the id, then:
# databricks service-principals delete <id> -p agents-labs
```

MLflow experiments under `/Users/<you>/agents-labs-*` are workspace files and
go with the workspace. If you keep the workspace, remove them from the UI:
`agents-labs-3b`, `-6-deploy`, `-7a`, `-7b`, `-capstone`, `-capstone-models`.

> ⚠️ **The Vector Search endpoint is the one object that keeps costing money
> after you stop using the course.** It is not in the resource group and not in
> the catalog, so both of the "one command removes everything" steps miss it.

## Local

```bash
# remove the two profiles added to ~/.databrickscfg
#   [agents-labs]     workspace
#   [agents-account]  account console
rm -rf "/Users/hadez/Documents/Company/training content/Agent_on_Databricks/.venv"
rm -rf "/Users/hadez/Documents/Company/training content/Agent_on_Databricks/.venv312"
```

## Order

1. Vector Search endpoint (it is billed, and nothing else deletes it).
2. UC objects — catalog, external location, storage credential.
3. Metastore assignment.
4. The Azure resource group.

Delete the UC objects **first**, then the resource group. Dropping the storage
account before the catalog leaves the catalog pointing at storage that no longer
exists, which makes it awkward to delete cleanly.
