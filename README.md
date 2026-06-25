# framebeetle

中小企業の事務業務向けローカル Web アプリフレームワークです。  
PC 上で Flask サーバーを起動し、Microsoft Edge で画面を表示します。フォームは YAML ファイルで定義するだけで、一覧・登録・編集・削除が使えるようになります。

## 特徴

- **ローカル完結** — インターネット不要で `127.0.0.1` 上で動作
- **ワンクリック起動** — サーバー起動とブラウザ表示を自動化
- **YAML でフォーム定義** — Python を書かずに業務フォームを追加可能
- **ユーザー管理** — 一般ユーザーと管理者の 2 ロール
- **操作ログ** — 誰がいつ何をしたかを記録
- **exe 配布** — PyInstaller で単体実行ファイルを作成可能

## 動作環境

- Windows 10 / 11
- Python 3.10 以上（仮想環境推奨）
- Microsoft Edge

## セットアップ

### 1. 依存パッケージのインストール

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 設定ファイルの作成

`conf.example.ini` を `conf.ini` にコピーし、環境に合わせて編集します。

```ini
[app]
appname = "SPECIAL APP"       # 画面上部に表示するアプリ名
developer = "Hoge Co."        # フッターに表示する開発者名
secret_key = change-this-secret-key  # セッション用（本番では必ず変更）

[logging]
log_dir = log                 # ログ出力先（相対パス可）

[server]
addr = 127.0.0.1
port = 5000
database = server.db

[dev]
edge_path = C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
python_path = C:\python\venv\2025_flask\Scripts\python.exe
```

| 項目 | 説明 |
|------|------|
| `appname` | アプリケーション名 |
| `secret_key` | ログインセッションの暗号化キー |
| `log_dir` | `app.log` / `server.log` の出力先 |
| `edge_path` | Microsoft Edge の実行ファイルパス |
| `python_path` | サーバー起動に使う Python のパス |

## 起動方法

### 開発・テスト

```powershell
python test.py
```

または

```powershell
python app.py
```

起動後、Edge が自動で開きます。停止は `Ctrl + C` です。

### 初回ログイン

初回起動時に以下のユーザーが自動作成されます。ログイン後、管理者画面からパスワードを変更してください。

| ロール | ユーザー名 | パスワード |
|--------|-----------|-----------|
| 管理者 | `admin` | `admin` |
| 一般 | `user` | `user` |

## フォームの追加方法

`forms` フォルダに YAML ファイルを 1 つ追加するだけで、新しい業務フォームが使えるようになります。サーバーを再起動してください。

### サンプル: `forms/reports.yaml`

```yaml
id: reports
title: 報告登録
description: 日々の業務報告を登録します
table: reports
roles:
  view: [admin, user]
  create: [admin, user]
  edit: [admin, user]
  delete: [admin]
list_columns: [content, category, created_at]
fields:
  - name: category
    label: 分類
    type: select
    required: true
    options: [一般, 緊急, その他]
  - name: content
    label: 内容
    type: textarea
    required: true
  - name: is_done
    label: 対応済み
    type: checkbox
```

### YAML の各項目

| 項目 | 必須 | 説明 |
|------|------|------|
| `id` | ○ | フォーム ID（英小文字・数字・アンダースコア） |
| `title` | ○ | 画面に表示する名前 |
| `description` | — | メニュー画面の説明文 |
| `table` | ○ | SQLite のテーブル名（通常は `id` と同じ） |
| `roles` | — | ロールごとの操作権限（下表参照） |
| `list_columns` | — | 一覧に表示するカラム名 |
| `fields` | ○ | 入力フィールドの定義 |

### 操作権限（roles）

| キー | 説明 | デフォルト |
|------|------|-----------|
| `view` | 一覧の閲覧 | admin, user |
| `create` | 新規登録 | admin, user |
| `edit` | 編集 | admin, user |
| `delete` | 削除 | admin |

### フィールド型（fields.type）

| 型 | 説明 |
|----|------|
| `text` | 1 行テキスト |
| `textarea` | 複数行テキスト |
| `number` | 数値 |
| `date` | 日付 |
| `select` | 選択肢（`options` が必要） |
| `checkbox` | チェックボックス |
| `email` | メールアドレス |

各フィールドで使える属性:

- `name` — DB カラム名（必須）
- `label` — 画面表示名（必須）
- `type` — フィールド型（省略時: `text`）
- `required` — 必須入力（`true` / `false`）
- `options` — `select` 用の選択肢リスト

## 管理者機能

管理者（`admin`）でログインすると、画面上部に以下のメニューが表示されます。

- **ユーザー管理** — ユーザーの作成・編集・削除、ロール変更、有効/無効の切り替え
- **操作ログ** — ログイン、データの登録・更新・削除など直近 200 件の履歴

問題が起きたときは、操作ログの内容を管理者やサポート担当に伝えてください。

## exe ビルド（配布用）

```powershell
python publish.py
```

`conf.ini` が存在することを確認してから実行してください。  
`app.exe` が生成され、ダブルクリックで起動できます。

> **注意:** `forms` フォルダ、`templates` フォルダ、`server.py` などは `app.exe` と同じフォルダに配置したまま配布してください。

## プロジェクト構成

```
framebeetle/
├── app.py              # ランチャー（サーバー起動 + Edge 表示）
├── server.py           # Flask サーバー・ルーティング
├── db.py               # データベース操作
├── auth.py             # 認証・権限チェック
├── forms_loader.py     # YAML フォーム定義の読み込み
├── crud.py             # 汎用 CRUD エンジン
├── config.py           # conf.ini 読み込み
├── log.py              # ログ設定
├── publish.py          # exe ビルド
├── test.py             # 開発用テスト起動
├── forms/              # フォーム定義（YAML）
│   ├── reports.yaml
│   └── payments.yaml
├── templates/          # HTML テンプレート
├── static/             # CSS / JS（Bootstrap）
├── conf.example.ini    # 設定ファイルのサンプル
└── requirements.txt    # Python 依存パッケージ
```

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| ログインできない | `conf.ini` の `secret_key` を変更した後は再ログイン。ユーザーが無効化されていないか管理者に確認 |
| フォームが表示されない | YAML の `id` が英小文字で始まっているか確認。サーバーを再起動 |
| Edge が開かない | `conf.ini` の `edge_path` が正しいか確認 |
| エラーが起きた | `log` フォルダ内の `server.log` を確認 |

## ライセンス

MIT License — Copyright (c) 2025 YASUO MIYAZAKI
