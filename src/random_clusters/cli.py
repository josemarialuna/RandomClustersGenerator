"""One command line interface for individual datasets, batches, and added noise."""

import argparse
import hashlib
from dataclasses import replace
from pathlib import Path

import pandas as pd

from . import __version__
from .core import GeneratorConfig, _seed, add_noise, generate
from .io import check_output, read_batch, save_dataset, write_table


def _output(parser: argparse.ArgumentParser, *, directory: bool = False) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/batch" if directory else "data/dataset.csv"),
        help="output directory" if directory else "output CSV path (also writes a JSON sidecar)",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")


def _ordering(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-labels", action="store_true", help="omit the cluster column")
    parser.add_argument("--ordered", action="store_true", help="keep rows grouped by cluster")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="random-clusters", description="Reproducible synthetic clustering datasets."
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("generate", help="generate one dataset")
    for flag, default, help_text in (
        ("clusters", 4, "number of clusters (<= 2**features)"),
        ("samples", 100, "samples PER cluster"),
        ("features", 2, "number of signal coordinates"),
        ("noise", 2, "number of uniform noise features"),
    ):
        single.add_argument(f"--{flag}", type=int, default=default, help=help_text)
    single.add_argument("--std", type=float, default=0.05, help="Gaussian standard deviation")
    single.add_argument(
        "--seed", type=int, help="nonnegative seed; generated and recorded if omitted"
    )
    _ordering(single)
    _output(single)

    batch = commands.add_parser("batch", help="generate one dataset per configuration row")
    batch.add_argument("config", type=Path, help="CSV with explicit parameters and seeds")
    _ordering(batch)
    _output(batch, directory=True)

    noise = commands.add_parser("add-noise", help="append noise without replacing existing columns")
    noise.add_argument("input", type=Path, help="existing comma-separated CSV with a header")
    noise.add_argument("--count", type=int, required=True, help="number of NEW noise columns")
    noise.add_argument("--seed", type=int, help="nonnegative random seed")
    noise.add_argument("--distribution", choices=("uniform", "normal"), default="uniform")
    noise.add_argument("--mean", type=float, default=1.0, help="normal noise mean (normal only)")
    noise.add_argument("--std", type=float, default=0.05, help="normal noise std (normal only)")
    _output(noise)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            config = GeneratorConfig(
                **{
                    key: getattr(args, key)
                    for key in ("clusters", "samples", "features", "noise", "std", "seed")
                },
                shuffle=not args.ordered,
                labels=not args.no_labels,
            )
            check_output(args.output, args.overwrite)
            dataset = generate(config)
            paths = save_dataset(dataset, args.output, overwrite=args.overwrite)
            print(
                f"{len(dataset.data)} rows x {len(dataset.data.columns)} columns; "
                f"seed={dataset.config.seed}"
            )
            print(f"Saved {paths[0]} and {paths[1]}")
        elif args.command == "batch":
            configs = read_batch(args.config)
            outputs = [args.output / f"dataset_{i:03d}.csv" for i in range(1, len(configs) + 1)]
            # Validate the entire batch and all destination names before writing.
            for output in outputs:
                if output.resolve() == args.config.resolve():
                    raise ValueError("batch output must not replace its configuration file")
                check_output(output, args.overwrite)
            for config, output in zip(configs, outputs):
                config = replace(config, shuffle=not args.ordered, labels=not args.no_labels)
                save_dataset(generate(config), output, overwrite=args.overwrite)
                print(f"Saved {output} and {output.with_suffix('.json')}")
            print(f"Generated {len(configs)} datasets.")
        else:
            if args.input.resolve() == args.output.resolve():
                raise ValueError("input and output must be different files")
            check_output(args.output, args.overwrite)
            seed = _seed(args.seed)
            data = pd.read_csv(args.input, float_precision="round_trip")
            result = add_noise(
                data,
                args.count,
                seed=seed,
                distribution=args.distribution,
                mean=args.mean,
                std=args.std,
            )
            digest = hashlib.sha256()
            with args.input.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            paths = write_table(
                result,
                args.output,
                {
                    "operation": "add-noise",
                    "input": str(args.input),
                    "input_sha256": digest.hexdigest(),
                    "parameters": {
                        "count": args.count,
                        "seed": seed,
                        "distribution": args.distribution,
                        **(
                            {"mean": args.mean, "std": args.std}
                            if args.distribution == "normal"
                            else {}
                        ),
                    },
                },
                overwrite=args.overwrite,
            )
            print(f"Saved {paths[0]} and {paths[1]}; seed={seed}")
    except (ValueError, OSError, pd.errors.ParserError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0
