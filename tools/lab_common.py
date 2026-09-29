"""
Shared helpers for the Agents on Databricks labs.

Works in two places without changes:
  * a Databricks notebook  — picks up the notebook's own credentials
  * your laptop            — uses a ~/.databrickscfg profile (default: DATABRICKS_PROFILE or "DEFAULT")

Nothing here is specific to the workspace the labs were authored in. Set
DATABRICKS_PROFILE (or run inside a notebook) and everything resolves.
"""
from __future__ import annotations
import os, functools

DEFAULT_CHAT_MODEL = os.environ.get("LAB_CHAT_MODEL", "databricks-claude-sonnet-5")
DEFAULT_EMBED_MODEL = os.environ.get("LAB_EMBED_MODEL", "databricks-gte-large-en")


def _in_notebook() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


@functools.lru_cache(maxsize=1)
def workspace():
    """A databricks-sdk WorkspaceClient, however we happen to be running."""
    from databricks.sdk import WorkspaceClient
    if _in_notebook():
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_PROFILE", "DEFAULT")
    return WorkspaceClient(profile=profile)


@functools.lru_cache(maxsize=1)
def bearer_token() -> str:
    """
    A bearer token for the serving endpoints.

    Note: WorkspaceClient.config.oauth_token() raises for azure-cli auth, so we
    read the Authorization header the SDK would send instead. That path works
    for every auth type.
    """
    return workspace().config.authenticate()["Authorization"].removeprefix("Bearer ")


def llm_client():
    """An OpenAI-compatible client pointed at this workspace's serving endpoints."""
    from openai import OpenAI
    w = workspace()
    return OpenAI(api_key=bearer_token(), base_url=f"{w.config.host}/serving-endpoints")


def host() -> str:
    return workspace().config.host
