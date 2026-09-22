import argparse
import os

from . import llm
from .game import run


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cyberlife", description="A text-based cyberpunk life sim.")
    parser.add_argument("--seed", type=int, help="seed the RNG for a repeatable run")
    parser.add_argument("--save-dir", help="directory to keep save slots in "
                                           "(default: $CYBERLIFE_SAVE_DIR or ~/.cyberlife/saves)")
    parser.add_argument("--llm", choices=list(llm.BACKENDS), default=os.environ.get("CYBERLIFE_LLM", "off"),
                        help="voice NPC dialog with a language model: 'mlx' talks to a local "
                             "mlx_lm.server, 'deepseek' to DeepSeek's API using $DEEPSEEK_API_KEY "
                             "(default: $CYBERLIFE_LLM or off)")
    parser.add_argument("--llm-url", default=os.environ.get("CYBERLIFE_LLM_URL"),
                        help="dialog server URL (default: $CYBERLIFE_LLM_URL, else "
                             f"{llm.MlxBackend.DEFAULT_URL} for mlx, {llm.DeepSeekBackend.DEFAULT_URL} for deepseek)")
    parser.add_argument("--llm-model", default=os.environ.get("CYBERLIFE_LLM_MODEL"),
                        help="model to request (default: $CYBERLIFE_LLM_MODEL, else whatever mlx_lm.server "
                             f"loaded, or {llm.DeepSeekBackend.DEFAULT_MODEL})")
    parser.add_argument("--llm-timeout", type=float,
                        help="seconds to wait for a line before using a stock one "
                             "(default: 5 for mlx, 10 for deepseek)")
    args = parser.parse_args(argv)
    try:
        backend = llm.make_backend(args.llm, url=args.llm_url, model=args.llm_model, timeout=args.llm_timeout)
    except ValueError as exc:   # missing API key, or a bad $CYBERLIFE_LLM (skips argparse's check)
        parser.error(str(exc))
    llm.use(backend)
    run(seed=args.seed, save_dir=args.save_dir)


if __name__ == "__main__":
    main()
