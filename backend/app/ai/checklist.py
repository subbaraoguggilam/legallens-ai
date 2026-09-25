"""Next-steps and lawyer-question checklist (design doc section 2.5).

Built from the risk scanner's findings so the checklist is personalised to what
was actually detected in the user's document, with page/clause references kept.
"""
from __future__ import annotations

from app.ai.risk_scanner import RiskFinding, group_by_category

BASE_STEPS = [
    "Read the relevant clause completely, in its original wording.",
    "Confirm how each highlighted term applies to your specific situation.",
    "Ask the other party whether any unclear or one-sided terms are negotiable.",
    "Save a copy of the signed agreement and any amendments.",
]

QUESTION_TEMPLATES: dict[str, str] = {
    "Termination": "What exactly happens if either party ends this agreement, and under what conditions?",
    "Payment and penalties": "Are there any penalties, late fees or conditions attached to payment?",
    "Renewal and automatic renewal": "Does this agreement renew automatically, and how do I opt out?",
    "Liability and indemnity": "What am I liable for, and is that liability capped in any way?",
    "Confidentiality": "How long does the confidentiality obligation last after the agreement ends?",
    "Intellectual property": "Who owns work or ideas created during this agreement?",
    "Restrictive clauses": "How does the restrictive clause apply to my situation, and for how long?",
    "Dispute resolution and arbitration": "What happens if there is a disagreement — court, mediation or arbitration?",
    "Jurisdiction": "Which laws and courts apply if there is a dispute?",
    "Data and privacy": "How is my personal data used, stored and shared under this agreement?",
    "Notice period": "What happens if I don't give the full notice period?",
    "Refund and cancellation": "Under what conditions can I get a refund or cancel?",
}


def build_checklist(findings: list[RiskFinding]) -> dict:
    grouped = group_by_category(findings)
    situation = [
        {
            "category": cat,
            "page": items[0].page,
            "clause": items[0].clause,
            "needs_attention": any(i.needs_attention for i in items),
        }
        for cat, items in grouped.items()
    ]
    steps = list(BASE_STEPS)
    if any(s["needs_attention"] for s in situation):
        steps.append("Pay close attention to clauses flagged for review below before signing.")
    steps.append("Consider professional legal review, especially for flagged clauses.")

    questions = [QUESTION_TEMPLATES[cat] for cat in grouped if cat in QUESTION_TEMPLATES]
    if not questions:
        questions = ["What obligations does this document create for me, and are any of them unusual?"]

    return {"your_situation": situation, "next_steps": steps, "questions_for_a_lawyer": questions}
