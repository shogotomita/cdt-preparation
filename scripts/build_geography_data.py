#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build public/data/geography.json from jitsumu past-question explanations.

Heuristic extraction + curated seed facts for dense exam topics
(festivals, onsen, specialties, landmarks).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data" / "questions"
OUT = ROOT / "public" / "data" / "geography.json"

PREFECTURES: list[tuple[str, str, str]] = [
    ("hokkaido", "北海道", "北海道"),
    ("aomori", "青森県", "東北"),
    ("iwate", "岩手県", "東北"),
    ("miyagi", "宮城県", "東北"),
    ("akita", "秋田県", "東北"),
    ("yamagata", "山形県", "東北"),
    ("fukushima", "福島県", "東北"),
    ("ibaraki", "茨城県", "関東"),
    ("tochigi", "栃木県", "関東"),
    ("gunma", "群馬県", "関東"),
    ("saitama", "埼玉県", "関東"),
    ("chiba", "千葉県", "関東"),
    ("tokyo", "東京都", "関東"),
    ("kanagawa", "神奈川県", "関東"),
    ("niigata", "新潟県", "中部"),
    ("toyama", "富山県", "中部"),
    ("ishikawa", "石川県", "中部"),
    ("fukui", "福井県", "中部"),
    ("yamanashi", "山梨県", "中部"),
    ("nagano", "長野県", "中部"),
    ("gifu", "岐阜県", "中部"),
    ("shizuoka", "静岡県", "中部"),
    ("aichi", "愛知県", "中部"),
    ("mie", "三重県", "近畿"),
    ("shiga", "滋賀県", "近畿"),
    ("kyoto", "京都府", "近畿"),
    ("osaka", "大阪府", "近畿"),
    ("hyogo", "兵庫県", "近畿"),
    ("nara", "奈良県", "近畿"),
    ("wakayama", "和歌山県", "近畿"),
    ("tottori", "鳥取県", "中国"),
    ("shimane", "島根県", "中国"),
    ("okayama", "岡山県", "中国"),
    ("hiroshima", "広島県", "中国"),
    ("yamaguchi", "山口県", "中国"),
    ("tokushima", "徳島県", "四国"),
    ("kagawa", "香川県", "四国"),
    ("ehime", "愛媛県", "四国"),
    ("kochi", "高知県", "四国"),
    ("fukuoka", "福岡県", "九州・沖縄"),
    ("saga", "佐賀県", "九州・沖縄"),
    ("nagasaki", "長崎県", "九州・沖縄"),
    ("kumamoto", "熊本県", "九州・沖縄"),
    ("oita", "大分県", "九州・沖縄"),
    ("miyazaki", "宮崎県", "九州・沖縄"),
    ("kagoshima", "鹿児島県", "九州・沖縄"),
    ("okinawa", "沖縄県", "九州・沖縄"),
]

NAME_TO_ID = {name: pid for pid, name, _ in PREFECTURES}
# short name → id
for pid, name, _ in PREFECTURES:
    short = name.replace("県", "").replace("府", "").replace("都", "").replace("道", "")
    NAME_TO_ID[short] = pid
NAME_TO_ID["東京"] = "tokyo"
NAME_TO_ID["大阪"] = "osaka"
NAME_TO_ID["京都"] = "kyoto"

TYPES = ("place", "onsen", "festival", "specialty", "heritage", "park", "course")

TYPE_HINTS = [
    ("onsen", re.compile(r"温泉|湯$|湯の|奥座敷")),
    ("festival", re.compile(r"祭|まつり|くんち|ねぶた|ねぷた|踊り|おどり|曳山|祇園|御柱|花笠|鷺舞|お水送り|お水取り")),
    ("specialty", re.compile(r"焼|漬|そば|鍋|ずし|寿し|うどん|名産|特産|郷土|しもつかれ|しょっつる|千枚漬|出石|大谷焼|ます")),
    ("heritage", re.compile(r"世界遺産|構成資産|グスク|銀山|縄文|登録")),
    ("park", re.compile(r"国立公園|国定公園|ラムサール|湿原")),
    ("course", re.compile(r"コース|→|―")),
]


def guess_type(label: str, note: str = "") -> str:
    text = label + note
    for t, rx in TYPE_HINTS:
        if rx.search(text):
            return t
    return "place"


def normalize_label(s: str) -> str:
    s = s.strip().strip("「」『』・")
    s = re.sub(r"\s+", "", s)
    # Strip quiz choice markers: 「ア.」/「A.」 and glued「エ野付」→「野付」
    # Do not strip bare ア-エ before kana (アドベンチャーワールド).
    s = re.sub(r"^[ア-エA-D][.．]", "", s)
    s = re.sub(r"^[ア-エ](?=[一-龥])", "", s)
    return s


SKIP_LABEL = re.compile(
    r"(営業キロ|加算|運賃|特急|正解|不正解|よって|選択肢|本問|学習|キロ|割引|グリーン|空港)"
)
# Labels that are too fragmented / noisy when auto-extracted.
# Do NOT list full curated place names here (they would be blocked entirely).
BARE_SHORT = {
    "ジブリ",
    "登呂",
    "宇奈月",
    "赤目",
    "丸亀",
    "姫路",
    "三内丸山",
    "彦根",
    "東山",
    "三保",
    "宮之浦岳",
    "安比",
    "作並・五大堂",
    "小田原",
    "奥津",
    "鈍川",
    "杖立",
    "蓮台寺・石廊崎",
    "せんべい汁",
    "釧路",
    "野付",
}


def is_bad_label(label: str) -> bool:
    if len(label) < 2 or len(label) > 28:
        return True
    if SKIP_LABEL.search(label):
        return True
    if label in BARE_SHORT:
        return True
    return False


def dedupe_facts(facts: list[dict]) -> list[dict]:
    # Prefer curated entries as merge hosts so auto labels like「奥津・鷲羽山」
    # do not swallow curated「鷲羽山」.
    facts = sorted(
        facts,
        key=lambda f: (
            0 if "curated" in f.get("sources", []) else 1,
            -len(f["label"]),
            f["label"],
        ),
    )
    kept: list[dict] = []
    for f in facts:
        host = next(
            (
                k
                for k in kept
                if k["type"] == f["type"]
                and k["label"] != f["label"]
                and (
                    k["label"].startswith(f["label"])
                    or f["label"] in k["label"]
                    or k["label"] in f["label"]
                )
            ),
            None,
        )
        if host:
            for h in f["hooks"]:
                if h not in host["hooks"]:
                    host["hooks"].append(h)
            for s in f["sources"]:
                if s not in host["sources"]:
                    host["sources"].append(s)
            continue
        kept.append(f)
    return kept


# Curated high-value facts: (pref_id, type, label, hooks)
CURATED: list[tuple[str, str, str, list[str]]] = [
    # 北海道
    ("hokkaido", "place", "羊ヶ丘展望台", ["クラーク像", "少年よ大志を抱け", "札幌"]),
    ("hokkaido", "place", "積丹半島・神威岬", ["積丹ブルー"]),
    ("hokkaido", "place", "定山渓", ["札幌の奥座敷", "豊平川"]),
    ("hokkaido", "place", "オシンコシンの滝", ["知床", "双美の滝"]),
    ("hokkaido", "place", "野付半島", ["道東"]),
    ("hokkaido", "onsen", "登別温泉", ["洞爺・大沼コース"]),
    ("hokkaido", "park", "釧路湿原", ["ラムサール第1号", "タンチョウ"]),
    ("hokkaido", "course", "函館―大沼―洞爺／昭和新山―支笏―新千歳", ["道南〜道央コース"]),
    # 東北
    ("aomori", "place", "白神山地", ["自然遺産", "青森＋秋田", "岩手は含まない"]),
    ("aomori", "place", "三内丸山遺跡", ["縄文遺跡群", "青森市"]),
    ("aomori", "place", "弘前城", ["ねぷた", "桜"]),
    ("aomori", "festival", "ねぶた／ねぷた", ["青森市はねぶた", "弘前はねぷた"]),
    ("aomori", "place", "奥入瀬渓流", ["十和田湖の排水河川"]),
    ("aomori", "place", "発荷峠", ["十和田湖南の玄関", "八甲田展望"]),
    ("iwate", "place", "龍泉洞", ["三陸", "秋芳洞と混同注意"]),
    ("iwate", "place", "碁石海岸", ["しょっつる鍋（秋田）と県違いひっかけ"]),
    ("miyagi", "place", "伊豆沼・内沼", ["ラムサール", "ハス・ガンカモ", "豊岡のコウノトリと混同注意"]),
    ("miyagi", "place", "松島", ["日本三景", "瑞巌寺"]),
    ("akita", "specialty", "しょっつる鍋", ["秋田", "岩手名所とクロス注意"]),
    ("akita", "place", "田沢湖", ["十和田八幡平国立公園外がひっかけ"]),
    ("akita", "place", "角館", ["盛岡―田沢湖コース"]),
    ("yamagata", "festival", "花笠まつり", ["銀山温泉とセット"]),
    ("yamagata", "onsen", "銀山温泉", ["花笠まつりとセット"]),
    ("fukushima", "park", "尾瀬", ["福島・栃木・群馬・新潟", "釧路湿原と第1号混同注意"]),
    # 関東
    ("ibaraki", "place", "偕楽園", ["日本三名園", "好文亭", "水戸"]),
    ("ibaraki", "place", "弘道館", ["水戸"]),
    ("ibaraki", "place", "袋田の滝", ["県北", "花貫渓谷とセット", "水戸周遊コース"]),
    ("ibaraki", "place", "花貫渓谷", ["県北", "袋田の滝とセット", "水戸周遊コース"]),
    ("tochigi", "specialty", "しもつかれ", ["東尋坊（福井）とクロスひっかけ"]),
    ("gunma", "place", "吹割の滝", ["東洋のナイアガラ"]),
    ("gunma", "place", "茂林寺", ["ぶんぶく茶釜", "館林"]),
    ("saitama", "place", "長瀞", ["岩畳", "寳登山神社", "秩父"]),
    ("chiba", "place", "九十九里", ["鴨川シーワールドとセット"]),
    ("chiba", "place", "鴨川シーワールド", ["九十九里とセット"]),
    ("kanagawa", "place", "猿島", ["横須賀", "東京湾", "旧軍施設", "利島・初島・八景島と混同注意"]),
    ("kanagawa", "place", "箱根・芦ノ湖", ["富士箱根伊豆国立公園"]),
    # 中部
    ("niigata", "heritage", "佐渡島の金山", ["2024登録", "西三川", "北沢浮遊選鉱場は構成外のひっかけ"]),
    ("toyama", "onsen", "宇奈月温泉", ["お水送り（福井）とクロス注意"]),
    ("toyama", "place", "きときと空港", ["富山空港", "方言で新鮮", "ます寿しと同県", "新潟と混同注意"]),
    ("toyama", "specialty", "ます寿し", ["きときと空港と同県", "鮒ずし（滋賀）・へぎそば（新潟）と混同注意"]),
    ("ishikawa", "place", "兼六園", ["日本三名園"]),
    ("ishikawa", "place", "那谷寺", ["加賀", "白山信仰", "遊仙境", "奥の細道"]),
    ("ishikawa", "place", "九十九湾", ["能登", "蓬莱島", "英虞湾と混同注意"]),
    ("fukui", "festival", "お水送り", ["小浜", "お水取り（奈良）と混同注意", "あわら温泉とセット"]),
    ("fukui", "onsen", "あわら温泉", ["お水送りとセット"]),
    ("fukui", "place", "東尋坊", ["しもつかれ（栃木）とクロス注意"]),
    ("fukui", "place", "霞ヶ城", ["丸岡城", "千鳥城・鯉城と混同注意"]),
    ("yamanashi", "place", "恵林寺", ["武田信玄", "善光寺（長野）と混同注意"]),
    ("yamanashi", "place", "身延山久遠寺", ["日蓮宗総本山", "善光寺（長野）と混同注意"]),
    ("yamanashi", "place", "昇仙峡", ["富士箱根伊豆国立公園外のひっかけ"]),
    ("nagano", "place", "善光寺", ["びんずる", "御開帳"]),
    ("nagano", "festival", "御柱祭", ["諏訪", "松本城と同県"]),
    ("nagano", "place", "松本城", ["北アルプス借景", "御柱とセット"]),
    ("nagano", "place", "妻籠宿", ["重要伝統的建造物群", "長野・中山道", "馬籠（岐阜）と隣接・県違い", "御柱と同県設問"]),
    ("nagano", "onsen", "浅間温泉", ["鹿教湯・湯田中とセット"]),
    ("nagano", "onsen", "鹿教湯温泉", ["浅間・湯田中とセット"]),
    ("nagano", "onsen", "湯田中温泉", ["浅間・鹿教湯とセット"]),
    ("nagano", "course", "善光寺―飯綱―戸隠―妙高", ["長野北郊"]),
    ("gifu", "festival", "郡上おどり", ["御柱（長野）と隣接県ひっかけ"]),
    ("aichi", "place", "白帝城", ["犬山城", "国宝天守", "木曽川", "愛知県犬山市（岐阜との境界付近）"]),
    ("shizuoka", "place", "三保松原", ["世界遺産構成", "久能山東照宮コース"]),
    ("shizuoka", "place", "登呂遺跡", ["弥生水田", "岩宿と対比"]),
    ("shizuoka", "course", "静岡―三保―久能山―三島SW―熱海", []),
    ("hokkaido", "place", "屈斜路湖", ["国内最大カルデラ湖", "御神渡り", "白鳥"]),
    ("hokkaido", "place", "支笏湖", ["深度国内2位", "チップ料理", "田沢湖と深度対比"]),
    ("hokkaido", "specialty", "三平汁", ["北海道の郷土料理", "ます寿しと混同注意"]),
    ("aomori", "specialty", "せんべい汁", ["川越（埼玉）とクロスひっかけ"]),
    ("aomori", "specialty", "いちご煮", ["八戸", "ウニとアワビ", "宮城と混同注意"]),
    ("iwate", "onsen", "つなぎ温泉", ["猊鼻渓と同県", "盛岡周辺"]),
    ("iwate", "place", "猊鼻渓", ["一関", "つなぎ温泉と同県"]),
    ("miyagi", "place", "蔵王", ["御釜など"]),
    ("miyagi", "place", "金華山", ["石巻・牡鹿半島沖", "稲庭うどん（秋田）とクロスひっかけ", "山形と混同注意"]),
    ("fukushima", "place", "大内宿", ["会津", "鶴ヶ城コース"]),
    ("fukushima", "onsen", "東山温泉", ["会津若松", "大内宿・鶴ヶ城と同県", "福井と混同注意"]),
    ("ibaraki", "specialty", "あんこう鍋", ["潮来と同県セット"]),
    ("tochigi", "place", "足利学校", ["渋沢栄一記念館（埼玉）とクロスひっかけ"]),
    ("tochigi", "course", "湯西川温泉―霧降高原―輪王寺", ["日光・鬼怒川エリア"]),
    ("tochigi", "place", "いろは坂", ["日光東照宮と中禅寺湖を結ぶ"]),
    ("saitama", "place", "川越", ["せんべい汁（青森）とクロスひっかけ"]),
    ("saitama", "place", "渋沢栄一記念館", ["深谷", "足利学校（栃木）とクロス"]),
    ("saitama", "place", "三峯神社", ["秩父", "狼信仰", "雲取山"]),
    ("saitama", "place", "鉄道博物館", ["さいたま市", "大宮"]),
    ("chiba", "place", "東京ディズニーリゾート", ["浦安", "TDL・TDS"]),
    ("chiba", "place", "鋸山", ["富津", "日本寺大仏", "房総"]),
    ("kochi", "place", "龍河洞", ["鍾乳洞", "桂浜とセット"]),
    ("kanagawa", "place", "鶴岡八幡宮", ["鎌倉", "源頼朝", "若宮大路"]),
    ("niigata", "place", "村上市", ["鮭", "瀬波温泉", "笹川流れ"]),
    ("niigata", "place", "笹川流れ", ["北海岸", "瀬波の後"]),
    ("ishikawa", "onsen", "和倉温泉", ["七尾", "花嫁のれん"]),
    ("yamanashi", "place", "忍野八海", ["河口湖・富士北麓コース"]),
    ("gifu", "place", "養老", ["白浜・道成寺（和歌山）とクロスひっかけ"]),
    ("gifu", "place", "郡上八幡", ["郡上おどり"]),
    ("gifu", "place", "馬籠宿", ["中山道", "岐阜", "妻籠（長野）と隣接・県違い"]),
    ("shizuoka", "place", "三嶋大社", ["伊豆一の宮", "蒔絵手箱", "総けやき本殿"]),
    ("shizuoka", "place", "登呂遺跡", ["弥生水田", "岩宿と対比"]),
    ("aichi", "place", "ジブリパーク", ["赤目四十八滝（三重）とクロス注意"]),
    ("aichi", "place", "熱田神宮", ["名古屋", "草薙剣"]),
    ("mie", "place", "赤目四十八滝", ["ジブリパーク（愛知）とクロス注意"]),
    ("mie", "place", "英虞湾", ["志摩", "リアス", "九十九湾と混同注意"]),
    ("mie", "place", "伊勢神宮", ["内宮・外宮", "お伊勢参り"]),
    ("osaka", "place", "大阪城", ["豊臣・徳川", "大阪城公園"]),
    ("osaka", "place", "通天閣", ["新世界", "ビリケン"]),
    ("kochi", "place", "桂浜", ["坂本龍馬像", "高知市"]),
    ("kochi", "place", "四万十川", ["清流", "沈下橋"]),
    ("yamagata", "place", "山寺（立石寺）", ["芭蕉", "奥の細道"]),
    ("fukushima", "place", "鶴ヶ城", ["会津若松城", "大内宿コース"]),
    ("miyagi", "place", "青葉城", ["仙台城", "千鳥城・霞ヶ城と混同注意"]),
    ("chiba", "place", "成田山新勝寺", ["成田", "門前町"]),
    ("tokyo", "place", "浅草寺", ["雷門", "仲見世"]),
    ("kanagawa", "place", "江の島", ["湘南", "弁財天"]),
    ("toyama", "place", "立山", ["黒部ダム・室堂コース"]),
    ("nara", "place", "東大寺", ["大仏", "お水取り"]),
    ("tottori", "place", "鳥取砂丘", ["山陰海岸", "らくだ"]),
    ("miyazaki", "place", "青島", ["神話", "鬼の洗濯板"]),
    ("kyoto", "place", "天龍寺", ["嵐山", "保津川下り終点付近", "古都京都構成資産"]),
    ("kyoto", "onsen", "湯の花温泉", ["亀岡", "但馬・兵庫と混同注意"]),
    ("kyoto", "place", "鞍馬寺", ["牛若丸", "毘沙門天", "貴船とセット"]),
    ("kyoto", "place", "貴船神社", ["貴船", "鞍馬とセット"]),
    ("wakayama", "place", "那智の滝", ["熊野那智大社", "紀伊山地の霊場と参詣道"]),
    ("wakayama", "place", "橋杭岩", ["串本", "紀南海岸"]),
    ("wakayama", "place", "白浜", ["アドベンチャーワールドと同県", "道成寺とセット", "養老（岐阜）とクロス注意"]),
    ("wakayama", "place", "道成寺", ["白浜とセット", "養老（岐阜）とクロス注意"]),
    ("shimane", "onsen", "温泉津温泉", ["石見銀山関連の港町", "出雲大社と同県"]),
    ("okayama", "festival", "西大寺会陽", ["桃太郎空港と同県", "岡山の代表行事"]),
    ("okayama", "place", "鷲羽山", ["瀬戸大橋", "倉敷〜香川ルート"]),
    ("hiroshima", "onsen", "湯来温泉", ["縮景園・鞆の浦と同県"]),
    ("hiroshima", "place", "縮景園", ["湯来温泉・鞆の浦と同県"]),
    ("hiroshima", "place", "鞆の浦", ["湯来温泉・縮景園と同県"]),
    ("tokushima", "place", "大歩危・小歩危", ["阿波おどり空港と同県", "景勝"]),
    ("tokushima", "place", "大塚国際美術館", ["鳴門", "陶板名画"]),
    ("ehime", "specialty", "砥部焼", ["内子座と同県"]),
    ("ehime", "place", "内子座", ["砥部焼と同県"]),
    ("ehime", "place", "天赦園", ["宇和島", "島根・松江と混同注意"]),
    ("fukuoka", "festival", "玉取祭（玉せせり）", ["筥崎宮（福岡市東区）", "柳川と同県"]),
    ("fukuoka", "place", "太宰府天満宮", ["北九州〜柳川コース"]),
    ("fukuoka", "place", "柳川", ["北原白秋", "太宰府と同県コース"]),
    ("nagasaki", "place", "西海橋", ["針尾瀬戸", "佐世保〜西彼杵", "重要文化財"]),
    ("nagasaki", "place", "雲仙", ["仁田峠", "島原", "発荷峠と展望ひっかけ"]),
    ("nagasaki", "onsen", "小浜温泉", ["雲仙周辺", "鉄輪・別府（大分）と混同注意"]),
    ("nagasaki", "heritage", "大浦天主堂", ["長崎市南山手", "潜伏キリシタン遺産", "五島と混同注意"]),
    ("nagasaki", "heritage", "原城跡", ["長崎・南島原", "島原の乱", "天草＝熊本と混同注意"]),
    ("kumamoto", "place", "大江天主堂", ["天草", "原城・雲仙コース"]),
    ("oita", "place", "城島高原", ["別府周辺", "誤肢になりやすい"]),
    ("miyazaki", "place", "西都原", ["古墳群"]),
    ("miyazaki", "place", "高千穂", ["通潤橋ルート", "神話・峡谷"]),
    ("kagoshima", "place", "吹上浜", ["南さつま", "砂丘", "砂の祭典"]),
    ("okinawa", "place", "川平湾", ["石垣島", "ヤエヤマヤシ群落コース"]),
    ("shiga", "place", "竹生島", ["宝厳寺・弁才天", "嫁ヶ島との混同注意"]),
    # 近畿
    ("shiga", "place", "彦根城", ["琵琶湖八景", "鮒ずし"]),
    ("shiga", "specialty", "鮒ずし", ["彦根", "ます寿しと混同注意"]),
    ("shiga", "course", "米原―彦根―百済寺―近江八幡―大津", ["湖東"]),
    ("kyoto", "specialty", "千枚漬", ["保津峡・嵐山エリアと同県"]),
    ("kyoto", "place", "保津峡", ["トロッコ", "保津川下り", "千枚漬"]),
    ("kyoto", "heritage", "古都京都の文化財", ["京都・宇治・大津", "延暦寺は滋賀だが構成"]),
    ("osaka", "place", "天王寺", ["USJと同府"]),
    ("osaka", "place", "USJ", ["天王寺と同府"]),
    ("hyogo", "place", "白鷺城", ["姫路城", "世界遺産", "出石焼"]),
    ("hyogo", "specialty", "出石焼", ["豊岡・出石", "姫路と同県"]),
    ("hyogo", "onsen", "有馬温泉", ["淡路・竹田城とセット"]),
    ("hyogo", "place", "淡路島", ["花さじき", "大鳴門・明石海峡"]),
    ("hyogo", "place", "竹田城", ["但馬", "有馬・淡路とセット"]),
    ("hyogo", "place", "玄武洞", ["島根と混同注意"]),
    ("nara", "festival", "お水取り", ["東大寺", "お水送り（福井）と混同注意"]),
    ("nara", "course", "興福寺―東大寺―若草山―春日大社", []),
    ("wakayama", "place", "潮岬", ["アドベンチャーワールドとセット"]),
    # 中国
    ("tottori", "onsen", "三朝温泉", ["三朝町・三徳山", "鷺舞（島根）とクロス注意", "皆生・岩井も鳥取", "東郷湖周辺ではない"]),
    ("tottori", "onsen", "皆生温泉", ["米子の奥座敷", "弓ヶ浜・美保湾"]),
    ("tottori", "place", "弓ヶ浜", ["米子", "美保湾", "香川・琴平と混同注意"]),
    ("tottori", "place", "鍵掛峠", ["江府町・大山町", "鳥取県内", "岡山県境ではない", "発荷峠と混同注意"]),
    ("shimane", "place", "千鳥城", ["松江城", "宍道湖", "鯉城・霞ヶ城と混同注意"]),
    ("shimane", "heritage", "石見銀山", ["2007", "玉造温泉は構成外"]),
    ("shimane", "place", "足立美術館", ["出雲―宍道湖―皆生コース"]),
    ("shimane", "place", "隠岐", ["島後＋島前", "国賀海岸・ローソク島"]),
    ("okayama", "place", "後楽園", ["日本三名園"]),
    ("okayama", "onsen", "湯郷温泉", ["皆生（鳥取）と混同注意"]),
    ("hiroshima", "place", "宮島（厳島）", ["ラムサール", "ミヤジマトンボ", "宍道湖説明の混入ひっかけ"]),
    ("hiroshima", "place", "鯉城", ["広島城", "千鳥城と混同注意"]),
    ("shimane", "festival", "鷺舞", ["津和野", "三朝温泉（鳥取）とクロス注意"]),
    ("yamaguchi", "place", "赤間神宮", ["下関", "安徳天皇", "福岡・門司と混同注意"]),
    ("yamaguchi", "place", "秋芳洞", ["龍泉洞と混同注意"]),
    ("yamaguchi", "course", "新山口―防府天満宮―錦帯橋―宮島―広島", []),
    # 四国
    ("tokushima", "place", "脇町（うだつの町並み）", ["藍商人", "祖谷そばと同県設問"]),
    ("tokushima", "specialty", "祖谷そば", ["脇町と同県"]),
    ("tokushima", "specialty", "大谷焼", ["阿波おどりとセット"]),
    ("tokushima", "festival", "阿波おどり", ["大谷焼とセット"]),
    ("kagawa", "place", "金刀比羅宮", ["こんぴらさん", "石段", "うどん"]),
    ("kagawa", "place", "金丸座", ["旧金毘羅大芝居", "琴平", "高知と混同注意"]),
    ("kagawa", "place", "丸亀城", ["扇の勾配", "寒霞渓と同県"]),
    ("kagawa", "place", "寒霞渓", ["小豆島", "丸亀城と同県"]),
    ("ehime", "course", "松山―子規堂―琴弾公園―金刀比羅―高松", ["香川への接続"]),
    ("ehime", "place", "石鎚山", ["西日本最高峰", "愛媛", "修験", "宮之浦岳と対比"]),
    # 九州・沖縄
    ("fukuoka", "onsen", "原鶴温泉", ["日田（大分）と同県ひっかけ注意"]),
    ("saga", "festival", "唐津くんち", ["武雄温泉とセット"]),
    ("saga", "onsen", "武雄温泉", ["唐津くんちとセット"]),
    ("saga", "onsen", "嬉野温泉", ["吉野ヶ里・祐徳稲荷とセット"]),
    ("saga", "place", "吉野ヶ里", ["嬉野・祐徳稲荷とセット"]),
    ("saga", "place", "祐徳稲荷", ["嬉野・吉野ヶ里とセット"]),
    ("nagasaki", "place", "雲仙", ["発荷峠（十和田）と展望ひっかけ", "島原半島"]),
    ("kumamoto", "place", "通潤橋", ["放水", "国宝", "高千穂ルート"]),
    ("kumamoto", "park", "阿蘇くじゅう国立公園", ["カルデラ", "菊池渓谷", "内牧温泉"]),
    ("oita", "place", "日田", ["天領", "日田祇園", "鉄輪温泉と同県"]),
    ("oita", "onsen", "鉄輪温泉", ["別府", "日田と同県"]),
    ("oita", "festival", "日田祇園の曳山行事", ["日田"]),
    ("miyazaki", "place", "高千穂", ["通潤橋ルート", "神話・峡谷"]),
    ("kagoshima", "onsen", "指宿温泉", ["与論・霧島神宮とセット"]),
    ("kagoshima", "place", "与論島", ["指宿・霧島とセット"]),
    ("kagoshima", "place", "霧島神宮", ["指宿・与論とセット"]),
    ("kagoshima", "place", "屋久島・宮之浦岳", ["自然遺産", "石鎚（愛媛）と対比"]),
    ("okinawa", "place", "糸満", ["ひめゆり", "平和祈念公園", "沖縄本島最南端"]),
    ("okinawa", "heritage", "琉球王国のグスク及び関連遺産群", ["首里・今帰仁・座喜味・中城・玉陵・識名園など", "宮良殿内は含まない"]),
    ("okinawa", "course", "那覇―識名園―座喜味―万座毛―本部", ["南→北"]),
    # 有名観光地の補完（試験・定番）
    ("hokkaido", "heritage", "知床", ["自然遺産", "羅臼岳", "流氷", "オシンコシンの滝と同エリア"]),
    ("hokkaido", "place", "函館", ["五稜郭", "夜景", "函館山"]),
    ("hokkaido", "place", "洞爺湖", ["有珠山", "昭和新山", "洞爺湖温泉"]),
    ("hokkaido", "place", "富良野", ["ラベンダー", "美瑛とセット"]),
    ("iwate", "heritage", "中尊寺", ["平泉", "文化遺産", "金色堂", "毛越寺とセット"]),
    ("iwate", "place", "浄土ヶ浜", ["宮古", "三陸"]),
    ("akita", "place", "男鹿半島", ["なまはげ", "入道崎"]),
    ("akita", "specialty", "稲庭うどん", ["干うどん", "金華山クロス注意"]),
    ("yamagata", "place", "出羽三山", ["羽黒・月山・湯殿", "修験"]),
    ("yamagata", "place", "蔵王（山形）", ["樹氷", "宮城側と跨ぎ"]),
    ("fukushima", "place", "猪苗代湖", ["磐梯山", "裏磐梯", "五色沼"]),
    ("tochigi", "place", "日光東照宮", ["陽明門", "三猿", "輪王寺・二荒山とセット"]),
    ("tochigi", "place", "華厳の滝", ["中禅寺湖", "いろは坂の先"]),
    ("tochigi", "onsen", "鬼怒川温泉", ["日光・霧降とセット"]),
    ("gunma", "onsen", "草津温泉", ["湯畑", "西の字湯もみ", "四万・伊香保と混同注意"]),
    ("gunma", "heritage", "富岡製糸場", ["世界遺産", "官営模範工場"]),
    ("gunma", "onsen", "伊香保温泉", ["石段街", "草津と混同注意"]),
    ("tokyo", "place", "明治神宮", ["代々木", "明治天皇"]),
    ("tokyo", "place", "東京スカイツリー", ["墨田", "高さ634m"]),
    ("tokyo", "place", "皇居", ["江戸城跡", "二重橋"]),
    ("kanagawa", "place", "鎌倉大仏", ["高徳院", "鶴岡八幡宮とセット"]),
    ("kanagawa", "place", "横浜中華街", ["山下公園", "みなとみらい"]),
    ("niigata", "specialty", "へぎそば", ["十日町など", "ます寿しと混同注意"]),
    ("niigata", "place", "清津峡", ["柱状節理", "トンネル歩道"]),
    ("toyama", "place", "黒部ダム", ["立山黒部アルペンルート", "室堂"]),
    ("toyama", "heritage", "五箇山", ["合掌造り", "白川郷と同遺産・県違い"]),
    ("ishikawa", "place", "ひがし茶屋街", ["金沢", "兼六園とセット"]),
    ("fukui", "place", "永平寺", ["曹洞宗大本山", "福井市近郊"]),
    ("fukui", "place", "一乗谷朝倉氏遺跡", ["戦国大名の城下", "永平寺とセット"]),
    ("yamanashi", "place", "河口湖", ["富士五湖", "忍野八海コース"]),
    ("yamanashi", "place", "富士山（山梨側）", ["北口本宮富士浅間神社", "静岡側と跨ぎ"]),
    ("nagano", "place", "上高地", ["河童橋", "梓川", "穂高"]),
    ("nagano", "place", "軽井沢", ["旧軽井沢銀座", "碓氷峠付近"]),
    ("gifu", "heritage", "白川郷", ["合掌造り", "五箇山と同遺産・県違い"]),
    ("gifu", "place", "高山", ["古い町並み", "飛騨", "朝市"]),
    ("gifu", "onsen", "下呂温泉", ["日本三名泉", "飛騨"]),
    ("shizuoka", "onsen", "熱海温泉", ["伊豆東海岸", "来宮神社"]),
    ("shizuoka", "place", "久能山東照宮", ["石段", "三保松原コース"]),
    ("shizuoka", "place", "浜名湖", ["うなぎ", "舘山寺"]),
    ("aichi", "place", "名古屋城", ["金鯱", "熱田とセット"]),
    ("aichi", "place", "岡崎", ["家康生誕地", "大樹寺"]),
    ("mie", "place", "鳥羽", ["真珠", "ミキモト", "志摩とセット"]),
    ("mie", "place", "志摩", ["英虞湾", "伊勢志摩国立公園"]),
    ("mie", "place", "熊野古道（伊勢路）", ["馬越峠など", "和歌山・奈良と跨ぎ"]),
    ("shiga", "place", "琵琶湖", ["日本最大の湖", "竹生島・彦根"]),
    ("kyoto", "place", "清水寺", ["音羽の滝", "清水の舞台", "古都京都構成"]),
    ("kyoto", "place", "金閣寺", ["鹿苑寺", "舎利殿", "古都京都構成"]),
    ("kyoto", "place", "伏見稲荷大社", ["千本鳥居", "稲荷山"]),
    ("kyoto", "place", "平等院", ["宇治", "鳳凰堂", "古都京都構成"]),
    ("kyoto", "place", "天橋立", ["日本三景", "宮津", "松島・宮島とセット"]),
    ("osaka", "place", "道頓堀", ["グリコ看板", "くいだおれ"]),
    ("hyogo", "place", "神戸", ["異人館", "南京町", "ハーバーランド"]),
    ("hyogo", "onsen", "城崎温泉", ["外湯めぐり", "但馬", "有馬と混同注意"]),
    ("nara", "heritage", "法隆寺", ["世界最古の木造建築", "斑鳩", "東大寺と混同注意"]),
    ("nara", "place", "春日大社", ["万灯籠", "奈良公園", "東大寺とセット"]),
    ("nara", "place", "吉野山", ["千本桜", "金峯山寺", "世界遺産構成"]),
    ("wakayama", "place", "高野山", ["金剛峯寺", "奥の院", "紀伊山地の霊場"]),
    ("wakayama", "place", "熊野本宮大社", ["大斎原", "中辺路", "那智とセット"]),
    ("wakayama", "place", "アドベンチャーワールド", ["白浜", "パンダ", "潮岬とセット"]),
    ("tottori", "place", "大山", ["伯耆富士", "鍵掛峠から望む"]),
    ("shimane", "place", "出雲大社", ["縁結び", "神在月", "玉造・宍道湖コース"]),
    ("shimane", "place", "宍道湖", ["夕日", "シジミ", "千鳥城から望む"]),
    ("okayama", "place", "倉敷美観地区", ["白壁", "大原美術館", "鷲羽山コース"]),
    ("hiroshima", "heritage", "原爆ドーム", ["世界遺産", "平和記念公園", "宮島とセット"]),
    ("yamaguchi", "place", "錦帯橋", ["岩国", "木造五連アーチ", "防府天満宮コース"]),
    ("yamaguchi", "place", "防府天満宮", ["日本三天神", "錦帯橋とセット"]),
    ("tokushima", "place", "鳴門の渦潮", ["大鳴門橋", "観潮船", "兵庫・淡路と対岸"]),
    ("tokushima", "place", "祖谷渓", ["かずら橋", "祖谷そばと同県"]),
    ("kagawa", "specialty", "讃岐うどん", ["金刀比羅とセット"]),
    ("ehime", "onsen", "道後温泉", ["本館", "神の湯", "松山", "別府と混同注意"]),
    ("ehime", "place", "松山城", ["現存天守", "道後とセット"]),
    ("kochi", "place", "室戸岬", ["弘法大師", "足摺と対比"]),
    ("kochi", "place", "足摺岬", ["ジョン万次郎", "太平洋"]),
    ("fukuoka", "place", "門司港レトロ", ["関門海峡", "下関と対岸"]),
    ("fukuoka", "place", "博多", ["中洲", "キャナルシティ", "太宰府コース"]),
    ("nagasaki", "place", "ハウステンボス", ["佐世保", "西海橋エリア"]),
    ("nagasaki", "heritage", "軍艦島", ["端島", "世界遺産構成", "炭鉱"]),
    ("kumamoto", "place", "熊本城", ["武者返し", "加藤清正"]),
    ("kumamoto", "place", "阿蘇山", ["カルデラ", "草千里", "くじゅうとセット"]),
    ("oita", "onsen", "別府温泉", ["地獄めぐり", "鉄輪・明礬", "由布院とセット"]),
    ("oita", "onsen", "由布院温泉", ["湯の坪街道", "別府と混同注意"]),
    ("miyazaki", "place", "鵜戸神宮", ["日南海岸", "おがま岩"]),
    ("miyazaki", "place", "日南海岸", ["青島・鵜戸", "フェニックス"]),
    ("kagoshima", "place", "桜島", ["活火山", "垂水・鹿児島港"]),
    ("kagoshima", "place", "仙巌園", ["磯庭園", "桜島展望"]),
    ("okinawa", "place", "首里城", ["正殿", "守礼門", "グスク遺産構成"]),
    ("okinawa", "place", "美ら海水族館", ["本部", "ジンベエザメ", "万座毛とセット"]),
    ("okinawa", "place", "万座毛", ["象の鼻", "本部・名護"]),
    # 公園・遺産（跨ぎ）
    ("aomori", "park", "十和田八幡平国立公園", ["青森・秋田・岩手", "田沢湖は外"]),
    ("ishikawa", "park", "白山国立公園", ["御前峰", "お池巡り", "禅定道", "4県"]),
    ("tokyo", "park", "秩父多摩甲斐国立公園", ["西沢渓谷", "大菩薩", "三峯", "浅間は上信越"]),
    ("gunma", "park", "上信越高原国立公園", ["浅間山"]),
    # 城・寺社・遺産の網羅補完
    ("okayama", "place", "備中松山城", ["現存12天守", "山城", "松山城（愛媛）と混同注意"]),
    ("ehime", "place", "宇和島城", ["現存12天守", "天赦園と同市", "伊達"]),
    ("kochi", "place", "高知城", ["現存12天守", "本丸御殿現存", "桂浜・龍河洞と同県"]),
    ("okayama", "place", "烏城", ["岡山城", "後楽園とセット", "烏城公園"]),
    ("hokkaido", "place", "五稜郭", ["函館", "星形堡塁", "箱館戦争"]),
    ("ishikawa", "place", "金沢城", ["兼六園とセット", "菱櫓", "加賀藩"]),
    ("shiga", "place", "延暦寺", ["比叡山", "天台宗総本山", "古都京都構成だが滋賀", "京都市内と県違いひっかけ"]),
    ("nara", "place", "興福寺", ["五重塔", "阿修羅", "古都奈良", "東大寺・春日とセット"]),
    ("nara", "place", "薬師寺", ["東塔", "白鳳伽藍", "西ノ京", "興福・東大と混同注意"]),
    ("kyoto", "place", "銀閣寺", ["慈照寺", "東山文化", "金閣と対比", "古都京都構成"]),
    ("kyoto", "place", "二条城", ["徳川", "大政奉還", "古都京都構成", "世界遺産"]),
    ("hiroshima", "heritage", "厳島神社", ["世界遺産", "海上社殿", "平清盛", "宮島（厳島）とセット"]),
    ("iwate", "place", "毛越寺", ["平泉", "浄土庭園", "中尊寺とセット", "文化遺産構成"]),
    ("oita", "place", "宇佐神宮", ["八幡総本宮", "国宝本殿", "太宰府と混同注意"]),
    ("tochigi", "place", "輪王寺", ["日光三社寺", "東照宮・二荒山とセット"]),
    ("tochigi", "place", "日光二荒山神社", ["男体山", "日光三社寺", "東照宮・輪王寺とセット"]),
    ("wakayama", "place", "熊野那智大社", ["那智の滝とセット", "青岸渡寺", "紀伊山地の霊場"]),
    ("fukuoka", "heritage", "宗像・沖ノ島と関連遺産群", ["神宿る島", "沖ノ島", "宗像大社", "2017登録", "女人禁制"]),
    ("tokyo", "heritage", "小笠原諸島", ["自然遺産", "父島・母島", "固有種", "東京だが本土外"]),
    ("osaka", "heritage", "百舌鳥・古市古墳群", ["仁徳天皇陵など", "堺・羽曳野・藤井寺", "2019登録"]),
    ("tokyo", "heritage", "国立西洋美術館", ["ル・コルビュジエ作品群", "上野", "世界遺産構成"]),
    (
        "kagoshima",
        "heritage",
        "奄美大島、徳之島、沖縄島北部及び西表島",
        ["自然遺産", "2021登録", "やんばる・西表", "屋久島・知床と区別", "鹿児島＋沖縄"],
    ),
    (
        "iwate",
        "heritage",
        "平泉—仏国土（浄土）を表す建築・庭園及び考古学的遺跡群",
        ["中尊寺・毛越寺・無量光院跡", "文化遺産", "2011登録"],
    ),
    ("nara", "heritage", "古都奈良の文化財", ["東大寺・興福寺・春日大社・薬師寺など", "法隆寺は別遺産"]),
    ("tochigi", "heritage", "日光の社寺", ["東照宮・輪王寺・二荒山神社", "文化遺産"]),
    ("wakayama", "heritage", "紀伊山地の霊場と参詣道", ["熊野・高野・吉野", "和歌山・奈良・三重", "参詣道"]),
    (
        "yamanashi",
        "heritage",
        "富士山—信仰の対象と芸術の源泉",
        ["山梨・静岡", "三保松原は構成資産", "浅間神社"],
    ),
    # 空港愛称（令和3実務の出題セット）
    ("hokkaido", "place", "たんちょう空港", ["釧路空港", "タンチョウ", "釧路湿原と同県"]),
    ("shimane", "place", "縁結び空港", ["出雲空港", "出雲大社", "石見銀山と同県"]),
    ("okayama", "place", "桃太郎空港", ["岡山空港", "西大寺会陽と同県"]),
    ("tokushima", "place", "阿波おどり空港", ["徳島空港", "阿波おどり", "大歩危・小歩危と同県"]),
    # 焼物（過去問ひっかけ＋六古窯・定番産地）
    ("tochigi", "specialty", "益子焼", ["栃木", "笠間と対比", "出石焼と混同注意"]),
    ("ibaraki", "specialty", "笠間焼", ["茨城", "益子と対比"]),
    ("ishikawa", "specialty", "九谷焼", ["石川・加賀", "色絵", "出石焼と混同注意"]),
    ("gifu", "specialty", "美濃焼", ["多治見など", "六古窯"]),
    ("aichi", "specialty", "常滑焼", ["六古窯", "急須", "三重と混同注意"]),
    ("aichi", "specialty", "瀬戸焼", ["六古窯", "瀬戸物"]),
    ("shiga", "specialty", "信楽焼", ["六古窯", "狸の置物", "時代祭（京都）と県違いひっかけ"]),
    ("kyoto", "specialty", "清水焼", ["京焼", "清水寺門前"]),
    ("hyogo", "specialty", "丹波焼", ["六古窯", "丹波篠山", "出石焼と同県"]),
    ("nara", "specialty", "赤膚焼", ["奈良", "出石焼と混同注意"]),
    ("okayama", "specialty", "備前焼", ["六古窯", "焼き締め", "烏城と同県"]),
    ("yamaguchi", "specialty", "萩焼", ["茶陶", "松本・深川窯"]),
    ("saga", "specialty", "有田焼", ["伊万里", "磁器", "玉取祭（福岡）と県違いひっかけ"]),
    ("saga", "specialty", "唐津焼", ["唐津くんちと同県", "茶陶"]),
    ("kagoshima", "specialty", "薩摩焼", ["白薩摩・黒薩摩", "鹿児島"]),
    ("nagasaki", "specialty", "波佐見焼", ["日用磁器", "有田と近接・県違い注意"]),
    ("okinawa", "specialty", "やちむん", ["壺屋", "読谷"]),
    # 郷土料理・名産（過去問組合せ＋定番）
    ("hokkaido", "specialty", "松前漬", ["昆布・スルメ", "千枚漬と混同注意"]),
    ("iwate", "specialty", "わんこそば", ["盛岡など", "小岩井農場と同県"]),
    ("akita", "specialty", "きりたんぽ", ["比内地鶏", "稲庭・しょっつると同県"]),
    ("akita", "specialty", "いぶりがっこ", ["燻製たくあん", "秋田"]),
    ("gunma", "specialty", "下仁田ネギ", ["鬼押出しと同県"]),
    ("tokyo", "specialty", "深川めし", ["アサリ", "秋川渓谷と同都"]),
    ("yamanashi", "specialty", "ほうとう", ["カボチャ", "勝沼と同県"]),
    ("fukui", "specialty", "小鯛のささ漬", ["若狭", "鮒ずしと混同注意"]),
    ("ishikawa", "specialty", "治部煮", ["鴨", "金沢", "九谷と同県"]),
    ("aichi", "specialty", "ひつまぶし", ["うなぎ", "名古屋"]),
    ("mie", "specialty", "伊勢うどん", ["柔らか麺", "二見浦と同県"]),
    ("nara", "specialty", "柿の葉ずし", ["鯖・鮭", "法起寺と同県", "赤膚焼と同県"]),
    ("shimane", "specialty", "出雲そば", ["割子そば", "出雲大社と同県"]),
    ("okayama", "specialty", "ままかり", ["酢漬け", "烏城と同県"]),
    ("hiroshima", "specialty", "かきめし", ["牡蠣", "帝釈峡と同県"]),
    ("yamaguchi", "specialty", "瓦そば", ["下関・豊浦", "茶そばを瓦で"]),
    ("kochi", "specialty", "皿鉢料理", ["大皿盛り", "室戸岬と同県"]),
    ("ehime", "specialty", "伊予さつま", ["さつまあげ系", "砥部焼と同県"]),
    ("fukuoka", "specialty", "がめ煮", ["筑前煮", "秋月と同県"]),
    ("nagasaki", "specialty", "ちゃんぽん", ["長崎", "波佐見と同県"]),
    ("kagoshima", "specialty", "山川漬", ["指宿・山川", "つぼ漬け", "千枚漬と混同注意"]),
    ("kagoshima", "specialty", "かるかん", ["蒸菓子", "知覧と同県"]),
    ("okinawa", "specialty", "沖縄そば", ["豚骨など", "やちむんと同県"]),
    # 祭・行事（三大祭・定番＋過去問ひっかけ）
    ("hokkaido", "festival", "さっぽろ雪まつり", ["大通公園", "氷像"]),
    ("hokkaido", "festival", "こたんまつり", ["アイヌ", "過去問ひっかけ"]),
    ("miyagi", "festival", "仙台七夕まつり", ["七夕飾り", "東北三大まつり"]),
    ("akita", "festival", "竿燈まつり", ["秋田市", "東北三大まつり", "ねぶたと混同注意"]),
    ("akita", "festival", "なまはげ", ["男鹿", "大晦日〜正月"]),
    ("tokyo", "festival", "三社祭", ["浅草", "益子焼と県違いひっかけ"]),
    ("tokyo", "festival", "神田祭", ["神田明神", "天下祭"]),
    ("kanagawa", "festival", "黒船祭", ["横須賀・久里浜", "ペリー"]),
    ("toyama", "festival", "こきりこ祭り", ["五箇山", "民謡"]),
    ("ishikawa", "festival", "青柏祭", ["七尾", "でか山", "キリコ"]),
    ("yamanashi", "festival", "吉田の火祭り", ["富士吉田", "北口本宮", "御柱と混同注意"]),
    ("saitama", "festival", "秩父夜祭", ["秩父神社", "屋台・花火", "日本三大曳山"]),
    ("gifu", "festival", "高山祭", ["春の山王・秋の八幡", "屋台"]),
    ("shiga", "festival", "長浜曳山まつり", ["長浜", "子ども歌舞伎"]),
    ("kyoto", "festival", "祇園祭", ["八坂神社", "山鉾", "宵山", "日本三大祭"]),
    ("kyoto", "festival", "葵祭", ["上賀茂・下鴨", "王朝行列"]),
    ("kyoto", "festival", "時代祭", ["平安神宮", "時代行列", "信楽焼と県違いひっかけ"]),
    ("osaka", "festival", "天神祭", ["大阪天満宮", "船渡御", "日本三大祭"]),
    ("fukuoka", "festival", "博多祇園山笠", ["櫛田神社", "追い山"]),
    ("nagasaki", "festival", "長崎くんち", ["諏訪神社", "竜踊", "唐津くんちと混同注意"]),
    ("yamaguchi", "festival", "先帝祭", ["赤間神宮", "安徳天皇", "下関"]),
    ("kumamoto", "festival", "山鹿灯籠まつり", ["山鹿", "千人灯籠踊り"]),
    ("kagoshima", "festival", "砂の祭典", ["吹上浜", "砂像"]),
    # 温泉・景勝・公園等の補完（過去問正解・定番の穴）
    ("aomori", "onsen", "浅虫温泉", ["青森市", "岩木山・弘前とセット"]),
    ("aomori", "place", "岩木山", ["津軽富士", "浅虫・弘前とセット"]),
    ("miyagi", "onsen", "作並温泉", ["仙台奥座敷", "秋保とセット"]),
    ("miyagi", "place", "瑞巌寺", ["松島", "円通院", "日本三景とセット"]),
    ("shimane", "onsen", "玉造温泉", ["宍道湖・出雲コース", "石見銀山の構成外"]),
    ("nagano", "onsen", "別所温泉", ["上田", "信州最古級", "和倉・花嫁のれんと県違いひっかけ"]),
    ("ehime", "onsen", "鈍川温泉", ["今治", "日田ひなまつりと県違いひっかけ"]),
    ("fukushima", "place", "五色沼", ["裏磐梯", "毘沙門沼など", "猪苗代・磐梯とセット"]),
    ("hokkaido", "place", "大沼", ["大沼国定公園", "函館〜洞爺コース"]),
    ("hokkaido", "place", "宗谷岬", ["日本最北端", "稚内", "旭山・サロベツコース"]),
    ("hokkaido", "place", "旭山動物園", ["旭川", "行動展示", "宗谷・サロベツコース"]),
    ("hokkaido", "park", "大雪山国立公園", ["層雲峡", "旭岳", "定山渓は園域外のひっかけ"]),
    ("hokkaido", "park", "阿寒摩周国立公園", ["阿寒湖", "摩周湖", "屈斜路とセット"]),
    ("shizuoka", "place", "白糸ノ滝", ["富士宮", "富士山世界遺産構成"]),
    ("iwate", "place", "遠野", ["民話のふるさと", "柳田國男", "カッパ淵"]),
    ("yamaguchi", "place", "関門橋", ["下関〜門司", "関門海峡", "西海橋・瀬戸大橋と混同注意"]),
    ("kagawa", "place", "栗林公園", ["高松", "大名庭園", "三名園外の名園"]),
    ("tokyo", "place", "東京タワー", ["芝公園", "電波塔", "スカイツリーと対比"]),
    # 温泉・景勝の追補（過去問ひっかけ・定番）
    ("gunma", "onsen", "四万温泉", ["吾妻", "草津と混同注意"]),
    ("yamagata", "onsen", "かみのやま温泉", ["上山", "銀山と混同注意"]),
    ("kumamoto", "onsen", "黒川温泉", ["南小国", "外湯めぐり", "人吉と混同注意"]),
    ("kumamoto", "onsen", "人吉温泉", ["球磨川", "黒川と混同注意"]),
    ("fukui", "place", "蘇洞門", ["小浜", "洞窟遊覧船", "東尋坊と混同注意"]),
    ("nagano", "place", "寝覚の床", ["上松", "木曽川", "渓谷"]),
    ("shizuoka", "place", "石廊崎", ["伊豆最南端", "富士箱根伊豆国立公園"]),
    ("kagawa", "place", "直島", ["地中美術館", "ベネッセ", "瀬戸内アート"]),
    ("hiroshima", "park", "瀬戸内海国立公園", ["多県に跨る", "宮島・鷲羽山など"]),
    ("kagoshima", "park", "霧島錦江湾国立公園", ["桜島", "霧島", "指宿"]),
    ("tottori", "park", "大山隠岐国立公園", ["大山", "隠岐", "島根にも跨る"]),
    ("nagasaki", "park", "雲仙天草国立公園", ["雲仙", "天草は熊本側も"]),
]


def add_fact(
    store: dict[str, dict[str, dict]],
    pref_id: str,
    typ: str,
    label: str,
    hooks: list[str] | None = None,
    sources: list[str] | None = None,
    *,
    curated: bool = False,
) -> None:
    label = normalize_label(label)
    valid_ids = {p[0] for p in PREFECTURES}
    if not label or pref_id not in valid_ids:
        return
    if not curated and is_bad_label(label):
        return
    key = f"{typ}::{label}"
    bucket = store[pref_id]
    if key not in bucket:
        bucket[key] = {
            "type": typ,
            "label": label,
            "hooks": [],
            "sources": [],
        }
    entry = bucket[key]
    for h in hooks or []:
        h = h.strip()
        if not h or h in entry["hooks"]:
            continue
        if not curated and is_bad_label(h):
            continue
        entry["hooks"].append(h)
    for s in sources or []:
        if s and s not in entry["sources"]:
            entry["sources"].append(s)


def extract_from_text(store: dict, text: str, qid: str) -> None:
    """Pull simple 名称（都道府県） and 名称＝都道府県 patterns."""
    # 名称（青森） / 名称（青森県）
    for m in re.finditer(
        r"([一-龥ぁ-んァ-ヶA-Za-z0-9・ー]{2,30})[（(](北海道|東京都|大阪府|京都府|.+?[県])[）)]",
        text,
    ):
        label, pref = m.group(1), m.group(2)
        if pref not in NAME_TO_ID and pref.replace("県", "") in NAME_TO_ID:
            pref_id = NAME_TO_ID[pref.replace("県", "")]
        else:
            pref_id = NAME_TO_ID.get(pref) or NAME_TO_ID.get(pref.replace("県", "").replace("府", "").replace("都", ""))
        if not pref_id:
            continue
        # skip if label looks like a sentence fragment
        if any(x in label for x in ("正解", "不正解", "よって", "学習", "本問", "選択肢")):
            continue
        add_fact(store, pref_id, guess_type(label, text[m.start() : m.end() + 40]), label, sources=[qid])

    # 名称＝都道府県 / 名称＝地名（県）
    for m in re.finditer(
        r"([一-龥ぁ-んァ-ヶA-Za-z0-9・ー]{2,24})＝([一-龥ぁ-んァ-ヶA-Za-z0-9・ー県府都道]{2,24})",
        text,
    ):
        left, right = m.group(1), m.group(2)
        pref_id = None
        hooks: list[str] = []
        for name, pid in NAME_TO_ID.items():
            if right == name or right.startswith(name) or name in right:
                # prefer longer official names
                if pref_id is None or len(name) > 2:
                    pref_id = pid
        if pref_id:
            # right may be place within pref — skip polluted exam-phrasing tails
            if re.search(r"一致しない|混同|正解|不正解|ひっかけ|誤り", right):
                pass
            elif not any(right.endswith(x) for x in ("県", "府", "都", "道")) and right not in NAME_TO_ID:
                hooks.append(right)
            add_fact(store, pref_id, guess_type(left + right), left, hooks=hooks, sources=[qid])


def main() -> None:
    store: dict[str, dict[str, dict]] = defaultdict(dict)

    for pref_id, typ, label, hooks in CURATED:
        add_fact(store, pref_id, typ, label, hooks=hooks, sources=["curated"], curated=True)

    for path in sorted(DATA.glob("20*-jitsumu.json")):
        questions = json.loads(path.read_text(encoding="utf-8"))["questions"]
        for q in questions:
            qid = q["id"]
            chunks = [q.get("overallExplanation") or "", q.get("stem") or ""]
            for c in q.get("choices") or []:
                chunks.append(c.get("explanation") or "")
                chunks.append(c.get("text") or "")
            blob = "\n".join(chunks)
            if not re.search(
                r"温泉|祭|まつり|名産|特産|郷土|世界遺産|国立公園|ラムサール|城|寺|神社|焼|漬|そば|くんち|御柱|ねぶた|学習メモ|組合せ|所在",
                blob,
            ):
                continue
            extract_from_text(store, blob, qid)

    prefectures = []
    total_facts = 0
    type_order = {t: i for i, t in enumerate(TYPES)}
    for pid, name, region in PREFECTURES:
        facts = dedupe_facts(list(store.get(pid, {}).values()))
        facts.sort(key=lambda f: (type_order.get(f["type"], 99), f["label"]))
        total_facts += len(facts)
        prefectures.append(
            {
                "id": pid,
                "name": name,
                "region": region,
                "facts": facts,
            }
        )

    payload = {
        "version": 1,
        "description": "国内旅行実務向け。過去問解説から抽出・整理した都道府県別の地名・祭り・特産・温泉等。",
        "types": [
            {"id": "place", "label": "名所・地形"},
            {"id": "onsen", "label": "温泉"},
            {"id": "festival", "label": "祭り・行事"},
            {"id": "specialty", "label": "特産・郷土料理"},
            {"id": "heritage", "label": "世界遺産・史跡"},
            {"id": "park", "label": "国立公園・湿地"},
            {"id": "course", "label": "モデルコース"},
        ],
        "prefectures": prefectures,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    nonempty = sum(1 for p in prefectures if p["facts"])
    print(f"wrote {OUT.relative_to(ROOT)} facts={total_facts} prefs_with_facts={nonempty}/47")


if __name__ == "__main__":
    main()
