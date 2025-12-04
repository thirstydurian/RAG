from pathlib import Path
from huggingface_hub import snapshot_download

MODEL_ID = "kakaocorp/kanana-nano-2.1b-instruct"

# 이 파일이 있는 디렉터리 (models/code)
CURRENT_DIR = Path(__file__).resolve().parent
# 저장할 디렉토리 (models/downloaded_models/kanana...)
SAVE_DIR = CURRENT_DIR.parent / "downloaded_models" / "kanana-nano-2.1b-instruct"

def download_model():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading model to: {SAVE_DIR}")
    print("Using snapshot_download for space efficiency...")

    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=SAVE_DIR,
        local_dir_use_symlinks=False,
        resume_download=True
    )

    print("Download finished!")

if __name__ == "__main__":
    download_model()
