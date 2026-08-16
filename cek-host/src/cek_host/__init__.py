"""cek-host — Python Host runtime (language port of decide).

Public surface is stable. Implementation lives in host.py.
"""

from __future__ import annotations

from .bound import BoundAsk
from .cap import CapError, CapService, args_hash, resource_of, scope_allows
from .digest import result_digest
from .doctor import DEMO_SECRET, MIN_SECRET_LEN, DoctorReport, doctor
from .explain import Explanation, explain
from .host import Host, KernelResult, LAW_GENERATION
from .idem import FileIdemBackend, IdemConflict, IdemBackend, MemoryIdemBackend
from .legal import (
    IllegalOp,
    LEGAL_FQS,
    LEGAL_PAIRS,
    default_stamp_pairs,
    in_stamp,
    is_legal,
    normalize_stamp,
    project_wire,
)
from .lineage import (
    FileLineageBackend,
    LineageBackend,
    LineageError,
    MemoryLineageBackend,
    ReverseOutcome,
)
from .once import FileOnceBackend, MemoryOnceBackend, OnceBackend, OnceUsed, StoreDown
from .rust_wrap import RustHostKernel, find_cek_bin

__version__ = "0.1.2"

__all__ = [
    "Host",
    "KernelResult",
    "BoundAsk",
    "CapService",
    "CapError",
    "OnceBackend",
    "MemoryOnceBackend",
    "FileOnceBackend",
    "StoreDown",
    "OnceUsed",
    "IdemBackend",
    "MemoryIdemBackend",
    "FileIdemBackend",
    "IdemConflict",
    "LineageBackend",
    "MemoryLineageBackend",
    "FileLineageBackend",
    "LineageError",
    "ReverseOutcome",
    "args_hash",
    "resource_of",
    "scope_allows",
    "result_digest",
    "explain",
    "Explanation",
    "doctor",
    "DoctorReport",
    "DEMO_SECRET",
    "MIN_SECRET_LEN",
    "LAW_GENERATION",
    "project_wire",
    "is_legal",
    "LEGAL_FQS",
    "LEGAL_PAIRS",
    "IllegalOp",
    "default_stamp_pairs",
    "normalize_stamp",
    "in_stamp",
    "RustHostKernel",
    "find_cek_bin",
    "__version__",
]
