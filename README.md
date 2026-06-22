# 日本合唱曲データベース

管理者なし・コスト0円で自律的に育つ、日本の合唱曲データベース。
GitHub Actions が定期的に情報源を巡回してデータを追加し、
信頼度の低い項目はコミュニティが Pull Request で校正していく仕組みです。

## アーキテクチャ

```
GitHub Actions（週次クロール） ──┐
                                  ├─→ data/songs.json ──→ GitHub Pages（index.html + Fuse.js）
コミュニティのPull Request ──────┘
```

外部サービス・APIキー・サーバーは一切使用しません。GitHubのみで完結します。

| 役割 | 実体 |
|---|---|
| データ本体 | `data/songs.json`（1曲1レコードのJSON配列） |
| スキーマ定義 | `schema/song.schema.json`（JSON Schema） |
| 自動収集 | `crawler/jca_meikyoku_crawler.py`（GitHub Actionsから実行） |
| 自動検証 | `.github/workflows/validate.yml`（PR時にスキーマ適合チェック） |
| 定期実行 | `.github/workflows/crawl.yml`（毎週月曜3:00 JST） |
| 検索UI | `index.html`（GitHub Pagesで配信、Fuse.jsでクライアント検索） |

## ディレクトリ構成

```
.
├── index.html                  # 検索ページ（GitHub Pagesのルートに配置）
├── data/
│   └── songs.json              # 楽曲データ本体
├── schema/
│   └── song.schema.json        # JSON Schema定義
├── crawler/
│   ├── parser.py                # テキスト→構造化データの変換ロジック
│   ├── jca_meikyoku_crawler.py  # 全日本合唱連盟サイトのクローラー本体
│   ├── test_parser.py           # パーサーの回帰テスト
│   └── requirements.txt
└── .github/workflows/
    ├── crawl.yml                # 週次自動クロール
    └── validate.yml             # PR時の自動検証
```

## セットアップ（最初の1回だけ）

1. このディレクトリをそのままGitHubリポジトリの中身として `git init` → push する。
2. リポジトリの **Settings → Pages** で、Source を「Deploy from a branch」、
   Branch を `main` / `（root）` に設定する（`index.html` がリポジトリ直下にあるため）。
3. **Settings → Actions → General** で、Workflow permissions を
   「Read and write permissions」に変更する（`crawl.yml` が `git push` するため）。
4. これで完了。あとは毎週自動的に `data/songs.json` が更新され、
   GitHub Pagesのサイトにも自動で反映される。

## confidence（信頼度）と needs_review について

クローラーは「コンクール課題曲一覧」のような自由記述テキストを正規表現でパースしています。
**2018〜2025年度（No.48〜No.53）の実データ6エディション・計72曲**を使って検証した結果、
**約89%（64/72曲）が高信頼度（confidence ≥ 0.9）で自動分離できています**。
日本語の曲名・作詞者・作曲者は語の区切りが明確なため特に精度が高く、
旧形式（クレジット全体を括弧で囲む2018年度以前の表記）や、
詩／訳詩／曲／編曲／詩曲／採譜が複数の「／」で連結されるケースにも対応済みです。

残り約11%（8曲）が`needs_review: true`になる理由:

- **欧文（特にドイツ語）の曲名と作曲者名の境界**は、正規表現だけでは原理的に
  確実に判定できません（ドイツ語は名詞をすべて大文字で書くため、
  "Das edle Herz"のようなタイトルと人名の区別が構造的に不可能なケースがあります）。
- **「詩」「曲」がスペースのみで連結され、出典が固有名詞でない**ケース
  （アイヌ民謡の採譜者、落語由来の詞など）は、役割の境界が曖昧なため
  自動分離を諦めています。
- パーサーは「人名に本来含まれないはずの記号（「」やトレーリングの『より』
  『訳詩』）」を検知すると、たとえ一見もっともらしい分離ができていても
  自動的に confidence を下げて要レビュー扱いにします（誤った自信を持たない設計）。

検索ページ上では、そうした項目に朱色の「朱」マークが表示されます。
`sources[].raw_text` に元のテキストがそのまま保存されているので、
人間が正しい区切りを判断してPRで修正できます。

**自動クロールは既存レコードを絶対に上書きしません。** 一度人間が修正したレコードは、
次回以降のクロールで再びパースされても無視されます（`id` の重複チェックによる）。

パーサーの検証データと期待値は `crawler/fixtures/raw_editions.py` と
`crawler/test_parser.py` に全て残してあるので、ロジックを変更する際はまず
このテストを通すこと。

## コミュニティによるデータ追加・修正の流れ

1. `data/songs.json` を直接編集する（または新しいレコードを追記する）PRを作成。
2. `validate.yml` が自動的にJSON Schemaへの適合・ID重複の有無をチェック。
3. パスすればマージ可能（ブランチ保護ルールで「チェック必須」に設定しておくと、
   人間のレビューなしでも安全に自動マージできる状態にできる）。

新規レコードの `id` は次のルールを推奨:
- コンクール課題曲: `jca-{年度}-{曲記号}`（例: `jca-2025-G1`）
- それ以外: 任意のスラッグ（英数字・ハイフン・アンダースコアのみ、3〜80文字）

## クローラーをローカルで試す

```bash
cd crawler
pip install -r requirements.txt
python3 test_parser.py                           # まずパーサーの単体テストを確認

# 初回セットアップ時：全エディションをバックフィル（結果を表示するのみ）
python3 jca_meikyoku_crawler.py --start-no 1 --end-no 53 --dry-run

# 通常運用：最新からさかのぼってDEFAULT_LOOKBACK件のみ取得
python3 jca_meikyoku_crawler.py --dry-run

# 抽出テキストをファイルに保存して構造を目視確認したい場合
python3 jca_meikyoku_crawler.py --start-no 53 --end-no 53 --dry-run --save-raw-dir /tmp/jca-pages
```

### 既知の制約（重要）

- **対象URL**: 各エディションは
  `https://jcanet.or.jp/Public/meikyoku/meikyoku-No{番号}.htm` という
  個別ページに分かれています（青森県・埼玉県の合唱連盟の告知ページから
  URLパターンを確認済み）。クローラーはこの番号を直接指定して巡回します。
  `meikyoku-index.htm` から最新号を自動検出しますが、ページ構造が
  変わると検出に失敗する可能性があるため、`--end-no` で明示的に
  指定することもできます。
- **小学校編（E1〜E6等）は未対応です。** レギュラー版（G/M/F）と異なり、
  作詞者・作曲者情報を全体的にもう一段階括弧で囲む表記の亜種を使っており、
  `parser.py` は曲を1件も検出できずそのページをスキップします
  （実行時に "曲目を検出できず" というログが出ます）。対応する場合は
  `parser.py` に新しい分岐を追加してください。
- **発行年度の推定（`extract_publication_year`）は best-effort** です。
  「発行日：YYYY年M月D日」のような表記から推定していますが、
  実際のページで表記が異なる場合は正しく取得できないことがあります。
  `source_detail.edition_no`（エディション番号）の方が確実な識別子です。
- 同サイトは Shift-JIS（cp932）配信で、Content-Typeにcharsetが
  明示されていません。エンコーディング関連のエラーが出た場合は
  `fetch_html()` 内の明示的な `cp932` デコードを疑ってください。

パーサーの検証データと期待値は `crawler/fixtures/raw_editions.py` と
`crawler/test_parser.py` に全て残してあるので、ロジックを変更する際はまず
このテストを通すこと。

## 今後の拡張案

- 小学校編（E1〜E6）向けの括弧囲みフォーマットに対応する。
- No.1〜No.47など、より古いエディションでもテストを拡充し、
  パーサーの対応範囲をさらに広げる。
- 他の情報源（演奏会プログラムPDF、出版社サイトなど）に対応するクローラーを
  `crawler/` 配下に追加していく（`parser.py` の信頼度設計の考え方を踏襲）。
- Wikidata / MusicBrainz と連携し、作曲家の生没年などを自動補完する。
- `voicing_detail`（SATB等の詳細表記）をコミュニティ投稿で充実させていく。
