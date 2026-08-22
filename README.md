# Mira-project

Mira 専用リポジトリ。設計メモ・対話ログ・Project Instructions を GitHub 経由で ChatGPT に読ませるための正本です。

## 目的

- **Mira** に関する思考・設計・記録を一か所に集約する
- ChatGPT（Project + GitHub コネクタ）からリポジトリ内容を参照できるようにする
- ローカル編集 → commit → push → ChatGPT で参照、というループを回す

## リポジトリ構成

```
Mira-project/
├── README.md                          # このファイル
├── .cursor/rules/
│   └── mira-workflow.mdc              # Cursor エージェント向け常時ルール
├── docs/
│   ├── START_HERE.md                  # ChatGPT / 人間向け入口
│   ├── CURSOR_START.md                # Cursor 実装セッション入口
│   ├── handoff-template.md            # ChatGPT → Cursor 引き継ぎ
│   └── chatgpt-project-instructions.md  # ChatGPT Project に貼る指示文
├── notes/                             # 自由メモ（Markdown）
│   └── .gitkeep
└── logs/                              # セッション記録・接続ログ
    └── .gitkeep
```

## チャネル分担

| チャネル | 役割 |
|---------|------|
| **ChatGPT Project「Mira」** | 設計・思考・方針（GitHub 読み取り） |
| **Cursor** | 実装・ファイル編集・commit / push |

Handoff: ChatGPT で設計 → `notes/` に `handoff-template.md` 形式で保存 → Cursor で実装。

## ChatGPT との連携（概要）

1. ChatGPT **Settings → Apps → GitHub** で `kyo01kuni19-byte/Mira-project` を接続
2. ChatGPT **Project「Mira」** を作成し、このリポジトリをソースに追加
3. `docs/chatgpt-project-instructions.md` の内容を Project Instructions に貼る
4. 新規リポジトリでインデックスが効かない場合、GitHub で次を検索して 5〜10 分待つ:
   `repo:kyo01kuni19-byte/Mira-project import`

## ローカル clone / Cursor で開く

```bash
git clone https://github.com/kyo01kuni19-byte/Mira-project.git
cd Mira-project
```

Cursor: **File → Open Folder** → `/Users/kuni/Documents/GitHub/Mira-project`  
実装セッション開始: `docs/CURSOR_START.md` を参照

## 更新の流れ

1. `notes/` や `docs/` を編集
2. `git add` → `git commit` → `git push`
3. ChatGPT Project 内で内容を参照（数分後に反映）

## 注意

- GitHub コネクタは **読み取り専用**。ChatGPT から直接 push できない
- commit 履歴は読まれない。**ファイルとして push した内容**が参照対象
- 秘密情報（API キー、パスワード）はリポジトリに入れない（public リポジトリ）

---

*Last updated: 2026-08-22*
