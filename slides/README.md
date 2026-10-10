# Slide deck — Building Agentic AI Systems on Databricks

177 slides covering the seven sessions. The deck is authored as HTML and published as
a Slides Artifact; this folder is the source of truth for it.

The capstone was removed from the deck on 2026-10-08 — its three slides, and every
mention of it on seven other slides. `../capstone/` still holds the capstone material
itself; nothing there was touched.

Two running counts depended on it and were corrected with it. The capstone supplied one
of the wrong automated judgements (**four → three**, on `about`, `s6-divider`,
`s6-t2-why` and `s6-quiz-answers`) and two of the broken measuring instruments
(**six → four**, on `close-themes`, `close` and `s7-t6-pitfalls`). If the capstone ever
comes back, those numbers have to move with it.

Live deck: https://claude.ai/artifact/9AZq59YL7v7UADZRjFcYrz

## Layout

    project/deck.json        slide order, title, sections, fonts
    project/slides/*.html    one file per slide, named by id
    assets/                  documentation images (see assets/MAPPING.md)
    gen.py                   helpers used to generate slides consistently
    build_preview.py         regenerates preview.html from deck.json
    preview.html             standalone local view of every slide, with notes

`deck.json`'s `order` array is the running order. A slide file's `id` must match its
key in that array. Page numbers are written into each slide and must match the
slide's position in `order` — `gen.py` has the renumbering snippet.

## Structure

Every topic follows the same shape: **What** and **Why** as separate slides, then
**How**, **See it in action**, and **Do / Don't** where the topic warrants them.
Each slide carries 5–8 lines of speaker notes in its `<aside>`: how to explain it,
an analogy, a likely learner question with its answer, and a timing.

## Reviewer additions (2026-10-09)

Four slides added from Subhash's review:

    s4-why-now        bridges Session 3 into Genie - what the agent already has,
                      and the question it still cannot answer
    s5-t2-problem     the problem MCP solves (N x M connectors, duplicated
                      schemas, no interoperability), placed before MCP itself
    s7-t1-patterns    four multi-agent topologies: manager-workers,
                      planner-executor, hierarchical, swarm
    s7-t1-choose      when to reach for each, what it costs, how it fails

A fifth followed on 2026-10-09, after the Lab 1B and 6B fixes:

    s6-t3-parity      the deployed agent is not automatically the evaluated one:
                      configuration, version and behaviour, each checked

`s1-gate` and `s1-t3-what` were rebuilt the same day so the gate they show is the
four-rule gate Lab 1B now ships, not the two-condition one it used to.

The PPTX versions of these four were not hand-placed. `mcq/render_pptx.py` reads the
rendered geometry of each HTML slide out of a real browser and emits PPTX shapes at
those coordinates, so the two stay identical. It inserts by position in `deck.json`,
never by matching slide text - the agenda lists every session name, so an anchor like
"Databricks Genie" matches slide 2 and silently shifts the whole deck.

## Knowledge checks

Each session ends with two slides: `<sid>-quiz` (four multiple-choice questions) and
`<sid>-quiz-answers` (the correct option plus why the distractors fail). 28 questions
in all. The answer key is balanced — A, B, C and D are each correct exactly seven
times — so the pattern cannot be guessed; `mcq/gen_mcq.py` enforces that balance by
permuting the options, which means **the explanations must never refer to an option by
letter**. Each quiz slide's `<aside>` carries the answer key and how to run the poll.

Both slides use fixed-height rows and were checked against a real browser layout at
1920×1080: every one is exactly 1080px, with no overflow. If you edit the text,
re-check it — the earlier 2×2 grid overflowed by up to 335px and nothing in the
source made that visible.

## Previewing

    python3 build_preview.py && python3 -m http.server 8777
    open http://127.0.0.1:8777/preview.html

`build_preview.py` rewrites `/_blob/<id>` to the local files in `assets/` and applies
the `p{margin:0}` reset the artifact runtime provides. Without that reset every
paragraph picks up default browser margins and the slides measure far taller than they
really are.

## Images

Slides reference documentation images by artifact asset id (`/_blob/<id>`), so the
HTML stays publish-ready. The originals are in `assets/` with their source URLs in
`assets/MAPPING.md`. Opening a slide file directly in a browser will show broken
images — that is expected; view the deck at the link above.

These are Databricks' copyrighted screenshots, credited on each slide. Two of the
conceptual diagrams have been redrawn natively; two have not.

## Product naming

Databricks renamed several products in 2026. The deck uses the current names:
AI Search (was Vector Search), Genie Agent (was Genie space), Unity Gateway
(was AI Gateway), Foundation Models. Check against the live docs before reusing
this material — they moved once and will move again.
