import argparse
from pathlib import Path


def generate_dataset(output_dir: Path, num_files: int, lines_per_file: int, error_every: int) -> None:
    """Generate synthetic log files for benchmarking sequential vs. parallel search."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for file_idx in range(num_files):
        file_path = output_dir / f"app_{file_idx}.log"
        with open(file_path, "w", encoding="utf-8") as f:
            chunk = []
            for line_idx in range(lines_per_file):
                if line_idx % error_every == 0:
                    chunk.append(f"ERROR line {line_idx} timeout on worker-{file_idx}\n")
                else:
                    chunk.append(f"INFO line {line_idx} ok request processed normally\n")
                if len(chunk) >= 10000:
                    f.writelines(chunk)
                    chunk.clear()
            if chunk:
                f.writelines(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic log files for benchmarking")
    parser.add_argument("--dir", type=str, default="large_logs", help="Output directory (default: large_logs)")
    parser.add_argument("--files", type=int, default=64, help="Number of log files (default: 64)")
    parser.add_argument("--lines", type=int, default=100000, help="Lines per file (default: 100000)")
    parser.add_argument("--error-every", type=int, default=100, help="Insert ERROR every N lines (default: 100)")
    args = parser.parse_args()

    out = Path(args.dir)
    generate_dataset(out, args.files, args.lines, args.error_every)
    total_bytes = sum(p.stat().st_size for p in out.glob("*.log"))
    print(f"Generated {args.files} files in '{out}' ({total_bytes / (1024 * 1024):.2f} MB total)")


if __name__ == "__main__":
    main()
