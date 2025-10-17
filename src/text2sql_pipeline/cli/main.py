# src/text2sql_pipeline/cli/main.py
import argparse
from text2sql_pipeline.pipeline.engine import run_pipeline

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True)
    args = ap.parse_args()
    run_pipeline(args.config)

if __name__ == "__main__":
    main()