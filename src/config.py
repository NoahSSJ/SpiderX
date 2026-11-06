from pathlib import Path


ROOT_DIR = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)
SRC_DIR = next((dir / "src" for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)

MAX_WORKER = 3

TIME_DELAY_MIN = 3
TIME_DELAY_MAX = 10 

LOG_LEVEL = 1