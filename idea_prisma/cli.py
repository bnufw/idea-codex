from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings
from .files import ensure_directory, ensure_markdown_file
from .gemini_rest import GeminiRestClient, GeminiError
from .orchestrator import IdeaPrismaOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idea_prisma",
        description="Prisma-style multi-agent idea generator for local-first research workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the Prisma-style idea workflow.")
    run_parser.add_argument("-d", "--direction-md", required=True, help="Markdown file containing the current direction.")
    run_parser.add_argument(
        "-p",
        "--papers-dir",
        default="papers",
        help="Directory of local Markdown paper notes. Defaults to papers.",
    )
    run_parser.add_argument(
        "--output-dir",
        default="runs",
        help="Directory where timestamped run artifacts will be created.",
    )
    run_parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum total expert rounds, including the first round.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        ensure_markdown_file(args.direction_md, "direction_md")
        ensure_directory(args.papers_dir, "papers_dir")
        settings = load_settings()
        client = GeminiRestClient(settings)
        orchestrator = IdeaPrismaOrchestrator(client)
        run_dir = orchestrator.run(
            direction_md=args.direction_md,
            papers_dir=args.papers_dir,
            output_dir=args.output_dir,
            max_rounds=max(1, args.max_rounds),
        )
    except (ValueError, GeminiError) as exc:
        parser.exit(1, f"错误：{exc}\n")

    parser.exit(0, f"\n运行完成。产物目录：{Path(run_dir)}\n")
