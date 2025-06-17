#!/usr/bin/env python3
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path
import glob

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

def generate_jekyll_filename(title, date_str, suffix=""):
    """Jekyll形式のファイル名を生成 (YYYY-MM-DD-title-with-dashes.md)"""
    # タイトルをURLフレンドリーに変換
    clean_title = title.lower()

    # ドイツ語特殊文字の変換
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
    }

    for old, new in replacements.items():
        clean_title = clean_title.replace(old, new)

    # 英数字とハイフンのみ残す
    clean_title = re.sub(r'[^a-z0-9\s-]', '', clean_title)

    # スペースをハイフンに変換、連続するハイフンを単一化
    clean_title = re.sub(r'\s+', '-', clean_title.strip())
    clean_title = re.sub(r'-+', '-', clean_title)
    clean_title = clean_title.strip('-')

    # ファイル名を組み立て
    if suffix:
        filename = f"{date_str}-{clean_title}-{suffix}.md"
    else:
        filename = f"{date_str}-{clean_title}.md"

    return filename

def get_latest_word_file():
    """Get the most recently modified word file from data/words/"""
    word_files = glob.glob("data/words/*.txt")

    if not word_files:
        print("No word files found in data/words/")
        return None, None, None

    # Get the most recently modified file
    latest_file = max(word_files, key=os.path.getmtime)

    # Extract level and number from filename (e.g., A2_1.txt -> A2, 1)
    filename = os.path.basename(latest_file)
    match = re.match(r'([A-C][1-2])_(\d+)\.txt', filename)

    if not match:
        print(f"Invalid filename format: {filename}")
        return None, None, None

    level = match.group(1)
    number = match.group(2)

    return latest_file, level, number

def read_words_from_file(file_path):
    """Read words from a text file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    return words

def determine_topic_from_words(words):
    """Determine an appropriate topic based on the word list"""
    # Simple topic detection based on common themes
    topic_keywords = {
        "Familie und Freunde": ["mutter", "vater", "kind", "bruder", "schwester", "familie", "freund", "freundin"],
        "Essen und Trinken": ["essen", "trinken", "brot", "käse", "fleisch", "fisch", "wasser", "kaffee"],
        "Wohnen und Hausarbeit": ["haus", "wohnung", "zimmer", "küche", "badezimmer", "schlafzimmer"],
        "Arbeit und Beruf": ["arbeit", "beruf", "büro", "firma", "chef", "kollege"],
        "Verkehrsmittel und Reisen": ["auto", "bus", "zug", "flugzeug", "reise", "urlaub"],
        "Alltägliches Leben": []  # Default topic
    }

    # Count matches for each topic
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = sum(1 for word in words if any(kw in word.lower() for kw in keywords))
        topic_scores[topic] = score

    # Return topic with highest score, or default
    best_topic = max(topic_scores.items(), key=lambda x: x[1])
    return best_topic[0] if best_topic[1] > 0 else "Alltägliches Leben"

def main():
    print("🚀 Starting German content generation from word file...")

    # Get the latest word file
    word_file, level, number = get_latest_word_file()

    if not word_file:
        print("❌ No word file found to process")
        sys.exit(1)

    print(f"📄 Processing word file: {word_file}")
    print(f"📊 Level: {level}, Number: {number}")

    # Read words from file
    words = read_words_from_file(word_file)
    print(f"📝 Found {len(words)} words to use")

    if not words:
        print("❌ No words found in the file")
        sys.exit(1)

    # Determine topic from words
    topic = determine_topic_from_words(words)
    print(f"📚 Determined topic: {topic}")

    # Create title in the format "A2 1. Topic"
    title = f"{level} {number}. {topic}"
    print(f"📖 Blog title: {title}")

    # Today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Generating content for: {today}")

    # Build prompt for Claude
    words_list = ", ".join(words)

    prompt = f"""Schreibe einen interessanten deutschen Text zum Thema '{topic}'.

Anforderungen:
- Genau 300 Wörter
- Niveau {level}
- Verwende ALLE diese Wörter im Text: {words_list}
- Jedes Wort muss mindestens einmal vorkommen
- Natürlicher fließender Schreibstil
- Die Wörter sollen sinnvoll in den Kontext eingebettet sein

Der Text soll für {level}-Deutschlernende interessant sein.
Schreibe nur den deutschen Text, keine zusätzlichen Erklärungen."""

    print("🤖 Calling Claude API...")

    # Anthropic API call
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    # Retry logic for API calls
    for attempt in range(3):
        try:
            print(f"API attempt {attempt + 1}/3...")
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            generated_text = message.content[0].text.strip()
            print(f"✅ Generated {len(generated_text.split())} words")
            break

        except Exception as e:
            print(f"❌ Error calling Claude API (attempt {attempt + 1}): {e}")
            if attempt < 2:  # Don't sleep on the last attempt
                print("⏳ Waiting 30 seconds before retry...")
                time.sleep(30)
            else:
                print("❌ All API attempts failed")
                return

    # Verify all words were used
    text_lower = generated_text.lower()
    used_words = [word for word in words if word.lower() in text_lower]
    unused_words = [word for word in words if word.lower() not in text_lower]

    if unused_words:
        print(f"⚠️  Warning: {len(unused_words)} words were not used: {', '.join(unused_words)}")
    else:
        print(f"✅ All {len(words)} words were successfully used")

    # Jekyll _posts directory
    posts_dir = Path("_posts")
    posts_dir.mkdir(exist_ok=True)

    # Generate Jekyll-style filenames
    main_filename = generate_jekyll_filename(title, today)
    jp_filename = generate_jekyll_filename(title, today, "jp")
    en_filename = generate_jekyll_filename(title, today, "en")

    # Create main blog post
    blog_content = f"""---
title: "{title}"
date: {today}
topic: "{topic}"
difficulty_level: "{level}"
word_count: {len(generated_text.split())}
source_file: "{os.path.basename(word_file)}"
generated: true
---

{generated_text}

---

**📝 Verwendete Wörter / Used Words:**
{', '.join(words)}
"""

    blog_file = posts_dir / main_filename
    with open(blog_file, 'w', encoding='utf-8') as f:
        f.write(blog_content)

    print(f"📄 Main blog post created: {blog_file}")

    # Generate Japanese explanation
    print("🇯🇵 Generating Japanese explanation...")

    japanese_prompt = f"""Create a detailed Japanese explanation article for {level} German learners based on this German text:

GERMAN TEXT:
{generated_text}

TOPIC: {topic}
WORDS TO EXPLAIN: {', '.join(words)}

Please create a comprehensive Japanese explanation article that includes:

1. 🎯 **今日の学習目標** - Learning objectives for the day
2. 📖 **重要語彙解説** - Detailed vocabulary explanation for ALL the words: {', '.join(words)}
   - Pronunciation in katakana
   - Meaning in Japanese
   - Example sentences from the text
   - Grammar notes for each word
3. 📝 **重要文法ポイント** - Important grammar points from the text
4. 🗣️ **実用フレーズ** - Practical phrases related to the topic

Format the article in markdown with proper headers.
Focus on {level}-level grammar and vocabulary.
Write everything in Japanese.
Do not include practice questions or homework sections."""

    # Retry logic for Japanese explanation
    for attempt in range(3):
        try:
            print(f"Japanese API attempt {attempt + 1}/3...")
            jp_message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": japanese_prompt}]
            )

            japanese_explanation = jp_message.content[0].text.strip()

            jp_blog_content = f"""---
title: "{title} - 日本語解説"
date: {today}
topic: "{topic}"
type: "japanese_explanation"
difficulty_level: "{level}"
original_post: "{main_filename}"
---

# 📚 {level}解説: {topic}

**原文記事**: [{title}](../{main_filename.replace('.md', '.html')})

---

{japanese_explanation}
"""

            jp_blog_file = posts_dir / jp_filename
            with open(jp_blog_file, 'w', encoding='utf-8') as f:
                f.write(jp_blog_content)

            print(f"📄 Japanese explanation created: {jp_blog_file}")
            break

        except Exception as e:
            print(f"❌ Error generating Japanese explanation (attempt {attempt + 1}): {e}")
            if attempt < 2:
                print("⏳ Waiting 30 seconds before retry...")
                time.sleep(30)
            else:
                print("❌ Japanese explanation generation failed after all attempts")

# 📚 {level} German Study Guide: {topic}

**Original Article**: [{title}](../{main_filename.replace('.md', '.html')})

---

{english_explanation}
"""

            en_blog_file = posts_dir / en_filename
            with open(en_blog_file, 'w', encoding='utf-8') as f:
                f.write(en_blog_content)

            print(f"📄 English explanation created: {en_blog_file}")
            break

        except Exception as e:
            print(f"❌ Error generating English explanation (attempt {attempt + 1}): {e}")
            if attempt < 2:
                print("⏳ Waiting 30 seconds before retry...")
                time.sleep(30)
            else:
                print("❌ English explanation generation failed after all attempts")

    print("\n✅ Content generation completed!")
    print(f"📚 Title: {title}")
    print(f"📝 Words used: {len(used_words)}/{len(words)}")
    print(f"📄 Files created:")
    print(f"   - {main_filename}")
    print(f"   - {jp_filename}")
    print(f"   - {en_filename}")

if __name__ == "__main__":
    main()