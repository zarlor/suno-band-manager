#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Merge module help entries into a module-help.csv.

Reads a source CSV with module help entries and merges them into a target CSV.
Uses an anti-zombie pattern: all existing rows matching the source module code
are removed before appending fresh rows. Rows from other modules are kept.

Header: the BMad v6.12 installer schema names columns 9-10 `preceded-by,followed-by`.
An existing target that still uses the older `after,before` names is rewritten to
the canonical header (the columns are positional, so row data is unchanged).

This script deletes no files. Per-module CSVs under _bmad/ (core/, other modules,
and _bmad/{module}/module-help.csv, which the v6.12 installer merges into its
help catalog) are left alone.

Exit codes: 0=success, 1=validation error, 2=runtime error
"""

import argparse
import csv
import json
import sys
from io import StringIO
from pathlib import Path

# Canonical header (BMad v6.12 MODULE_HELP_CSV_HEADER)
HEADER = [
    "module",
    "skill",
    "display-name",
    "menu-code",
    "description",
    "action",
    "args",
    "phase",
    "preceded-by",
    "followed-by",
    "required",
    "output-location",
    "outputs",
]
LEGACY_COLUMNS = {"after": "preceded-by", "before": "followed-by"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge module help entries into a module-help.csv with anti-zombie pattern."
    )
    parser.add_argument("--target", required=True, help="Path to the target module-help.csv file")
    parser.add_argument("--source", required=True, help="Path to the source module-help.csv with entries to merge")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress to stderr")
    return parser.parse_args()


def reject_unresolved_paths(named_paths: list[tuple[str, str | None]]) -> None:
    """Exit with a clear error if any path argument still contains the literal
    ``{project-root}`` token. That token is meaningful only inside config
    values; filesystem path arguments must be resolved by the caller. Failing
    loudly here prevents silently creating a junk ``{project-root}/`` directory.
    """
    for name, value in named_paths:
        if value and "{project-root}" in value:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": (
                            f"Unresolved '{{project-root}}' token in {name} path: {value!r}. "
                            "Resolve '{project-root}' to the actual project root before running "
                            "this script — it is a filesystem path, not a config value."
                        ),
                    },
                    indent=2,
                )
            )
            sys.exit(1)


def read_csv_rows(path: str) -> tuple[list[str], list[list[str]]]:
    """Read CSV file returning (header, data_rows). Empty if the file doesn't exist."""
    file_path = Path(path)
    if not file_path.exists():
        return [], []
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(StringIO(f.read())))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def canonical_header(header: list[str]) -> list[str]:
    """Rename the old after/before columns to preceded-by/followed-by."""
    return [LEGACY_COLUMNS.get(col.strip(), col) for col in header]


def choose_header(target_header: list[str], source_header: list[str]) -> list[str]:
    """Pick the header to write.

    The source header wins when the target is new or has the same column count
    (columns are positional). A target with a different column count keeps its
    own header so its existing rows stay readable. Either way old column names
    are canonicalized.
    """
    source = canonical_header(source_header) if source_header else HEADER
    if not target_header or len(target_header) == len(source):
        return source
    return canonical_header(target_header)


def extract_module_codes(rows: list[list[str]]) -> set[str]:
    return {row[0].strip() for row in rows if row and row[0].strip()}


def filter_rows(rows: list[list[str]], module_code: str) -> list[list[str]]:
    """Remove all rows matching the given module code."""
    return [row for row in rows if not row or row[0].strip() != module_code]


def write_csv(path: str, header: list[str], rows: list[list[str]], verbose: bool = False) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"Writing {len(rows)} data rows to {path}", file=sys.stderr)
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    args = parse_args()
    reject_unresolved_paths([("--target", args.target), ("--source", args.source)])

    source_header, source_rows = read_csv_rows(args.source)
    if not source_rows:
        print(json.dumps({"status": "error", "error": f"No data rows found in source {args.source}"}))
        sys.exit(1)
    source_codes = extract_module_codes(source_rows)
    if not source_codes:
        print(json.dumps({"status": "error", "error": "Could not determine module code from source rows"}))
        sys.exit(1)

    target_existed = Path(args.target).exists()
    target_header, target_rows = read_csv_rows(args.target)
    header = choose_header(target_header, source_header)
    header_migrated = bool(target_header) and target_header != header

    filtered_rows = target_rows
    for code in source_codes:
        filtered_rows = filter_rows(filtered_rows, code)
    removed_count = len(target_rows) - len(filtered_rows)
    merged_rows = filtered_rows + source_rows

    write_csv(args.target, header, merged_rows, args.verbose)

    print(
        json.dumps(
            {
                "status": "success",
                "target_path": str(Path(args.target).resolve()),
                "target_existed": target_existed,
                "header_migrated": header_migrated,
                "module_codes": sorted(source_codes),
                "rows_removed": removed_count,
                "rows_added": len(source_rows),
                "total_rows": len(merged_rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
