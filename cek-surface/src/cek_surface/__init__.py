"""cek-surface — CEK-native surface runtime.

Carrier is opt-in plug-and-play (default: subprocess NDJSON).
"""

from .cap import CapError, CapService
from .carrier import Carrier, MemoryCarrier, SubprocessNdjsonCarrier, WebSocketCarrier, open_carrier
from .continuation import Continuation, match_continuation, resolve_args
from .kernel import EmbeddedHostKernel, HostKernel, KernelResult, load_host_kernel
from .ops import Op, as_wire, plan
from .policy import PolicyDecision, SurfacePolicy
from .session import PeerSession
from .surface import Ctx, Surface
from .host import ActionContext, Host, Intent, Result

__all__ = [
    "Op", "plan", "as_wire",
    "Surface", "Ctx",
    "HostKernel", "EmbeddedHostKernel", "KernelResult", "load_host_kernel",
    "CapService", "CapError", "PeerSession",
    "SurfacePolicy", "PolicyDecision",
    "Continuation", "match_continuation", "resolve_args",
    "Carrier", "open_carrier", "MemoryCarrier", "SubprocessNdjsonCarrier", "WebSocketCarrier",
    "Host", "Intent", "Result", "ActionContext",
]
