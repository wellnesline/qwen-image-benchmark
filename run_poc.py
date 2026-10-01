import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def request_json(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Qwen Image 2.1 ComfyUI PoC")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prompt-file", default="api_prompt.json")
    parser.add_argument("--result-file", default="result.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    prompt = json.loads((root / args.prompt_file).read_text(encoding="utf-8"))
    client_id = str(uuid.uuid4())
    started = time.time()

    queued = request_json(
        f"{args.server}/prompt", {"prompt": prompt, "client_id": client_id}
    )
    prompt_id = queued["prompt_id"]
    print(f"queued prompt_id={prompt_id}", flush=True)

    while time.time() - started < args.timeout:
        history = request_json(f"{args.server}/history/{prompt_id}")
        if prompt_id in history:
            record = history[prompt_id]
            status = record.get("status", {})
            if status.get("completed"):
                elapsed = time.time() - started
                images = []
                for output in record.get("outputs", {}).values():
                    images.extend(output.get("images", []))
                result = {
                    "prompt_id": prompt_id,
                    "elapsed_seconds": round(elapsed, 2),
                    "images": images,
                    "status": status,
                }
                (root / args.result_file).write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return
        time.sleep(2)

    raise TimeoutError(f"Prompt {prompt_id} did not finish in {args.timeout}s")


if __name__ == "__main__":
    main()
