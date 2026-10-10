# データシート（リンク集）

PDF はメーカー・販売店の著作物なので、リポジトリには入れずにリンクだけ残す（ローカルにダウンロードした PDF は `.gitignore` で除外）。

| 部品 | 資料 | URL |
|------|------|-----|
| TC78H653FTG（東芝） | データシート（日本語） | https://akizukidenshi.com/goodsaffix/TC78H653FTG_datasheet_ja_20190129.pdf |
| AE-TC78H653FTG（秋月モジュール） | 説明書 / 回路図 | https://akizukidenshi.com/goodsaffix/AE-TC78H653FTG_20190730.pdf ／ https://akizukidenshi.com/goodsaffix/AE-TC78H653FTG_schematic_20191127.pdf |
| FA-130RA-2270 | 外形・特性 | https://akizukidenshi.com/goodsaffix/FA-130RA-2270_20190306.pdf |
| LBR-123F | データシート | https://akizukidenshi.com/goodsaffix/lbr-123f.pdf |
| LBR-127HLD（Lite） | データシート | https://akizukidenshi.com/goodsaffix/lbr127hld.pdf |
| Seeed Studio XIAO ESP32C6（Lite） | 解説（ピン配置・電源） | https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/ |
| 同上 | 回路図 / KiCad データ（基板） | https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH_260114.pdf ／ https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32C6/XIAO_ESP32_C6_v1.0_SCH&PCB_260114.zip |
| ESP32-C6（Espressif） | データシート（Table 2-1 にピンの起動時の状態） | https://documentation.espressif.com/esp32-c6_datasheet_en.pdf |
| MicroPython ESP32_GENERIC_C6 | ファームウェア | https://micropython.org/download/ESP32_GENERIC_C6/ |
| 圧電スピーカー PKM13EPYH4000-A0（村田、標準版のオプション・Lite rev.L3） | 秋月の商品ページ（共振 4 kHz、足の間隔 5.0 mm） | https://akizukidenshi.com/catalog/g/g104118/ |
| 電池ボックス BH-331-3ASTH-150MM | 外形図（底の皿穴 φ3.5、30 mm 間隔） | https://akizukidenshi.com/goodsaffix/BH-331-3ASTH-150MM.pdf |
| Raspberry Pi Pico | データシート | https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf |
| CD4051B（TC4051BP と同等） | データシート | https://www.ti.com/lit/ds/symlink/cd4052b.pdf |
| 2SK4017（検討のみ・不採用） | データシート | https://akizukidenshi.com/goodsaffix/2SK4017.pdf |

ダウンロード（任意）:

```bash
cd docs/datasheets
for u in \
  https://akizukidenshi.com/goodsaffix/TC78H653FTG_datasheet_ja_20190129.pdf \
  https://akizukidenshi.com/goodsaffix/AE-TC78H653FTG_20190730.pdf \
  https://akizukidenshi.com/goodsaffix/AE-TC78H653FTG_schematic_20191127.pdf \
  https://akizukidenshi.com/goodsaffix/FA-130RA-2270_20190306.pdf \
  https://akizukidenshi.com/goodsaffix/lbr-123f.pdf \
  https://akizukidenshi.com/goodsaffix/lbr127hld.pdf \
  https://akizukidenshi.com/goodsaffix/BH-331-3ASTH-150MM.pdf ; do curl -sSLO "$u"; done
```
