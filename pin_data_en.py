# pinterest-kit/pin_data_en.py
# The Japan Desk のピン画像に載せるデータ。**すべて記事本文に実在する値だけ**を置く。
#
# ★ここに書いてよいのは、記事が一次ソース付きで確定させた事実だけ。
#   記事に無い数値を足さない（ピンは2〜3年生き続けるため、後から直しても回収できない）。
#
# 1記事につき c（情報図版）と a（活字）の2つ。**同じ数字を c と a の両方に出さない。**
#   Pinterest のフレッシュピン判定は画像もテキストも作り直して初めて成立し、
#   同じ数字を並べると人間の目にも重複ピンに見える。
#
# kind: "table"  -> columns / rows / highlight_col
#       "timeline" -> steps [[左ラベル, 右本文], ...]
#       "list"   -> items [[見出し, 補足], ...]

PIN_DATA = {
    # ---------------------------------------------------------------- 旅行・実務
    "is-jr-pass-worth-it-2026": {
        "c": {
            "kind": "table",
            "eyebrow": "JR PASS VS REGIONAL",
            "title": "The nationwide pass is no longer default",
            "columns": ["Pass", "Price", "Hiked?"],
            "rows": [["JR Pass 7-day", "¥50,000", "Yes"],
                     ["JR Pass 14-day", "¥80,000", "Yes"],
                     ["Kansai WIDE 5d", "¥12,000", "No"],
                     ["Kansai+Hiroshima 5d", "¥17,000", "No"]],
            "highlight_col": 1,
            "verdict": "Regional passes dodged the hikes. Nationwide didn't.",
            "source": "japanrailpass.net",
        },
        "a": {
            "num": "¥4,960",
            "unit": "TOKYO-KYOTO",
            "title": "The pass skips the fastest bullet trains",
            "sub": "Nozomi and Mizuho cost extra.\nTwo legs eat most of a ¥10,000 saving.",
        },
    },
    "suica-pasmo-icoca-guide": {
        "c": {
            "kind": "list",
            "eyebrow": "IC CARD BASICS",
            "title": "What to know before you tap in Japan",
            "items": [["Any card works", "Suica, PASMO, ICOCA are interchangeable"],
                      ["Buy at a machine", "No special counter needed"],
                      ["Load ¥2,000", "Top up in small amounts as you go"],
                      ["¥500 deposit", "Welcome Suica has none, 28-day validity"],
                      ["Not a rail pass", "Local taps only, not Shinkansen"]],
            "verdict": "Your foreign credit card won't open the gates.",
            "source": "jreast.co.jp",
        },
        "a": {
            "num": "10",
            "unit": "IC CARDS",
            "title": "Ten cards, one nationwide network",
            "sub": "Buy any of them, anywhere.\nIt taps almost everywhere.",
        },
    },
    "cheapest-time-to-fly-to-japan": {
        "c": {
            "kind": "timeline",
            "eyebrow": "JAPAN'S FIXED PEAKS",
            "title": "The weeks Japan travels all at once",
            "steps": [["Late Mar-Apr", "Cherry blossom, soft peak"],
                      ["Apr 29-May 5", "Golden Week, the worst week"],
                      ["Aug 13-15", "Obon, plus peak humidity"],
                      ["November", "Autumn foliage, softer peak"],
                      ["Dec 28-Jan 4", "New Year, the biggest peak"]],
            "verdict": "Move one week off these and save more than any trick.",
            "source": "cao.go.jp",
        },
        "a": {
            "num": "Jan-Mar",
            "unit": "BEST VALUE",
            "title": "The strongest value window is mid-winter",
            "sub": "New Year rush is over.\nSpring surge hasn't started.",
        },
    },
    "best-esim-for-japan": {
        "c": {
            "kind": "table",
            "eyebrow": "JAPAN TRAVEL DATA",
            "title": "What getting online actually costs",
            "columns": ["Option", "Typical cost", "Best for"],
            "rows": [["eSIM", "US$10-40", "Solo travellers"],
                     ["Pocket Wi-Fi", "¥300-1,500/day", "Groups"],
                     ["Roaming", "US$10-15/day", "Zero setup"],
                     ["Physical SIM", "Varies", "No-eSIM phones"]],
            "highlight_col": 1,
            "verdict": "Solo? eSIM. Group? Pocket Wi-Fi splits cheaper.",
            "source": "",
        },
        "a": {
            "num": "0.7-1 GB",
            "unit": "PER DAY",
            "title": "Maps and messaging use less than you think",
            "sub": "Photos and video are what drain it.\n10-20 GB covers a 1-2 week trip.",
        },
    },
    "japan-packing-list": {
        "c": {
            "kind": "list",
            "eyebrow": "BRING FROM HOME",
            "title": "What's actually worth packing for Japan",
            "items": [["Broken-in shoes", "The single most important item"],
                      ["Power bank", "10,000 mAh+ for all-day Maps"],
                      ["Type A adapter", "Two flat pins, 100V, plus cables"],
                      ["Coin purse", "Japan still runs on some cash"],
                      ["Prescription meds", "Some need a Yakkan Shoumei"]],
            "verdict": "Buy the rest in your first konbini.",
            "source": "mhlw.go.jp",
        },
        "a": {
            "num": "20-30k",
            "unit": "STEPS A DAY",
            "title": "Japan is a walking country",
            "sub": "Bring shoes you've already worn in.\nComfort beats fashion.",
        },
    },

    # ---------------------------------------------------------------- 旅程
    "7-day-japan-itinerary": {
        "c": {
            "kind": "timeline",
            "eyebrow": "7 DAYS IN JAPAN",
            "title": "The route that actually works for week one",
            "steps": [["Day 1-2", "Tokyo: icons + teamLab"],
                      ["Day 3", "Day trip: Mt. Fuji or Hakone"],
                      ["Day 4", "Shinkansen to Kyoto (~2.5h)"],
                      ["Day 5", "Arashiyama, Fushimi Inari"],
                      ["Day 6-7", "Osaka: Dotonbori, the castle"]],
            "verdict": "Three bases, one big train leg. Nothing more.",
            "source": "",
        },
        "a": {
            "num": "5",
            "unit": "MISTAKES",
            "title": "The five mistakes that wreck a first week in Japan",
            "sub": "Too many bases. Rail pass on autopilot.\nWritten from Japan",
        },
    },
    "2-week-japan-itinerary": {
        "c": {
            "kind": "table",
            "eyebrow": "14 DAYS IN JAPAN",
            "title": "Week one is the icons. Week two is the choice.",
            "columns": ["Week 2 option", "What you get"],
            "rows": [["Alps", "Takayama, Shirakawa-go"],
                     ["West", "Hiroshima, Miyajima, cycling"],
                     ["North", "Sapporo and Hokkaido"]],
            "highlight_col": 0,
            "verdict": "Pick one region for week two. Never two.",
            "source": "japanrailpass.net",
        },
        "a": {
            "num": "¥80,000",
            "unit": "14-DAY JR PASS",
            "title": "Two weeks is where the pass math flips",
            "sub": "Aug 2026 price; ¥84,000 from Oct 1\nTwo regions? The 14-day pass often wins",
        },
    },
    "1-month-japan-itinerary": {
        "c": {
            "kind": "timeline",
            "eyebrow": "30 DAYS IN JAPAN",
            "title": "Four regions, one week each, unhurried",
            "steps": [["Week 1", "Tokyo and the golden route"],
                      ["Week 2", "Kansai plus a Japan Alps detour"],
                      ["Week 3", "West Japan and Shikoku"],
                      ["Week 4", "Kyushu or Hokkaido finish"]],
            "verdict": "Four regions done properly, not all 47.",
            "source": "japanrailpass.net",
        },
        "a": {
            "num": "30",
            "unit": "NIGHTS",
            "title": "At 30 nights, lodging beats every travel hack",
            "sub": "Weekly rates save more than any pass\nWritten from Japan",
        },
    },
    "2-months-in-japan-long-stay": {
        "c": {
            "kind": "list",
            "eyebrow": "1-2 MONTHS IN JAPAN",
            "title": "Set up a temporary life, not a long trip",
            "items": [["Housing", "Monthly flat or share house"],
                      ["Data", "Monthly SIM, not travel eSIMs"],
                      ["Movement", "Home base, weekend trips"],
                      ["Language", "Study from day one"],
                      ["Money", "Low-fee card, IC, cash buffer"]],
            "verdict": "Stop planning a trip. Start a temporary life.",
            "source": "",
        },
        "a": {
            "num": "2",
            "unit": "MONTHS",
            "title": "Two months is when Japanese starts paying off",
            "sub": "Base, monthly SIM, monthly housing\nThen spend the time on the language",
        },
    },
    "japan-souvenirs-worth-buying": {
        "c": {
            "kind": "table",
            "eyebrow": "JAPAN SOUVENIRS",
            "title": "Three crafts worth the suitcase space",
            "columns": ["Craft", "Getting it home"],
            "rows": [["Knives", "Checked luggage, always"],
                     ["Ceramics", "Wrapped in clothes, center"],
                     ["Pens", "Carry-on; fly empty or full"]],
            "highlight_col": 1,
            "verdict": "Buy what you'll use daily. Skip the drawer stuff.",
            "source": "",
        },
        "a": {
            "num": "400",
            "unit": "YEAR-OLD KILNS",
            "title": "Why a mug from a kiln town beats any trinket",
            "sub": "Arita, Mino, Bizen, Mashiko\nBuy what you'll use every day",
        },
    },
    "best-klook-tours-tokyo": {
        "c": {
            "kind": "table",
            "eyebrow": "TOKYO TOURS",
            "title": "What to lock in and what to leave open",
            "columns": ["Tour", "Time", "Book ahead"],
            "rows": [["teamLab", "2-3h", "Yes - sells out"],
                     ["Shibuya Sky", "1-1.5h", "Yes for sunset"],
                     ["Mt. Fuji day trip", "10-12h", "Yes, a week out"],
                     ["Izakaya night crawl", "~3h", "Yes"]],
            "highlight_col": 2,
            "verdict": "Lock the timed-entry ones. Leave the rest flexible.",
            "source": "klook.com",
        },
        "a": {
            "num": "7",
            "unit": "TOURS",
            "title": "Tokyo tours sorted by who you actually are",
            "sub": "Chosen by use case, not by\nstar rating or hype.",
        },
    },

    # ---------------------------------------------------------------- 語学
    "japanesepod101-review": {
        "c": {
            "kind": "table",
            "eyebrow": "WHICH TIER",
            "title": "What each tier actually gets you",
            "columns": ["Tier", "What you get", "Best for"],
            "rows": [["Free", "Sample lessons, kana", "Testing the style"],
                     ["Basic", "Lesson audio + notes", "Budget listeners"],
                     ["Premium", "Study tools, quizzes", "Most learners"],
                     ["Premium PLUS", "1-on-1 teacher", "Speaking practice"]],
            "verdict": "Premium is the sweet spot. Start on the free account.",
            "source": "",
        },
        "a": {
            "num": "2,000+",
            "unit": "AUDIO LESSONS",
            "title": "Great for listening. Almost nothing for kanji",
            "sub": "Native dialogues, bilingual hosts.\nIt's a spine, not a whole stack.",
        },
    },
    "learn-japanese-from-anime": {
        "c": {
            "kind": "timeline",
            "eyebrow": "THE METHOD",
            "title": "From passive watching to actual study",
            "steps": [["Step 0", "Kana, basic grammar: 4-8 weeks"],
                      ["Step 1", "Switch subtitles to Japanese"],
                      ["Step 2", "Pause and look up recurring words"],
                      ["Step 3", "Mine sentences into an SRS deck"],
                      ["Step 4", "Shadow the lines out loud"]],
            "verdict": "Build the base first, or none of the rest works.",
            "source": "",
        },
        "a": {
            "num": "4",
            "unit": "SPEECH TRAPS",
            "title": "Anime Japanese you should never copy",
            "sub": "Tough-guy speech, role language,\ngendered endings, no politeness.",
        },
    },
    "migaku-vs-alternatives": {
        "c": {
            "kind": "table",
            "eyebrow": "IMMERSION TOOLS",
            "title": "Which one turns your content into cards",
            "columns": ["Tool", "Approach", "Friction"],
            "rows": [["Migaku", "Mine real video + web", "Very low"],
                     ["Anki + Yomitan", "DIY pop-up mining", "Medium"],
                     ["Language Reactor", "Netflix dual subs", "Low, exports"],
                     ["LingQ", "Import text + audio", "Low for reading"]],
            "verdict": "Try a free on-ramp before you pay for the polish.",
            "source": "",
        },
        "a": {
            "num": "1",
            "unit": "CLICK",
            "title": "Lookup to flashcard, with the scene attached",
            "sub": "Collapsing that loop is what\nyou're actually paying for.",
        },
    },
    "wanikani-alternatives": {
        "c": {
            "kind": "list",
            "eyebrow": "KANJI TOOLS",
            "title": "Pick by what you want to be tested on",
            "items": [["Renshuu", "Free, structured, grammar too"],
                      ["Anki", "Total control, deck quality decides"],
                      ["Bunpro", "JLPT-ordered grammar SRS"],
                      ["KaniWani", "Reverse drilling, produce the word"],
                      ["Skritter", "Handwriting, stroke by stroke"]],
            "verdict": "Start with the free options before you pay for one.",
            "source": "",
        },
        "a": {
            "num": "6",
            "unit": "ALTERNATIVES",
            "title": "If WaniKani's pace isn't working for you",
            "sub": "Native-checked comparison.\nNo affiliate for WaniKani itself.",
        },
    },

    "japanese-culture-experiences-worth-booking": {
        "c": {
            "kind": "list",
            "eyebrow": "BEFORE YOU BOOK",
            "title": "Four different products, one listing page",
            "items": [["Kimono rental", "Wear it all day, return by evening"],
                      ["Kimono photoshoot", "You leave with images, not a day out"],
                      ["Tea ceremony", "Short group demo, or private half-day"],
                      ["Non-verbal show", "No Japanese needed to follow it"],
                      ["Guided walk", "You are paying for the narration"]],
            "verdict": "Check whether admission is included. That is the price gap.",
            "source": "",
        },
        "a": {
            "num": "6",
            "unit": "THINGS TO CHECK",
            "title": "The listing title hides the difference",
            "sub": "Inclusions, meeting point, guide's language,\ncancellation, return time, private or group.",
        },
    },

    "japan-highway-bus-and-ferry-guide": {
        "c": {
            "kind": "list",
            "eyebrow": "OFF THE RAIL MAP",
            "title": "The places a Japan rail pass cannot take you",
            "items": [["Shirakawa-go", "No station. Never had one. Bus only"],
                      ["Kawaguchiko", "Direct coach beats the three-leg rail route"],
                      ["Beppu", "Overnight ferry replaces a hotel night"],
                      ["FujiQ Highland", "The bus stops at the gate, not the city"],
                      ["Airports", "Door to door, luggage stays under the floor"]],
            "verdict": "A rail-shaped itinerary deletes these without telling you.",
            "source": "",
        },
        "a": {
            "num": "2",
            "unit": "HOURS",
            "title": "The rule of thumb for trains vs buses",
            "sub": "Under two hours by rail, take the train.\nOver it, check the road and the water first.",
        },
    },

    # ---------------------------------------------------------------- 自然
    # 数値はすべて気象庁「生物季節観測累年表」（かえでの紅葉／落葉・1953-2025）から
    # 記事側で計算した2016-2025の10年平均。記事の表と1つでも食い違わせないこと。
    "japan-autumn-foliage-guide": {
        "c": {
            "kind": "table",
            "eyebrow": "AUTUMN COLOUR, MEASURED",
            "title": "Japan's leaves peak later than you were told",
            "columns": ["City", "Full colour", "Window"],
            "rows": [["Sapporo", "Nov 7", "4 days"],
                     ["Sendai", "Nov 23", "10 days"],
                     ["Tokyo", "Nov 28", "12 days"],
                     ["Fukuoka", "Dec 4", "12 days"],
                     ["Kyoto", "Dec 10", "11 days"]],
            "highlight_col": 1,
            "verdict": "Kyoto averages December 10, not mid-November.",
            "source": "data.jma.go.jp",
        },
        "a": {
            "num": "13",
            "unit": "DAYS OF SPREAD",
            "title": "There is no single peak week",
            "sub": "Over the last decade the colour date moved\n13 days between the earliest and latest year.",
        },
    },
    "japan-onsen-towns-worth-the-detour": {
        "c": {
            "kind": "table",
            "eyebrow": "ONSEN TOWNS, BY ACCESS",
            "title": "Which onsen towns let you bathe without a room",
            "columns": ["Town", "Day visitor pays", "Baths"],
            "rows": [["Nozawa", "Donation", "13"],
                     ["Beppu", "¥300", "8+"],
                     ["Kusatsu", "Free", "3+"],
                     ["Kinosaki", "¥1,500 pass", "6"],
                     ["Kurokawa", "¥1,500 pass", "3"],
                     ["Shibu", "¥800", "1"]],
            "highlight_col": 1,
            "verdict": "Shibu's other 8 baths are for overnight guests only.",
            "source": "town tourism associations",
        },
        "a": {
            "num": "13",
            "unit": "FREE BATHS",
            "title": "One village asks only for a donation",
            "sub": "Nozawa Onsen's 13 public baths are run by the\nvillagers themselves. There is no ticket window.",
        },
    },
}
