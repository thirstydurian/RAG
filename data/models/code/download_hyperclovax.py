from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B"

# 이 파일이 있는 디렉터리 (models)
CURRENT_DIR = Path(__file__).resolve().parent
SAVE_DIR = CURRENT_DIR.parent / "downloaded_models" / "HyperCLOVAX-SEED-Text-Instruct-1.5B"

def download_model():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading HyperCLOVAX model to: {SAVE_DIR}")

    # 허깅페이스 접근 권한이 필요한 모델이라, 사전에 토큰 동의/발급 필요
    # 환경 변수 HF_TOKEN 이나 huggingface-cli login 으로 인증해 둔다.[web:62][web:66]
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_auth_token=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, use_auth_token=True)

    tokenizer.save_pretrained(SAVE_DIR)
    model.save_pretrained(SAVE_DIR)

    print("Download & save finished!")

if __name__ == "__main__":
    download_model()
