# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Fast, pure-Python, zero-dependency language detector optimized for language cards."""

from __future__ import annotations

import re
import unicodedata

# Default dedicated neural voices per language code
DEFAULT_VOICES: dict[str, str] = {
    "it": "it-IT-ElsaNeural",
    "it_IT": "it-IT-ElsaNeural",
    "fr": "fr-FR-DeniseNeural",
    "fr_FR": "fr-FR-DeniseNeural",
    "fr_CA": "fr-CA-SylvieNeural",
    "es": "es-ES-ElviraNeural",
    "es_ES": "es-ES-ElviraNeural",
    "es_MX": "es-MX-DaliaNeural",
    "de": "de-DE-KatjaNeural",
    "de_DE": "de-DE-KatjaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ru_RU": "ru-RU-SvetlanaNeural",
    "en": "en-US-JennyNeural",
    "en_US": "en-US-JennyNeural",
    "en_GB": "en-GB-SoniaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "pt_BR": "pt-BR-FranciscaNeural",
    "ja": "ja-JP-NanamiNeural",
    "ja_JP": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "zh_CN": "zh-CN-XiaoxiaoNeural",
    "uk": "uk-UA-PolinaNeural",
    "uk_UA": "uk-UA-PolinaNeural",
    "el": "el-GR-AthinaNeural",
    "el_GR": "el-GR-AthinaNeural",
    "ar": "ar-SA-ZariyahNeural",
    "he": "he-IL-HilaNeural",
    "nl": "nl-NL-ColetteNeural",
    "pl": "pl-PL-AgnieszkaNeural",
    "sv": "sv-SE-SofieNeural",
    "tr": "tr-TR-EmelNeural",
}

# --- Core Frequent Vocabulary Dictionaries ---

EN_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not",
    "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from",
    "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would",
    "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us", "say",
    "tell", "tells", "said", "saying", "speak", "speaks", "spoke", "spoken", "backpack",
    "pack", "rucksack", "school", "need", "needs", "needed", "better", "evidence", "hypothesis",
    "convincing", "courage", "truth", "public", "something", "diplomatic", "circumstances",
    "normal", "yes", "director", "same", "thing", "opposite", "contrary", "notice", "catch",
    "sight", "neighbor", "crowd", "people", "walk", "see", "hear", "listen", "find", "leave",
    "put", "keep", "let", "begin", "seem", "help", "talk", "turn", "start", "show", "hear",
    "play", "run", "move", "like", "live", "believe", "hold", "bring", "happen", "must",
    "write", "provide", "sit", "stand", "lose", "pay", "meet", "include", "continue",
    "set", "learn", "change", "lead", "understand", "watch", "follow", "stop", "create",
    "speak", "read", "allow", "add", "spend", "grow", "open", "walk", "win", "offer",
    "remember", "love", "consider", "appear", "buy", "wait", "serve", "die", "send",
    "expect", "build", "stay", "fall", "cut", "reach", "kill", "remain", "suggest",
    "raise", "pass", "sell", "require", "report", "decide", "pull", "free", "gloss",
}

IT_WORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "un'", "del", "dello",
    "della", "dei", "degli", "delle", "al", "allo", "alla", "ai", "agli", "alle",
    "dal", "dallo", "dalla", "dai", "dagli", "dalle", "nel", "nello", "nella", "nei",
    "negli", "nelle", "sul", "sullo", "sulla", "sui", "sugli", "sulle", "di", "a", "da",
    "in", "con", "su", "per", "tra", "fra", "e", "ed", "o", "od", "ma", "se", "perché",
    "perche", "perchè", "come", "quando", "dove", "che", "chi", "cui", "non", "più", "piu",
    "meno", "molto", "poco", "tanto", "tutto", "tutti", "tutte", "tutta", "niente", "nulla",
    "io", "tu", "lui", "lei", "noi", "voi", "loro", "mi", "ti", "si", "ci", "vi", "ne",
    "mio", "tuo", "suo", "nostro", "vostro", "loro", "mia", "tua", "sua", "nostra", "vostra",
    "miei", "tuoi", "suoi", "nostri", "vostri", "mie", "tue", "sue", "nostre", "vostre",
    "questo", "quello", "questa", "quella", "questi", "quelli", "queste", "quelle",
    "essere", "avere", "fare", "dire", "andare", "potere", "volere", "sapere", "stare",
    "dovere", "vedere", "venire", "dare", "parlare", "trovare", "sentire", "lasciare",
    "prendere", "mettere", "pensare", "capire", "finire", "preferire", "spedire",
    "ho", "hai", "ha", "abbiamo", "avete", "hanno", "sono", "sei", "è", "e", "siamo",
    "siete", "ero", "eri", "era", "eravamo", "eravate", "erano", "avevo", "avevi", "aveva",
    "avevamo", "avevate", "avevano", "fatto", "detto", "andato", "stato", "avuto",
    "direi", "diresti", "direbbe", "diremmo", "direste", "direbbero", "dovette", "ammettere",
    "bisogno", "zaino", "scuola", "ipotesi", "convincente", "coraggio", "verità", "verita",
    "pubblico", "qualcosa", "diplomatico", "circostanze", "normali", "davanti", "direttore",
    "stessa", "cosa", "prove", "migliori", "contrario", "buongiorno", "buonasera", "grazie",
    "mille", "prego", "arrivederci", "ciao", "piacere", "sempre", "adesso", "ora", "bene",
    "male", "meglio", "peggio", "ancora", "gia", "già", "anche", "proprio", "subito",
}

FR_WORDS = {
    "le", "la", "les", "l'", "un", "une", "des", "du", "de", "d'", "au", "aux", "à",
    "dans", "en", "par", "pour", "sur", "avec", "sans", "sous", "vers", "chez", "et",
    "ou", "mais", "donc", "car", "ni", "si", "que", "qu'", "quand", "comme", "comment",
    "où", "qui", "quoi", "dont", "ce", "cet", "cette", "ces", "ceci", "cela", "ça",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses", "notre", "votre", "leur",
    "nos", "vos", "leurs", "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "me", "te", "se", "lui", "leur", "y", "moi", "toi", "soi", "ne", "pas", "plus",
    "jamais", "rien", "personne", "être", "avoir", "faire", "dire", "aller", "voir",
    "savoir", "pouvoir", "falloir", "vouloir", "venir", "prendre", "croire", "aimer",
    "suis", "es", "est", "sommes", "êtes", "sont", "ai", "as", "a", "avons", "avez",
    "ont", "été", "eu", "fait", "dit", "apercevoir", "aperçu", "apercu", "voisin", "foule",
    "bonjour", "bonsoir", "merci", "beaucoup", "salut", "s'il", "plaît", "plait", "adieu",
    "très", "tres", "aussi", "bien", "mal", "mieux", "maintenant", "toujours", "déjà", "deja",
}

ES_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del", "de", "a",
    "en", "con", "por", "para", "sin", "sobre", "tras", "hacia", "desde", "hasta", "entre",
    "y", "e", "o", "u", "pero", "sino", "porque", "como", "cuando", "donde", "que",
    "qué", "quien", "quién", "cual", "cuál", "cuyo", "no", "sí", "si", "más", "mas",
    "menos", "muy", "mucho", "poco", "todo", "toda", "todos", "todas", "nada", "nadie",
    "yo", "tú", "él", "ella", "usted", "nosotros", "vosotros", "ellos", "ellas", "ustedes",
    "me", "te", "se", "nos", "os", "le", "les", "lo", "mi", "tu", "su", "mis", "tus", "sus",
    "nuestro", "vuestro", "este", "ese", "aquel", "esta", "esa", "aquella", "estos", "esos",
    "ser", "estar", "haber", "tener", "hacer", "decir", "ir", "ver", "dar", "saber",
    "poder", "querer", "llegar", "pasar", "deber", "poner", "parecer", "hablar", "seguir",
    "encontrar", "llamar", "venir", "pensar", "salir", "estudiar", "buenos", "días", "dias",
    "gracias", "muchas", "favor", "hola", "adiós", "adios", "hasta", "luego", "ahora",
    "siempre", "nunca", "bien", "mal", "también", "tambien",
}

DE_WORDS = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines", "einem",
    "einen", "im", "in", "an", "auf", "für", "fuer", "von", "mit", "zu", "nach", "bei",
    "über", "ueber", "unter", "vor", "zwischen", "durch", "gegen", "ohne", "um", "und",
    "oder", "aber", "denn", "doch", "weil", "wenn", "als", "wie", "dass", "daß", "ob",
    "wer", "was", "wo", "wann", "warum", "nicht", "kein", "keine", "keinem", "keinen",
    "keiner", "keines", "sehr", "mehr", "viel", "wenig", "alle", "alles", "nichts", "ich",
    "du", "er", "sie", "es", "wir", "ihr", "mich", "dich", "ihn", "uns", "euch", "ihnen",
    "mir", "dir", "ihm", "mein", "dein", "sein", "unser", "euer", "haben", "werden",
    "können", "koennen", "müssen", "muessen", "sagen", "machen", "geben", "kommen", "wollen",
    "gehen", "wissen", "sehen", "lassen", "stehen", "finden", "bleiben", "liegen", "heißen",
    "denken", "nehmen", "tun", "dürfen", "duerfen", "glauben", "halten", "nennen", "mögen",
    "moegen", "zeigen", "führen", "fuehren", "sprechen", "bringen", "leben", "fahren",
    "geschrieben", "schreiben", "guten", "morgen", "danke", "bitte", "tschüss", "auf",
    "wiedersehen", "immer", "jetzt", "schon", "auch", "sehr", "gut", "schlecht",
}

PT_WORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "pelo", "pela", "pelos", "pelas", "com",
    "sem", "sob", "sobre", "para", "pra", "e", "ou", "mas", "se", "porque", "porquê",
    "como", "quando", "onde", "que", "quem", "qual", "não", "nao", "sim", "mais",
    "menos", "muito", "pouco", "tudo", "nada", "ninguém", "ninguem", "eu", "tu", "ele",
    "ela", "você", "voce", "nós", "nos", "vós", "eles", "elas", "vocês", "voces", "me",
    "te", "se", "lhe", "lhes", "meu", "teu", "seu", "nosso", "este", "esse", "aquele",
    "esta", "essa", "aquela", "ser", "estar", "ter", "haver", "fazer", "dizer", "ir",
    "ver", "dar", "saber", "poder", "querer", "falar", "obrigado", "obrigada", "olá",
    "ola", "bom", "dia", "boa", "tarde", "noite", "amanhã", "amanha", "coração", "coracao",
}


def _strip_accents(text: str) -> str:
    """Normalize text removing accents for base vocabulary comparison."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def detect_language(text: str, context_lang: str | None = None) -> str:
    """Accurately detect language of the given text, using context_lang as an intelligent tie-breaker."""
    raw = text.strip()
    if not raw:
        return context_lang or "it"

    # --- 1. Non-Latin Script Checks (100% Deterministic) ---

    # Cyrillic
    if re.search(r"[\u0400-\u04FF]", raw):
        if re.search(r"[іїєґІЇЄҐ]", raw):
            return "uk"
        return "ru"

    # Japanese (Hiragana / Katakana)
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", raw):
        return "ja"

    # Korean (Hangul)
    if re.search(r"[\uAC00-\uD7AF\u1100-\u11FF]", raw):
        return "ko"

    # Greek
    if re.search(r"[\u0370-\u03FF]", raw):
        return "el"

    # Arabic
    if re.search(r"[\u0600-\u06FF]", raw):
        return "ar"

    # Hebrew
    if re.search(r"[\u0590-\u05FF]", raw):
        return "he"

    # CJK Ideographs without Japanese kana -> Chinese
    if re.search(r"[\u4E00-\u9FFF]", raw):
        return "zh"

    # --- 2. Latin-Script Statistical & Heuristic Scoring ---
    scores: dict[str, float] = {
        "en": 0.0,
        "it": 0.0,
        "fr": 0.0,
        "es": 0.0,
        "de": 0.0,
        "pt": 0.0,
    }

    low_raw = raw.lower()

    # Apply small context prior if specified
    if context_lang:
        c_short = context_lang.split("_")[0].split("-")[0].lower()
        if c_short in scores:
            scores[c_short] += 1.5

    # A. Distinctive Diacritics & Letter Combinations
    # Italian didactic accents: ò, ó, ì, ù, à, è, é
    scores["it"] += len(re.findall(r"[òóìù]", low_raw)) * 4.0
    scores["it"] += len(re.findall(r"[àèé]", low_raw)) * 1.5
    # Italian apostrophe elisions: un', dell', all', dall', nell', sull', quest', quell'
    scores["it"] += len(re.findall(r"\b(?:un|dell|all|dall|nell|sull|quest|quell)['’]", low_raw)) * 5.0
    # Italian double consonants: zz, bb, cc, dd, ff, gg, ll, mm, nn, pp, rr, ss, tt, vv
    scores["it"] += len(re.findall(r"(?:zz|tt|ll|ss|cc|pp|bb|mm|nn|ff|gg)", low_raw)) * 0.8
    # Italian specific diphthongs/trigrams: gl, gn, sc+e/i
    scores["it"] += len(re.findall(r"(?:gli|gno|gna|gne|gni|sce|sci)", low_raw)) * 1.5

    # French diacritics & ligatures: ç, œ, æ, â, ê, î, ô, û, ë, ï, ü
    scores["fr"] += len(re.findall(r"[çœæâêîôûëï]", low_raw)) * 5.0
    scores["fr"] += len(re.findall(r"[éèàù]", low_raw)) * 1.5
    # French apostrophe elisions: c', d', j', l', m', n', s', t', qu', lorsqu', puisqu'
    scores["fr"] += len(re.findall(r"\b(?:c|d|j|l|m|n|s|t|qu|lorsqu|puisqu)['’]", low_raw)) * 4.5
    # French letter endings / ngrams: eau, oux, eux, ois, ait, aient
    scores["fr"] += len(re.findall(r"(?:eau|oux|eux|ois|ait|aient|ent\b|eur\b|euse\b)", low_raw)) * 2.0

    # Spanish distinctive characters: ñ, ¿, ¡
    scores["es"] += len(re.findall(r"[ñ¿¡]", low_raw)) * 8.0
    scores["es"] += len(re.findall(r"[áíóú]", low_raw)) * 2.0
    scores["es"] += len(re.findall(r"(?:ción|ciones|mente|ando|iendo)\b", low_raw)) * 2.5
    scores["es"] += len(re.findall(r"(?:ll|rr|ch)", low_raw)) * 0.8

    # German distinctive characters: ß, ä, ö, ü
    scores["de"] += len(re.findall(r"ß", low_raw)) * 8.0
    scores["de"] += len(re.findall(r"[äöüÄÖÜ]", raw)) * 5.0
    # German ngrams & suffixes: sch, tsch, tz, pf, ung, keit, heit, schaft, lich, isch
    scores["de"] += len(re.findall(r"(?:sch|tsch|tz|pf)", low_raw)) * 2.0
    scores["de"] += len(re.findall(r"(?:ung|ungen|keit|heit|schaft|lich|isch|bar)\b", low_raw)) * 3.0

    # Portuguese distinctive characters: ã, õ
    scores["pt"] += len(re.findall(r"[ãõ]", low_raw)) * 8.0
    scores["pt"] += len(re.findall(r"(?:ção|ções|mente|ando|endo)\b", low_raw)) * 3.0

    # English ngrams & suffixes: th, wh, sh, ch, ing, ed, tion, ness, ly, ck
    scores["en"] += len(re.findall(r"\b(?:th|wh)", low_raw)) * 3.0
    scores["en"] += len(re.findall(r"(?:ing|ed|ness|ment|tion|ight|ought|ould|pack|back)\b", low_raw)) * 3.0
    scores["en"] += len(re.findall(r"(?:ck|sh|ch|ea|ee|oo)", low_raw)) * 0.7

    # B. Vocabulary & Word Matching
    tokens = re.findall(r"[a-zA-Zà-öù-žÀ-ÖÙ-Ž']+", low_raw)
    for tok in tokens:
        clean_tok = tok.strip("'’")
        stripped_tok = _strip_accents(clean_tok)

        # Exact token match in core vocabulary (strong +6.0 weighting)
        if clean_tok in EN_WORDS or stripped_tok in EN_WORDS:
            scores["en"] += 6.0
        if clean_tok in IT_WORDS or stripped_tok in IT_WORDS:
            scores["it"] += 6.0
        if clean_tok in FR_WORDS or stripped_tok in FR_WORDS:
            scores["fr"] += 6.0
        if clean_tok in ES_WORDS or stripped_tok in ES_WORDS:
            scores["es"] += 6.0
        if clean_tok in DE_WORDS or stripped_tok in DE_WORDS:
            scores["de"] += 6.0
        if clean_tok in PT_WORDS or stripped_tok in PT_WORDS:
            scores["pt"] += 6.0

        # Substring/stem matches for verbs
        # Italian verb endings
        if re.search(r"(?:are|ere|ire|eva|ava|ivano|avano|ebbe|ebbero|esti|emmo|este|ando|endo|ato|uto|ito)$", clean_tok):
            scores["it"] += 1.8
        # French verb endings
        if re.search(r"(?:er|ir|re|ait|aient|ant|ent)$", clean_tok):
            scores["fr"] += 1.2
        # Spanish verb endings
        if re.search(r"(?:ar|er|ir|aba|aban|ando|iendo|ado|ido)$", clean_tok):
            scores["es"] += 1.2

    # Pick highest score
    best_lang = max(scores, key=lambda k: scores[k])
    if scores[best_lang] <= 0:
        return context_lang or "it"

    return best_lang


def get_voice_for_text(text: str, context_lang: str | None = None, voice_override: str | None = None) -> str:
    """Determine the optimal dedicated neural voice for the provided text."""
    if voice_override:
        return voice_override

    detected = detect_language(text, context_lang=context_lang)
    return DEFAULT_VOICES.get(detected, DEFAULT_VOICES.get("it", "it-IT-ElsaNeural"))
