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

Nothing else in that metastore was touched.

## Local

```bash
# remove the two profiles added to ~/.databrickscfg
#   [agents-labs]     workspace
#   [agents-account]  account console
rm -rf "/Users/hadez/Documents/Company/training content/Agent_on_Databricks/.venv"
```

## Order

Delete the UC objects **first**, then the resource group. Dropping the storage
account before the catalog leaves the catalog pointing at storage that no longer
exists, which makes it awkward to delete cleanly.
