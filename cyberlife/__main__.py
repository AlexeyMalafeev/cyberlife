import argparse

from .game import run


def main():
    parser = argparse.ArgumentParser(prog="cyberlife", description="A text-based cyberpunk life sim.")
    parser.add_argument("--seed", type=int, help="seed the RNG for a repeatable run")
    parser.add_argument("--save-dir", help="directory to keep save slots in "
                                           "(default: $CYBERLIFE_SAVE_DIR or ~/.cyberlife/saves)")
    args = parser.parse_args()
    run(seed=args.seed, save_dir=args.save_dir)


if __name__ == "__main__":
    main()
