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
    s = re.sub(r"^[ア-エA-D][.．]?", "", s)
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
    "きときと空港",
    "桃太郎空港",
    "阿波おどり空港",
    "安比",
    "金華山",
    "作並・五大堂",
    "小田原",
    "奥津",
    "鈍川",
    "杖立",
    "金丸座",
    "蓮台寺・石廊崎",
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
    facts = sorted(facts, key=lambda f: (-len(f["label"]), f["label"]))
    kept: list[dict] = []
    for f in facts:
        host = next(
            (
                k
                for k in kept
                if k["type"] == f["type"]
                and k["label"] != f["label"]
                and (k["label"].startswith(f["label"]) or f["label"] in k["label"])
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
    ("miyagi", "place", "松島", ["日本三景"]),
    ("akita", "specialty", "しょっつる鍋", ["秋田", "岩手名所とクロス注意"]),
    ("akita", "place", "田沢湖", ["十和田八幡平国立公園外がひっかけ"]),
    ("akita", "place", "角館", ["盛岡―田沢湖コース"]),
    ("yamagata", "festival", "花笠まつり", ["銀山温泉とセット"]),
    ("yamagata", "onsen", "銀山温泉", ["花笠まつりとセット"]),
    ("fukushima", "park", "尾瀬", ["福島・群馬・新潟", "釧路湿原と第1号混同注意"]),
    # 関東
    ("ibaraki", "place", "偕楽園", ["日本三名園", "好文亭", "水戸"]),
    ("ibaraki", "place", "弘道館", ["水戸"]),
    ("ibaraki", "place", "袋田の滝・花貫渓谷", ["県北", "水戸周遊コース"]),
    ("tochigi", "specialty", "しもつかれ", ["東尋坊（福井）とクロスひっかけ"]),
    ("gunma", "place", "吹割の滝", ["東洋のナイアガラ"]),
    ("gunma", "place", "茂林寺", ["ぶんぶく茶釜", "館林"]),
    ("saitama", "place", "長瀞", ["岩畳", "寳登山神社", "秩父"]),
    ("chiba", "place", "九十九里", ["鴨川シーワールドとセット"]),
    ("chiba", "place", "鴨川シーワールド", ["九十九里とセット"]),
    ("tokyo", "place", "猿島", ["横須賀", "東京湾", "旧軍施設"]),
    ("kanagawa", "place", "箱根・芦ノ湖", ["富士箱根伊豆国立公園"]),
    # 中部
    ("niigata", "heritage", "佐渡島の金山", ["2024登録", "西三川", "北沢浮遊選鉱場は構成外のひっかけ"]),
    ("toyama", "onsen", "宇奈月温泉", ["お水送り（福井）とクロス注意"]),
    ("toyama", "specialty", "ます寿し", ["鮒ずし（滋賀）と混同注意"]),
    ("ishikawa", "place", "兼六園", ["日本三名園"]),
    ("ishikawa", "place", "那谷寺", ["加賀", "白山信仰", "遊仙境", "奥の細道"]),
    ("ishikawa", "place", "九十九湾", ["能登", "蓬莱島", "英虞湾と混同注意"]),
    ("fukui", "festival", "お水送り", ["小浜", "お水取り（奈良）と混同注意", "あわら温泉とセット"]),
    ("fukui", "onsen", "あわら温泉", ["お水送りとセット"]),
    ("fukui", "place", "東尋坊", ["しもつかれ（栃木）とクロス注意"]),
    ("yamanashi", "place", "恵林寺・身延山久遠寺", ["善光寺（長野）と混同注意"]),
    ("yamanashi", "place", "昇仙峡", ["富士箱根伊豆国立公園外のひっかけ"]),
    ("nagano", "place", "善光寺", ["びんずる", "御開帳"]),
    ("nagano", "festival", "御柱祭", ["諏訪", "松本城と同県"]),
    ("nagano", "place", "松本城", ["北アルプス借景", "御柱とセット"]),
    ("nagano", "place", "妻籠宿", ["重要伝統的建造物群", "御柱と同県設問"]),
    ("nagano", "onsen", "浅間温泉", ["鹿教湯・湯田中とセット"]),
    ("nagano", "onsen", "鹿教湯温泉", ["浅間・湯田中とセット"]),
    ("nagano", "onsen", "湯田中温泉", ["浅間・鹿教湯とセット"]),
    ("nagano", "course", "善光寺―飯綱―戸隠―妙高", ["長野北郊"]),
    ("gifu", "festival", "郡上おどり", ["御柱（長野）と隣接県ひっかけ"]),
    ("aichi", "place", "犬山城", ["国宝天守", "木曽川", "白帝城", "愛知県犬山市（岐阜との境界付近）"]),
    ("shizuoka", "place", "三保松原", ["世界遺産構成", "久能山東照宮コース"]),
    ("shizuoka", "place", "登呂遺跡", ["弥生水田", "岩宿と対比"]),
    ("shizuoka", "course", "静岡―三保―久能山―三島SW―熱海", []),
    ("hokkaido", "place", "屈斜路湖", ["国内最大カルデラ湖", "御神渡り", "白鳥"]),
    ("hokkaido", "place", "支笏湖", ["深度国内2位", "チップ料理", "田沢湖と深度対比"]),
    ("aomori", "specialty", "せんべい汁", ["川越（埼玉）とクロスひっかけ"]),
    ("iwate", "onsen", "つなぎ温泉", ["猊鼻渓と同県", "盛岡周辺"]),
    ("iwate", "place", "猊鼻渓", ["一関", "つなぎ温泉と同県"]),
    ("miyagi", "place", "蔵王", ["御釜など"]),
    ("fukushima", "place", "大内宿", ["会津", "鶴ヶ城コース"]),
    ("ibaraki", "specialty", "あんこう鍋", ["潮来と同県セット"]),
    ("tochigi", "place", "足利学校", ["渋沢栄一記念館（埼玉）とクロスひっかけ"]),
    ("tochigi", "course", "湯西川温泉―霧降高原―輪王寺", ["日光・鬼怒川エリア"]),
    ("tochigi", "place", "いろは坂", ["日光東照宮と中禅寺湖を結ぶ"]),
    ("saitama", "place", "川越", ["せんべい汁（青森）とクロスひっかけ"]),
    ("saitama", "place", "渋沢栄一記念館", ["深谷", "足利学校（栃木）とクロス"]),
    ("kanagawa", "place", "鶴岡八幡宮", ["鎌倉", "源頼朝", "若宮大路"]),
    ("niigata", "place", "村上市", ["鮭", "瀬波温泉", "笹川流れ"]),
    ("niigata", "place", "笹川流れ", ["北海岸", "瀬波の後"]),
    ("ishikawa", "onsen", "和倉温泉", ["七尾", "花嫁のれん"]),
    ("yamanashi", "place", "忍野八海", ["河口湖・富士北麓コース"]),
    ("gifu", "place", "養老", ["白浜・道成寺（和歌山）とクロスひっかけ"]),
    ("gifu", "place", "郡上八幡", ["郡上おどり"]),
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
    ("fukushima", "place", "鶴ヶ城（会津若松城）", ["大内宿コース"]),
    ("chiba", "place", "成田山新勝寺", ["成田", "門前町"]),
    ("tokyo", "place", "浅草寺", ["雷門", "仲見世"]),
    ("kanagawa", "place", "江の島", ["湘南", "弁財天"]),
    ("toyama", "place", "立山", ["黒部ダム・室堂コース"]),
    ("nara", "place", "東大寺", ["大仏", "お水取り"]),
    ("tottori", "place", "鳥取砂丘", ["山陰海岸", "らくだ"]),
    ("miyazaki", "place", "青島", ["神話", "鬼の洗濯板"]),
    ("kyoto", "place", "天龍寺", ["嵐山", "保津川下り終点付近", "古都京都構成資産"]),
    ("kyoto", "place", "鞍馬寺", ["牛若丸", "毘沙門天"]),
    ("wakayama", "place", "那智の滝", ["熊野那智大社", "紀伊山地の霊場と参詣道"]),
    ("wakayama", "place", "橋杭岩", ["串本", "紀南海岸"]),
    ("wakayama", "place", "白浜・道成寺", ["AWも和歌山", "養老（岐阜）とクロス注意"]),
    ("shimane", "onsen", "温泉津温泉", ["石見銀山関連の港町", "出雲大社と同県"]),
    ("okayama", "festival", "西大寺会陽", ["桃太郎空港＝岡山", "岡山の代表行事"]),
    ("okayama", "place", "鷲羽山", ["瀬戸大橋", "倉敷〜香川ルート"]),
    ("hiroshima", "place", "湯来温泉・縮景園・鞆の浦", ["同県セット"]),
    ("tokushima", "place", "大歩危・小歩危", ["阿波おどり空港＝徳島", "景勝"]),
    ("tokushima", "place", "大塚国際美術館", ["鳴門", "陶板名画"]),
    ("ehime", "specialty", "砥部焼", ["内子座と同県"]),
    ("ehime", "place", "内子座", ["砥部焼と同県"]),
    ("fukuoka", "festival", "玉取祭（玉せせり）", ["筥崎宮（福岡市東区）", "柳川と同県"]),
    ("fukuoka", "place", "太宰府天満宮", ["北九州〜柳川コース"]),
    ("fukuoka", "place", "柳川", ["北原白秋", "太宰府と同県コース"]),
    ("nagasaki", "place", "西海橋", ["針尾瀬戸", "佐世保〜西彼杵", "重要文化財"]),
    ("nagasaki", "place", "雲仙", ["仁田峠", "島原", "発荷峠と展望ひっかけ"]),
    ("nagasaki", "onsen", "小浜温泉", ["雲仙周辺", "日田の鉄輪と混同注意"]),
    ("nagasaki", "heritage", "原城跡", ["島原の乱", "天草キリシタンコース"]),
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
    ("kyoto", "place", "鞍馬・貴船", ["牛若丸"]),
    ("kyoto", "heritage", "古都京都の文化財", ["京都・宇治・大津", "延暦寺は滋賀だが構成"]),
    ("osaka", "place", "天王寺・USJ", ["同府セット"]),
    ("hyogo", "place", "姫路城", ["世界遺産", "出石焼"]),
    ("hyogo", "specialty", "出石焼", ["豊岡・出石", "姫路と同県"]),
    ("hyogo", "onsen", "有馬温泉", ["淡路・竹田城とセット"]),
    ("hyogo", "place", "淡路島", ["花さじき", "大鳴門・明石海峡"]),
    ("hyogo", "place", "竹田城", ["但馬", "有馬・淡路とセット"]),
    ("hyogo", "place", "玄武洞", ["島根と混同注意"]),
    ("nara", "festival", "お水取り", ["東大寺", "お水送り（福井）と混同注意"]),
    ("nara", "course", "興福寺―東大寺―若草山―春日大社", []),
    ("wakayama", "place", "潮岬", ["アドベンチャーワールドとセット"]),
    # 中国
    ("tottori", "onsen", "三朝温泉", ["鷺舞（島根）とクロス注意", "皆生・岩井も鳥取"]),
    ("tottori", "onsen", "皆生温泉", ["米子の奥座敷", "弓ヶ浜・美保湾"]),
    ("shimane", "place", "松江城（千鳥城）", ["宍道湖", "鯉城・霞ヶ城と混同注意"]),
    ("shimane", "heritage", "石見銀山", ["2007", "玉造温泉は構成外"]),
    ("shimane", "place", "足立美術館", ["出雲―宍道湖―皆生コース"]),
    ("shimane", "place", "隠岐", ["島後＋島前", "国賀海岸・ローソク島"]),
    ("okayama", "place", "後楽園", ["日本三名園"]),
    ("okayama", "onsen", "湯郷温泉", ["皆生（鳥取）と混同注意"]),
    ("hiroshima", "place", "宮島（厳島）", ["ラムサール", "ミヤジマトンボ", "宍道湖説明の混入ひっかけ"]),
    ("hiroshima", "place", "鯉城（広島城）", ["千鳥城と混同注意"]),
    ("shimane", "festival", "鷺舞", ["津和野", "三朝温泉（鳥取）とクロス注意"]),
    ("yamaguchi", "place", "秋芳洞", ["龍泉洞と混同注意"]),
    ("yamaguchi", "course", "新山口―防府天満宮―錦帯橋―宮島―広島", []),
    # 四国
    ("tokushima", "place", "脇町（うだつの町並み）", ["藍商人", "祖谷そばと同県設問"]),
    ("tokushima", "specialty", "祖谷そば", ["脇町と同県"]),
    ("tokushima", "specialty", "大谷焼", ["阿波おどりとセット"]),
    ("tokushima", "festival", "阿波おどり", ["大谷焼とセット"]),
    ("kagawa", "place", "金刀比羅宮", ["こんぴらさん", "石段", "うどん"]),
    ("kagawa", "place", "丸亀城", ["扇の勾配", "寒霞渓と同県"]),
    ("kagawa", "place", "寒霞渓", ["小豆島", "丸亀城と同県"]),
    ("ehime", "course", "松山―子規堂―琴弾公園―金刀比羅―高松", ["香川への接続"]),
    ("kochi", "place", "石鎚山", ["西日本最高峰", "修験", "宮之浦岳と対比"]),
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
    ("kagoshima", "place", "屋久島・宮之浦岳", ["自然遺産", "石鎚と対比"]),
    ("okinawa", "place", "糸満", ["ひめゆり", "平和祈念公園", "最南端"]),
    ("okinawa", "heritage", "琉球王国のグスク及び関連遺産群", ["首里・今帰仁・座喜味・中城・玉陵・識名園など", "宮良殿内は含まない"]),
    ("okinawa", "course", "那覇―識名園―座喜味―万座毛―本部", ["南→北"]),
    # 公園・遺産（跨ぎ）
    ("aomori", "park", "十和田八幡平国立公園", ["青森・秋田・岩手", "田沢湖は外"]),
    ("ishikawa", "park", "白山国立公園", ["御前峰", "お池巡り", "禅定道", "4県"]),
    ("tokyo", "park", "秩父多摩甲斐国立公園", ["西沢渓谷", "大菩薩", "三峯", "浅間は上信越"]),
    ("gunma", "park", "上信越高原国立公園", ["浅間山"]),
]


def add_fact(
    store: dict[str, dict[str, dict]],
    pref_id: str,
    typ: str,
    label: str,
    hooks: list[str] | None = None,
    sources: list[str] | None = None,
) -> None:
    label = normalize_label(label)
    valid_ids = {p[0] for p in PREFECTURES}
    if not label or is_bad_label(label) or pref_id not in valid_ids:
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
        if h and h not in entry["hooks"] and not is_bad_label(h):
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
            # right may be place within pref
            if not any(right.endswith(x) for x in ("県", "府", "都", "道")) and right not in NAME_TO_ID:
                hooks.append(right)
            add_fact(store, pref_id, guess_type(left + right), left, hooks=hooks, sources=[qid])


def main() -> None:
    store: dict[str, dict[str, dict]] = defaultdict(dict)

    for pref_id, typ, label, hooks in CURATED:
        add_fact(store, pref_id, typ, label, hooks=hooks, sources=["curated"])

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
