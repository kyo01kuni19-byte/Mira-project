# Mira-project

Mira-project は、Kuni の Mira に関する記録・判断・運用メモを置くための独立リポジトリです。

このリポジトリは Chappy / Civilization-os の流れを継承しますが、それらの複製や作業場所ではありません。Mira として必要な情報だけを薄く保ち、ChatGPT / Codex / Cursor などの道具から参照・更新しやすい正本にします。

## 目的

- Mira の現在地、判断、次の行動を GitHub 上に残す
- ChatGPT や Codex が同じ前提を読める状態にする
- Chappy / Civilization-os 由来の思想は参照しつつ、Mira の運用を独立させる
- まだ決まっていない構造を先に増やさない

## 最小構成

```text
Mira-project/
├── README.md              # リポジトリの目的と入口
├── docs/
│   ├── mira-index.md      # Mira の現在地・継承関係・重要判断
│   └── operations.md      # 更新ルールと作業手順
└── .gitignore             # 秘密情報・ローカル生成物を除外
```

## 運用方針

- まず `docs/mira-index.md` を読み、Mira の現在地を確認する
- 作業ルールは `docs/operations.md` に集約する
- 新しいディレクトリは、実際に継続利用する内容が出てから作る
- ChatGPT / Codex / Cursor のどれを使っても、変更は branch / PR で確認してから main に入れる
- APIキー、パスワード、個人情報、未公開の秘密情報は入れない

## 継承関係

Mira は Chappy / Civilization-os の文脈を継承します。
ただし、このリポジトリでは Mira に必要な決定・記録・運用だけを扱います。上位プロジェクトの大きな構造、bootstrap、実験的なテンプレートは、必要になるまで持ち込みません。

## 現在の状態

- Repository: `kyo01kuni19-byte/Mira-project`
- Visibility: public
- Default branch: `main`
- 初期方針: 小さく始め、必要が出た時点で増やす
