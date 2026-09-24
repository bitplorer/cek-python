"""cek CLI — never silent (G7 / Vercel DX)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="cek",
        description="CEK Host — mint/verify Caps. check · explain · create-app",
    )
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("check", help="go/no-go for this Host")
    d.add_argument("--misconfigured", action="store_true", help="inspect a production Host that still uses a memory once-store")
    d.add_argument("--fail", action="store_true", help="exit 1 if any finding is FAIL")
    old = sub.add_parser("doctor", help="old name for check")
    old.add_argument("--fail", action="store_true", help="exit 1 if any finding is FAIL")
    old.add_argument("--misconfigured", action="store_true", help="inspect a production Host that still uses a memory once-store")

    e = sub.add_parser("explain", help="teach a Host/Surface error string")
    e.add_argument("error", nargs="?", default="cap required")

    c = sub.add_parser("create-app", help="one-file running app (require_cap=True)")
    c.add_argument("dest", nargs="?", default="cek-app")

    sub.add_parser("version", help="print cek-host version")

    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        print("\nTry:  python -m cek_host check --fail")
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
        print(f"next   : python {dest / 'app.py'}")
        print(f"check  : python -m cek_host check --fail")
        return 0

    if args.cmd in ("check", "doctor"):
        from . import Host
        from .doctor import doctor
        from .once import MemoryOnceBackend

        if args.misconfigured:
            # Deliberate misconfig so the critic can paste FAIL output.
            host = Host(mode="production", once=MemoryOnceBackend())
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
