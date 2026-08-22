# CURSOR START — Mira-project

Cursor で **実装・編集・Git 操作** を行うセッションの入口です。

## このセッションの役割

**Cursor = 実装担当。** 設計・方針・長い対話は ChatGPT Project「Mira」で行い、ここではファイル変更と push を行います。

## 開始前チェック

1. ワークスペース root が `Mira-project` であること
2. `git pull` で最新化（必要なら）
3. ChatGPT で決めた内容が `notes/` に push 済みか確認

## 典型的な依頼例

| Kuni の依頼 | Cursor の action |
|-------------|------------------|
| 「このメモを実装して」 | `notes/` の handoff を読み、コード/ファイルを作成 |
| 「README を更新して push」 | 編集 → commit → push |
| 「設計を一緒に考えたい」 | ChatGPT Project を案内（または `notes/` に要点を残す） |

## コピペ用（新規 Cursor チャット）

```
Mira-project — Cursor 実装セッション

Read: docs/CURSOR_START.md
Role: 実装・編集・Git（設計は ChatGPT Project「Mira」）
Language: 日本語

Task: [ここに具体的な実装タスク]
```

## Git 操作

```bash
cd /Users/kuni/Documents/GitHub/Mira-project
git pull
# 作業後
git add -A
git commit -m "説明的なメッセージ"
git push origin main
```

## 関連ファイル

| ファイル | 用途 |
|---------|------|
| `docs/START_HERE.md` | 全体入口 |
| `docs/handoff-template.md` | ChatGPT → Cursor 引き継ぎ形式 |
| `.cursor/rules/mira-workflow.mdc` | Cursor エージェント向け常時ルール |

---

*Interface: Cursor — implementation*
