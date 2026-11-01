import argparse
from pathlib import Path

import anthropic

from aithena.config.settings import DEFAULT_MODELS
from aithena.output.writers import JsonWriter, RustWriter, write_results
from aithena.pipeline.routing import extract_licenses, process_licenses


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

    return parser.parse_args(argv)


def main() -> None:
    """Run the analysis and write results to the output directory."""

    args = parse_args()
    data_dir: Path = args.data_dir
    out_dir: Path = args.out_dir

    client = anthropic.Anthropic()
    models = DEFAULT_MODELS

    licenses = extract_licenses(client, models, data_dir)
    saved = write_results(licenses, JsonWriter(out_dir / "licenses.json"))
    print(f"Saved license info for {len(licenses)} file(s) to {saved}")

    functions, rust = process_licenses(client, models, licenses, data_dir)
    saved = write_results(functions, JsonWriter(out_dir / "functions.json"))
    print(f"Saved functions for {len(functions)} file(s) to {saved}")

    saved = RustWriter(out_dir / "rust").write(rust)
    print(f"Saved {len(rust)} Rust rewrite(s) to {saved}")


if __name__ == "__main__":
    main()
