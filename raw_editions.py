# -*- coding: utf-8 -*-
"""
web_search経由で取得した全日本合唱連盟公式サイトの実データ（文字化けなし）。
2018〜2025年度、6エディション分。parser.py の回帰テスト用フィクスチャ。
"""

EDITIONS = {
    53: {
        "year_hint": 2025,
        "text": """\
［混声］
G1 Dies sanctificatus（1563） Giovannni Pierluigi da Palestrina曲
G2 Das edle Herz Ernst Marinelli詩／Anton Bruckner曲
G3 秋の午後（「光る砂漠」から） 矢澤宰詩／萩原英彦曲
G4 不思議（「不思議」から） 金子みすゞ詩／石若雅弥曲
［男声］
M1 Ascendens Christus in altum Giovannni Pierluigi da Palestrina曲
M2 Geistesgruß（「Drei Lieder」から） Johann Wolfgang von Goethe詩／Hugo Wolf曲
M3 彼岸花（「雪と花火」から） 北原白秋詩／多田武彦曲
M4 いきよう（「しずかなる星へ」から） きむらえいり詩／相澤直人曲
［女声］
F1 Sub tuum praesidium（1545a） Giovannni Pierluigi da Palestrina曲
F2 Die Capelle Johann Ludwig Uhland詩／Robert Schumann曲
F3 T（「Motet Vernale」から） 草野心平詩／間宮芳生曲
F4 かつて私は信じていた（「世界恋愛詩集」から） 菅原敏詩（原文：Heinrich Heine）／平木悟曲
※G1、M1、F1はラテン語、G2、M2、F2はドイツ語
※G3、F4はピアノ伴奏
""",
    },
    52: {
        "year_hint": 2023,
        "text": """\
[混声]
G1 Ave Maria／Josquin des Prez 曲
G2 Deep River／Brian Trant 編曲
G3 七里浜（「二つの碑銘」から）／西田幾多郎 詩／團 伊玖磨 曲
G4 この船の行く先で（「月の世界へ」から）／村本晋也 詩曲
[男声]
M1 Matona mia cara／Orlande de Lassus 曲
M2 The Battle of Jericho／Marshall Bartholomew 編曲
M3 秋の歌（「月下の一群 第1集」から）／Paul Verlaine 詩／堀口大學 訳詩／南 弘明 曲
M4 陥星（「瞬間の輝き」から）／高見 順 詩／松本 望 曲
[女声]
F1 O vos omnes／Thomás Luis de Victoria 曲
F2 This Train Is Bound for Glory／John C. Phillips 編曲
F3 ねむの花／壺田花子 詩／中田喜直 曲
F4 子守唄／立原道造 詩／三宅悠太 曲
※G1、F1はラテン語。M1はイタリア語、G2、M2、F2は英語。
※G4、M3、F3はピアノ伴奏。
""",
    },
    51: {
        "year_hint": 2022,
        "text": """\
[混声]
G1 Wenn mein Stündlein vorhanden ist（「Psalmen und Christliche Gesäng」から）／Hans Leo Hassler 曲
G2 Les fleurs et les arbres（「Deux choeurs」から／Camille Saint-Saëns 詩曲
G3 水上（「三つの無伴奏混声合唱曲」から）／北原白秋 詩／柴田南雄 曲
G4 T―空と涙について―（「恋の色彩」から）／古今和歌集より／田畠佑一 曲
[男声]
M1 Agnus Dei（「Mass for four voices」から）／Thomas Tallis 曲
M2 Salut, Dame Sainte（「Quatre petites prières de Saint François d'Assise」から）／Francis Poulenc 曲
M3 ピリカピリカ（「アイヌのウポポ」から）／アイヌ民謡／近藤鏡二郎 採譜／清水脩 曲
M4 ぜんぶ（「ぜんぶ ここに」から）／さくらももこ 詩／相澤直人 曲
[女声]
F1 Salve Regina／Giovanni Pierluigi da Palestrina 曲
F2 Sanctus（「Messe à trois voix」から）／André Caplet 曲
F3 街路灯（「街路灯」から）／北岡淳子 詩／三善 晃 曲
F4 ねんね根来の(「紀の国のこどもうた1」から) ／松下 耕 曲
※M1、F1、F2はラテン語。G1はドイツ語、G2、M2はフランス語。
※G4、F3はピアノ伴奏。
""",
    },
    50: {
        "year_hint": 2021,
        "text": """\
[混声]
G1 Gaude virgo, mater Christi／Josquin des Prez 曲
G2 Es ist verrathen（「Spanisches Liederspiel」から）／Emanuel Geibel ドイツ語訳詩 Robert Schumann 曲
G3 草原の別れ／阪田寛夫 詩 大中 恩 曲
G4 智慧の湖（「遠望」から）／高橋元吉 詩 根岸宏輔 曲
[男声]
M1 Surrexit pastor bonus／Giovanni Pierluigi da Palestrina 曲
M2 Frühlingsglocken（「6 Lieder」から）／Robert Reinick 詩 Robert Schumann 曲
M3 平林／落語「平林」より 大中 恩 曲
M4 花と画家（「そのあと」から）／谷川俊太郎 詩 上田真樹 曲
[女声]
F1 Quam pulchra es／John Dunstable 曲
F2 Lied（「3 Gedichte」から）／Emanuel von Geibel 詩 Robert Schumann 曲
F3 寂庵の祈り（「ある真夜中に」から）／瀬戸内寂聴 詩 千原英喜 曲
F4 定点観測（「定点観測」から）／三角みづ紀 詩 宮本正太郎 曲
※G1、M1、F1はラテン語。G2、M2、F2はドイツ語。
※G2、G4、F2、F3、F4はピアノ伴奏。ただしF3は無伴奏でも可。
""",
    },
    49: {
        "year_hint": 2020,
        "text": """\
[混声]
G1 Ehre sei dir, Christe（「Die Matthäus-Passion」から）／Heinrich Schütz 曲
G2 O salutaris Hostia／Gioachino Rossini 曲
G3 うたをうたうのはわすれても（「うたをうたうのはわすれても」から）／岸田衿子 詩 津田 元 曲
G4 骨（「4つの追憶の曲」から）／中原中也 詩 山口龍彦 曲
[男声]
M1 De coelo veniet／Jacobus Handl 曲
M2 Preghiera／Giuseppe Torre 詩 Gioachino Rossini 曲
M3 T（合唱のためのコンポジション 第6番「男声合唱のためのコンポジション」から）／間宮芳生 曲
M4 心象U（「風と浪三唱」から）／中原中也 詩 寺嶋陸也 曲
[女声]
F1 O sacrum convivium／Tomas Luis de Victoria 曲
F2 La Fede（「3 cori religiosi」から）／Gioachino Rossini 曲
F3 夜来香（「花の四季」から）／江間章子 詩 池辺晋一郎 曲
F4 いたいな（「愛のとき」から）／木島 始 詩 嶋みどり 曲
※G1はドイツ語、G2、M1、F1はラテン語、M2、F2はイタリア語。
※G4、M4、F2、F3はピアノ伴奏。
""",
    },
    48: {
        "year_hint": 2018,
        "text": """\
[混声]
Ｇ１ Ave Maria （Tomás Luis de Victoria 曲）
Ｇ２ Ensam i dunkla skogarnas famn （Emil von Qvanten 詩／Jean Sibelius 曲）
Ｇ３ 蜂が一ぴき…（「無声慟哭」から） （宮沢賢治 詩／林 光 曲）
Ｇ４ 雪（「甃のうへ」から）（三好達治 詩／川浦義広 曲）
[男声]
Ｍ１ Kyrie（「Missa Presque transi」から） （Jean de Ockeghem 曲）
Ｍ２ Ne pitkän matkan kulkijat （「Two Partsongs」から） （Larin Kyösti 詩／Jean Sibelius 曲）
Ｍ３ まじめな顔つき（「クレーの絵本 第2集」から） （谷川俊太郎 詩／三善 晃 曲）
Ｍ４ 物語（「Enfance finie」から） （三好達治 詩／木下牧子 曲）
[女声]
Ｆ１ Gabriel Archangelus （Francisco Guerrero 曲）
Ｆ２ Kantat till ord av W. von Konow（Walter von Konow 詩／Jean Sibelius 曲）
Ｆ３ 飛翔―白鷺（「内なる遠さ」から） （高野喜久雄 詩／田三郎 曲）
Ｆ４ その木々は緑（「その木々は緑」から） （覚 和歌子 詩／横山潤子 曲）
※G1、M1、F1はラテン語、G2、F2はスウェーデン語、M2はフィンランド語。
※G4、M4、F3、F4はピアノ伴奏。
""",
    },
}
