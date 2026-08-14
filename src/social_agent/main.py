import argparse
import sys

from social_agent.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn a git commit into LinkedIn/X drafts.")
    parser.add_argument("repo_path", help="Path to a local git repository")
    parser.add_argument("commit_sha", nargs="?", default="HEAD", help="Commit to process (default: HEAD)")
    args = parser.parse_args()

    try:
        run_pipeline(args.repo_path, args.commit_sha)
    except Exception as exc:
        print(f"[fatal] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()