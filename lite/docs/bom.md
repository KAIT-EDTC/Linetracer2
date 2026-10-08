# Linetracer2 Lite rev.L3 部品表（秋月のリンクつき）

> 最終更新: 2026-10-09（赤 LED → **フルカラー LED PL9823 ×6**（左右の端に 3 こずつ）、テストパッドは基板の銅だけで部品なし）。秋月の通販コード・品名・価格は、この日に**全部のリンクを開いて確かめた**（19 品目）。価格は税込・変わることがある。
> 機械可読の部品表（KiCad から自動で出る）: [`../hardware/kicad/bom/Linetracer2-Lite_bom.csv`](../hardware/kicad/bom/Linetracer2-Lite_bom.csv)。くわしい理由は [`../README.md`](../README.md) §5。
> 買い方のルール（実店舗か T 番号のある通販だけ）は [`../../docs/05_bom.md`](../../docs/05_bom.md) §0。

## 1. 基板に載る部品（1 台分、すべて秋月）

| 記号 | 部品 | 数 | 秋月 | 秋月の売り方 | 1 台分 |
|------|------|----|------|-------------|-------|
| U1 | Seeed Studio XIAO ESP32C6 | 1 | [129481](https://akizukidenshi.com/catalog/g/g129481/) | 1 個 ¥1,100 | ¥1,100 |
| — | ピンヘッダー 1×40（7 ピン × 2 本に切って XIAO に） | 14 ピン | [100167](https://akizukidenshi.com/catalog/g/g100167/) | 1 本 ¥35 | ≒¥14 |
| U2 | TC78H653FTG モータードライバーモジュール（1×8 ピンヘッダー 2 本付き） | 1 | [114746](https://akizukidenshi.com/catalog/g/g114746/) | 1 個 ¥200 | ¥200 |
| PS1〜PS3 | フォトリフレクター LBR-127HLD | 3 | [104500](https://akizukidenshi.com/catalog/g/g104500/) | 1 個 ¥80 | ¥240 |
| BZ1 | 圧電スピーカー 13 mm PKM13EPYH4000-A0 | 1 | [104118](https://akizukidenshi.com/catalog/g/g104118/) | 1 個 ¥30 | ¥30 |
| Q1 | トランジスター 2SC1815-GR | 1 | [117089](https://akizukidenshi.com/catalog/g/g117089/) | 20 個 ¥100 | ¥5 |
| D1 | ショットキーダイオード 1N5819 | 1 | [117244](https://akizukidenshi.com/catalog/g/g117244/) | 10 個 ¥100 | ¥10 |
| R1〜R3, R9 | 抵抗 100 Ω（ちゃ くろ **ちゃ** きん） | 4 | [125101](https://akizukidenshi.com/catalog/g/g125101/) | 100 本 ¥200 | ¥8 |
| R4〜R6 | 抵抗 10 kΩ（ちゃ くろ **だいだい** きん） | 3 | [125103](https://akizukidenshi.com/catalog/g/g125103/) | 100 本 ¥100 | ¥3 |
| R7, R10 | 抵抗 1 kΩ（ちゃ くろ **あか** きん） | 2 | [125102](https://akizukidenshi.com/catalog/g/g125102/) | 100 本 ¥100 | ¥2 |
| C1, C2 | 電解コンデンサー 470 µF 16 V（ルビコン WXA） | 2 | [108426](https://akizukidenshi.com/catalog/g/g108426/) | 1 個 ¥10 | ¥20 |
| C3, C4 | 積層セラミックコンデンサー 0.1 µF 50 V | 2 | [113582](https://akizukidenshi.com/catalog/g/g113582/) | 10 個 ¥100 | ¥20 |
| D2〜D7 | **5 mm シリアル制御フルカラー LED PL9823-F5**（NeoPixel 型） | 6 | [108411](https://akizukidenshi.com/catalog/g/g108411/) | 1 個 ¥40 | ¥240 |
| SW1 | タクトスイッチ（黒） | 1 | [108075](https://akizukidenshi.com/catalog/g/g108075/) | 1 個 ¥10 | ¥10 |
| J1 | XH コネクター ベース付ポスト 2P B2B-XH-A | 1 | [112247](https://akizukidenshi.com/catalog/g/g112247/) | 1 個 ¥10 | ¥10 |
| | | | | **小計** | **≒¥1,912** |

- （やり方 B）XIAO を抜き差しして使い回すなら、7 ピンのピンソケット 2 本も要る。
- 基板そのものは特注（JLCPCB など、30 枚で 1 枚 ≒¥80）。Gerber: [`../hardware/Linetracer2-Lite_rev.L3_gerber.zip`](../hardware/Linetracer2-Lite_rev.L3_gerber.zip)。

## 2. 機械部品（1 台分）

| 部品 | 数 | 買う所 | 売り方 | 1 台分 |
|------|----|-------|-------|-------|
| DC モーター FA-130RA-2270 | 2 | 秋月 [106437](https://akizukidenshi.com/catalog/g/g106437/) | 1 個 ¥150 | ¥300 |
| 電池ボックス 単3×3 本 スイッチ・XH コネクター付き | 1 | 秋月 [112243](https://akizukidenshi.com/catalog/g/g112243/) | 1 個 ¥130 | ¥130 |
| なべ小ねじ M3×20 | 4 | 秋月 [107437](https://akizukidenshi.com/catalog/g/g107437/)（またはホームセンター） | 10 本 ¥320 | ≒¥128 |
| 六角ナット M3 | 6 | 秋月 [114372](https://akizukidenshi.com/catalog/g/g114372/)（またはホームセンター） | 10 個 ¥120 | ≒¥72 |
| 皿小ねじ M3×8 | 2 | ホームセンター | | ≒¥20 |
| ピニオンギヤ 8T（タミヤ 15289「8T ピニオンギヤ」） | 2 | 模型店・ヨドバシ・Amazon（Amazon.co.jp 販売） | 1 袋 ¥308（4 台分） | ≒¥77 |
| 車軸 真鍮丸棒 φ2 mm × 20 mm（光 HIKARI など） | 2 | ホームセンター | 1 m（約 45 本） | ≒¥15 |
| 3D プリント部品（枠 L / R、デッキ、平歯車 40T ×2、車輪 ×2、ボールキャスター） | 1 式 | P1S で印刷（PLA 約 30 g） | | ≒¥90 |
| TPU タイヤ `tire_tpu.stl` | 2 | P1S で印刷（TPU 95A） | | ≒¥15 |
| モーター用の電線（赤・黒、6 cm × 4 本） | 少し | 秋月・ホームセンター | | ≒¥10 |
| | | | **小計** | **≒¥860**（ねじ・ナットをホームセンターで買えば ≒¥770） |

印刷する STL と設定: [`../../hardware/mechanical/README.md`](../../hardware/mechanical/README.md)（Lite は §5）。

## 3. 合計（1 台、全部新品）

| | 金額 |
|---|---|
| 基板に載る部品 | ≒¥1,912 |
| 基板 | ≒¥80 |
| 機械部品 | ≒¥770〜860 |
| **合計** | **約 ¥2,760〜2,850** |

## 4. 授業 10 台分の注文（秋月でまとめて買う数）

| 品物 | 秋月 | 必要な数 | 注文する数 | 金額 |
|------|------|---------|-----------|------|
| XIAO ESP32C6 | [129481](https://akizukidenshi.com/catalog/g/g129481/) | 10 | 10 | ¥11,000 |
| ピンヘッダー 1×40 | [100167](https://akizukidenshi.com/catalog/g/g100167/) | 140 ピン | 4 本 | ¥140 |
| モータードライバーモジュール | [114746](https://akizukidenshi.com/catalog/g/g114746/) | 10 | 10 | ¥2,000 |
| LBR-127HLD | [104500](https://akizukidenshi.com/catalog/g/g104500/) | 30 | 30 | ¥2,400 |
| 圧電スピーカー | [104118](https://akizukidenshi.com/catalog/g/g104118/) | 10 | 10 | ¥300 |
| 2SC1815 | [117089](https://akizukidenshi.com/catalog/g/g117089/) | 10 | 1 袋（20 個） | ¥100 |
| 1N5819 | [117244](https://akizukidenshi.com/catalog/g/g117244/) | 10 | 1 袋（10 個） | ¥100 |
| 抵抗 100 Ω | [125101](https://akizukidenshi.com/catalog/g/g125101/) | 40 | 1 袋（100 本） | ¥200 |
| 抵抗 10 kΩ | [125103](https://akizukidenshi.com/catalog/g/g125103/) | 30 | 1 袋（100 本） | ¥100 |
| 抵抗 1 kΩ | [125102](https://akizukidenshi.com/catalog/g/g125102/) | 20 | 1 袋（100 本） | ¥100 |
| 470 µF 16 V | [108426](https://akizukidenshi.com/catalog/g/g108426/) | 20 | 20 | ¥200 |
| 0.1 µF | [113582](https://akizukidenshi.com/catalog/g/g113582/) | 20 | 2 袋（10 個入り） | ¥200 |
| フルカラー LED PL9823-F5 | [108411](https://akizukidenshi.com/catalog/g/g108411/) | 60 | 60 | ¥2,400 |
| タクトスイッチ | [108075](https://akizukidenshi.com/catalog/g/g108075/) | 10 | 10 | ¥100 |
| XH ポスト 2P | [112247](https://akizukidenshi.com/catalog/g/g112247/) | 10 | 10 | ¥100 |
| 電池ボックス | [112243](https://akizukidenshi.com/catalog/g/g112243/) | 10 | 10 | ¥1,300 |
| FA-130RA-2270 | [106437](https://akizukidenshi.com/catalog/g/g106437/) | 20 | 20 | ¥3,000 |
| なべ小ねじ M3×20 | [107437](https://akizukidenshi.com/catalog/g/g107437/) | 40 | 4 袋（10 本入り） | ¥1,280 |
| 六角ナット M3 | [114372](https://akizukidenshi.com/catalog/g/g114372/) | 60 | 6 袋（10 個入り） | ¥720 |
| | | | **秋月の合計** | **¥25,740** |

秋月以外: タミヤ 15289 ×3 袋（≒¥924）、真鍮丸棒 φ2 1 m、皿小ねじ M3×8 ×20、電線、PLA（約 300 g）・TPU 95A（約 25 g）、単3 アルカリ電池 ×30、基板（JLCPCB など）。ねじ・ナットはホームセンターのほうが安いことが多い。

- 抵抗・トランジスター・ダイオード・0.1 µF は袋の余りが多いので、次の授業や予備にまわせる。
- 秋月の在庫はリンク先で確かめてから注文する（とくに XIAO、LBR-127HLD、**PL9823-F5 は 60 こ要る**）。
- 前の版（赤 LED 1 こ）からの差: 赤 LED ¥10 と 1 kΩ 1 本をやめ、PL9823 ×6（¥240）を足して **1 台 +¥229**。テストパッド（7 こ）は基板の銅なので部品代は 0。
