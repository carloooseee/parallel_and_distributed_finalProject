import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

SUPPORTED_EXTENSIONS = {".txt", ".log", ".csv"}
MatchRecord = Tuple[str, int, str]  # (file_path, line_number, line_text)


def collect_files(target_dir: Path) -> List[str]:
    files: List[str] = []
    for root, _, filenames in os.walk(target_dir):
        for name in sorted(filenames):
            ext = Path(name).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, name))
    return files


def search_single_file(file_path: str, keyword: str, case_sensitive: bool = False) -> List[MatchRecord]:
    matches: List[MatchRecord] = []
    needle = keyword if case_sensitive else keyword.lower()
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                haystack = line if case_sensitive else line.lower()
                if needle in haystack:
                    matches.append((file_path, line_no, line.rstrip("\r\n")))
    except OSError as exc:
        matches.append((file_path, 0, f"[ERROR reading file: {exc}]"))
    return matches


def run_sequential(files: List[str], keyword: str, case_sensitive: bool = False) -> Tuple[List[MatchRecord], float]:
    start = time.perf_counter()
    all_matches: List[MatchRecord] = []
    for file_path in files:
        all_matches.extend(search_single_file(file_path, keyword, case_sensitive))
    elapsed = time.perf_counter() - start
    return all_matches, elapsed


def run_parallel(
    files: List[str],
    keyword: str,
    workers: int,
    case_sensitive: bool = False,
) -> Tuple[List[MatchRecord], float]:
    start = time.perf_counter()
    all_matches: List[MatchRecord] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(search_single_file, file_path, keyword, case_sensitive)
            for file_path in files
        ]
        for future in as_completed(futures):
            all_matches.extend(future.result())
    elapsed = time.perf_counter() - start
    return all_matches, elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Parallel Keyword Search in Text Files")
    parser.add_argument("directory", type=str, help="Target directory containing text/log/csv files")
    parser.add_argument("keyword", type=str, help="Keyword to search for")
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[2, 4, 8],
        help="Worker counts to benchmark (default: 2 4 8)",
    )
    parser.add_argument("--case-sensitive", action="store_true", help="Enable case-sensitive matching")
    parser.add_argument("--show-matches", action="store_true", help="Print individual matching lines")
    args = parser.parse_args()

    target_dir = Path(args.directory)
    if not target_dir.is_dir():
        raise SystemExit(f"Directory not found: {target_dir}")

    files = collect_files(target_dir)
    if not files:
        raise SystemExit(f"No .txt, .log, or .csv files found in: {target_dir}")

    seq_matches, seq_time = run_sequential(files, args.keyword, args.case_sensitive)
    seq_matches.sort(key=lambda m: (m[0], m[1]))

    print(f"Files scanned : {len(files)}")
    print(f"Keyword       : '{args.keyword}'")
    print(f"Total matches : {len(seq_matches)}")
    print(f"Sequential    : {seq_time:.6f} s\n")

    if args.show_matches:
        for path, line_no, text in seq_matches:
            print(f"  {path}:{line_no}: {text}")
        print()

    print(f"{'Workers':>7} | {'Time (s)':>10} | {'Speedup':>8} | {'Efficiency':>10} | {'Match Parity':>12}")
    print("-" * 61)

    metrics: List[Dict[str, float]] = []
    for w in args.workers:
        par_matches, par_time = run_parallel(files, args.keyword, w, args.case_sensitive)
        par_matches.sort(key=lambda m: (m[0], m[1]))
        speedup = seq_time / par_time if par_time > 0 else 0.0
        efficiency = speedup / w if w > 0 else 0.0
        parity_ok = seq_matches == par_matches
        metrics.append({
            "workers": w,
            "time": par_time,
            "speedup": speedup,
            "efficiency": efficiency,
        })
        print(f"{w:>7} | {par_time:>10.6f} | {speedup:>8.2f}x | {efficiency * 100:>9.1f}% | {str(parity_ok):>12}")


if __name__ == "__main__":
    main()