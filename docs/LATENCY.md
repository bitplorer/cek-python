# Latency

Human: ≤100ms instant; 100–300ms OK; >1s broken for clicks.

Measured: Host compose ~0.03ms; local Peer ~0.5ms; wall time ≈ RTT.
Multi-round search ≈ N×RTT — use Peer IR chrome + coalesce.

Doctrine: Lag ≈ RTT × (Host decisions). Apply is free once Result is local.
