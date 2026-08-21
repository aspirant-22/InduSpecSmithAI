"""Canonical fact/evidence representation for extracted product information.

Every extracted attribute is a Fact carrying its own provenance:

    label      canonical ATTRIBUTE_LABEL
    value      normalized value ('' when unknown)
    uom        unit-of-measure token ('' when none)
    source     input column the fact came from
    evidence   the exact matched span in the source text
    status     COPIED | NORMALIZED | DERIVED | INFERRED | UNKNOWN

Status rules for Phase 4:
    COPIED      value taken verbatim from the input row
    NORMALIZED  deterministic normalization of a supported source token
    DERIVED     deterministic transform of already-supported information
    INFERRED    category-level guess - NEVER emitted into the output
    UNKNOWN     insufficient evidence - value stays blank

Fact implements __iter__ yielding (label, value, uom) so existing consumers
that unpack attribute triples keep working unchanged.
"""
from dataclasses import dataclass, field

COPIED = "COPIED"
NORMALIZED = "NORMALIZED"
DERIVED = "DERIVED"
INFERRED = "INFERRED"
UNKNOWN = "UNKNOWN"

STATUSES = (COPIED, NORMALIZED, DERIVED, INFERRED, UNKNOWN)


@dataclass(frozen=True)
class Fact:
    label: str
    value: str = ""
    uom: str = ""
    source: str = "Part_Desc"
    evidence: str = ""
    status: str = NORMALIZED

    def __iter__(self):
        return iter((self.label, self.value, self.uom))

    @property
    def triple(self):
        return (self.label, self.value, self.uom)


def blank_slot(label):
    """A schema slot whose value could not be supported (UNKNOWN)."""
    return Fact(label=label, value="", uom="", status=UNKNOWN)


def provenance_totals(facts_by_row):
    """Aggregate status counts across rows.

    facts_by_row: iterable of lists of Fact (emitted facts only).
    Returns dict with counts per status plus emitted/blank totals.
    """
    totals = {s: 0 for s in STATUSES}
    emitted = 0
    blanks = 0
    for facts in facts_by_row:
        for f in facts:
            if f.value:
                totals[f.status] = totals.get(f.status, 0) + 1
                emitted += 1
            else:
                blanks += 1
                if f.status in totals:
                    totals[f.status] += 1
    return {"emitted_populated": emitted, "emitted_blank": blanks,
            "by_status": totals}
