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
├── docs/
│   ├── START_HERE.md                  # ChatGPT / 人間向け入口
│   └── chatgpt-project-instructions.md  # ChatGPT Project に貼る指示文
├── notes/                             # 自由メモ（Markdown）
│   └── .gitkeep
└── logs/                              # セッション記録・接続ログ
    └── .gitkeep
```

## ChatGPT との連携（概要）

1. ChatGPT **Settings → Apps → GitHub** で `kyo01kuni19-byte/Mira-project` を接続
2. ChatGPT **Project「Mira」** を作成し、このリポジトリをソースに追加
3. `docs/chatgpt-project-instructions.md` の内容を Project Instructions に貼る
4. 新規リポジトリでインデックスが効かない場合、GitHub で次を検索して 5〜10 分待つ:
   `repo:kyo01kuni19-byte/Mira-project import`

## ローカル clone

```bash
git clone https://github.com/kyo01kuni19-byte/Mira-project.git
cd Mira-project
```

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
