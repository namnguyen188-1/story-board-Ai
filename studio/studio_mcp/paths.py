from pathlib import Path
def app_root():
    return Path(__file__).resolve().parent.parent
