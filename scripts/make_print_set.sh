#!/bin/sh
# Lite のロボット 1 台分の 3D プリント部品を、プレート（印刷設定）ごとのフォルダに分けて 1 つの zip にする。
#   ./make_print_set.sh      ->  lite/hardware/Linetracer2-Lite_print_set.zip
# STL は hardware/mechanical/ のもの（linetracer2_mech.scad から書き出したもの）をそのままコピーする。
set -e
cd "$(dirname "$0")/.."
M=hardware/mechanical
OUT=lite/hardware/Linetracer2-Lite_print_set
T=$(mktemp -d)
D="$T/Linetracer2-Lite_print_set"
mkdir -p "$D/1_PLA_0.20mm" "$D/2_PLA_0.08mm_gear" "$D/3_PLA_0.16mm_wheel" "$D/4_PETG_0.12mm_caster" "$D/5_TPU_tire"
cp $M/frame_left.stl $M/frame_right.stl $M/deck.stl "$D/1_PLA_0.20mm/"
cp $M/gear40.stl "$D/2_PLA_0.08mm_gear/"
cp $M/wheel.stl "$D/3_PLA_0.16mm_wheel/"
cp $M/caster_lite_print_h75.stl "$D/4_PETG_0.12mm_caster/"
cp $M/tire_tpu.stl "$D/5_TPU_tire/"
cat > "$D/README_print.txt" <<'TXT'
Linetracer2 Lite（1 台分）3D プリント部品

フォルダごとに別のプレートで印刷します（材料と層の厚さがちがうため）。
STL は書き出したままの向きで、サポートは要りません。数は 1 台分です。

フォルダ                    ファイル            数  材料   層     壁  インフィル  メモ
1_PLA_0.20mm                frame_left.stl      1   PLA    0.20   3   30%         ギヤボックス枠。「L」が左
1_PLA_0.20mm                frame_right.stl     1   PLA    0.20   3   30%         ギヤボックス枠。「R」が右
1_PLA_0.20mm                deck.stl            1   PLA    0.20   3   25%         電池ボックスの台。上下逆さ（電池側がベッド）で書き出し済み
2_PLA_0.08mm_gear           gear40.stl          2   PLA    0.08   4   40%         平歯車 40T。細かい層なので別のプレート。六角の穴の面が下
3_PLA_0.16mm_wheel          wheel.stl           2   PLA    0.16   3   40%         車輪。ハブと車軸（φ3.5）が上
4_PETG_0.12mm_caster        caster_lite_print_h75.stl  1  PETG（PLA も可）  0.12  3  40%  前の支え（玉ごと印刷のボールキャスター）。横倒しで書き出し済み
5_TPU_tire                  tire_tpu.stl        2   TPU 95A  0.20  -   100%        タイヤ。ゆっくり印刷

・合計の数: 枠 2、デッキ 1、平歯車 2、車輪 2、キャスター 1、タイヤ 2（全部で 10 個）
・平歯車の歯は GEAR_BACKLASH 0.15、軸間は 12.1 mm（GEAR_CD_ADD 0.10）の版です。
・印刷のあと: キャスターは玉を指で押して回し、受けから離しておく。車輪と平歯車は
  手で回して引っかかりがないか見る。
・くわしい設定とチェック: hardware/mechanical/README.md、組み立て: lite/docs/assembly.md
TXT
rm -f "$OUT.zip"
(cd "$T" && zip -qr -X - Linetracer2-Lite_print_set) > "$OUT.zip"
rm -rf "$T"
unzip -l "$OUT.zip"
