import argparse
import asyncio
import pathlib
import sys

import uvicorn

# Ensure migrations package is importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from migrations import run_migrations
from .main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.add_argument("--db", default="meeting_minutes.db", help="Path to SQLite database")

    serve_parser = subparsers.add_parser("serve", help="Run migrations and start the API server")
    serve_parser.add_argument("--db", default="meeting_minutes.db", help="Path to SQLite database")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "migrate":
        asyncio.run(run_migrations(args.db))
    elif args.command == "serve":
        asyncio.run(run_migrations(args.db))
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
