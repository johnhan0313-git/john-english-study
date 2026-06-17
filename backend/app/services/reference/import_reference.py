"""Seed data and import for phonetics & grammar reference."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.reference import GrammarPoint, PhoneticSymbol
from app.utils.json_helpers import dump_json_field, parse_json_field

PHONETIC_CATEGORY_ZH = {
    "short_vowel": "短元音",
    "long_vowel": "长元音",
    "diphthong": "双元音",
    "consonant": "辅音",
}

GRAMMAR_CATEGORY_ZH = {
    "tense": "动词时态",
    "voice": "语态",
    "non_finite": "非谓语动词",
    "clause": "从句",
    "subjunctive": "虚拟语气",
    "agreement": "主谓一致",
    "inversion": "倒装与强调",
    "comparison": "比较结构",
    "article": "冠词",
    "preposition": "介词与固定搭配",
    "special": "特殊句式",
}

PHONETICS_SEED: list[dict] = [
    # 短元音 7
    {"symbol": "ɪ", "category": "short_vowel", "subcategory": "前元音", "name_zh": "短元音 /ɪ/", "name_en": "short i",
     "description": "舌位比 /iː/ 低且短，口型较松。", "examples": [{"word": "sit", "ipa": "/sɪt/", "meaning_zh": "坐"}, {"word": "big", "ipa": "/bɪɡ/", "meaning_zh": "大的"}]},
    {"symbol": "e", "category": "short_vowel", "subcategory": "前元音", "name_zh": "短元音 /e/", "name_en": "short e",
     "examples": [{"word": "bed", "ipa": "/bed/", "meaning_zh": "床"}, {"word": "pen", "ipa": "/pen/", "meaning_zh": "钢笔"}]},
    {"symbol": "æ", "category": "short_vowel", "subcategory": "前元音", "name_zh": "短元音 /æ/", "name_en": "ash",
     "examples": [{"word": "cat", "ipa": "/kæt/", "meaning_zh": "猫"}, {"word": "map", "ipa": "/mæp/", "meaning_zh": "地图"}]},
    {"symbol": "ʌ", "category": "short_vowel", "subcategory": "中元音", "name_zh": "短元音 /ʌ/", "name_en": "strut",
     "examples": [{"word": "cup", "ipa": "/kʌp/", "meaning_zh": "杯子"}, {"word": "love", "ipa": "/lʌv/", "meaning_zh": "爱"}]},
    {"symbol": "ɒ", "category": "short_vowel", "subcategory": "后元音", "name_zh": "短元音 /ɒ/", "name_en": "lot (BrE)",
     "description": "英式发音；美式常作 /ɑː/ 或 /ɔː/。", "examples": [{"word": "hot", "ipa": "/hɒt/", "meaning_zh": "热的"}, {"word": "dog", "ipa": "/dɒɡ/", "meaning_zh": "狗"}]},
    {"symbol": "ʊ", "category": "short_vowel", "subcategory": "后元音", "name_zh": "短元音 /ʊ/", "name_en": "foot",
     "examples": [{"word": "book", "ipa": "/bʊk/", "meaning_zh": "书"}, {"word": "good", "ipa": "/ɡʊd/", "meaning_zh": "好的"}]},
    {"symbol": "ə", "category": "short_vowel", "subcategory": "中元音", "name_zh": "弱读元音 /ə/", "name_en": "schwa",
     "description": "英语中最常见的弱读音，多见于非重读音节。", "examples": [{"word": "about", "ipa": "/əˈbaʊt/", "meaning_zh": "关于"}, {"word": "teacher", "ipa": "/ˈtiːtʃə/", "meaning_zh": "教师"}]},
    # 长元音 5
    {"symbol": "iː", "category": "long_vowel", "subcategory": "前元音", "name_zh": "长元音 /iː/", "name_en": "long ee",
     "examples": [{"word": "see", "ipa": "/siː/", "meaning_zh": "看见"}, {"word": "meet", "ipa": "/miːt/", "meaning_zh": "遇见"}]},
    {"symbol": "ɑː", "category": "long_vowel", "subcategory": "后元音", "name_zh": "长元音 /ɑː/", "name_en": "long ah",
     "examples": [{"word": "car", "ipa": "/kɑː/", "meaning_zh": "汽车"}, {"word": "start", "ipa": "/stɑːt/", "meaning_zh": "开始"}]},
    {"symbol": "ɔː", "category": "long_vowel", "subcategory": "后元音", "name_zh": "长元音 /ɔː/", "name_en": "long aw",
     "examples": [{"word": "door", "ipa": "/dɔː/", "meaning_zh": "门"}, {"word": "more", "ipa": "/mɔː/", "meaning_zh": "更多"}]},
    {"symbol": "uː", "category": "long_vowel", "subcategory": "后元音", "name_zh": "长元音 /uː/", "name_en": "long oo",
     "examples": [{"word": "food", "ipa": "/fuːd/", "meaning_zh": "食物"}, {"word": "blue", "ipa": "/bluː/", "meaning_zh": "蓝色"}]},
    {"symbol": "ɜː", "category": "long_vowel", "subcategory": "中元音", "name_zh": "长元音 /ɜː/", "name_en": "nurse",
     "examples": [{"word": "bird", "ipa": "/bɜːd/", "meaning_zh": "鸟"}, {"word": "work", "ipa": "/wɜːk/", "meaning_zh": "工作"}]},
    # 双元音 8
    {"symbol": "eɪ", "category": "diphthong", "name_zh": "双元音 /eɪ/", "name_en": "face",
     "examples": [{"word": "day", "ipa": "/deɪ/", "meaning_zh": "天"}, {"word": "make", "ipa": "/meɪk/", "meaning_zh": "制作"}]},
    {"symbol": "aɪ", "category": "diphthong", "name_zh": "双元音 /aɪ/", "name_en": "price",
     "examples": [{"word": "time", "ipa": "/taɪm/", "meaning_zh": "时间"}, {"word": "like", "ipa": "/laɪk/", "meaning_zh": "喜欢"}]},
    {"symbol": "ɔɪ", "category": "diphthong", "name_zh": "双元音 /ɔɪ/", "name_en": "choice",
     "examples": [{"word": "boy", "ipa": "/bɔɪ/", "meaning_zh": "男孩"}, {"word": "voice", "ipa": "/vɔɪs/", "meaning_zh": "声音"}]},
    {"symbol": "aʊ", "category": "diphthong", "name_zh": "双元音 /aʊ/", "name_en": "mouth",
     "examples": [{"word": "now", "ipa": "/naʊ/", "meaning_zh": "现在"}, {"word": "house", "ipa": "/haʊs/", "meaning_zh": "房子"}]},
    {"symbol": "əʊ", "category": "diphthong", "name_zh": "双元音 /əʊ/", "name_en": "goat (BrE)",
     "examples": [{"word": "go", "ipa": "/ɡəʊ/", "meaning_zh": "去"}, {"word": "home", "ipa": "/həʊm/", "meaning_zh": "家"}]},
    {"symbol": "ɪə", "category": "diphthong", "name_zh": "双元音 /ɪə/", "name_en": "near",
     "examples": [{"word": "here", "ipa": "/hɪə/", "meaning_zh": "这里"}, {"word": "idea", "ipa": "/aɪˈdɪə/", "meaning_zh": "想法"}]},
    {"symbol": "eə", "category": "diphthong", "name_zh": "双元音 /eə/", "name_en": "square",
     "examples": [{"word": "air", "ipa": "/eə/", "meaning_zh": "空气"}, {"word": "care", "ipa": "/keə/", "meaning_zh": "关心"}]},
    {"symbol": "ʊə", "category": "diphthong", "name_zh": "双元音 /ʊə/", "name_en": "cure",
     "examples": [{"word": "tour", "ipa": "/tʊə/", "meaning_zh": "旅行"}, {"word": "pure", "ipa": "/pjʊə/", "meaning_zh": "纯粹的"}]},
    # 辅音 - 爆破音
    {"symbol": "p", "category": "consonant", "subcategory": "爆破音", "name_zh": "清辅音 /p/", "name_en": "p",
     "examples": [{"word": "pen", "ipa": "/pen/", "meaning_zh": "钢笔"}, {"word": "open", "ipa": "/ˈəʊpən/", "meaning_zh": "打开"}]},
    {"symbol": "b", "category": "consonant", "subcategory": "爆破音", "name_zh": "浊辅音 /b/", "name_en": "b",
     "examples": [{"word": "book", "ipa": "/bʊk/", "meaning_zh": "书"}, {"word": "job", "ipa": "/dʒɒb/", "meaning_zh": "工作"}]},
    {"symbol": "t", "category": "consonant", "subcategory": "爆破音", "name_zh": "清辅音 /t/", "name_en": "t",
     "examples": [{"word": "time", "ipa": "/taɪm/", "meaning_zh": "时间"}, {"word": "city", "ipa": "/ˈsɪti/", "meaning_zh": "城市"}]},
    {"symbol": "d", "category": "consonant", "subcategory": "爆破音", "name_zh": "浊辅音 /d/", "name_en": "d",
     "examples": [{"word": "day", "ipa": "/deɪ/", "meaning_zh": "天"}, {"word": "read", "ipa": "/riːd/", "meaning_zh": "阅读"}]},
    {"symbol": "k", "category": "consonant", "subcategory": "爆破音", "name_zh": "清辅音 /k/", "name_en": "k",
     "examples": [{"word": "cat", "ipa": "/kæt/", "meaning_zh": "猫"}, {"word": "school", "ipa": "/skuːl/", "meaning_zh": "学校"}]},
    {"symbol": "g", "category": "consonant", "subcategory": "爆破音", "name_zh": "浊辅音 /g/", "name_en": "g",
     "examples": [{"word": "go", "ipa": "/ɡəʊ/", "meaning_zh": "去"}, {"word": "big", "ipa": "/bɪɡ/", "meaning_zh": "大的"}]},
    # 摩擦音
    {"symbol": "f", "category": "consonant", "subcategory": "摩擦音", "name_zh": "清辅音 /f/", "name_en": "f",
     "examples": [{"word": "fish", "ipa": "/fɪʃ/", "meaning_zh": "鱼"}, {"word": "life", "ipa": "/laɪf/", "meaning_zh": "生活"}]},
    {"symbol": "v", "category": "consonant", "subcategory": "摩擦音", "name_zh": "浊辅音 /v/", "name_en": "v",
     "examples": [{"word": "voice", "ipa": "/vɔɪs/", "meaning_zh": "声音"}, {"word": "love", "ipa": "/lʌv/", "meaning_zh": "爱"}]},
    {"symbol": "θ", "category": "consonant", "subcategory": "摩擦音", "name_zh": "清辅音 /θ/", "name_en": "th (thin)",
     "description": "舌尖轻触上齿，送气摩擦。", "examples": [{"word": "think", "ipa": "/θɪŋk/", "meaning_zh": "思考"}, {"word": "three", "ipa": "/θriː/", "meaning_zh": "三"}]},
    {"symbol": "ð", "category": "consonant", "subcategory": "摩擦音", "name_zh": "浊辅音 /ð/", "name_en": "th (this)",
     "examples": [{"word": "this", "ipa": "/ðɪs/", "meaning_zh": "这个"}, {"word": "mother", "ipa": "/ˈmʌðə/", "meaning_zh": "母亲"}]},
    {"symbol": "s", "category": "consonant", "subcategory": "摩擦音", "name_zh": "清辅音 /s/", "name_en": "s",
     "examples": [{"word": "see", "ipa": "/siː/", "meaning_zh": "看见"}, {"word": "bus", "ipa": "/bʌs/", "meaning_zh": "公交车"}]},
    {"symbol": "z", "category": "consonant", "subcategory": "摩擦音", "name_zh": "浊辅音 /z/", "name_en": "z",
     "examples": [{"word": "zoo", "ipa": "/zuː/", "meaning_zh": "动物园"}, {"word": "easy", "ipa": "/ˈiːzi/", "meaning_zh": "容易的"}]},
    {"symbol": "ʃ", "category": "consonant", "subcategory": "摩擦音", "name_zh": "清辅音 /ʃ/", "name_en": "sh",
     "examples": [{"word": "she", "ipa": "/ʃiː/", "meaning_zh": "她"}, {"word": "wish", "ipa": "/wɪʃ/", "meaning_zh": "希望"}]},
    {"symbol": "ʒ", "category": "consonant", "subcategory": "摩擦音", "name_zh": "浊辅音 /ʒ/", "name_en": "zh",
     "examples": [{"word": "vision", "ipa": "/ˈvɪʒən/", "meaning_zh": "视觉"}, {"word": "pleasure", "ipa": "/ˈpleʒə/", "meaning_zh": "愉悦"}]},
    {"symbol": "h", "category": "consonant", "subcategory": "摩擦音", "name_zh": "清辅音 /h/", "name_en": "h",
     "examples": [{"word": "he", "ipa": "/hiː/", "meaning_zh": "他"}, {"word": "home", "ipa": "/həʊm/", "meaning_zh": "家"}]},
    # 破擦音
    {"symbol": "tʃ", "category": "consonant", "subcategory": "破擦音", "name_zh": "清辅音 /tʃ/", "name_en": "ch",
     "examples": [{"word": "chair", "ipa": "/tʃeə/", "meaning_zh": "椅子"}, {"word": "watch", "ipa": "/wɒtʃ/", "meaning_zh": "观看"}]},
    {"symbol": "dʒ", "category": "consonant", "subcategory": "破擦音", "name_zh": "浊辅音 /dʒ/", "name_en": "j",
     "examples": [{"word": "job", "ipa": "/dʒɒb/", "meaning_zh": "工作"}, {"word": "age", "ipa": "/eɪdʒ/", "meaning_zh": "年龄"}]},
    # 鼻音
    {"symbol": "m", "category": "consonant", "subcategory": "鼻音", "name_zh": "鼻音 /m/", "name_en": "m",
     "examples": [{"word": "man", "ipa": "/mæn/", "meaning_zh": "男人"}, {"word": "time", "ipa": "/taɪm/", "meaning_zh": "时间"}]},
    {"symbol": "n", "category": "consonant", "subcategory": "鼻音", "name_zh": "鼻音 /n/", "name_en": "n",
     "examples": [{"word": "no", "ipa": "/nəʊ/", "meaning_zh": "不"}, {"word": "sun", "ipa": "/sʌn/", "meaning_zh": "太阳"}]},
    {"symbol": "ŋ", "category": "consonant", "subcategory": "鼻音", "name_zh": "鼻音 /ŋ/", "name_en": "ng",
     "examples": [{"word": "sing", "ipa": "/sɪŋ/", "meaning_zh": "唱歌"}, {"word": "long", "ipa": "/lɒŋ/", "meaning_zh": "长的"}]},
    # 近音/侧音
    {"symbol": "l", "category": "consonant", "subcategory": "近音", "name_zh": "近音 /l/", "name_en": "l",
     "examples": [{"word": "like", "ipa": "/laɪk/", "meaning_zh": "喜欢"}, {"word": "school", "ipa": "/skuːl/", "meaning_zh": "学校"}]},
    {"symbol": "r", "category": "consonant", "subcategory": "近音", "name_zh": "近音 /r/", "name_en": "r",
     "examples": [{"word": "red", "ipa": "/red/", "meaning_zh": "红色"}, {"word": "read", "ipa": "/riːd/", "meaning_zh": "阅读"}]},
    {"symbol": "j", "category": "consonant", "subcategory": "近音", "name_zh": "近音 /j/", "name_en": "y",
     "examples": [{"word": "yes", "ipa": "/jes/", "meaning_zh": "是的"}, {"word": "you", "ipa": "/juː/", "meaning_zh": "你"}]},
    {"symbol": "w", "category": "consonant", "subcategory": "近音", "name_zh": "近音 /w/", "name_en": "w",
     "examples": [{"word": "we", "ipa": "/wiː/", "meaning_zh": "我们"}, {"word": "water", "ipa": "/ˈwɔːtə/", "meaning_zh": "水"}]},
]

GRAMMAR_SEED: list[dict] = [
    {"slug": "simple-present", "category": "tense", "title": "一般现在时", "level": "cet4",
     "summary": "表示习惯、真理、经常性动作或目前状态。",
     "structure": "主语 + 动词原形/第三人称单数",
     "rules": ["第三人称单数加 -s/-es", "否定用 don't/doesn't + 原形", "疑问用 Do/Does 提前"],
     "examples": [{"en": "She works in a hospital.", "zh": "她在医院工作。", "note": "习惯"}, {"en": "The earth moves around the sun.", "zh": "地球绕太阳转。", "note": "真理"}],
     "tips": "标志词：always, usually, often, every day"},
    {"slug": "simple-past", "category": "tense", "title": "一般过去时", "level": "cet4",
     "summary": "表示过去某时发生的动作或存在的状态。",
     "structure": "主语 + 动词过去式",
     "rules": ["规则动词加 -ed", "不规则动词需记忆", "否定用 didn't + 原形"],
     "examples": [{"en": "I visited Beijing last year.", "zh": "我去年去了北京。"}, {"en": "He didn't finish the report.", "zh": "他没有完成报告。"}],
     "tips": "标志词：yesterday, ago, last week, in 2020"},
    {"slug": "simple-future", "category": "tense", "title": "一般将来时", "level": "cet4",
     "summary": "表示将来发生的动作或状态。",
     "structure": "will/shall + 原形 或 be going to + 原形",
     "rules": ["will 表示意愿或预测", "be going to 表示计划或迹象", "shall 多用于第一人称（正式）"],
     "examples": [{"en": "I will call you tomorrow.", "zh": "我明天给你打电话。"}, {"en": "It is going to rain.", "zh": "要下雨了。"}]},
    {"slug": "present-continuous", "category": "tense", "title": "现在进行时", "level": "cet4",
     "summary": "表示此刻或现阶段正在进行的动作。",
     "structure": "am/is/are + doing",
     "rules": ["某些动词不用进行时：know, like, believe 等", "与 always 连用表感情色彩"],
     "examples": [{"en": "She is reading a novel.", "zh": "她正在读小说。"}, {"en": "They are working on a new project.", "zh": "他们正在做新项目。"}]},
    {"slug": "past-continuous", "category": "tense", "title": "过去进行时", "level": "cet4",
     "summary": "表示过去某时刻正在进行的动作。",
     "structure": "was/were + doing",
     "examples": [{"en": "I was studying when he called.", "zh": "他打电话时我正在学习。"}]},
    {"slug": "present-perfect", "category": "tense", "title": "现在完成时", "level": "cet4",
     "summary": "表示过去发生但与现在有联系，或持续到现在的动作。",
     "structure": "have/has + 过去分词",
     "rules": ["for/since 常连用", "already, yet, ever, never 常出现", "短暂动词与 for 连用需注意"],
     "examples": [{"en": "I have lived here for ten years.", "zh": "我在这里住了十年了。"}, {"en": "Have you ever been to London?", "zh": "你去过伦敦吗？"}],
     "tips": "CET 高频考点，注意与过去时的区别"},
    {"slug": "past-perfect", "category": "tense", "title": "过去完成时", "level": "cet6",
     "summary": "表示过去某时之前已完成的动作（过去的过去）。",
     "structure": "had + 过去分词",
     "examples": [{"en": "By the time I arrived, the meeting had started.", "zh": "我到的时候会议已经开始了。"}]},
    {"slug": "future-perfect", "category": "tense", "title": "将来完成时", "level": "cet6",
     "summary": "表示将来某时之前将完成的动作。",
     "structure": "will have + 过去分词",
     "examples": [{"en": "I will have finished the thesis by June.", "zh": "到六月我将完成论文。"}]},
    {"slug": "passive-voice", "category": "voice", "title": "被动语态", "level": "cet4",
     "summary": "强调动作的承受者，结构为 be + 过去分词。",
     "structure": "主语 + be + done (+ by agent)",
     "rules": ["各时态被动 = 对应 be 形式 + done", "不及物动词无被动", "双宾语两种被动均可"],
     "examples": [{"en": "The book was written by him.", "zh": "这本书是他写的。"}, {"en": "English is spoken worldwide.", "zh": "英语在世界范围内被使用。"}]},
    {"slug": "infinitive", "category": "non_finite", "title": "不定式", "level": "cet4",
     "summary": "to + 动词原形，作主语、宾语、定语、状语等。",
     "structure": "to + verb",
     "rules": ["too...to 太…而不能", "enough to 足够…去", "疑问词 + to do"],
     "examples": [{"en": "I want to improve my English.", "zh": "我想提高英语。"}, {"en": "She is old enough to vote.", "zh": "她已到投票年龄。"}]},
    {"slug": "gerund", "category": "non_finite", "title": "动名词", "level": "cet4",
     "summary": "动词 -ing 形式，具有名词特征。",
     "rules": ["某些动词后只接 doing：enjoy, finish, mind", "介词后接 doing", "There is no doing 结构"],
     "examples": [{"en": "I enjoy reading in the library.", "zh": "我喜欢在图书馆阅读。"}, {"en": "He is good at speaking.", "zh": "他擅长口语。"}]},
    {"slug": "participle", "category": "non_finite", "title": "分词（现在/过去）", "level": "cet6",
     "summary": "现在分词表主动进行，过去分词表被动完成，可作定语、状语、补语。",
     "examples": [{"en": "The rising sun brings hope.", "zh": "升起的太阳带来希望。"}, {"en": "Seen from the hill, the city looks beautiful.", "zh": "从山上看，城市很美。"}]},
    {"slug": "attributive-clause", "category": "clause", "title": "定语从句", "level": "cet4",
     "summary": "修饰名词/代词，关系词 who/which/that/whom/whose。",
     "rules": ["先行词是人用 who/that", "物用 which/that", "非限制性从句用逗号隔开，不能用 that"],
     "examples": [{"en": "The student who won the prize is from our class.", "zh": "得奖的学生来自我们班。"}, {"en": "This is the book that I recommended.", "zh": "这是我推荐的书。"}]},
    {"slug": "noun-clause", "category": "clause", "title": "名词性从句", "level": "cet4",
     "summary": "作主语、宾语、表语、同位语，引导词 that/whether/if/wh-。",
     "examples": [{"en": "What he said is true.", "zh": "他说的是真的。"}, {"en": "I wonder whether she will come.", "zh": "我想知道她是否会来。"}]},
    {"slug": "adverbial-clause", "category": "clause", "title": "状语从句", "level": "cet4",
     "summary": "表时间、原因、条件、让步、目的、结果等。",
     "rules": ["although 不与 but 连用", "so...that 结果状语", "in order that 目的"],
     "examples": [{"en": "Although it rained, we went out.", "zh": "虽然下雨，我们还是出去了。"}, {"en": "I will go if you invite me.", "zh": "如果你邀请我，我会去。"}]},
    {"slug": "subjunctive", "category": "subjunctive", "title": "虚拟语气", "level": "cet6",
     "summary": "表示与事实相反的假设或非真实条件。",
     "structure": "If + 过去式, would/could/might + 原形（与现在相反）",
     "rules": ["与过去相反：If had done, would have done", "wish 后从句用过去式/had done", "suggest/insist 表建议时用 (should+) 原形"],
     "examples": [{"en": "If I were you, I would accept the offer.", "zh": "如果我是你，我会接受这个 offer。"}, {"en": "I wish I had studied harder.", "zh": "我希望当初更努力学习。"}]},
    {"slug": "subject-verb-agreement", "category": "agreement", "title": "主谓一致", "level": "cet4",
     "summary": "谓语动词在人称和数上与主语一致。",
     "rules": ["就远原则：along with, as well as", "集合名词：family/team 看整体或成员", "不定式、动名词短语作主语用单数"],
     "examples": [{"en": "The number of students is increasing.", "zh": "学生人数在增加。"}, {"en": "Neither he nor I am wrong.", "zh": "他和我都没错。"}]},
    {"slug": "inversion", "category": "inversion", "title": "倒装句", "level": "cet6",
     "summary": "谓语或部分谓语置于主语之前以强调或符合语法。",
     "rules": ["否定词开头：Never, Hardly, Not only", "Only + 状语开头", "So/Neither 引导的倒装"],
     "examples": [{"en": "Never have I seen such a beautiful view.", "zh": "我从未见过如此美景。"}, {"en": "Only in this way can we succeed.", "zh": "只有这样我们才能成功。"}]},
    {"slug": "emphatic-it", "category": "inversion", "title": "强调句 It is...that", "level": "cet6",
     "summary": "It is/was + 被强调部分 + that/who + 其余。",
     "examples": [{"en": "It was in 2020 that the project started.", "zh": "正是在2020年项目启动了。"}]},
    {"slug": "comparative", "category": "comparison", "title": "比较级与最高级", "level": "cet4",
     "summary": "形容词/副词的比较与最高形式。",
     "rules": ["more/most + 多音节", "-er/-est 单音节", "the + 比较级, the + 比较级", "as...as 同级比较"],
     "examples": [{"en": "She is taller than her sister.", "zh": "她比她姐姐高。"}, {"en": "The more you practice, the better you speak.", "zh": "练得越多，说得越好。"}]},
    {"slug": "articles", "category": "article", "title": "冠词 a/an/the", "level": "cet4",
     "summary": "泛指用 a/an，特指用 the；元音音素前用 an。",
     "rules": ["独一无二用 the：sun, earth", "球类、三餐、学科前常不用 the", "the + 形容词表一类人"],
     "examples": [{"en": "An hour ago, I saw a UFO.", "zh": "一小时前我看到了不明飞行物。"}, {"en": "The rich should help the poor.", "zh": "富人应帮助穷人。"}]},
    {"slug": "prepositions", "category": "preposition", "title": "常用介词与固定搭配", "level": "cet4",
     "summary": "介词后接名词/动名词；大量固定搭配需积累。",
     "examples": [{"en": "He is interested in science.", "zh": "他对科学感兴趣。"}, {"en": "She succeeded in passing the exam.", "zh": "她成功通过了考试。"}],
     "tips": "CET 常考：depend on, result in/from, consist of, apply for"},
    {"slug": "there-be", "category": "special", "title": "There be 句型", "level": "cet4",
     "summary": "表示某处存在某物/人，be 的形式随最近主语变化。",
     "examples": [{"en": "There is a book on the desk.", "zh": "桌上有一本书。"}, {"en": "There have been many changes.", "zh": "发生了许多变化。"}]},
    {"slug": "modal-verbs", "category": "special", "title": "情态动词", "level": "cet4",
     "summary": "can/could, may/might, must, should, would 等表能力、许可、义务、推测。",
     "rules": ["must 表必须；mustn't 表禁止", "should have done 表本应做却未做", "can/could have done 表本能够"],
     "examples": [{"en": "You must hand in the paper on time.", "zh": "你必须按时交论文。"}, {"en": "He should have told me earlier.", "zh": "他本该早点告诉我。"}]},
    {"slug": "conditional", "category": "special", "title": "条件句（真实/非真实）", "level": "cet6",
     "summary": "第一类真实条件，第二类/第三类非真实条件。",
     "examples": [{"en": "If it rains tomorrow, we will cancel the trip.", "zh": "如果明天下雨，我们就取消旅行。"}]},
    {"slug": "direct-indirect-speech", "category": "special", "title": "直接引语与间接引语", "level": "cet6",
     "summary": "转述时人称、时态、时间状语需相应变化。",
     "rules": ["现在→过去", "come→go", "today→that day"],
     "examples": [{"en": "He said (that) he was busy.", "zh": "他说他很忙。"}]},
    {"slug": "parallel-structure", "category": "special", "title": "平行结构", "level": "cet6",
     "summary": "并列成分在形式上保持一致。",
     "examples": [{"en": "She likes reading, writing, and swimming.", "zh": "她喜欢阅读、写作和游泳。"}]},
    {"slug": "run-on-sentences", "category": "special", "title": "并列连词与句子合并", "level": "cet4",
     "summary": "and, but, or, so, for, yet, nor 连接并列句。",
     "examples": [{"en": "I was tired, but I kept working.", "zh": "我很累，但我继续工作。"}]},
]


def import_reference(db: Session) -> dict[str, int]:
    phonetics_count = db.query(PhoneticSymbol).count()
    grammar_count = db.query(GrammarPoint).count()
    if phonetics_count > 0 and grammar_count > 0:
        return {
            "phonetics": phonetics_count,
            "grammar": grammar_count,
            "skipped": True,
        }

    if phonetics_count == 0:
        for i, item in enumerate(PHONETICS_SEED):
            db.add(PhoneticSymbol(
                symbol=item["symbol"],
                category=item["category"],
                subcategory=item.get("subcategory"),
                name_zh=item["name_zh"],
                name_en=item["name_en"],
                description=item.get("description"),
                examples=dump_json_field(item.get("examples", [])),
                sort_order=i,
            ))

    if grammar_count == 0:
        for i, item in enumerate(GRAMMAR_SEED):
            db.add(GrammarPoint(
                slug=item["slug"],
                category=item["category"],
                title=item["title"],
                level=item["level"],
                summary=item["summary"],
                structure=item.get("structure"),
                rules=dump_json_field(item.get("rules", [])),
                examples=dump_json_field(item.get("examples", [])),
                tips=item.get("tips"),
                sort_order=i,
            ))

    db.commit()
    return {
        "phonetics": db.query(PhoneticSymbol).count(),
        "grammar": db.query(GrammarPoint).count(),
        "skipped": False,
    }


def phonetic_to_brief(p: PhoneticSymbol) -> dict:
    examples = parse_json_field(p.examples, [])
    return {
        "id": p.id,
        "symbol": p.symbol,
        "category": p.category,
        "subcategory": p.subcategory,
        "name_zh": p.name_zh,
        "name_en": p.name_en,
        "preview_word": examples[0]["word"] if examples else None,
    }


def phonetic_to_detail(p: PhoneticSymbol) -> dict:
    from app.services.reference.phonetic_audio import SYMBOL_SOUND_CUE, build_phonetic_symbol_speech_text

    symbol = p.symbol.strip()
    return {
        **phonetic_to_brief(p),
        "description": p.description,
        "examples": parse_json_field(p.examples, []),
        "sound_cue": SYMBOL_SOUND_CUE.get(symbol) or build_phonetic_symbol_speech_text(p),
    }


def grammar_to_brief(g: GrammarPoint) -> dict:
    return {
        "id": g.id,
        "slug": g.slug,
        "category": g.category,
        "title": g.title,
        "level": g.level,
        "summary": g.summary,
    }


def grammar_to_detail(g: GrammarPoint) -> dict:
    return {
        **grammar_to_brief(g),
        "structure": g.structure,
        "rules": parse_json_field(g.rules, []),
        "examples": parse_json_field(g.examples, []),
        "tips": g.tips,
    }
