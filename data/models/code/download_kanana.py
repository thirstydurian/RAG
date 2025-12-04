from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "kakaocorp/kanana-nano-2.1b-instruct"

# 이 파일이 있는 디렉터리 (models)
CURRENT_DIR = Path(__file__).resolve().parent
SAVE_DIR = CURRENT_DIR.parent / "downloaded_models" / "kanana-nano-2.1b-instruct"

def download_model():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading model to: {SAVE_DIR}")

    # 허깅페이스에서 모델/토크나이저 내려받기
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

    # 이 스크립트와 같은 경로(models) 안에 저장
    tokenizer.save_pretrained(SAVE_DIR)
    model.save_pretrained(SAVE_DIR)

    print("Download & save finished!")

if __name__ == "__main__":
    download_model()
