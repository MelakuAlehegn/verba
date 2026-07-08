"""A tiny, self-contained corpus + question set for retrieval eval.

Kept small and in-repo so runs are reproducible and cheap (a handful of
embedding calls). `billing.md` intentionally repeats the late-fee point across
several paragraphs — near-duplicate chunks that a plain top-k would stack,
giving MMR reranking a diversity win to demonstrate. Grow this over time; the
runner and metrics don't care how many cases there are.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalDoc:
    name: str
    text: str


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected_docs: tuple[str, ...]


CORPUS: list[EvalDoc] = [
    EvalDoc(
        name="billing.md",
        text=(
            "Invoices are issued on the first day of each month.\n\n"
            "Payment is due within 30 days of the invoice date.\n\n"
            "A late fee of 1.5% per month applies to any balance not paid within 30 days.\n\n"
            "Overdue invoices accrue a 1.5% monthly late charge until settled.\n\n"
            "Accounts more than 30 days past due are subject to the 1.5% monthly late fee.\n\n"
            "Refunds are processed to the original payment method within 10 business days."
        ),
    ),
    EvalDoc(
        name="security.md",
        text=(
            "All data is encrypted at rest using AES-256.\n\n"
            "Data in transit is protected with TLS 1.3.\n\n"
            "Access to production systems requires multi-factor authentication.\n\n"
            "Audit logs record every access to customer records."
        ),
    ),
    EvalDoc(
        name="onboarding.md",
        text=(
            "New accounts are created by an organization administrator.\n\n"
            "Single sign-on can be configured through SAML with your identity provider.\n\n"
            "Users receive an email invitation to set their password on first login.\n\n"
            "Default roles are Viewer, Editor, and Admin."
        ),
    ),
    EvalDoc(
        name="support.md",
        text=(
            "Support is available by email 24 hours a day.\n\n"
            "Priority phone support is included on the Enterprise plan.\n\n"
            "The typical first-response time is under four business hours."
        ),
    ),
]


CASES: list[EvalCase] = [
    EvalCase("What late fee applies to overdue invoices?", ("billing.md",)),
    EvalCase("When are payments due?", ("billing.md",)),
    EvalCase("How is customer data encrypted?", ("security.md",)),
    EvalCase("Is multi-factor authentication required?", ("security.md",)),
    EvalCase("How do I set up single sign-on?", ("onboarding.md",)),
    EvalCase("What roles can users have?", ("onboarding.md",)),
    EvalCase("How fast does support respond?", ("support.md",)),
]
