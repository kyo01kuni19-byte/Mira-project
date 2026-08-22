# Operations

Mira-project を小さく持続させるための運用メモです。

## 読む順序

1. `README.md`
2. `docs/mira-index.md`
3. `docs/operations.md`

## 更新ルール

- 変更は小さく分ける
- main へ直接 push せず、可能な限り branch / PR を使う
- 新しいフォルダは、実際に継続利用する内容が出てから作る
- 1回限りのメモや未整理の会話ログは、すぐにリポジトリへ増やさない
- Chappy / Civilization-os 由来の内容を入れる場合は、Mira に必要な要点へ圧縮する

## ChatGPT / Codex / Cursor の使い分け

| 道具 | 主な用途 |
|------|----------|
| ChatGPT | 相談、整理、方針確認 |
| Codex | GitHub上の安全な編集、branch / PR 作成、差分整理 |
| Cursor | ローカル編集、実装、手元での確認 |

どの道具を使っても、最終的な正本は GitHub の main branch です。

## 変更前チェック

- Mira に直接関係する内容か
- 既存ファイルに追記・修正すれば足りるか
- 新しい構造を作る理由があるか
- public リポジトリに置いて問題ない内容か

## PRに含める説明

- 何を変えたか
- なぜ変えたか
- 削ったもの、残したもの
- main に入れた後の次の一手
