import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.demo import run_demo

if __name__ == "__main__":
    import json

    print(json.dumps(run_demo("output/demo"), ensure_ascii=False, indent=2))
