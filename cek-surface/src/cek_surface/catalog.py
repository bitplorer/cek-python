"""Surface binding of the declared catalog — re-exports cek_host.catalog (one Python table).

Declared catalog = Baseline ∪ UI seed. There is no law noun "S".
Must match cek-contract domain.rs + baseline.rs.
Undeclared pair is not in the catalog. Concatenation is not identity.
"""

from __future__ import annotations

from cek_host.catalog import (
    BASELINE_FQS,
    BASELINE_PAIRS,
    DOMAIN_FQS,
    DOMAIN_PACKS,
    DOMAIN_PAIRS,
    CATALOG_FQS,
    CATALOG_PAIRS,
    IllegalOp,
    default_stamp_pairs,
    fq_of,
    in_stamp,
    is_baseline,
    is_domain_pair,
    in_catalog,
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
    "CATALOG_FQS",
    "CATALOG_PAIRS",
    "IllegalOp",
    "default_stamp_pairs",
    "fq_of",
    "in_stamp",
    "is_baseline",
    "is_domain_pair",
    "in_catalog",
    "name_is_token",
    "normalize_stamp",
    "pack_is_scoped",
    "pack_of",
    "pack_of_pair",
    "project",
    "project_wire",
]
