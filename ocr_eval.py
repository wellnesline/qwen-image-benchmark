import difflib
import json
import re
import sys
from pathlib import Path

from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
OUTPUTS = ROOT / "benchmark_outputs"
CASES = {
    "jp_poster": ["未来をつくるAI", "2000年1月1日", "開催"],
    "en_infographic": ["LOCAL AI WORKFLOW", "1. PLAN", "2. GENERATE", "3. VERIFY"],
    "flow_diagram": ["PROMPT", "MODEL", "IMAGE", "REVIEW"],
    "2k_jp_poster_40": ["生成AI 実践フォーラム", "2000.01.01", "HALL A"],
    "edit_poster_accent": ["未来をつくるAI", "2000年1月1日", "開催"],
}


def normalize(text):
    return re.sub(r"[^0-9A-Z\u3040-\u30ff\u3400-\u9fff]", "", text.upper())


def score_token(expected, recognized):
    target = normalize(expected)
    candidates = [normalize(text) for text in recognized]
    candidates.append("".join(candidates))
    return round(max((difflib.SequenceMatcher(None, target, value).ratio() for value in candidates), default=0.0), 3)


def main():
    engine = RapidOCR()
    report = {}
    for case_id, expected in CASES.items():
        result, elapsed = engine(str(OUTPUTS / f"{case_id}.png"))
        lines = [] if not result else [{"text": item[1], "confidence": round(float(item[2]), 3)} for item in result]
        recognized = [line["text"] for line in lines]
        token_scores = {token: score_token(token, recognized) for token in expected}
        elapsed_total = sum(elapsed) if isinstance(elapsed, (list, tuple)) else float(elapsed)
        report[case_id] = {
            "elapsed_seconds": round(float(elapsed_total), 3),
            "lines": lines,
            "expected_token_scores": token_scores,
            "mean_expected_score": round(sum(token_scores.values()) / len(token_scores), 3),
        }
        print(case_id, report[case_id]["mean_expected_score"], recognized)
    (ROOT / "ocr_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
