"""Surface binding of S — re-exports cek_host.legal (one Python table).

Must match cek-contract domain.rs + baseline.rs.
Undeclared pair is illegal. Concatenation is not identity.
"""

from __future__ import annotations

from cek_host.legal import (
    BASELINE_FQS,
    BASELINE_PAIRS,
    DOMAIN_FQS,
    DOMAIN_PACKS,
    DOMAIN_PAIRS,
    LEGAL_FQS,
    LEGAL_PAIRS,
    IllegalOp,
    default_stamp_pairs,
    fq_of,
    in_stamp,
    is_baseline,
    is_domain_pair,
    is_legal,
    name_is_token,
    normalize_stamp,
    pack_is_scoped,
    pack_of,
    pack_of_pair,
    project,
    project_wire,
)

__all__ = [
    "BASELINE_FQS",
    "BASELINE_PAIRS",
    "DOMAIN_FQS",
    "DOMAIN_PACKS",
    "DOMAIN_PAIRS",
    "LEGAL_FQS",
    "LEGAL_PAIRS",
    "IllegalOp",
    "default_stamp_pairs",
    "fq_of",
    "in_stamp",
    "is_baseline",
    "is_domain_pair",
    "is_legal",
    "name_is_token",
    "normalize_stamp",
    "pack_is_scoped",
    "pack_of",
    "pack_of_pair",
    "project",
    "project_wire",
]
