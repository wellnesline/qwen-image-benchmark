import copy
import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import threading
import time
import urllib.request
import os
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parent
# Set COMFY_DIR to the inner ComfyUI directory of your ComfyUI install.
COMFY_ROOT = Path(os.environ.get("COMFY_DIR", "ComfyUI"))
COMFY_OUTPUT = COMFY_ROOT / "output"
COMFY_INPUT = COMFY_ROOT / "input"
BENCH_OUTPUT = ROOT / "benchmark_outputs"
SERVER = "http://127.0.0.1:8188"


T2I_CASES = [
    {
        "id": "product_photo_a",
        "prompt": "Premium studio product photograph of a matte black compact AI camera on pale oak, soft window light, realistic metal and glass, clean commercial composition, small white label reading 'QWEN 2.1', highly detailed.",
        "size": (1024, 1024), "seed": 1001, "steps": 25,
    },
    {
        "id": "product_photo_b",
        "prompt": "Premium studio product photograph of a matte black compact AI camera on pale oak, soft window light, realistic metal and glass, clean commercial composition, small white label reading 'QWEN 2.1', highly detailed.",
        "size": (1024, 1024), "seed": 1002, "steps": 25,
    },
    {
        "id": "portrait",
        "prompt": "Editorial portrait photograph of a Japanese woman in her thirties wearing a navy linen jacket, natural skin texture, subtle makeup, soft Rembrandt lighting, neutral gray studio background, 85mm lens look.",
        "size": (768, 1344), "seed": 2001, "steps": 25,
    },
    {
        "id": "hands_cooking",
        "prompt": "Close-up documentary photograph of two human hands carefully slicing a red bell pepper on a wooden cutting board, all ten fingers anatomically correct and clearly visible, bright home kitchen, realistic food texture.",
        "size": (1344, 768), "seed": 3001, "steps": 25,
    },
    {
        "id": "anime_action",
        "prompt": "Dynamic Japanese anime key visual: a young courier on a bicycle racing through a rainy neon city street, dramatic perspective, expressive face, correct hands, crisp cel shading, cinematic reflections.",
        "size": (768, 1344), "seed": 4001, "steps": 25,
    },
    {
        "id": "jp_poster",
        "prompt": "Minimal Japanese event poster on a warm ivory background. Large exact headline: '未来をつくるAI'. Exact subheading: '2000年1月1日 開催'. Bold modern Japanese typography, red circle accent, strict grid, print design.",
        "size": (768, 1344), "seed": 5001, "steps": 25,
    },
    {
        "id": "en_infographic",
        "prompt": "Clean vertical business infographic titled exactly 'LOCAL AI WORKFLOW'. Three numbered sections with exact labels '1. PLAN', '2. GENERATE', '3. VERIFY'. Navy, cyan and white palette, sharp readable typography, simple icons, professional layout.",
        "size": (768, 1344), "seed": 6001, "steps": 25,
    },
    {
        "id": "flow_diagram",
        "prompt": "A clean technical flowchart on white. Four rounded boxes connected left to right with exact text: 'PROMPT' then 'MODEL' then 'IMAGE' then 'REVIEW'. Blue arrows, consistent spacing, flat vector style, all text legible.",
        "size": (1344, 768), "seed": 7001, "steps": 25,
    },
    {
        "id": "landscape",
        "prompt": "Wide cinematic landscape photograph of the Japanese Alps at sunrise, layers of mist, alpine lake reflection, detailed rocks and pine trees, natural color, high dynamic range without oversaturation.",
        "size": (1344, 768), "seed": 8001, "steps": 25,
    },
    {
        "id": "architecture",
        "prompt": "Photorealistic contemporary Japanese micro-house exterior in a narrow urban lot, exposed concrete and cedar slats, accurate perspective, overcast daylight, architectural magazine photography.",
        "size": (1024, 1024), "seed": 9001, "steps": 25,
    },
    {
        "id": "transparent_icon",
        "prompt": "This is an RGBA format image with transparency. A polished 3D blue robot assistant icon, centered, soft studio reflections, no floor and no shadow outside the object. The image has an alpha channel and a transparent background.",
        "size": (1024, 1024), "seed": 10001, "steps": 25,
    },
    {
        "id": "transparent_mascot",
        "prompt": "This is an RGBA format image with transparency. A cute flat-vector tanuki mascot holding a tiny laptop, clean sticker-like edges, centered. The image has an alpha channel and a transparent background.",
        "size": (1024, 1024), "seed": 10002, "steps": 25,
    },
    {
        "id": "determinism_a",
        "prompt": "A red ceramic teapot beside one green apple on a plain gray table, centered studio photograph, soft shadow.",
        "size": (1024, 1024), "seed": 424242, "steps": 25,
    },
    {
        "id": "determinism_b",
        "prompt": "A red ceramic teapot beside one green apple on a plain gray table, centered studio photograph, soft shadow.",
        "size": (1024, 1024), "seed": 424242, "steps": 25,
    },
    {
        "id": "2k_product_25",
        "prompt": "Luxury wristwatch product photograph on black volcanic stone, precise brushed steel, sapphire reflections, dramatic rim light, premium advertising image, extremely fine detail.",
        "size": (2048, 2048), "seed": 11001, "steps": 25,
    },
    {
        "id": "2k_jp_poster_40",
        "prompt": "High-end Japanese technology conference poster. Exact large headline: '生成AI 実践フォーラム'. Exact date: '2000.01.01'. Exact venue: 'HALL A'. Black, white and electric blue, Swiss grid, crisp Japanese typography, print-ready detail.",
        "size": (2048, 2048), "seed": 11002, "steps": 40,
    },
]


EDIT_CASES = [
    {
        "id": "edit_add_object", "source": "product_photo_a", "seed": 12001,
        "prompt": "Keep <image1> unchanged except add one small green succulent in a white ceramic pot immediately to the right of the camera. Preserve camera, label, lighting and composition exactly.",
    },
    {
        "id": "edit_change_color", "source": "product_photo_a", "seed": 12002,
        "prompt": "In <image1>, change only the camera body from matte black to deep metallic red. Keep shape, label, desk, lighting, framing and every other detail unchanged.",
    },
    {
        "id": "edit_remove_label", "source": "product_photo_a", "seed": 12003,
        "prompt": "Remove only the small white label from <image1> and fill the revealed desk naturally. Keep the camera, lighting, shadows and composition unchanged.",
    },
    {
        "id": "edit_portrait_hair", "source": "portrait", "seed": 12004,
        "prompt": "In <image1>, change only the woman's hair color to silver-gray. Preserve her identity, facial features, hairstyle, clothing, pose, lighting and background exactly.",
    },
    {
        "id": "edit_poster_accent", "source": "jp_poster", "seed": 12005,
        "prompt": "In <image1>, change only the red circle accent to cobalt blue. Preserve all Japanese text, typography, alignment and background exactly.",
    },
]


def request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def remap_graph(graph, suffix):
    mapping = {key: f"{key}_{suffix}" for key in graph}

    def visit(value):
        if isinstance(value, list):
            if len(value) == 2 and isinstance(value[0], str) and value[0] in mapping:
                return [mapping[value[0]], value[1]]
            return [visit(v) for v in value]
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        return value

    return {mapping[key]: visit(node) for key, node in graph.items()}


class GpuMonitor:
    def __init__(self):
        self.stop_event = threading.Event()
        self.memory = []
        self.util = []
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self.stop_event.is_set():
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                    text=True, timeout=3, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                ).strip().split(",")
                self.memory.append(int(out[0].strip()))
                self.util.append(int(out[1].strip()))
            except Exception:
                pass
            self.stop_event.wait(0.25)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join(timeout=5)

    def stats(self):
        return {
            "peak_vram_mib": max(self.memory) if self.memory else None,
            "mean_gpu_util_percent": round(float(np.mean(self.util)), 1) if self.util else None,
        }


def run_prompt(prompt, suffix, timeout=2400):
    graph = remap_graph(prompt, suffix)
    started = time.perf_counter()
    queued = request_json(f"{SERVER}/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
    prompt_id = queued["prompt_id"]
    with GpuMonitor() as monitor:
        while time.perf_counter() - started < timeout:
            history = request_json(f"{SERVER}/history/{prompt_id}")
            if prompt_id in history:
                record = history[prompt_id]
                status = record.get("status", {})
                if status.get("status_str") in {"success", "error"}:
                    elapsed = time.perf_counter() - started
                    images = []
                    for output in record.get("outputs", {}).values():
                        images.extend(output.get("images", []))
                    error_messages = [m for m in status.get("messages", []) if m and m[0] == "execution_error"]
                    return {
                        "prompt_id": prompt_id,
                        "success": status.get("status_str") == "success",
                        "elapsed_seconds": round(elapsed, 2),
                        "images": images,
                        "errors": error_messages,
                        **monitor.stats(),
                    }
            time.sleep(1)
    raise TimeoutError(prompt_id)


def image_metrics(path):
    image = Image.open(path)
    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)
    payload = path.read_bytes()
    return {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "pixel_sha256": hashlib.sha256(np.asarray(rgba).tobytes()).hexdigest(),
        "alpha_min": int(alpha.min()),
        "alpha_max": int(alpha.max()),
        "transparent_pixel_percent": round(float(np.mean(alpha < 250) * 100), 3),
    }


def copy_result(image_info, case_id):
    source = COMFY_OUTPUT / image_info.get("subfolder", "") / image_info["filename"]
    suffix = source.suffix.lower() or ".png"
    target = BENCH_OUTPUT / f"{case_id}{suffix}"
    shutil.copy2(source, target)
    return target


def diff_metrics(source_path, edited_path):
    a = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.float32)
    b = np.asarray(Image.open(edited_path).convert("RGB"), dtype=np.float32)
    if a.shape != b.shape:
        return {"same_dimensions": False}
    diff = np.abs(a - b)
    mse = float(np.mean((a - b) ** 2))
    return {
        "same_dimensions": True,
        "mean_abs_diff": round(float(diff.mean()), 3),
        "changed_pixel_percent_gt16": round(float(np.mean(np.max(diff, axis=2) > 16) * 100), 3),
        "psnr_db": round(20 * math.log10(255.0 / math.sqrt(mse)), 3) if mse else 99.0,
    }


def save_progress(results):
    (ROOT / "benchmark_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_contact_sheet(results):
    rows = [r for r in results if r.get("success") and r.get("local_file")]
    tile_w, tile_h, label_h, cols = 300, 300, 42, 4
    sheet = Image.new("RGB", (cols * tile_w, math.ceil(len(rows) / cols) * (tile_h + label_h)), "#e9edf2")
    draw = ImageDraw.Draw(sheet)
    for index, row in enumerate(rows):
        image = Image.open(ROOT / row["local_file"]).convert("RGBA")
        thumb = ImageOps.contain(image, (tile_w - 16, tile_h - 16))
        bg = Image.new("RGBA", thumb.size, "white")
        bg.alpha_composite(thumb)
        x = (index % cols) * tile_w + (tile_w - bg.width) // 2
        y = (index // cols) * (tile_h + label_h) + (tile_h - bg.height) // 2
        sheet.paste(bg.convert("RGB"), (x, y))
        label_y = (index // cols) * (tile_h + label_h) + tile_h + 5
        draw.text(((index % cols) * tile_w + 8, label_y), f"{row['id']}  {row['elapsed_seconds']}s", fill="#18202a")
    path = BENCH_OUTPUT / "contact_sheet.jpg"
    sheet.save(path, quality=90)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edits-only", action="store_true")
    args = parser.parse_args()
    BENCH_OUTPUT.mkdir(parents=True, exist_ok=True)
    base_t2i = json.loads((ROOT / "api_prompt.json").read_text(encoding="utf-8"))
    base_edit = json.loads((ROOT / "api_prompt_edit.json").read_text(encoding="utf-8"))
    results = []
    generated = {}

    if args.edits_only and (ROOT / "benchmark_results.json").exists():
        existing = json.loads((ROOT / "benchmark_results.json").read_text(encoding="utf-8"))
        existing_rows = existing.get("results", existing) if isinstance(existing, dict) else existing
        results = [row for row in existing_rows if row.get("kind") == "t2i"]
        for row in results:
            if row.get("success") and row.get("local_file"):
                path = ROOT / row["local_file"]
                row.update(image_metrics(path))
                generated[row["id"]] = path

    for index, case in ([] if args.edits_only else enumerate(T2I_CASES, 1)):
        prompt = copy.deepcopy(base_t2i)
        prompt["3"]["inputs"]["prompt"] = case["prompt"]
        prompt["4"]["inputs"].update(width=case["size"][0], height=case["size"][1])
        prompt["5"]["inputs"].update(seed=case["seed"], steps=case["steps"])
        prompt["8"]["inputs"]["filename_prefix"] = f"qwen21_benchmark/{case['id']}"
        print(f"[{index}/{len(T2I_CASES) + len(EDIT_CASES)}] {case['id']}", flush=True)
        row = {"id": case["id"], "kind": "t2i", "seed": case["seed"], "steps": case["steps"], "requested_size": list(case["size"])}
        try:
            row.update(run_prompt(prompt, f"t{index}_{uuid.uuid4().hex[:6]}"))
            if row["success"] and row["images"]:
                target = copy_result(row["images"][0], case["id"])
                row["local_file"] = str(target.relative_to(ROOT)).replace("\\", "/")
                row.update(image_metrics(target))
                generated[case["id"]] = target
        except Exception as exc:
            row.update(success=False, exception=repr(exc))
        results.append(row)
        save_progress(results)

    for offset, case in enumerate(EDIT_CASES, 1):
        index = len(T2I_CASES) + offset
        print(f"[{index}/{len(T2I_CASES) + len(EDIT_CASES)}] {case['id']}", flush=True)
        row = {"id": case["id"], "kind": "edit", "source": case["source"], "seed": case["seed"], "steps": 25}
        source = generated.get(case["source"])
        if source is None:
            row.update(success=False, exception="source generation failed")
            results.append(row)
            save_progress(results)
            continue
        input_name = f"benchmark_{case['id']}.png"
        shutil.copy2(source, COMFY_INPUT / input_name)
        prompt = copy.deepcopy(base_edit)
        prompt["4"]["inputs"]["image"] = input_name
        prompt["5"]["inputs"].update(prompt=case["prompt"], resolution=1024)
        prompt["7"]["inputs"].update(seed=case["seed"], steps=25)
        prompt["9"]["inputs"]["filename_prefix"] = f"qwen21_benchmark/{case['id']}"
        try:
            row.update(run_prompt(prompt, f"e{offset}_{uuid.uuid4().hex[:6]}"))
            if row["success"] and row["images"]:
                target = copy_result(row["images"][0], case["id"])
                row["local_file"] = str(target.relative_to(ROOT)).replace("\\", "/")
                row.update(image_metrics(target))
                row.update(diff_metrics(source, target))
        except Exception as exc:
            row.update(success=False, exception=repr(exc))
        results.append(row)
        save_progress(results)

    det_a = next((r for r in results if r["id"] == "determinism_a" and r.get("success")), None)
    det_b = next((r for r in results if r["id"] == "determinism_b" and r.get("success")), None)
    deterministic = bool(det_a and det_b and det_a.get("pixel_sha256") == det_b.get("pixel_sha256"))
    summary = {
        "total": len(results),
        "successes": sum(bool(r.get("success")) for r in results),
        "failures": sum(not r.get("success") for r in results),
        "deterministic_repeat_pixel_match": deterministic,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    payload = {"summary": summary, "results": results}
    (ROOT / "benchmark_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    keys = sorted({key for row in results for key in row if key not in {"images", "errors"}})
    with (ROOT / "benchmark_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key) for key in keys})
    create_contact_sheet(results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
