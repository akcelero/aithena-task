import argparse
import sys
from pathlib import Path

import anthropic

from aithena.config.settings import DEFAULT_MODELS, ModelConfig
from aithena.llm.cache import JsonCache
from aithena.llm.client import BudgetExceededError, ClaudeClient, Usage
from aithena.output.writers import JsonValue, JsonWriter, RustWriter, write_results
from aithena.pipeline.plan import RunPlan, plan_run
from aithena.pipeline.routing import extract_licenses, process_licenses

EXIT_OK = 0
EXIT_FILE_ERRORS = 1
EXIT_BUDGET_REACHED = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments: a required data directory and an optional output directory."""

    parser = argparse.ArgumentParser(prog="aithena", description="Analyse license and code in source files.")
    parser.add_argument("data_dir", type=Path, help="directory containing the .py files to analyse")
    parser.add_argument(
        "out_dir",
        type=Path,
        nargs="?",
        default=Path("output"),
        help="where to write results (default: output)",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=None,
        help="stop after this many API calls; cached answers are free",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the expected number of API calls and exit without calling the API",
    )

    return parser.parse_args(argv)


def print_usage(usage: Usage) -> None:
    """Print how many API calls ran, how many came from the cache, and the tokens used."""

    print(
        f"API calls: {usage.calls}, cache hits: {usage.cache_hits}, "
        f"input tokens: {usage.input_tokens}, output tokens: {usage.output_tokens}"
    )


def print_plan(plan: RunPlan) -> None:
    """Print the expected API calls for a run, without making any."""

    print(f"Files: {plan.files} ({plan.unreadable} unreadable)")
    print(f"License calls needed: {plan.license_calls} ({plan.cached_license_calls} cached)")
    print(f"Worst-case total API calls: {plan.worst_case_calls}")


def run(data_dir: Path, out_dir: Path, llm: ClaudeClient, models: ModelConfig) -> int:
    """Analyse the files and write results. Returns the process exit code."""

    try:
        licenses, license_errors = extract_licenses(llm, models, data_dir)
        saved = write_results(licenses, JsonWriter(out_dir / "licenses.json"))
        print(f"Saved license info for {len(licenses)} file(s) to {saved}")

        functions, rust, process_errors = process_licenses(llm, models, licenses, data_dir)
    except BudgetExceededError as exc:
        print(
            f"Stopped: {exc}. Run again with a higher --max-calls; cached results are reused.",
            file=sys.stderr,
        )
        print_usage(llm.usage)
        return EXIT_BUDGET_REACHED

    saved = write_results(functions, JsonWriter(out_dir / "functions.json"))
    print(f"Saved functions for {len(functions)} file(s) to {saved}")

    saved = RustWriter(out_dir / "rust").write(rust)
    print(f"Saved {len(rust)} Rust rewrite(s) to {saved}")

    errors: dict[str, JsonValue] = {**license_errors, **process_errors}
    saved = JsonWriter(out_dir / "errors.json").write(errors)
    print_usage(llm.usage)

    if errors:
        print(f"{len(errors)} file(s) failed, see {saved}", file=sys.stderr)
        return EXIT_FILE_ERRORS

    return EXIT_OK


def main() -> None:
    """Build the API client from the command line and run the analysis."""

    args = parse_args()
    cache = JsonCache(args.out_dir / "cache")

    if args.dry_run:
        print_plan(plan_run(args.data_dir, cache, DEFAULT_MODELS))
        return

    llm = ClaudeClient(anthropic.Anthropic(), cache=cache, max_calls=args.max_calls)
    sys.exit(run(args.data_dir, args.out_dir, llm, DEFAULT_MODELS))


if __name__ == "__main__":
    main()
