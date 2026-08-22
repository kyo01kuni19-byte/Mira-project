# START HERE — Mira-project

このファイルは、ChatGPT または人間が **Mira-project を初めて開いたとき** に読む入口です。

## Mira とは

Mira は Kuni の個人プロジェクト領域です。このリポジトリは Mira 関連の設計・メモ・ログの **正本（source of truth）** です。

## 読む順序

1. **README.md** — リポジトリ全体の目的と構成
2. **docs/chatgpt-project-instructions.md** — ChatGPT Project 用の振る舞い指示
3. **docs/CURSOR_START.md** — Cursor 実装セッション用（設計と実装の分担）
4. **notes/** — 最新の思考・設計メモ（随時追加）
5. **logs/** — セッション記録（随時追加）

## ChatGPT 向けルール

- 応答言語: **日本語**（Kuni が英語を指定しない限り）
- このリポジトリのファイル内容を前提に回答する
- リポジトリにない情報は推測せず、不明と明示する
- 新しい成果物を提案するときは、**保存先パス**（例: `notes/2026-08-22_テーマ.md`）を示す
- Kuni が「保存して」と言うまで、リポジトリへの書き込みはできない（読み取りのみ）

## 現在の状態

| 項目 | 値 |
|------|-----|
| リポジトリ | `kyo01kuni19-byte/Mira-project` |
| 可視性 | public |
| フェーズ | ChatGPT 連携済み · Cursor 設定済み |
| 主要トピック | （Kuni が `notes/` に追記） |

## チャネル分担

| チャネル | 用途 |
|---------|------|
| **ChatGPT Project「Mira」** | 設計・方針・メモ案 |
| **Cursor** | 実装・編集・commit / push |

引き継ぎ形式: `docs/handoff-template.md` → `notes/` に保存 → Cursor で実装

## 次のアクション（Kuni）

- [x] ChatGPT Project「Mira」を作成し、GitHub リポジトリを接続
- [x] `docs/chatgpt-project-instructions.md` を Project Instructions に貼る
- [x] Cursor で Mira-project をワークスペースとして開く
- [ ] 最初のメモまたは Handoff を `notes/` に追加して push

---

*Interface: GitHub → ChatGPT Project · Cursor → implementation*
