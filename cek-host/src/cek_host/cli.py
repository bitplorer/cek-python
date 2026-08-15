"""cek CLI — never silent (G7 / Vercel DX)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="cek",
        description="CEK Host — mint/verify Caps. doctor · explain · create-app",
    )
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("doctor", help="go/no-go checklist (≡ production factory)")
    d.add_argument("--fail", action="store_true", help="exit 1 if any finding is FAIL")
    d.add_argument("--production-demo", action="store_true", help="inspect a misconfigured Host")

    e = sub.add_parser("explain", help="teach a Host/Surface error string")
    e.add_argument("error", nargs="?", default="cap required")

    c = sub.add_parser("create-app", help="one-file running app (require_cap=True)")
    c.add_argument("dest", nargs="?", default="cek-app")

    sub.add_parser("version", help="print cek-host version")

    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        print("\nTry:  python -m cek_host doctor --fail")
        print("      python -m cek_host create-app ./my-app")
        print("      python -m cek_host explain 'once cap already used'")
        return 2

    if args.cmd == "version":
        from . import __version__

        print(f"cek-host {__version__}")
        return 0

    if args.cmd == "explain":
        from .explain import explain

        print(explain(args.error).render())
        return 0

    if args.cmd == "create-app":
        from .scaffold import create_app

        dest = create_app(args.dest)
        print(f"created {dest.resolve() / 'app.py'}")
        print(f"next   : pip install cek-host cek-surface && python {dest / 'app.py'}")
        print(f"doctor : python -m cek_host doctor --fail")
        return 0

    if args.cmd == "doctor":
        from . import Host
        from .doctor import doctor
        from .once import MemoryOnceBackend

        if args.production_demo:
            # Deliberate misconfig so the critic can paste FAIL output.
            host = Host(mode="adapt", once=MemoryOnceBackend())
        else:
            host = Host()
        report = doctor(host, fail=False)
        print(report.to_text())
        if args.fail and not report.ok:
            return 1
        return 0

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
