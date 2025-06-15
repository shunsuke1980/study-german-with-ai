#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Check API key first
if 'ANTHROPIC_API_KEY' not in os.environ:
    print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
    sys.exit(1)

if not os.environ['ANTHROPIC_API_KEY']:
    print("ERROR: ANTHROPIC_API_KEY is empty")
    sys.exit(1)
    
print(f"API Key found (length: {len(os.environ['ANTHROPIC_API_KEY'])})")

try:
    import anthropic
    print("Successfully imported anthropic module")
except ImportError as e:
    print(f"ERROR: Failed to import anthropic: {e}")
    sys.exit(1)

# 語彙管理クラス（ここに前回のVocabularyManagerが埋め込まれる）
class VocabularyManager:
    def __init__(self, data_dir="data/vocabulary"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.used_words_file = self.data_dir / "used_words.json"
        self.word_frequency_file = self.data_dir / "word_frequency.json"
        self.topics_used_file = self.data_dir / "topics_used.json"
        self.difficulty_levels_file = self.data_dir / "difficulty_levels.json"
        self.a2_target_words_file = self.data_dir / "a2_target_words.json"

        self.load_data()
        self.initialize_a2_target_words()

    def initialize_a2_target_words(self):
        """A2レベルの目標単語1,500語を初期化"""
        if not self.a2_target_words_file.exists():
            # A2レベルの基本語彙（実際のプロジェクトではドイツ語A2語彙リストを使用）
            a2_words = {
                # 家族・人間関係 (80語)
                "family": ["familie", "mutter", "vater", "kind", "sohn", "tochter", "bruder", "schwester", "eltern", "großmutter", "großvater", "baby", "freund", "freundin", "nachbar", "kollege", "chef", "lehrer", "schüler", "student"],

                # 身体・健康 (70語)
                "body": ["körper", "kopf", "auge", "nase", "mund", "ohr", "hand", "finger", "arm", "bein", "fuß", "herz", "gesundheit", "krankheit", "schmerz", "fieber", "erkältung", "arzt", "medikament", "sport"],

                # 食べ物・飲み物 (120語)
                "food": ["essen", "trinken", "brot", "käse", "fleisch", "fisch", "ei", "milch", "wasser", "kaffee", "tee", "bier", "wein", "apfel", "orange", "banane", "kartoffel", "reis", "nudeln", "salat", "suppe", "kuchen", "schokolade", "zucker", "salz", "pfeffer", "restaurant", "café", "küche", "kochen"],

                # 住居・家 (100語)
                "home": ["haus", "wohnung", "zimmer", "küche", "badezimmer", "schlafzimmer", "wohnzimmer", "bett", "tisch", "stuhl", "sofa", "fenster", "tür", "schlüssel", "telefon", "computer", "fernseher", "radio", "lampe", "buch", "zeitung", "garten", "balkon"],

                # 時間・日程 (80語)
                "time": ["zeit", "tag", "woche", "monat", "jahr", "heute", "gestern", "morgen", "montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag", "januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember", "uhr", "minute", "stunde", "früh", "spät", "pünktlich"],

                # 天気・自然 (60語)
                "weather": ["wetter", "sonne", "regen", "schnee", "wind", "warm", "kalt", "heiß", "kühl", "wolke", "himmel", "berg", "see", "fluss", "baum", "blume", "tier", "hund", "katze", "vogel", "park", "wald"],

                # 交通・旅行 (90語)
                "transport": ["auto", "bus", "zug", "flugzeug", "fahrrad", "straße", "bahnhof", "flughafen", "hotel", "reise", "urlaub", "koffer", "ticket", "fahren", "fliegen", "gehen", "laufen", "kommen", "ankommen", "abfahren", "links", "rechts", "geradeaus", "nah", "weit", "schnell", "langsam"],

                # 仕事・学校 (100語)
                "work": ["arbeit", "beruf", "büro", "firma", "geld", "euro", "bezahlen", "kaufen", "verkaufen", "geschäft", "markt", "bank", "post", "schule", "universität", "lernen", "studieren", "prüfung", "note", "buch", "heft", "stift", "computer", "internet", "e-mail"],

                # 服装・ショッピング (80語)
                "clothes": ["kleidung", "kleid", "hose", "hemd", "jacke", "mantel", "schuhe", "socken", "hut", "brille", "uhr", "ring", "tasche", "größe", "farbe", "rot", "blau", "grün", "gelb", "schwarz", "weiß", "grau", "braun", "neu", "alt", "schön", "hässlich", "groß", "klein"],

                # 感情・性格 (70語)
                "emotions": ["liebe", "freude", "angst", "trauer", "wut", "glück", "stress", "müde", "wach", "hungrig", "durstig", "satt", "zufrieden", "unzufrieden", "nervös", "ruhig", "fröhlich", "traurig", "böse", "nett", "freundlich", "hilfsbereit", "intelligent", "dumm", "fleißig", "faul"],

                # 基本動詞・形容詞 (200語)
                "basic": ["sein", "haben", "werden", "können", "müssen", "wollen", "sollen", "dürfen", "mögen", "geben", "nehmen", "machen", "tun", "sagen", "sprechen", "hören", "sehen", "verstehen", "wissen", "denken", "glauben", "finden", "suchen", "zeigen", "helfen", "arbeiten", "spielen", "schlafen", "essen", "trinken", "leben", "wohnen", "bleiben", "kommen", "gehen", "fahren", "lesen", "schreiben", "gut", "schlecht", "richtig", "falsch", "wichtig", "interessant", "langweilig", "einfach", "schwer", "möglich", "unmöglich"],

                # 数字・量 (50語)
                "numbers": ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn", "zwanzig", "dreißig", "vierzig", "fünfzig", "hundert", "tausend", "viel", "wenig", "alle", "nichts", "etwas"],

                # その他日常語彙 (170語)
                "misc": ["ja", "nein", "bitte", "danke", "entschuldigung", "hallo", "tschüss", "auf wiedersehen", "wie", "was", "wer", "wo", "wann", "warum", "welche", "hier", "dort", "da", "nur", "auch", "noch", "schon", "wieder", "immer", "nie", "oft", "manchmal", "vielleicht", "sicher", "natürlich", "problem", "lösung", "idee", "plan", "ziel", "wunsch", "hoffnung", "chance", "erfolg", "fehler", "grund", "beispiel", "frage", "antwort", "information", "nachricht", "brief", "paket", "geschenk", "party", "fest", "musik", "film", "foto", "spiel", "sport", "hobby", "interesse"]
            }

            # 全単語をフラットなリストに変換
            all_a2_words = []
            for category, words in a2_words.items():
                all_a2_words.extend(words)

            # 重複除去して1,500語に調整
            unique_words = list(set(all_a2_words))[:1500]

            target_data = {
                "total_target_words": len(unique_words),
                "words_by_category": a2_words,
                "all_words": unique_words,
                "words_learned": [],
                "learning_progress": 0.0
            }

            self._save_json(target_data, self.a2_target_words_file)
            self.a2_target_words = target_data
        else:
            self.a2_target_words = self._load_json(self.a2_target_words_file, {})

    def load_data(self):
        """既存データを読み込み"""
        self.used_words = self._load_json(self.used_words_file, {})
        self.word_frequency = self._load_json(self.word_frequency_file, {})
        self.topics_used = self._load_json(self.topics_used_file, [])
        self.difficulty_levels = self._load_json(self.difficulty_levels_file, {
            "current_level": "B1",
            "level_progression": [],
            "grammar_patterns_used": []
        })

    def _load_json(self, file_path, default):
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def _save_json(self, data, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def extract_words(self, text):
        """ドイツ語単語を抽出し、レベル分類"""
        german_word_pattern = r'\b[a-zA-ZäöüÄÖÜß]+\b'
        words = re.findall(german_word_pattern, text.lower())

        # 基本的なストップワード除去
        stop_words = {'der', 'die', 'das', 'und', 'oder', 'aber', 'ist', 'sind',
                     'war', 'waren', 'hat', 'haben', 'wird', 'werden', 'kann',
                     'könnte', 'ein', 'eine', 'einen', 'einem', 'einer', 'zu',
                     'von', 'mit', 'für', 'auf', 'in', 'an', 'bei', 'nach',
                     'vor', 'über', 'auch', 'nicht', 'nur', 'noch', 'wie', 'wenn'}

        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]
        return filtered_words

    def categorize_word_level(self, word):
        """単語のCEFRレベルを推定（簡易版）"""
        # 実際のプロジェクトでは、ドイツ語語彙データベースを使用
        if len(word) <= 5:
            return "A1"
        elif len(word) <= 8:
            return "A2"
        elif len(word) <= 12:
            return "B1"
        else:
            return "B2"

    def get_current_difficulty_level(self):
        """現在の学習レベルを取得（常にA2固定）"""
        return "A2"

    def update_vocabulary(self, text, date_str):
        """語彙データを更新し、A2進捗を追跡"""
        words = self.extract_words(text)

        if date_str not in self.used_words:
            self.used_words[date_str] = []

        # A2目標単語との照合
        new_a2_words_learned = []
        word_analysis = []

        for word in words:
            level = self.categorize_word_level(word)
            word_analysis.append({"word": word, "level": level})
            self.word_frequency[word] = self.word_frequency.get(word, 0) + 1

            # A2目標語彙に含まれているかチェック
            if word in self.a2_target_words["all_words"] and word not in self.a2_target_words["words_learned"]:
                self.a2_target_words["words_learned"].append(word)
                new_a2_words_learned.append(word)

        self.used_words[date_str] = word_analysis

        # 進捗率更新
        self.a2_target_words["learning_progress"] = len(self.a2_target_words["words_learned"]) / self.a2_target_words["total_target_words"] * 100

        # 難易度レベル更新
        self.difficulty_levels["current_level"] = "A2"
        self.difficulty_levels["level_progression"].append({
            "date": date_str,
            "level": "A2",
            "unique_words": len(set(words)),
            "a2_words_learned": len(new_a2_words_learned),
            "total_a2_progress": round(self.a2_target_words["learning_progress"], 2)
        })

        self.save_data()
        return words, new_a2_words_learned

    def get_recent_words(self, days=7):
        """最近使用した単語を取得"""
        recent_words = set()
        today = datetime.now()

        for date_str, word_data in self.used_words.items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if (today - date).days <= days:
                    if isinstance(word_data, list) and len(word_data) > 0:
                        if isinstance(word_data[0], dict):
                            recent_words.update([item["word"] for item in word_data])
                        else:
                            recent_words.update(word_data)
            except (ValueError, KeyError):
                continue

        return recent_words

    def get_overused_words(self, threshold=3):
        """使いすぎている単語を取得"""
        return {word: count for word, count in self.word_frequency.items()
                if count >= threshold}

    def generate_avoid_list(self):
        """90-120日で1,500語カバーを目指すスマート回避リスト"""
        total_days = len(self.used_words)
        target_words_per_day = 1500 / 120  # 約12.5語/日
        words_learned = len(self.a2_target_words["words_learned"])

        # 進捗に応じた動的調整
        if total_days > 0:
            current_pace = words_learned / total_days
            target_pace = 1500 / 120

            if current_pace < target_pace * 0.8:  # 進捗が遅い場合
                # より積極的に新語彙を導入（回避を緩める）
                recent_days = 3
                frequency_threshold = 4
            elif current_pace > target_pace * 1.2:  # 進捗が早い場合
                # 復習重視（回避を厳しく）
                recent_days = 14
                frequency_threshold = 2
            else:  # 適正ペース
                recent_days = 7
                frequency_threshold = 3
        else:
            recent_days = 7
            frequency_threshold = 3

        # 段階的回避リスト生成
        overused = set(self.get_overused_words(threshold=frequency_threshold).keys())
        recent = self.get_recent_words(days=recent_days)

        # 未学習のA2単語を優先的に含めるよう調整
        unlearned_a2_words = set(self.a2_target_words["all_words"]) - set(self.a2_target_words["words_learned"])

        # 回避リストから未学習A2単語を除外
        avoid_list = list((overused.union(recent)) - unlearned_a2_words)

        return avoid_list[:60]  # 最大60語に制限（Claude APIの制限考慮）

    def get_unused_topics(self):
        """未使用トピックを取得（A2レベルのみ）"""
        a2_topics = [
            "Familie und Freunde", "Essen und Trinken", "Einkaufen und Geschäfte",
            "Wohnen und Hausarbeit", "Tagesablauf und Routine", "Wetter und Jahreszeiten",
            "Verkehrsmittel und Reisen", "Kleidung und Mode", "Körper und Gesundheit",
            "Schule und Bildung", "Arbeit und Beruf", "Hobbys und Freizeit",
            "Stadt und Land", "Restaurants und Cafés", "Sport und Bewegung",
            "Feste und Feiertage", "Tiere und Natur", "Technologie im Alltag",
            "Geld und Preise", "Zeit und Termine", "Gefühle und Emotionen",
            "Nachbarn und Gemeinschaft", "Arztbesuch und Apotheke", "Öffentliche Verkehrsmittel"
        ]

        # 最近使用されたトピック除外（期間を短縮して多様性を確保）
        recent_topics = set()
        today = datetime.now()
        for topic_entry in self.topics_used:
            try:
                date = datetime.strptime(topic_entry['date'], '%Y-%m-%d')
                if (today - date).days <= 7:  # 1週間に短縮
                    recent_topics.add(topic_entry['topic'])
            except (ValueError, KeyError):
                continue

        return [topic for topic in a2_topics if topic not in recent_topics]

    def add_used_topic(self, topic, date_str):
        """使用済みトピックを追加"""
        self.topics_used.append({
            'topic': topic,
            'date': date_str,
            'level': "A2"  # 常にA2固定
        })
        self.save_data()

    def save_data(self):
        """全データを保存"""
        self._save_json(self.used_words, self.used_words_file)
        self._save_json(self.word_frequency, self.word_frequency_file)
        self._save_json(self.topics_used, self.topics_used_file)
        self._save_json(self.difficulty_levels, self.difficulty_levels_file)
        self._save_json(self.a2_target_words, self.a2_target_words_file)

    def generate_unique_title(self, topic):
        """重複しないユニークなタイトルを生成"""
        # 既存のタイトルを取得
        existing_titles = set()
        blog_dir = Path("blog")
        if blog_dir.exists():
            for file_path in blog_dir.glob("*.md"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.startswith('---'):
                            yaml_end = content.find('---', 3)
                            if yaml_end != -1:
                                yaml_content = content[3:yaml_end]
                                for line in yaml_content.split('\n'):
                                    if line.strip().startswith('title:'):
                                        title = line.split('title:', 1)[1].strip().strip('"\'')
                                        existing_titles.add(title)
                except:
                    continue

        # ベースタイトル
        base_title = f"[A2] {topic}"

        # 重複チェックとユニーク化
        if base_title not in existing_titles:
            return base_title

        # 重複している場合、バリエーションを生成
        topic_variations = {
            "Familie und Freunde": ["Familienleben", "Meine Familie", "Freundschaft", "Verwandte"],
            "Essen und Trinken": ["Lieblingsessen", "Kochen", "Restaurant", "Getränke", "Mahlzeiten"],
            "Einkaufen und Geschäfte": ["Shopping", "Supermarkt", "Kleiderkauf", "Markt"],
            "Wohnen und Hausarbeit": ["Mein Zuhause", "Hausarbeit", "Wohnungssuche", "Möbel"],
            "Tagesablauf und Routine": ["Mein Tag", "Morgendliche Routine", "Arbeitsalltag", "Wochenende"],
            "Wetter und Jahreszeiten": ["Heute ist schönes Wetter", "Frühling", "Winter", "Sommer", "Herbst"],
            "Verkehrsmittel und Reisen": ["Mit dem Bus fahren", "Urlaubsreise", "Bahnfahrt", "Flugzeug"],
            "Kleidung und Mode": ["Was ziehe ich an?", "Neue Kleidung", "Modetrends", "Schuhe"],
            "Körper und Gesundheit": ["Beim Arzt", "Sport treiben", "Gesund leben", "Krankheit"],
            "Schule und Bildung": ["In der Schule", "Deutschlernen", "Prüfungen", "Universität"],
            "Arbeit und Beruf": ["Mein Job", "Im Büro", "Arbeitssuche", "Kollegen"],
            "Hobbys und Freizeit": ["Meine Hobbys", "Wochenendaktivitäten", "Sport", "Musik hören"],
            "Stadt und Land": ["Stadtleben", "Auf dem Land", "Meine Stadt", "Dorfbesuch"],
            "Restaurants und Cafés": ["Im Restaurant", "Café-Besuch", "Bestellung", "Rechnung zahlen"],
            "Sport und Bewegung": ["Fitness", "Fußball spielen", "Schwimmen", "Wandern"],
            "Feste und Feiertage": ["Geburtstag feiern", "Weihnachten", "Ostern", "Hochzeit"],
            "Tiere und Natur": ["Haustiere", "Im Zoo", "Waldspaziergang", "Blumen"],
            "Technologie im Alltag": ["Handy benutzen", "Computer", "Internet", "Social Media"],
            "Geld und Preise": ["Beim Einkaufen", "Bank", "Sparen", "Preise vergleichen"],
            "Zeit und Termine": ["Terminplanung", "Uhrzeiten", "Kalender", "Pünktlichkeit"],
            "Gefühle und Emotionen": ["Wie ich mich fühle", "Glücklich sein", "Traurige Momente", "Stress"],
            "Nachbarn und Gemeinschaft": ["Nachbarschaft", "Freiwilligenarbeit", "Gemeinsam helfen", "Straßenfest"],
            "Arztbesuch und Apotheke": ["Termin beim Arzt", "In der Apotheke", "Medikamente", "Gesundheitscheck"],
            "Öffentliche Verkehrsmittel": ["U-Bahn fahren", "Busticket kaufen", "Zugverspätung", "Fahrplan lesen"]
        }

        variations = topic_variations.get(topic, [f"Teil {i}" for i in range(1, 6)])

        for variation in variations:
            candidate_title = f"[A2] {variation}"
            if candidate_title not in existing_titles:
                return candidate_title

        # すべて使用済みの場合、日付を追加
        today = datetime.now().strftime('%m-%d')
        return f"[A2] {topic} ({today})"

    def generate_daily_vocabulary_report(self):
        """毎日の語彙使用レポート生成（A2進捗含む）"""
        today = datetime.now()

        # 全体統計
        total_unique_words = len(self.word_frequency)
        total_words_used = sum(self.word_frequency.values())

        # A2進捗統計
        a2_words_learned = len(self.a2_target_words["words_learned"])
        a2_progress_percent = self.a2_target_words["learning_progress"]
        remaining_a2_words = self.a2_target_words["total_target_words"] - a2_words_learned

        # 学習ペース計算
        total_days = len(self.used_words)
        if total_days > 0:
            words_per_day = a2_words_learned / total_days
            estimated_days_to_complete = remaining_a2_words / max(words_per_day, 1)
        else:
            words_per_day = 0
            estimated_days_to_complete = 0

        # 最も使用頻度の高い単語トップ10
        most_common = sorted(self.word_frequency.items(),
                           key=lambda x: x[1], reverse=True)[:10]

        # 最近の語彙多様性（過去7日間）
        recent_unique_words = len(self.get_recent_words(days=7))

        # 過度に使用されている単語
        overused_words = self.get_overused_words(threshold=2)

        return {
            "date": today.strftime('%Y-%m-%d'),
            "total_unique_words": total_unique_words,
            "total_words_used": total_words_used,
            "recent_unique_words": recent_unique_words,
            "most_common_words": most_common,
            "overused_words": len(overused_words),
            "vocabulary_diversity_score": round(total_unique_words / max(total_words_used, 1) * 100, 2),
            "a2_progress": {
                "words_learned": a2_words_learned,
                "total_target": self.a2_target_words["total_target_words"],
                "progress_percent": round(a2_progress_percent, 2),
                "remaining_words": remaining_a2_words,
                "daily_pace": round(words_per_day, 2),
                "estimated_completion_days": round(estimated_days_to_complete, 0)
            }
        }

# メイン処理
def main():
    print("🚀 Starting German content generation...")

    # 語彙管理の初期化
    vocab_manager = VocabularyManager()

    # 今日の日付
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Generating content for: {today}")

    # 現在の学習レベルを取得
    current_level = vocab_manager.difficulty_levels["current_level"]
    print(f"🎯 Current difficulty level: {current_level}")

    # 回避すべき単語とトピック選択
    avoid_words = vocab_manager.generate_avoid_list()
    available_topics = vocab_manager.get_unused_topics()

    if not available_topics:
        # 全トピック使用済みの場合はリセット
        print("♻️  Resetting topics - all topics used recently")
        vocab_manager.topics_used = []
        available_topics = vocab_manager.get_unused_topics()

    selected_topic = available_topics[0] if available_topics else "Alltägliches Leben"
    print(f"📝 Selected topic: {selected_topic}")
    print(f"🚫 Avoiding {len(avoid_words)} recently used words")

    # レベル別プロンプト調整（A2固定）
    level_instructions = "Verwende einfache Sätze und grundlegende A2-Vocabulary. Vermeide komplexe Grammatik. Fokussiere dich auf alltägliche Situationen und praktische Vokabeln."

    # Claudeへのプロンプト作成（1,500語A2カバレッジ重視）
    a2_progress = vocab_manager.a2_target_words["learning_progress"]
    words_learned = len(vocab_manager.a2_target_words["words_learned"])
    target_words = vocab_manager.a2_target_words["total_target_words"]

    # Build avoid words string safely
    avoid_words_str = ", ".join(avoid_words) if avoid_words else "Keine spezifischen Wörter zu vermeiden"
    
    # Build prompt using string concatenation to avoid YAML issues
    prompt = "Schreibe einen interessanten deutschen Text zum Thema '" + selected_topic + "'.\n\n"
    prompt += "Anforderungen:\n"
    prompt += "- Genau 300 Wörter\n"
    prompt += "- Niveau A2 (Grundlegendes Deutsch)\n"
    prompt += "- " + level_instructions + "\n"
    prompt += "- Natürlicher fließender Schreibstil\n"
    prompt += "- ZIEL Neue A2-Vokabeln einführen (Fortschritt " + str(words_learned) + "/" + str(target_words) + " entspricht " + str(round(a2_progress, 1)) + " Prozent)\n\n"
    prompt += "WICHTIG für A2-Vokabular:\n"
    prompt += "- Verwende grundlegende Alltagsvokabeln\n"
    prompt += "- Fokussiere auf praktische nützliche Wörter\n"
    prompt += "- Vermeide zu einfache Wörter wie der die das und ist\n"
    prompt += "- Bevorzuge Substantive Verben und Adjektive des täglichen Lebens\n\n"
    prompt += "Vermeide diese bereits verwendeten Wörter:\n"
    prompt += avoid_words_str + "\n\n"
    prompt += "STRATEGISCHES ZIEL Hilf beim Erreichen des A2-Vokabulars von 1500 Wörtern in 120 Tagen.\n"
    prompt += "Verwende für jedes Konzept verschiedene Ausdrucksweisen und Synonyme.\n\n"
    prompt += "Der Text soll für A2-Deutschlernende interessant sein und viele neue praktische Vokabeln enthalten.\n"
    prompt += "Schreibe nur den deutschen Text keine zusätzlichen Erklärungen."

    print("🤖 Calling Claude API...")

    # Anthropic API呼び出し
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        generated_text = message.content[0].text.strip()
        print(f"✅ Generated {len(generated_text.split())} words")

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return

    # 語彙データの更新
    print("📊 Updating vocabulary database...")
    new_words, new_a2_words = vocab_manager.update_vocabulary(generated_text, today)
    vocab_manager.add_used_topic(selected_topic, today)

    # ユニークなタイトル生成
    unique_title = vocab_manager.generate_unique_title(selected_topic)

    # 毎日の語彙統計生成
    print("📊 Generating daily vocabulary statistics...")
    daily_report = vocab_manager.generate_daily_vocabulary_report()

    # ブログファイル作成
    blog_dir = Path("blog")
    blog_dir.mkdir(exist_ok=True)

    # 語彙統計の計算
    word_stats = {
        "total_words": len(generated_text.split()),
        "unique_new_words": len(set(new_words)),
        "new_a2_words": len(new_a2_words),
        "difficulty_level": "A2",
        "a2_progress": daily_report["a2_progress"]
    }

    # Build blog content using string concatenation
    new_a2_words_str = ', '.join(new_a2_words) if new_a2_words else 'Keine neuen A2-Zielwörter erkannt'
    
    blog_content = "---\n"
    blog_content += 'title: "' + unique_title + '"\n'
    blog_content += "date: " + today + "\n"
    blog_content += 'topic: "' + selected_topic + '"\n'
    blog_content += 'difficulty_level: "A2"\n'
    blog_content += "word_count: " + str(word_stats["total_words"]) + "\n"
    blog_content += "unique_words: " + str(word_stats["unique_new_words"]) + "\n"
    blog_content += "new_a2_words: " + str(word_stats["new_a2_words"]) + "\n"
    blog_content += "a2_progress_percent: " + str(word_stats["a2_progress"]["progress_percent"]) + "\n"
    blog_content += "estimated_completion_days: " + str(word_stats["a2_progress"]["estimated_completion_days"]) + "\n"
    blog_content += "generated: true\n"
    blog_content += "---\n\n"
    blog_content += generated_text + "\n\n"
    blog_content += "---\n\n"
    blog_content += "**📚 A2-Lernfortschritt:**\n"
    blog_content += "- **Neue A2-Wörter heute**: " + str(word_stats["new_a2_words"]) + "\n"
    blog_content += "- **A2-Wörter gelernt**: " + str(word_stats["a2_progress"]["words_learned"]) + "/" + str(word_stats["a2_progress"]["total_target"]) + " (" + str(word_stats["a2_progress"]["progress_percent"]) + "%)\n"
    blog_content += "- **Verbleibende Wörter**: " + str(word_stats["a2_progress"]["remaining_words"]) + "\n"
    blog_content += "- **Lerntempo**: " + str(word_stats["a2_progress"]["daily_pace"]) + " Wörter/Tag\n"
    blog_content += "- **Geschätzte Restzeit**: " + str(word_stats["a2_progress"]["estimated_completion_days"]) + " Tage\n\n"
    blog_content += "**📊 Tagesstatistiken:**\n"
    blog_content += "- Wortanzahl: " + str(word_stats["total_words"]) + "\n"
    blog_content += "- Einzigartige neue Wörter: " + str(word_stats["unique_new_words"]) + "\n"
    blog_content += "- Thema: " + selected_topic + "\n\n"
    blog_content += "**🎯 Neue A2-Vokabeln heute:**\n"
    blog_content += new_a2_words_str + "\n\n"
    blog_content += "---\n\n"
    blog_content += "**📖 Sprachhilfen / Language Support:**\n"
    blog_content += "- 🇯🇵 [日本語解説 / Japanese Explanation](" + today + "-jp.md)\n"
    blog_content += "- 🇺🇸 [English Explanation](" + today + "-en.md)\n"

    blog_file = blog_dir / (today + ".md")
    with open(blog_file, 'w', encoding='utf-8') as f:
        f.write(blog_content)

    print("📄 Main blog post created: " + str(blog_file))

    # 日本語解説記事の生成
    print("🇯🇵 Generating Japanese explanation...")

    # Build Japanese explanation prompt using string concatenation
    japanese_explanation_prompt = "Create a detailed Japanese explanation article for A2 German learners based on this German text:\n\n"
    japanese_explanation_prompt += "GERMAN TEXT:\n"
    japanese_explanation_prompt += generated_text + "\n\n"
    japanese_explanation_prompt += "TOPIC: " + selected_topic + "\n"
    japanese_explanation_prompt += "NEW A2 WORDS: " + ', '.join(new_a2_words) + "\n\n"
    japanese_explanation_prompt += "Please create a comprehensive Japanese explanation article that includes:\n\n"
    japanese_explanation_prompt += "1. 🎯 **今日の学習目標** - Learning objectives for the day\n"
    japanese_explanation_prompt += "2. 📖 **重要語彙解説** - Detailed vocabulary explanation with:\n"
    japanese_explanation_prompt += "   - Category grouping (家族関係, 職業, 性格・態度, 活動 etc.)\n"
    japanese_explanation_prompt += "   - Pronunciation in katakana\n"
    japanese_explanation_prompt += "   - Example sentences\n"
    japanese_explanation_prompt += "   - Grammar notes for each word\n"
    japanese_explanation_prompt += "3. 📝 **重要文法ポイント** - Important grammar points from the text with:\n"
    japanese_explanation_prompt += "   - Examples extracted from the original text\n"
    japanese_explanation_prompt += "   - Detailed explanations of case changes, verb conjugations\n"
    japanese_explanation_prompt += "   - Tables showing declensions where relevant\n"
    japanese_explanation_prompt += "4. 🗣️ **実用フレーズ** - Practical phrases related to the topic\n\n"
    japanese_explanation_prompt += "Format the article in markdown with proper headers, tables, and clear structure.\n"
    japanese_explanation_prompt += "Focus on A2-level grammar and vocabulary that Japanese learners need.\n"
    japanese_explanation_prompt += "Write everything in Japanese.\n"
    japanese_explanation_prompt += "Do not include practice questions, study tips, or homework sections."

    try:
        jp_message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": japanese_explanation_prompt}]
        )

        japanese_explanation = jp_message.content[0].text.strip()

        # 日本語解説記事のメタデータ
        jp_blog_content = "---\n"
        jp_blog_content += 'title: "' + unique_title + ' - 日本語解説"\n'
        jp_blog_content += "date: " + today + "\n"
        jp_blog_content += 'topic: "' + selected_topic + '"\n'
        jp_blog_content += 'type: "japanese_explanation"\n'
        jp_blog_content += 'difficulty_level: "A2"\n'
        jp_blog_content += 'original_post: "' + today + '.md"\n'
        jp_blog_content += "---\n\n"
        jp_blog_content += "# 📚 A2解説: " + selected_topic + "\n\n"
        jp_blog_content += "**原文記事**: [" + unique_title + "](" + today + ".md)\n\n"
        jp_blog_content += "---\n\n"
        jp_blog_content += japanese_explanation + "\n"

        jp_blog_file = blog_dir / (today + "-jp.md")
        with open(jp_blog_file, 'w', encoding='utf-8') as f:
            f.write(jp_blog_content)

        print("📄 Japanese explanation created: " + str(jp_blog_file))

    except Exception as e:
        print(f"❌ Error generating Japanese explanation: {e}")

    # 英語解説記事の生成
    print("🇺🇸 Generating English explanation...")

    english_explanation_prompt = "Create a detailed English explanation article for A2 German learners based on this German text:\n\n"
    english_explanation_prompt += "GERMAN TEXT:\n"
    english_explanation_prompt += generated_text + "\n\n"
    english_explanation_prompt += "TOPIC: " + selected_topic + "\n"
    english_explanation_prompt += "NEW A2 WORDS: " + ', '.join(new_a2_words) + "\n\n"
    english_explanation_prompt += "Please create a comprehensive English explanation article that includes:\n\n"
    english_explanation_prompt += "1. 🎯 **Today's Learning Goals** - Learning objectives for the day\n"
    english_explanation_prompt += "2. 📖 **Key Vocabulary Analysis** - Detailed vocabulary explanation with:\n"
    english_explanation_prompt += "   - Category grouping (Family relationships, Professions, Character traits, Activities etc.)\n"
    english_explanation_prompt += "   - Pronunciation guide in IPA or simple phonetics\n"
    english_explanation_prompt += "   - Example sentences\n"
    english_explanation_prompt += "   - Grammar notes and word formation\n"
    english_explanation_prompt += "3. 📝 **Important Grammar Points** - Important grammar points from the text with:\n"
    english_explanation_prompt += "   - Examples extracted from the original text\n"
    english_explanation_prompt += "   - Detailed explanations of case changes, verb conjugations\n"
    english_explanation_prompt += "   - Tables showing declensions where relevant\n"
    english_explanation_prompt += "4. 🗣️ **Useful Phrases** - Practical phrases related to the topic with translations\n\n"
    english_explanation_prompt += "Format the article in markdown with proper headers, tables, and clear structure.\n"
    english_explanation_prompt += "Focus on A2-level grammar and vocabulary explanations for English speakers learning German.\n"
    english_explanation_prompt += "Write everything in clear, educational English.\n"
    english_explanation_prompt += "Do not include practice exercises, study tips, or homework sections."

    try:
        en_message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": english_explanation_prompt}]
        )

        english_explanation = en_message.content[0].text.strip()

        # 英語解説記事のメタデータ
        en_blog_content = "---\n"
        en_blog_content += 'title: "' + unique_title + ' - English Explanation"\n'
        en_blog_content += "date: " + today + "\n"
        en_blog_content += 'topic: "' + selected_topic + '"\n'
        en_blog_content += 'type: "english_explanation"\n'
        en_blog_content += 'difficulty_level: "A2"\n'
        en_blog_content += 'original_post: "' + today + '.md"\n'
        en_blog_content += "---\n\n"
        en_blog_content += "# 📚 A2 German Study Guide: " + selected_topic + "\n\n"
        en_blog_content += "**Original Article**: [" + unique_title + "](" + today + ".md)\n\n"
        en_blog_content += "---\n\n"
        en_blog_content += english_explanation + "\n"

        en_blog_file = blog_dir / (today + "-en.md")
        with open(en_blog_file, 'w', encoding='utf-8') as f:
            f.write(en_blog_content)

        print("📄 English explanation created: " + str(en_blog_file))

    except Exception as e:
        print(f"❌ Error generating English explanation: {e}")
        
    print("🎯 Title: " + unique_title)
    print("📈 New A2 words learned: " + str(len(new_a2_words)))
    print("📚 A2 Progress: " + str(daily_report['a2_progress']['words_learned']) + "/" + str(daily_report['a2_progress']['total_target']) + " (" + str(daily_report['a2_progress']['progress_percent']) + "%)")
    print("⏱️  Estimated completion: " + str(daily_report['a2_progress']['estimated_completion_days']) + " days")
    print("🇯🇵 Japanese explanation: " + today + "-jp.md")
    print("🇺🇸 English explanation: " + today + "-en.md")

    # A2進捗チェックと調整提案
    if daily_report["a2_progress"]["estimated_completion_days"] > 150:
        print("⚠️  WARNING: A2 completion may take longer than 120 days! Increasing vocabulary focus.")
    elif daily_report["a2_progress"]["estimated_completion_days"] < 90:
        print("🚀 EXCELLENT: On track to complete A2 vocabulary ahead of schedule!")
    else:
        print("✅ GOOD: A2 vocabulary completion on target for ~120 days")

    # 毎日の語彙レポートをJSONファイルとして保存
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    daily_report_file = reports_dir / (today + "-vocabulary-report.json")
    with open(daily_report_file, 'w', encoding='utf-8') as f:
        json.dump(daily_report, f, ensure_ascii=False, indent=2)

    print("📋 Daily vocabulary report saved: " + str(daily_report_file))

    # 週次A2進捗レポート生成（日曜日のみ）
    if datetime.now().weekday() == 6:  # Sunday
        print("📊 Generating weekly A2 progress summary...")

        # 過去7日間のA2学習統計
        week_a2_stats = {
            "week_ending": today,
            "a2_words_learned_total": daily_report["a2_progress"]["words_learned"],
            "a2_progress_percent": daily_report["a2_progress"]["progress_percent"],
            "estimated_completion": daily_report["a2_progress"]["estimated_completion_days"],
            "daily_pace": daily_report["a2_progress"]["daily_pace"],
            "remaining_words": daily_report["a2_progress"]["remaining_words"]
        }

        weekly_summary = "---\n"
        weekly_summary += 'title: "[A2] Wöchentlicher Fortschrittsbericht"\n'
        weekly_summary += "date: " + today + "\n"
        weekly_summary += 'type: "weekly_progress_report"\n'
        weekly_summary += "---\n\n"
        weekly_summary += "# 📊 Wöchentlicher A2-Deutschlern-Fortschritt\n\n"
        weekly_summary += "## 🎯 A2-Vokabular Fortschritt\n"
        weekly_summary += "- **Gelernte A2-Wörter**: " + str(week_a2_stats["a2_words_learned_total"]) + "/1.500 (" + str(week_a2_stats["a2_progress_percent"]) + "%)\n"
        weekly_summary += "- **Verbleibende Wörter**: " + str(week_a2_stats["remaining_words"]) + "\n"
        weekly_summary += "- **Aktuelles Lerntempo**: " + str(round(week_a2_stats["daily_pace"], 1)) + " neue A2-Wörter pro Tag\n"
        weekly_summary += "- **Geschätzte Restzeit**: " + str(week_a2_stats["estimated_completion"]) + " Tage\n\n"
        weekly_summary += "## 📈 Leistungsbeurteilung\n"
        
        if week_a2_stats["estimated_completion"] < 90:
            weekly_summary += "🚀 Ausgezeichnet! Vor dem Zeitplan.\n\n"
        elif week_a2_stats["estimated_completion"] <= 130:
            weekly_summary += "✅ Gut! Im Zeitplan für ~120 Tage.\n\n"
        else:
            weekly_summary += "⚠️ Achtung: Möglicherweise länger als 120 Tage.\n\n"
            
        weekly_summary += "## 🎪 Empfehlungen\n"
        weekly_summary += "- Fokus auf alltägliche Substantive und Verben\n"
        weekly_summary += "- Vermeidung bereits häufig verwendeter Wörter\n"
        weekly_summary += "- Gezieltes Lernen spezifischer A2-Themenbereiche\n"
        weekly_summary += "- Regelmäßige Wiederholung neuer Vokabeln\n"

        weekly_file = blog_dir / (today + "-weekly-a2-progress.md")
        with open(weekly_file, 'w', encoding='utf-8') as f:
            f.write(weekly_summary)
        print("📋 Weekly A2 progress report created: " + str(weekly_file))

if __name__ == "__main__":
    main()