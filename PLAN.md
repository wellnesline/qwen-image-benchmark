# Qwen Image 2.1 ComfyUI PoC

## 目的

既存の ComfyUI Portable 上で Qwen Image 2.1 の公式 Text-to-Image ワークフローを再現し、VRAM 16GB 程度を要件とする GPU 環境で実画像を生成できることを確認する。

## 完了条件

- ComfyUI を Qwen Image 2.1 対応版へ更新する
- int8 diffusion model / int8 text encoder / bf16 VAE を所定位置へ配置する
- 公式ワークフローを保存し、ComfyUI API から実行する
- 出力 PNG、実行時間、主要設定、検証結果を記録する

## 検証方法

1. ComfyUI 起動ログで Qwen Image 2.1 関連ノードの import エラーがないことを確認
2. `/object_info` と `/prompt` API が正常応答することを確認
3. 1024x1024、25 steps、CFG 1、Euler/simple で画像を1枚生成
4. PNG の寸法・RGBA/RGBモードと生成履歴を確認

## 状態

- [x] 公式情報、ライセンス、必要ファイルを確認
- [x] GPU、空き容量、既存 ComfyUI を確認
- [x] ComfyUI 更新（0.37.0）
- [x] モデル配置（int8 + int8 + bf16、合計約16.1GB）
- [x] 公式ワークフロー保存・API実行
- [x] 出力検証・結果記録

## 結果

- Text-to-Image: 1024x1024 RGBA、25 steps、14.05秒、成功
- Image Edit: 正しい画像条件付きAPIで15.20〜35.18秒、5/5成功
- VRAM 16GB 程度の要件の範囲で OOM なし
- ComfyUI 0.37.0 / frontend 1.53.6
- Image Edit初回はAIMDOの `aimdo memory compile error` が発生。ComfyUIを `--disable-comfy-compiler` 付きで再起動すると解消
- 初版APIの動的入力キーを `images` としていたため画像が条件付けされていなかった。`images.image_1` へ修正し、編集5件を全て再実行済み
- GUI/API: `http://127.0.0.1:8188`（既定ポート）

## 注意

Qwen Image 2.1 は Qwen Research License Agreement。今回のPoCは非商用の研究・評価目的に限定する。

## 拡張ベンチマーク

### 目的

単発PoCでは判断できない速度のばらつき、解像度スケーリング、題材別の安定性、透過出力、再現性、局所編集時の原画像保持を約20ケースで評価する。

### 完了条件

- [x] 1MP相当で写真・人物・手・アニメ・文字・図解・風景・建築・透過を生成
- [x] 同一prompt/seedをサーバー再起動後に再実行し決定性を検証
- [x] 2Kを25 stepsと40 stepsで生成
- [x] 5種類のImage Editを実行
- [x] 成功率、時間、ピークVRAM、画像属性、透過率、編集差分をJSON/CSVへ記録
- [x] 全結果のコンタクトシートを作成
