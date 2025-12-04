from huggingface_hub import hf_hub_download
import os

# 현재 스크립트가 있는 디렉토리 (data/models/code)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 저장할 디렉토리 (data/models/downloaded_models)
save_dir = os.path.join(os.path.dirname(current_dir), 'downloaded_models')

print(f"다운로드 경로: {save_dir}")

model_path = hf_hub_download(
    repo_id="mykor/A.X-4.0-Light-gguf",
    filename="A.X-4.0-Light-Q4_K_M.gguf",
    local_dir=save_dir,
    local_dir_use_symlinks=False
)

print(f"✅ 모델 다운로드 완료: {model_path}")