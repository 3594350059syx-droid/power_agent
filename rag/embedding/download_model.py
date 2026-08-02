"""
手动下载 shibing624/text2vec-base-chinese 模型到本地目录。
绕过 huggingface_hub 库的 xet 下载问题, 直接用 requests 下载。

下载到: rag/models/text2vec-base-chinese/
embedder.py 会优先从本地路径加载。

用法:
    python rag/embedding/download_model.py

注意: 首次运行需联网, 下载约 390MB, 耗时 3-5 分钟。
"""
import os
import requests

BASE = "https://hf-mirror.com/shibing624/text2vec-base-chinese/resolve/main"
LOCAL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "text2vec-base-chinese"
)

FILES = [
    "pytorch_model.bin",
    "config.json",
    "vocab.txt",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "modules.json",
    "sentence_bert_config.json",
    "config_sentence_transformers.json",
    "1_Pooling/config.json",
]


def download_file(remote, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    if os.path.exists(local):
        size_mb = os.path.getsize(local) / 1024 / 1024
        print(f"  [SKIP] {local} ({size_mb:.1f} MB already exists)")
        return
    print(f"  [GET ] {remote}")
    r = requests.get(remote, stream=True, timeout=60, allow_redirects=True)
    r.raise_for_status()
    total = int(r.headers.get("Content-Length", 0))
    downloaded = 0
    with open(local, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                print(f"\r    {downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB ({pct:.0f}%)", end="", flush=True)
    print(f"\n  [DONE] {local} ({downloaded/1024/1024:.1f} MB)")


def main():
    print(f"download to: {LOCAL_DIR}")
    for fname in FILES:
        remote = f"{BASE}/{fname}"
        local = os.path.join(LOCAL_DIR, fname)
        try:
            download_file(remote, local)
        except Exception as e:
            print(f"\n  [FAIL] {fname}: {e}")
    print("\nall done.")


if __name__ == "__main__":
    main()
