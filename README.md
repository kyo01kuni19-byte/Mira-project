# Mira-project

Miraの継続的な設計・学習・検証を支える独立リポジトリです。

## Purpose

このリポジトリの目的は、MiraのCurrent Stateを失わず、変更理由と学習履歴をGit上で追跡しながら、Mira ArchitectureをEvidenceによって進化させることです。

## Source of Truth

- **`PROJECT_MEMORY.md`** — 現在のMira Project State。会話・時間・環境を越えて再開するための正本候補。
- **`docs/lineage.md`** — Chappy / Civilization OS / CGIからMiraへの継承関係。Miraは独立Systemとして扱う。
- **Git history** — 過去State、変更履歴、変更理由。

## Minimal Structure

```text
Mira-project/
├── README.md
├── PROJECT_MEMORY.md
├── .gitignore
├── .cursor/
│   └── rules/
│       └── mira-workflow.mdc
└── docs/
    └── lineage.md
```

必要性がUse Caseから確認されるまで、notes / logs / Wiki / 詳細taxonomy等は追加しません。

## Working Model

- ChatGPTはMiraの設計・思考・Project Memory更新・GitHub操作に利用できる。
- Cursorはローカルコード実装やrepository作業が必要な場合の実装手段として利用できる。
- Toolごとの役割を固定しすぎず、各Environmentで利用可能なCapability / Permissionを確認して使い分ける。
- 重要な変更は可能な限りbranch / PRで差分とRationaleを確認してからmainへ反映する。

## Continuity Pilot

GitHubをMiraのgoverned source-of-truth候補として検証中です。

主な評価観点：

- Current Stateを別セッション・別Environmentから復元できるか
- 更新理由とVersion Historyを追えるか
- Human負荷が過大にならないか
- Access / Disclosure / Governanceを扱えるか
- 必要なKnowledgeだけを保持し、過剰な構造を避けられるか

## Security

このrepositoryは現在publicです。APIキー、Password、Company confidential information、Personal confidential information等の秘密情報は保存しないでください。

---

*Last updated: 2026-08-22*
