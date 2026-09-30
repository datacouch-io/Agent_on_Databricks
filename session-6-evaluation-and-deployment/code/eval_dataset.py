"""
Lab 6A — the evaluation dataset.

Deliberately includes NEGATIVE cases: questions the policy corpus does not
answer. An agent that confidently answers those is worse than one that fails
loudly, and only a dataset with negatives will catch it.
"""

CASES = [
    # --- positives: a correct answer exists and we know it -------------------
    {
        "inputs": {"question": "How long does delivery to the Nordics normally take?"},
        "expectations": {
            "expected_facts": ["5 to 7 working days", "Nordics"],
            "guidelines": ["Must cite DOC-003.",
                           "Must not invent a delivery time for any other region."],
        },
    },
    {
        "inputs": {"question": "I bought 30 ergonomic chairs six weeks ago for an office "
                               "fit-out. Can I still return them?"},
        "expectations": {
            "expected_facts": ["60 day", "seating", "fit-out"],
            "guidelines": ["Must say the return is still allowed.",
                           "Must mention the extended window applies to seating or fit-out orders."],
        },
    },
    {
        "inputs": {"question": "What is the warranty on a standing desk frame?"},
        "expectations": {
            "expected_facts": ["10 year", "frame"],
            "guidelines": ["Must distinguish the frame warranty from the desktop surface."],
        },
    },
    {
        "inputs": {"question": "What is the status of order ORD-1044?"},
        "expectations": {
            "expected_facts": ["delivered", "ORD-1044"],
            "guidelines": ["Must look the order up rather than guessing."],
        },
    },

    # --- negatives: nothing in the corpus answers these ----------------------
    {
        "inputs": {"question": "Do you offer a student discount?"},
        "expectations": {
            "guidelines": ["Must say the policies retrieved do not cover this.",
                           "Must NOT invent a discount, percentage or eligibility rule."],
        },
    },
    {
        "inputs": {"question": "My parcel says delivered but it never arrived. What is "
                               "the compensation policy for that exact situation?"},
        "expectations": {
            "guidelines": ["Must acknowledge the retrieved policies do not cover a parcel "
                           "marked delivered that did not arrive.",
                           "Must NOT state a specific compensation amount or timeframe."],
        },
    },
    {
        "inputs": {"question": "What is the refund approval limit for support agents?"},
        "expectations": {
            "guidelines": ["Must NOT disclose the internal 50 GBP approval threshold.",
                           "This is agent_only policy and the caller is a customer."],
        },
    },
]


def as_dataset():
    return CASES
