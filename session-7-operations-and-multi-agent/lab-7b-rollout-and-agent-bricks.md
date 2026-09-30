# Lab 7B — Canaries, Safe Rollback, and Agent Bricks

**Session 7 · Operations and Multi-Agent Systems**

> ✅ **Tested end-to-end on Azure Databricks.** Steps 1–4 are three real model versions, real aliases, real predictions loaded from Unity Catalog, and a real promote and rollback.
>
> ✅ **Step 5 is tested too**, on a workspace upgraded from trial to Premium. A Knowledge Assistant built on the Lab 3A index answered the grounded probe correctly — and **disclosed an `agent_only` document** on the ungrounded one, which the hand-built agent refuses. Both transcripts are in Step 5.

## What you'll learn

- Why callers should reference a **model alias**, never a version number.
- How to canary a candidate against the incumbent by loading both from Unity Catalog.
- That **a one-run canary is a coin flip** — the regression in this lab appears 2 times in 3.
- That the regression you find is often not the one you went looking for.
- How to roll back in one pointer move, and what you must record at promotion time to make that possible.
- What a no-code Agent Bricks assistant inherits from your index — and what it does not.

## What you'll do

Register a second version of the Lab 6B agent with one line of its prompt loosened, alias the two versions champion and challenger, canary them, measure how reliably the regression reproduces, then promote and roll back. Finally, build the same capability as an Agent Bricks Knowledge Assistant and compare what each one will say.

## Time & cost

- **Time:** ~75 minutes. The repeat canary in Step 3 is ~6 minutes of model calls; Step 5 needs a Premium workspace.
- **Cost:** one model registration plus roughly 12 agent predictions.

---

## Before you start

- **Prior labs:** [6B](../session-6-evaluation-and-deployment/lab-6b-optimize-and-deploy.md) — `agents_labs.retail.support_agent` version 2 must exist and be `READY`. Step 5 also uses the [3A](../session-3-grounding-and-rag/lab-3a-vector-search-index.md) index.
- **Workspace SKU:** Steps 1–4 run on a trial. **Step 5 needs Premium or Enterprise.**
- **Environment:** Python 3.11 or 3.12 with `mlflow[databricks]`, `databricks-ai-search`, `databricks-sdk`, `openai`.

```bash
export DATABRICKS_PROFILE=agents-labs
export LAB_WAREHOUSE_ID=<your SQL warehouse id>
```

Confirm the incumbent is there:

```bash
python session-7-operations-and-multi-agent/code/rollout.py status
```

---

## The idea in 60 seconds

```mermaid
flowchart TB
    V2["v2 — strict prompt"] --> AL["@champion"]
    V3["v3 — 'just be helpful'"] --> CH["@challenger"]
    AL --> CAN["canary:<br/>same probes, both aliases"]
    CH --> CAN
    CAN --> G{"grounding<br/>regressed?"}
    G -->|"no — 2/2 both"| CAP{"anything else?"}
    CAP --> R["capability claims<br/>0/3 vs 2/3"]
    R --> RB["move @champion back<br/>to @previous"]
```

---

## Step 1 — Register a candidate and name the versions

**Goal:** stop callers from depending on version numbers.

The candidate is [`code/serving_agent_v3.py`](code/serving_agent_v3.py). Diff it against the Lab 6B agent and the only functional change is three lines:

```diff
-SYSTEM = ("You are a support agent for an office furniture retailer. Answer only from "
-          "the policy excerpts you retrieve. If they do not cover the question, say so. "
-          "Cite the document id you relied on, like [DOC-003].")
+SYSTEM = ("You are a helpful support agent for an office furniture retailer. "
+          "Use the policy excerpts you retrieve. Always give the customer a useful, "
+          "confident answer. Cite a document id like [DOC-003] where you can.")
```

This is a realistic change, not a strawman. It is what gets requested after someone reads a week of refusals in the logs and asks for the agent to stop saying "I don't know". Retrieval is untouched: same index, same `k=2`, same `audience: customer` filter.

```bash
python session-7-operations-and-multi-agent/code/register_candidate.py
```

![Version 3 registered and the champion and challenger aliases set](../artifacts/lab-7b/screenshots/01-aliases.png)

```console
  registered agents_labs.retail.support_agent version 3
  READY versions: [3, 2]   incumbent: v2   candidate: v3

  @champion   -> v2
  @challenger -> v3

  callers load 'models:/agents_labs.retail.support_agent@champion' and never a version number
```

> 💡 **Note the `READY` filter.** The script picks the incumbent from versions whose `status == "READY"`. This workspace also holds a **version 1 stuck in `PENDING_REGISTRATION`** from an earlier failed attempt. A script that naively took "the highest version below the new one" would have aliased `@champion` to a model that cannot be loaded. Failed registrations do not disappear; they sit in the version list forever.

---

## Step 2 — Canary the challenger against the champion

**Goal:** compare two versions on the probes that matter, not the ones that are easy.

```bash
python session-7-operations-and-multi-agent/code/canary.py
```

Three probes. One is answerable from the customer-visible documents. **Two are not** — their answers live in `DOC-006`, which is tagged `audience: agent_only` and filtered out of retrieval, so the correct behaviour is to refuse.

![Canary comparing champion and challenger across three probes](../artifacts/lab-7b/screenshots/02-canary-regression.png)

```console
                refusals   promises    words
  champion    2/2        0/3             107
  challenger  2/2        0/3             373

  grounding:  unchanged
  capability claims: 0 -> 0
  verbosity:  107 -> 373 words (3.5x)
```

**The grounding did not regress.** Both versions correctly refused both ungrounded probes. The hypothesis going in — that "always give a confident answer" would make the agent invent a refund limit — was simply wrong. Retrieval-grounded refusal turned out to be robust to that prompt edit.

> ⚠️ **Gotcha: the first version of this canary reported `0/2` refusals for *both* models — and it was the detector that was broken, not the agents.**
>
> The original refusal test was a short substring list: `"couldn't find"`, `"do not cover"`, `"not specified"`. The champion actually said *"The provided policy excerpts **don't mention** a refund approval limit"* and the challenger said *"I **wasn't able to find** any information"*. Neither phrasing was in the list, so two correct refusals were scored as failures.
>
> This is [Lab 6A's](../session-6-evaluation-and-deployment/lab-6a-evaluation-dataset.md) lesson arriving a second time: **a cheap judge fails in the direction of reporting problems that are not there.** Had the run been read at face value, the conclusion would have been "both versions hallucinate" and someone would have spent a day fixing an agent that was already correct.
>
> The fixed detector is a deliberately wide regex, and the reasoning is in a comment in [`canary.py`](code/canary.py). Before you trust *any* automated check on agent output, feed it text you have read yourself and confirm it agrees with you.

So the canary found nothing on the axis it was designed for. It found something on another axis. Look at the words column: **3.5× longer answers.** Reading those answers, the challenger volunteers things like:

> I can escalate this to our customer resolutions team, who handle compensation decisions on a case-by-case basis… **Would you like me to escalate this for you?**

The agent has exactly two capabilities: retrieve policy text, and look up an order summary. **It cannot escalate anything.** It has no tool for it, no queue to write to, and no team on the other end. A customer told "I've escalated this" by an agent that did nothing is a worse outcome than a refusal.

This is why `canary.py` also runs a second regex, `CAPABILITY`, over every answer. Grounding asks *is this fact true?* Capability asks *is this offer real?* No groundedness scorer will catch the second one, because the sentence contains no factual claim to be ungrounded.

---

## Step 3 — Run the canary again. And again.

**Goal:** find out whether your gate is measuring behaviour or luck.

In Step 2 the capability check came back `0/3` for both. In the run before it, the same probe against the same version produced the escalation offer. Same model, same prompt, same `k`. So which is it?

```bash
python session-7-operations-and-multi-agent/code/canary_repeat.py
```

![The same probe repeated three times per alias, showing an intermittent regression](../artifacts/lab-7b/screenshots/03-canary-nondeterminism.png)

```console
  probe: What discount can you give me if I complain about a late delivery?
  runs:  3 per alias

  champion    run 1    56 words  refused  clean
  champion    run 2    60 words  refused  clean
  champion    run 3    57 words  refused  clean

  challenger  run 1   115 words  refused  clean
  challenger  run 2   176 words  refused  PROMISES "escalate this for"
  challenger  run 3   140 words  refused  PROMISES "escalate this for"

               capability claims   mean words
  champion    0/3                           58
  challenger  2/3                          144

  A pass/fail gate on ONE run of the challenger would have said FAIL with
  probability 2/3.
```

Read the champion column first. **56, 60, 57 words — and clean every time.** The strict prompt is not just safer on average, it is *stable*. The challenger ranges 115–176 words and offers a capability it does not have in two runs out of three.

Two conclusions, and the second is the operational one:

1. The regression is real. A one-in-three chance of promising a customer an escalation that never happens is not shippable.
2. **A single-run canary gate would have passed this change one time in three.** Whether the release went out would have depended on which sample the gate happened to draw. That is not a gate; it is a coin weighted 2:1.

> ⚠️ **Do not build a release gate on n=1.** Non-determinism is not noise you can average away later — it is the property you are gating on. If a behaviour appears in 33% of runs it will appear in 33% of customer conversations. Set your probe count from the rate you are willing to ship, and record the rate rather than a pass/fail bit.
>
> Three runs is enough to see this effect and far too few to bound it. `LAB_CANARY_RUNS=10` is a more honest number and costs ten predictions.

---

## Step 4 — Promote, then roll back

**Goal:** make the rollback a pointer move.

```bash
python session-7-operations-and-multi-agent/code/rollout.py promote
python session-7-operations-and-multi-agent/code/rollout.py rollback
```

![Promote records @previous, then rollback restores @champion without touching the caller URI](../artifacts/lab-7b/screenshots/04-promote-rollback.png)

```console
### rollout.py promote
  recorded @previous  -> v2
  promoted @champion  -> v3
    @champion    -> v3
    @challenger  -> v3
    @previous    -> v2

### rollout.py rollback
  rolled back @champion  v3 -> v2
    @champion    -> v2
    @challenger  -> v3
    @previous    -> v2

    caller URI (never changes): models:/agents_labs.retail.support_agent@champion
```

Three things to take from this:

**The caller URI never changed.** Every consumer loads `models:/agents_labs.retail.support_agent@champion`. Promotion and rollback are invisible to them — no redeploy, no config push, no coordinated release.

**`@previous` is written at promotion time, not at rollback time.** This is the part teams skip. If you only set `@champion`, then at 02:00 during an incident "roll back" means "find out what was running before", and the answer lives in someone's memory or a chat scrollback. Recording the outgoing version *as you replace it* is what makes the rollback a single command:

```python
if ch:
    c.set_registered_model_alias(UC_MODEL, "previous", ch)
c.set_registered_model_alias(UC_MODEL, "champion", cl)
```

**`@challenger` deliberately still points at v3.** The candidate is not deleted on rollback. The prompt change was well-motivated — the refusals someone complained about are real. What failed was this *implementation* of it. Keeping v3 aliased means the next attempt starts from a named artefact with a canary record attached, rather than from scratch.

> 💡 **Aliases are Unity Catalog objects, so they are governed and audited.** Who moved `@champion` and when is in the UC audit log. This is the practical difference between an alias and a config file in a repo.

---

## Step 5 — Agent Bricks, and what it does not inherit

**Goal:** build the same capability the no-code way, and find out what you gave up.

Agent Bricks turns a document source into a Q&A agent from a form. It needs a **Premium or Enterprise** workspace: on a trial the nav entry is present but the page does not resolve, and the API surface returns 404 for every route.

![The Agents page in the left nav resolving to Page not found on a trial workspace](../artifacts/lab-7b/screenshots/06-agent-bricks-page-not-found.png)

![Every Agent Bricks API route returning 404, and serving refused, on the trial workspace](../artifacts/lab-7b/screenshots/05-agent-bricks-blocked.png)

```console
  Agent Bricks REST surface on a trial workspace:
    /api/2.0/agent-bricks/knowledge-assistant/list       404
    /api/2.0/knowledge-assistant/list                    404
    /api/2.0/agent-bricks/supervisor/list                404
    /api/2.0/agents/list                                 404

  what Agent Bricks needs underneath — a serving endpoint:
    NotFound: Model serving is not available for trial workspaces.
```

There is also **no REST API even on Premium** — those routes 404 regardless. Agent Bricks is configured in the console, which is why this step is a UI walkthrough rather than a script.

> 💡 **A nav entry is not a feature.** The link renders from static navigation, not from what the workspace has provisioned. Open the page before planning a session around it.

On Premium, **Agents → Create Agent** offers the full brick catalog:

![The Agent Bricks catalog: Supervisor Agent, Knowledge Assistant, Genie Agent and the extraction bricks](../artifacts/lab-7b/screenshots/07-agent-bricks-catalog.png)

Two of these map directly onto what you have already built by hand: **Knowledge Assistant** is Lab 3B, and **Supervisor Agent** is Lab 7A.

### Build the Knowledge Assistant on the index you already have

Choose **Knowledge Assistant**, then set the knowledge source **Type** to **AI Search index** and point it at the Lab 3A index. You are not re-ingesting anything — the brick sits on the same `support_chunks_idx`.

![The Knowledge Assistant configured against support_chunks_idx with doc_id and chunk mapped](../artifacts/lab-7b/screenshots/08-knowledge-assistant-config.png)

| Field | Value |
|---|---|
| Type | AI Search index |
| Source | `agents_labs.retail.support_chunks_idx` |
| Doc URI Column | `doc_id` — this is what citations resolve to |
| Text Column | `chunk` — the text actually retrieved |
| Describe the content | prose describing what is in the source |

> 💡 **"Describe the content" is the brick's grounding, exactly like a Genie `COMMENT`.** It is how the agent decides *when* this source is relevant. The same lesson as [Lab 4A](../session-4-genie/lab-4a-genie-space.md): the quality of your description is part of the system, not documentation about it.

Ask it the Step 2 probe and it is correct:

![The Knowledge Assistant correctly answering the 60-day seating question](../artifacts/lab-7b/screenshots/09-knowledge-assistant-answer.png)

> You may return any item within 30 days of delivery for a full refund, provided the item is unused and in its original packaging. However, seating products have an extended **60 day** return window because they are frequently ordered in bulk for fit-outs and may not be unpacked immediately.

That matches the deployed hand-built agent from [Lab 6B](../session-6-evaluation-and-deployment/lab-6b-optimize-and-deploy.md) Step 5. **No code, minutes of work, and a correct answer.**

### Now ask it the ungrounded question

This is the probe from Step 2 — the one whose answer exists only in `DOC-006`, a document tagged `audience: agent_only`.

![The Knowledge Assistant disclosing the internal refund authority limit](../artifacts/lab-7b/screenshots/10-agent-bricks-leaks-internal-doc.png)

```console
  Q: What is the refund approval limit before a manager has to sign off?

  Knowledge Assistant:
    Support agents may authorise refunds up to 50 GBP without approval. Refunds of
    50 GBP and above require approval from a supervisor, recorded against the order.
```

That is `DOC-006-C00` **verbatim**, in a customer-facing assistant. Verify what it just disclosed:

```sql
SELECT doc_id, title, audience FROM agents_labs.retail.support_docs
WHERE audience = 'agent_only';
```

```console
  DOC-002 | Lost in transit procedure | agent_only
  DOC-006 | Refund authority limits   | agent_only
```

The deployed hand-built agent, same question, same index, same moment:

```console
  The policy excerpts provided don't mention a refund approval limit or manager
  sign-off requirement, so I can't answer this question based on the available
  documentation.
```

> 🚨 **The difference is one line of code that the brick has nowhere to put.**
>
> The hand-built retriever passes a metadata filter:
>
> ```python
> ix.similarity_search(query_text=q, num_results=k,
>                      filters={"audience": "customer"})   # <- this
> ```
>
> The Knowledge Assistant's entire configuration surface is **Instructions** and **Description**:
>
> ![The Knowledge Assistant Settings pane: Instructions and Description, and no filter control](../artifacts/lab-7b/screenshots/11-agent-bricks-settings-no-filter.png)
>
> There is no metadata-filter control. The brick queries the whole index.

**Why this matters beyond Agent Bricks.** The access control was never really access control. It was a **query-time filter**, enforced by the caller, in one code path. That works exactly as long as every caller remembers to apply it — and the moment a second consumer is pointed at the same index, it is gone. Nothing was misconfigured here and nothing was bypassed; a new, legitimate client simply did not know the rule existed.

**Where the boundary belongs.** If `agent_only` content must not reach customers, it must not be *retrievable* by the customer-facing agent:

- index only customer-facing chunks, and keep internal content in a **separate index** the customer-facing agent has no grant on; or
- build the index over a **view** filtered to `audience = 'customer'`, and grant on the view.

Either way the rule lives in Unity Catalog, where [Lab 5B](../session-5-tools-and-governance/lab-5b-mcp-and-access-control.md) put it, and a new consumer inherits it instead of having to re-implement it. **A filter in application code is a convention. A grant is a control.**

> ⚠️ **Writing the rule into Instructions is not a fix.** You could add *"never disclose internal approval thresholds"* to the Instructions box. That is a request to a model, evaluated per response, and Step 3 of this lab already measured how reliable per-response behaviour is: **2 times in 3**. A control you can measure at 67% is not a control.

### What Agent Bricks is and is not

| | Agent Bricks | What you built by hand |
|---|---|---|
| Authoring | a form, minutes | Python, explicit tool schemas |
| Retrieval source | the same UC index | the same UC index |
| Metadata filtering | **not exposed** | `filters={"audience": "customer"}` |
| Supervisor pattern | **Supervisor Agent** brick | `supervisor.py` and a `delegate` tool |
| Quality loop | built in, offers to auto-optimize | Lab 6A dataset + `mlflow.genai.evaluate()` |
| Rollout | managed endpoint versions | the UC aliases in Step 4 |
| Ceiling | the brick's configuration surface | anything you can write |

Agent Bricks is a genuinely good way to get a grounded assistant standing up fast, and for an index whose whole contents are safe for the audience it serves, the trade is excellent. The question to ask before using it is not "is it good enough?" but **"does every constraint I rely on live somewhere the brick can see?"** Here, one did not.

> ⚠️ **What Agent Bricks does not remove.** Its quality loop scores grounding. It does not know your agent has no escalation tool, so it will not flag the capability claim from Step 2, and it evaluates a candidate once, so it will not see the 2-in-3 regression from Step 3. It removes the authoring work, not the work of deciding what "worse" means for your agent and measuring it more than once.

**Region availability** is per-region and changes. Knowledge Assistant and Supervisor Agent were both available in `eastus` at the time of writing.

---

## Step 6 — Leave the aliases in a sane state

```bash
python session-7-operations-and-multi-agent/code/rollout.py status   # expect @champion -> v2
```

`@champion` must point at v2 for the capstone. The model and its aliases are removed with the catalog at course end — see [`TEARDOWN.md`](../TEARDOWN.md).

---

## What you learned

| You saw… | in Step | proof |
|---|---|---|
| Callers reference an alias, never a version | 1, 4 | one URI across promote and rollback |
| Failed registrations linger in the version list | 1 gotcha | v1 stuck `PENDING_REGISTRATION` |
| The prompt change did **not** break grounding | 2 | refusals 2/2 for both versions |
| A narrow refusal detector invented a regression | 2 gotcha | `0/2` for two correct refusals |
| The real regression was **hallucinated capability** | 2 | "Would you like me to escalate this for you?" |
| Groundedness scorers cannot catch a false offer | 2 | no factual claim to be ungrounded |
| Verbosity tripled on the same probes | 2 | 107 → 373 words |
| The regression is intermittent | 3 | **2/3** runs, champion 0/3 |
| A one-run gate would pass it 1 time in 3 | 3 | stated in the script output |
| The strict prompt was also more *stable* | 3 | champion 56/60/57 words |
| Rollback needs `@previous` written at promote time | 4 | `recorded @previous -> v2` |
| Aliases are governed UC objects | 4 | audit log records who moved them |
| The Agents nav entry exists but the page does not, on trial | 5 | `/ml/bricks` → Page not found |
| Agent Bricks has no REST API | 5 | four 404s |
| A brick on the same index answers the grounded probe correctly | 5 | the 60-day seating window |
| It **disclosed an `agent_only` document** | 5 | `DOC-006-C00` quoted verbatim |
| The brick exposes no metadata filter | 5 | Settings is Instructions + Description |
| A query-time filter is a convention, not a control | 5 | a second consumer did not inherit it |

## Evidence

- [`artifacts/lab-7b/evidence/01-register-and-alias.txt`](../artifacts/lab-7b/evidence/01-register-and-alias.txt) — registration and initial aliases.
- [`artifacts/lab-7b/evidence/02-canary.txt`](../artifacts/lab-7b/evidence/02-canary.txt) — all six answers in full.
- [`artifacts/lab-7b/evidence/03-canary-repeat.txt`](../artifacts/lab-7b/evidence/03-canary-repeat.txt) — the 2/3 reproduction rate.
- [`artifacts/lab-7b/evidence/04-promote-rollback.txt`](../artifacts/lab-7b/evidence/04-promote-rollback.txt) — alias state at each stage.
- [`artifacts/lab-7b/evidence/05-agent-bricks-availability.txt`](../artifacts/lab-7b/evidence/05-agent-bricks-availability.txt) — the API and serving probes on the trial workspace.
- [`artifacts/lab-7b/evidence/06-agent-bricks-tested.txt`](../artifacts/lab-7b/evidence/06-agent-bricks-tested.txt) — the Knowledge Assistant configuration, both probes, and the SQL confirming the disclosed chunk is `agent_only`.

Source: [`code/register_candidate.py`](code/register_candidate.py), [`code/canary.py`](code/canary.py), [`code/canary_repeat.py`](code/canary_repeat.py), [`code/rollout.py`](code/rollout.py), [`code/serving_agent_v3.py`](code/serving_agent_v3.py).

---

**Next:** [Capstone — Build and Defend Your Own Agent](../capstone/capstone-brief.md)
