# -*- coding: utf-8 -*-
"""Three reviewer requests (Subhash, 2026-10-09):
   1. frame the problem MCP solves, before MCP
   2. more depth on multi-agent topologies
   3. a 'why Genie now?' bridge at the top of Session 4
"""
import sys, json, pathlib
sys.path.insert(0, "/Users/hadez/Documents/Company/training content/Agent_on_Databricks/slides")
from gen import (slide, h2, eyebrow, lead, cards, card, cols, panel, bar, callout,
                 rows, row, node, arrow, chain, stack, band, figure, mono)

ROOT = pathlib.Path("/Users/hadez/Documents/Company/training content/Agent_on_Databricks/slides")

# ---------------------------------------------------------------- 1. s4-why-now
slide("s4-why-now", 0, [
  eyebrow("Session 3 &rarr; Session 4"),
  h2("Why Genie, and why now?"),
  lead("Three sessions built an agent that can read your prose. Here is what you already "
       "have &mdash; and the question it still cannot answer."),
  cards([
    card("The loop", "Bounded, with tools described as schemas and a gate that reads the "
         "argument the model composed."),
    card("The seam", "One retrieval interface, two sources behind it, and an adapter so the "
         "same agent runs in four places."),
    card("The grounding", "A governed index in Unity Catalog, and traces you can query as "
         "an ordinary table."),
  ]),
  cols([
    panel("What none of it answers",
          "&ldquo;What was revenue last month?&rdquo; is not a document lookup. It is SQL over governed "
          "tables, and it needs rules that appear nowhere in your prose &mdash; which status means the "
          "order never happened, which rows are test accounts."),
    bar("The build-it-yourself path",
        "A schema in a prompt writes plausible SQL and knows no business rules. Everything you "
        "would add next &mdash; scope limits, definitions, examples, a regression suite &mdash; is "
        "what this session is about."),
  ]),
  callout("Same boundary, second half",
          "Genie is not a second agent framework. It is the <b>structured</b> half of the agent you "
          "already built &mdash; same catalog, same grants, same lineage. This session curates it; "
          "Session 5 calls it as a single tool.", icon="Database", tone="grey"),
], gap=22, notes="""This slide exists because the jump into Genie reads as a change of subject if you do not frame it.

Say the shape of the course out loud: Sessions 1 and 2 built the agent, Session 3 grounded it in documents. Everything so far retrieves prose. Genie is the other half of retrieval - the structured half - and it is not a different platform, it is the same Unity Catalog boundary from Session 3.

The honest framing is the second panel. Nobody needs convincing that text-to-SQL is possible; they need to see that the hard part is curation, and that curation needs somewhere governed to live. That is the whole session in one sentence.

Expected question: "Could we just give the agent a run_sql tool?" You could, and Session 5 shows what that costs - the rule then lives in your caller instead of at the data, and the next caller inherits nothing.

Timing: 3 minutes. It is a bridge, not a topic.""")

# ---------------------------------------------------------------- 2. s5-t2-problem
def mini(title, left, right, caption, bandtxt, tone="grey"):
    return figure(chain([stack(left, gap=10, flex=1), arrow(), stack(right, gap=10, flex=1)],
                        gap=18, align="center") + band(bandtxt, tone),
                  caption)

slide("s5-t2-problem", 0, [
  eyebrow("Before the protocol"),
  h2("Every tool integration used to be bespoke"),
  lead("Three problems, each one solved again by every team that met it."),
  cards([
    card("Custom connectors", "Every client needed its own adapter for every tool set. Four "
         "clients and five tool sets is twenty integrations, each maintained by somebody."),
    card("Duplicated schemas", "The same tool described again in every codebase that calls it. "
         "Four wordings of " + mono("get_order") + ", four behaviours, and no way to tell which drifted."),
    card("No interoperability", "A tool built for your agent cannot be used by a notebook or "
         "another team &mdash; not without an adapter nobody wants to own."),
  ]),
  cols([
    mini("", [node("Agent A"), node("Agent B"), node("Notebook")],
         [node("Orders tools"), node("Policy tools"), node("Finance tools")],
         "Every client speaks every tool set&rsquo;s own dialect.",
         "N &times; M bespoke integrations"),
    mini("", [node("Agent A"), node("Agent B"), node("Notebook")],
         [node("MCP server", "one per UC schema", tone="accent"),
          node("tools/list", "filtered by identity", tone="ghost"),
          node("tools/call", "definer&rsquo;s rights", tone="ghost")],
         "One wire format, so any client can use any server.",
         "N + M, one contract", tone="alert"),
  ]),
], gap=22, notes="""Do not skip to the protocol. Spend a minute on the arithmetic, because it is what makes MCP feel inevitable rather than fashionable.

Four clients, five tool sets, twenty integrations - and the number grows multiplicatively, so the second client is cheap and the fifth is not. Ask the room how many internal "connector" repositories they own. The answer is usually more than they expected.

The middle card is the one engineers feel. The same tool described in four codebases is four prompts, because a tool description is prompt text. They drift, and the drift shows up as the model picking the wrong tool in one client and not another.

Then the turn: MCP does not make your tools safer. It makes them reachable - and that is precisely why the next slide is about who is asking.

Expected question: "Is this just OpenAPI again?" Fair challenge. The difference is that the contract is written for a model rather than a programmer: descriptions, not just types, and discovery that depends on the caller's identity.

Timing: 4 minutes.""")

# ---------------------------------------------------------------- 3. s7-t1-patterns
def pat(name, topo, text):
    return ('<div style="flex:1;display:flex;flex-direction:column;gap:14px;background:#FFFFFF;'
            'padding:21px 28px;border:1px solid #E3E6EA;border-radius:12px">'
            '<p style="font-size:28px;font-weight:700;color:#8B0000">%s</p>'
            '%s'
            '<p style="font-size:24px;color:#4A5568;line-height:1.38">%s</p></div>' % (name, topo, text))

n = lambda l, s="", t="white": node(l, s, tone=t, fs=20, sfs=16)

slide("s7-t1-patterns", 0, [
  eyebrow("Four shapes"),
  h2("Supervisor&ndash;workers is one topology, not the only one"),
  lead("The mechanism never changes &mdash; a worker is a tool, and a model chooses. "
       "What changes is who holds the plan, and who decides when to stop."),
  cols([
    pat("Manager &ndash; Workers",
        chain([n("Manager", "routes"), arrow(w=40), stack([n("Orders"), n("Policy")], gap=8, flex=1)],
              gap=12, align="center"),
        "One router, narrow specialists. The manager owns the decision and the stopping "
        "condition. Lab 7A, and the default for clear domains."),
    pat("Planner &ndash; Executor",
        chain([n("Planner", "writes a plan"), arrow(w=40), n("Plan", "inspectable", "ghost"),
               arrow(w=40), n("Executor", "runs steps")], gap=10, align="center"),
        "The plan is produced once, as an artefact you can read, approve or diff &mdash; then "
        "executed. For when the sequence matters more than the routing."),
  ], gap=28),
  cols([
    pat("Hierarchical",
        chain([n("Lead", "top"), arrow(w=40),
               stack([n("Sub-manager A"), n("Sub-manager B")], gap=8, flex=1), arrow(w=40),
               n("Workers", "per domain", "ghost")], gap=10, align="center"),
        "Managers of managers. Each level narrows the tool set further, buying team "
        "boundaries at the price of a hop per level."),
    pat("Swarm &ndash; peer handoff",
        chain([n("Agent A"), arrow(w=34), n("Agent B"), arrow(w=34), n("Agent C")],
              gap=10, align="center"),
        "No router. Each agent hands control to a peer as the conversation moves. Flexible, "
        "and the hardest to bound &mdash; nobody owns termination."),
  ], gap=28),
], gap=22, notes="""The point of this slide is that these are not four technologies. They are four answers to one question: who holds the plan?

Manager-workers: the manager holds it, implicitly, one decision at a time. Planner-executor: the plan is written down before anything runs, which is the only pattern here where a human can approve it. Hierarchical: the plan is split across levels. Swarm: nobody holds it.

Walk the diagrams, not the prose. Each one is the same mechanism from the previous slide - a worker exposed as a tool, a model choosing - rearranged.

The one to dwell on is planner-executor, because it is the pattern people have not usually considered and it is the one that makes a multi-step agent auditable. A written plan is a thing you can diff between runs, which is what Session 6 will ask of everything else.

Expected question: "Which does LangGraph give me?" All of them - it is a graph runtime, not a pattern. That is the Session 2 argument again: the framework supplies the plumbing, you still choose the shape.

Timing: 5 minutes.""")

# ---------------------------------------------------------------- 4. s7-t1-choose
slide("s7-t1-choose", 0, [
  h2("Choosing a shape &mdash; and what each one costs"),
  rows([
    row("Manager &ndash; Workers",
        "<b>Reach for it when</b> requests fall into clear domains, or workers need different identities. "
        "<b>It costs</b> one extra model call per request. "
        "<b>It fails</b> by routing correctly and handing off incompletely &mdash; Lab 7A&rsquo;s result.", w=360),
    row("Planner &ndash; Executor",
        "<b>Reach for it when</b> the task is multi-step and the plan should be inspectable, approved or "
        "diffed before anything runs. <b>It costs</b> a planning round trip. "
        "<b>It fails</b> wholesale: a plausible plan executed faithfully, every step correct, the goal wrong.", w=360),
    row("Hierarchical",
        "<b>Reach for it when</b> one supervisor can no longer hold the tool set, or separate teams own "
        "separate branches. <b>It costs</b> latency and context at every level. "
        "<b>It fails</b> by dilution &mdash; each hop passes a little less than it received.", w=360),
    row("Swarm &ndash; peer handoff",
        "<b>Reach for it when</b> control should follow the conversation rather than a fixed map. "
        "<b>It costs</b> you the single routing record a trace is easiest to read from. "
        "<b>It fails</b> by circling &mdash; two agents handing the same request back and forth, with no "
        "owner for the stopping condition.", w=360),
  ], gap=13),
  callout("The order to try them in",
          "One agent. Then manager&ndash;workers. Everything beyond that needs a reason you can say out loud "
          "&mdash; tool count, identity, ownership or model &mdash; and a bounded loop at every level that can route.",
          icon="Lightbulb", tone="alert"),
], """This is the slide to photograph. Read the failure column down the page: incomplete handoff, a faithful execution of a wrong plan, dilution, circling. Four patterns, four distinct ways to be confidently wrong.

Planner-executor deserves the warning it gets. Every individual step can be correct and the outcome still wrong, because the mistake was made once, early, and then followed obediently. That failure is invisible in step-level traces and obvious in the plan - which is the argument for writing the plan down.

Swarm is the one people are most attracted to and least ready for. Ask who owns MAX_STEPS in a swarm. There is no good answer, which is the answer.

Tie it back: the reasons to split are the four from the previous slide - tools, identity, owner, model. If none of them applies, the shape you want is one agent.

Expected question: "Where does Agent Bricks fit?" It is not a topology - it is somebody else's agent. That is the next topic.

Timing: 4 minutes.""")

print("wrote 4 slides")

# three of these run a touch tall at the stock 160px bottom padding; the footer
# rule sits at bottom:96px, so 132px still clears it with room to spare.
for sid in ("s4-why-now", "s5-t2-problem", "s7-t1-patterns"):
    f = ROOT / "project" / "slides" / (sid + ".html")
    t = f.read_text()
    assert "padding:128px 128px 160px" in t, sid
    f.write_text(t.replace("padding:128px 128px 160px", "padding:112px 128px 132px", 1))
print("padding tightened on 3 slides")
