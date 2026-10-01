# qwen-image-benchmark

Reproducible text-to-image / image-edit API runs and a benchmark suite with OCR scoring for Qwen Image 2.1 on a local ComfyUI (research and evaluation use).

公開用に整理した、Qwen Image 2.1 を ComfyUI 上で動かす PoC とベンチマークです。

## 構成

- ComfyUI: Windows portable 版。内側の `ComfyUI` ディレクトリを環境変数 `COMFY_DIR` に設定する（`%COMFYUI_DIR%` と呼ぶ）
- GPU: 要件は VRAM 16GB 程度
- Model: Qwen Image 2.1 int8 convrot
- Text encoder: Qwen3-VL 8B int8 convrot
- VAE: Qwen Image 2.1 bf16

## 起動

```powershell
cd <ComfyUI_windows_portable>
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --disable-comfy-compiler
```

GUI はローカルの ComfyUI（既定ポート 8188）。Image Edit で AIMDO エラーを避けるため、`--disable-comfy-compiler` を維持する。

## API PoC再実行

```powershell
python run_poc.py
python run_poc.py --prompt-file api_prompt_edit.json --result-file result_edit.json
```

`api_prompt.json` がText-to-Image、`api_prompt_edit.json` がImage Edit。編集入力はComfyUIの `input\qwen21_poc_input.png`。

動的画像入力はAPI上で `images.image_1` のようなフラットキーを使う。`images: {image_1: ...}` では画像が条件付けされないため注意。

## 拡張ベンチマーク

```powershell
$env:COMFY_DIR = "<ComfyUI_windows_portable>\ComfyUI"
<ComfyUI_windows_portable>\python_embeded\python.exe benchmark_suite.py
```

結果は `benchmark_results.json` / `benchmark_results.csv` / `BENCHMARK_REPORT.md`。OCR評価は `ocr_eval.py` を使う。

## 設計のポイント

- API 用プロンプト JSON（`api_prompt*.json`）を保存し、同じ入力で再実行できる。ComfyUI 公式のワークフローテンプレート（Comfy-Org）は同梱していない。公式ドキュメントの Qwen Image 2.1 の手順から入手する。決定性の確認用に、再起動後の再実行結果（`result_determinism_restart.json`）を比較する構成になっている。
- 結果は JSON / CSV / Markdown レポートに残し、生成画像は再生成できるので同梱しない。
- 画像内の文字の描画精度は、生成画像を OCR にかけた結果と期待文字列の差分で評価する（`ocr_eval.py`）。OCR は代理指標なので、人の目視確認と併用する前提。

## 依存・注意

- Python: numpy, Pillow（benchmark_suite.py）、`rapidocr_onnxruntime`（ocr_eval.py。OCR評価用に別 venv 推奨）
- `nvidia-smi`（VRAM計測）
- `benchmark_outputs/`（生成画像・コンタクトシート）は非同梱。`benchmark_suite.py` で再生成できる。`ocr_eval.py` はこのディレクトリの画像を読む。
- ベンチマークのプロンプトはすべて汎用の評価用文面（商品写真・風景・図解など）。
- **公開版での置換の注記**: プライバシーのため、ポスター画像のプロンプト中の日付と OCR 結果の該当文字列は、測定後に合成日付へ置換した。一致率の数値は置換前の測定値である。

## 制限事項（閉包）

- **同梱していない依存**（3 件）: `numpy`、`PIL`（Pillow）、`rapidocr_onnxruntime`。`requirements` ファイルは同梱していない。標準ライブラリ以外の import はこの 3 件のみ。
- 同梱していないもの: ComfyUI 本体、モデルの重み（diffusion model / text encoder / VAE）、ComfyUI のカスタムノード類、生成画像。実行には ComfyUI の起動（`COMFY_DIR`）が必要で、外部サービスの API キーは使わない。
- 他の公開リポジトリへの依存はない。
- 公式テンプレート・モデルは各提供元のライセンスに従う。モデルは Qwen Research License Agreement に従う。今回の成果は非商用の研究・評価 PoC として扱う。

## ライセンス

All rights reserved. 閲覧目的で公開しています。詳細は LICENSE を参照。モデルの重みは本リポジトリに含まれず、各提供元のライセンスに従います。
