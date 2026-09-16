import argparse

from .game import run


def main():
    parser = argparse.ArgumentParser(prog="cyberlife", description="A text-based cyberpunk life sim.")
    parser.add_argument("--seed", type=int, help="seed the RNG for a repeatable run")
    args = parser.parse_args()
    run(seed=args.seed)


if __name__ == "__main__":
    main()
