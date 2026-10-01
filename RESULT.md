# PoC結果

## 判定

成功。VRAM 16GB 程度を要件とする構成の ComfyUI で、Qwen Image 2.1のText-to-ImageとImage Editを同一モデル構成で実行できた。

## 実測

| テスト | 設定 | 結果 | 総所要時間 |
|---|---|---|---:|
| Text-to-Image | 1024x1024 / 25 steps / CFG 1 / Euler / simple | 1024x1024 RGBA PNG | 14.05秒 |
| Image Edit | 1024x1024 / 25 steps / CFG 1 / Euler / simple / cache int8 | 1024x1024 RGBA PNG | 15.20秒 |

出力ファイルは `image/png` で取得でき、ローカル原本とのSHA-256一致を確認済み。

## 環境

- GPU: 要件は VRAM 16GB 程度(計測は `nvidia-smi`)
- ComfyUI: 0.37.0
- Frontend: 1.53.6
- diffusion: `qwen_image_2.1_int8_convrot.safetensors` (7,256,783,064 bytes)
- text encoder: `qwen3vl_8b_int8_convrot.safetensors` (9,350,798,360 bytes)
- VAE: `qwen_image_2.1_vae_bf16.safetensors` (675,509,688 bytes)

## 既知の注意点

ComfyUI 0.37.0の既定起動ではImage Edit時に `RuntimeError: aimdo memory compile error` が発生した。`--disable-comfy-compiler` を付けて再起動すると解消し、同じワークフローが12.06秒で成功した。PoC環境ではこの起動オプションを維持する。

初版のAPIは動的画像入力を誤ってネスト形式で渡していたため、画像条件付けなしで実行されていた。入力キーを `images.image_1` に修正し、画像条件付き編集を再検証した。正しい実測は15.20〜35.18秒。

`triton` 未導入の警告は出るが、今回の環境での生成・編集には影響しなかった。

## 公開版での置換の注記

プライバシーのため、ポスター画像のプロンプト中の日付と OCR 結果の該当文字列は、測定後に合成日付へ置換した。一致率の数値は置換前の測定値である。

## 参照

- 解説記事: https://aiaicreate.com/comfyui-qwen-image-2-1/
- ComfyUI公式手順: https://docs.comfy.org/tutorials/image/qwen/qwen-image-2-1
- 公式モデル: https://huggingface.co/Comfy-Org/Qwen-Image-2.1
- Qwen公式リポジトリ: https://github.com/QwenLM/Qwen-Image-2.1

Qwen Research License Agreementのため、本PoCは非商用の研究・評価用途に限定する。
