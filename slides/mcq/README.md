# Knowledge-check generator

    questions.py    the 28 questions: stem, four options, correct index,
                    why it is right, why the others fail
    gen_mcq.py      writes the 14 HTML slides and inserts them into deck.json
    pptx_build.py   applies the same change to the PPTX (capstone removal +
                    the 14 slides + page renumbering)

Run `gen_mcq.py` from this folder. It re-derives the balanced answer key each
time, so **explanations must never name an option by its letter** - the options
are permuted so that A, B, C and D are each correct exactly seven times.

`pptx_build.py` builds the new slides *before* removing the capstone ones. Do not
reverse that: python-pptx names a new slide part after the current slide count, so
removing first makes the new parts collide with existing ones and silently writes a
package with duplicate entries.

Both scripts are idempotent on deck.json (they strip any existing `-quiz` ids
first); `pptx_build.py` is not - it backs the PPTX up, then rewrites it from the
copy under the session scratchpad.
