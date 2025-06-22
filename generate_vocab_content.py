#!/usr/bin/env python3
"""
German Vocabulary Blog Generator
Generates blog content and podcast audio from word lists
"""
import os
import sys
import re
import time
import json
from datetime import datetime
from pathlib import Path
import glob
import anthropic
from google.cloud import texttospeech
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Check API keys
if 'ANTHROPIC_API_KEY' not in os.environ:
    print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
    sys.exit(1)

def generate_jekyll_filename(episode_number, date_str):
    """Generate Jekyll-format filename for vocabulary episode"""
    return f"{date_str}-german-vocab-episode-{episode_number}.md"

def get_next_episode_number():
    """Get the next episode number by checking existing files"""
    posts_dir = Path("_posts")
    if not posts_dir.exists():
        return 1
    
    # Find all vocabulary episode files
    vocab_files = list(posts_dir.glob("*-german-vocab-episode-*.md"))
    if not vocab_files:
        return 1
    
    # Extract episode numbers
    episode_numbers = []
    for file in vocab_files:
        match = re.search(r'episode-(\d+)\.md$', file.name)
        if match:
            episode_numbers.append(int(match.group(1)))
    
    return max(episode_numbers) + 1 if episode_numbers else 1

def generate_etymology_and_memory(word, client):
    """Generate etymology and memory technique for a German word"""
    prompt = f"""For the German word "{word}", provide:

1. Japanese meaning (簡潔に)
2. Etymology explanation in Japanese (語源の説明)
3. Memory technique using Japanese phonetics (カタカナを使った覚え方)

Format your response as JSON with these exact keys:
- "meaning": Japanese meaning
- "etymology": Etymology in Japanese (2-3 sentences)
- "memory": Memory technique in Japanese using katakana sounds

Example format:
{{
    "meaning": "走る",
    "etymology": "古高ドイツ語の「loufen」から派生。印欧語の「*leu-」（速く動く）が語源。",
    "memory": "「ラウフェン」→「ラブ編」→愛（ラブ）を編むために走る"
}}

Respond ONLY with the JSON, no additional text."""

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            # Parse JSON response
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error generating etymology for {word} (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(5)
    
    # Fallback if API fails
    return {
        "meaning": "（意味）",
        "etymology": "（語源情報）",
        "memory": "（覚え方）"
    }

def generate_example_sentences(word, client):
    """Generate 3 example sentences for a word"""
    prompt = f"""Generate 3 example sentences for the German word "{word}" at A2-B1 level.

Requirements:
- Each sentence should be practical and useful
- Include a natural Japanese translation
- Sentences should demonstrate different uses of the word

Format as JSON array:
[
    {{"german": "German sentence", "japanese": "Japanese translation"}},
    {{"german": "German sentence", "japanese": "Japanese translation"}},
    {{"german": "German sentence", "japanese": "Japanese translation"}}
]

Respond ONLY with the JSON array."""

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error generating sentences for {word} (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(5)
    
    # Fallback
    return [
        {"german": f"Beispiel mit {word}.", "japanese": "例文"},
        {"german": f"Satz mit {word}.", "japanese": "文"},
        {"german": f"Text mit {word}.", "japanese": "テキスト"}
    ]

def format_vocabulary_content(word, word_data, sentences, index):
    """Format vocabulary content for blog post"""
    content = f"""## 単語{index}: {word}

**意味**: {word_data['meaning']}
**語源**: {word_data['etymology']}
**覚え方**: {word_data['memory']}

**ゆっくり**: {word}... {word}... {word}
**普通**: {word}, {word}, {word}
**早口**: {word}-{word}-{word}

**例文トレーニング**:
"""
    
    for i, sentence in enumerate(sentences, 1):
        content += f"{i}. {sentence['german']} ({sentence['japanese']})\n"
    
    content += f"""
**ゆっくり**: {word}... {word}... {word}
**普通**: {word}, {word}, {word}
**早口**: {word}-{word}-{word}

"""
    
    return content

def create_ssml_content(words_data):
    """Create SSML content for Google Cloud TTS"""
    root = ET.Element("speak")
    
    # Introduction
    intro_ja = ET.SubElement(root, "lang")
    intro_ja.set("xml:lang", "ja-JP")
    intro_ja.text = "今日のドイツ語単語学習を始めましょう。"
    
    ET.SubElement(root, "break", time="1s")
    
    # Process each word
    for i, (word, data) in enumerate(words_data.items(), 1):
        # Word number announcement
        word_num = ET.SubElement(root, "lang")
        word_num.set("xml:lang", "ja-JP")
        word_num.text = f"単語{i}："
        
        # German word
        word_de = ET.SubElement(root, "lang")
        word_de.set("xml:lang", "de-DE")
        word_de.text = word
        
        ET.SubElement(root, "break", time="0.5s")
        
        # Meaning
        meaning = ET.SubElement(root, "lang")
        meaning.set("xml:lang", "ja-JP")
        meaning.text = f"意味：{data['meaning']}"
        
        ET.SubElement(root, "break", time="1s")
        
        # Slow pronunciation
        slow_ja = ET.SubElement(root, "lang")
        slow_ja.set("xml:lang", "ja-JP")
        slow_ja.text = "ゆっくり："
        
        for _ in range(3):
            slow = ET.SubElement(root, "prosody", rate="0.75")
            slow_de = ET.SubElement(slow, "lang")
            slow_de.set("xml:lang", "de-DE")
            slow_de.text = word
            ET.SubElement(root, "break", time="0.5s")
        
        # Normal speed
        normal_ja = ET.SubElement(root, "lang")
        normal_ja.set("xml:lang", "ja-JP")
        normal_ja.text = "普通："
        
        for _ in range(3):
            normal_de = ET.SubElement(root, "lang")
            normal_de.set("xml:lang", "de-DE")
            normal_de.text = word
            ET.SubElement(root, "break", time="0.3s")
        
        # Fast speed
        fast_ja = ET.SubElement(root, "lang")
        fast_ja.set("xml:lang", "ja-JP")
        fast_ja.text = "早口："
        
        fast = ET.SubElement(root, "prosody", rate="1.25")
        for j in range(3):
            fast_de = ET.SubElement(fast, "lang")
            fast_de.set("xml:lang", "de-DE")
            fast_de.text = word
            if j < 2:
                ET.SubElement(fast, "break", time="0.1s")
        
        ET.SubElement(root, "break", time="1s")
        
        # Example sentences
        examples_ja = ET.SubElement(root, "lang")
        examples_ja.set("xml:lang", "ja-JP")
        examples_ja.text = "例文トレーニング："
        
        ET.SubElement(root, "break", time="0.5s")
        
        for j, sentence in enumerate(data['sentences'], 1):
            # Sentence number
            num_ja = ET.SubElement(root, "lang")
            num_ja.set("xml:lang", "ja-JP")
            num_ja.text = f"{j}番。"
            
            # German sentence
            sent_de = ET.SubElement(root, "lang")
            sent_de.set("xml:lang", "de-DE")
            sent_de.text = sentence['german']
            
            ET.SubElement(root, "break", time="1s")
            
            # Japanese translation
            trans_ja = ET.SubElement(root, "lang")
            trans_ja.set("xml:lang", "ja-JP")
            trans_ja.text = sentence['japanese']
            
            ET.SubElement(root, "break", time="1s")
        
        # Practice repetition
        practice_ja = ET.SubElement(root, "lang")
        practice_ja.set("xml:lang", "ja-JP")
        practice_ja.text = "もう一度練習しましょう。"
        
        ET.SubElement(root, "break", time="0.5s")
        
        # Repeat slow/normal/fast
        for speed_name, rate in [("ゆっくり", "0.75"), ("普通", "1.0"), ("早口", "1.25")]:
            speed_ja = ET.SubElement(root, "lang")
            speed_ja.set("xml:lang", "ja-JP")
            speed_ja.text = f"{speed_name}："
            
            if rate != "1.0":
                prosody = ET.SubElement(root, "prosody", rate=rate)
                parent = prosody
            else:
                parent = root
            
            for _ in range(3):
                repeat_de = ET.SubElement(parent, "lang")
                repeat_de.set("xml:lang", "de-DE")
                repeat_de.text = word
                ET.SubElement(parent, "break", time="0.3s")
        
        ET.SubElement(root, "break", time="2s")
    
    # Quiz section
    quiz_ja = ET.SubElement(root, "lang")
    quiz_ja.set("xml:lang", "ja-JP")
    quiz_ja.text = "それでは、クイズタイムです。次のドイツ語を聞いて、意味を考えてください。"
    
    ET.SubElement(root, "break", time="1s")
    
    for i, (word, data) in enumerate(words_data.items(), 1):
        quiz_num = ET.SubElement(root, "lang")
        quiz_num.set("xml:lang", "ja-JP")
        quiz_num.text = f"問題{i}："
        
        quiz_word = ET.SubElement(root, "lang")
        quiz_word.set("xml:lang", "de-DE")
        quiz_word.text = word
        
        # 3 second pause for answer
        ET.SubElement(root, "break", time="3s")
        
        answer = ET.SubElement(root, "lang")
        answer.set("xml:lang", "ja-JP")
        answer.text = f"答えは、{data['meaning']}でした。"
        
        ET.SubElement(root, "break", time="1s")
    
    # Closing
    closing = ET.SubElement(root, "lang")
    closing.set("xml:lang", "ja-JP")
    closing.text = "今日の単語学習はこれで終わりです。復習を忘れずに、頑張ってください！"
    
    return root

def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_audio_file(ssml_content, output_path):
    """Generate MP3 audio file using Google Cloud TTS"""
    client = texttospeech.TextToSpeechClient()
    
    # Convert SSML to string
    ssml_text = ET.tostring(ssml_content, encoding='unicode')
    
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    
    # Voice configuration (using a female German voice as primary)
    voice = texttospeech.VoiceSelectionParams(
        language_code="de-DE",
        name="de-DE-Wavenet-F",  # High quality female voice
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    # Audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0
    )
    
    # Generate audio
    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio file
        with open(output_path, 'wb') as out:
            out.write(response.audio_content)
        
        print(f"✅ Audio saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return False

def process_word_file(word_file_path, episode_number):
    """Process a word file and generate all content"""
    print(f"📄 Processing word file: {word_file_path}")
    
    # Read words
    with open(word_file_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    
    if not words:
        print("❌ No words found in file")
        return False
    
    print(f"📝 Found {len(words)} words to process")
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    
    # Generate data for each word
    words_data = {}
    
    for i, word in enumerate(words, 1):
        print(f"🔄 Processing word {i}/{len(words)}: {word}")
        
        # Generate etymology and memory technique
        word_info = generate_etymology_and_memory(word, client)
        
        # Generate example sentences
        sentences = generate_example_sentences(word, client)
        
        words_data[word] = {
            'meaning': word_info['meaning'],
            'etymology': word_info['etymology'],
            'memory': word_info['memory'],
            'sentences': sentences
        }
        
        # Small delay to avoid rate limits
        if i < len(words):
            time.sleep(2)
    
    # Generate blog content
    today = datetime.now().strftime('%Y-%m-%d')
    blog_content = f"""---
layout: post
title: "German Vocabulary Episode {episode_number}"
date: {today}
categories: [german, vocabulary, learning]
episode_number: {episode_number}
audio_file: "episode-{episode_number}.mp3"
---

# ドイツ語単語学習 Episode {episode_number}

今日は{len(words)}個の新しい単語を学習します。各単語には語源説明、覚え方、例文が含まれています。

"""
    
    # Add vocabulary content
    for i, (word, data) in enumerate(words_data.items(), 1):
        sentences = data['sentences']
        blog_content += format_vocabulary_content(word, data, sentences, i)
    
    # Add quiz section
    blog_content += """## クイズ

以下の単語の意味を思い出してください：

"""
    
    for i, word in enumerate(words, 1):
        blog_content += f"{i}. **{word}** → ？？？\n"
    
    blog_content += "\n### 答え\n\n"
    
    for i, (word, data) in enumerate(words_data.items(), 1):
        blog_content += f"{i}. **{word}** → {data['meaning']}\n"
    
    blog_content += f"""

---

🎧 **Audio Version**: [Listen to Episode {episode_number}](/assets/audio/episode-{episode_number}.mp3)

📚 **Source**: Generated from word file on {today}
"""
    
    # Save blog post
    posts_dir = Path("_posts")
    posts_dir.mkdir(exist_ok=True)
    
    blog_filename = generate_jekyll_filename(episode_number, today)
    blog_path = posts_dir / blog_filename
    
    with open(blog_path, 'w', encoding='utf-8') as f:
        f.write(blog_content)
    
    print(f"✅ Blog post created: {blog_path}")
    
    # Generate SSML content
    ssml_content = create_ssml_content(words_data)
    
    # Save SSML for debugging
    ssml_dir = Path("data/ssml")
    ssml_dir.mkdir(parents=True, exist_ok=True)
    
    ssml_path = ssml_dir / f"episode-{episode_number}-ssml.xml"
    with open(ssml_path, 'w', encoding='utf-8') as f:
        f.write(prettify_xml(ssml_content))
    
    print(f"✅ SSML saved: {ssml_path}")
    
    # Generate audio file (only if Google Cloud credentials are available)
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        audio_dir = Path("assets/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_path = audio_dir / f"episode-{episode_number}.mp3"
        if generate_audio_file(ssml_content, audio_path):
            print(f"✅ Audio generated: {audio_path}")
        else:
            print("⚠️  Audio generation failed")
    else:
        print("ℹ️  Google Cloud credentials not found, skipping audio generation")
    
    return True

def main():
    """Main function to process latest word file"""
    print("🚀 Starting German vocabulary content generation...")
    
    # Find the latest word file
    word_files = glob.glob("data/words/*.txt")
    
    if not word_files:
        print("❌ No word files found in data/words/")
        sys.exit(1)
    
    # Get the most recently modified file
    latest_file = max(word_files, key=os.path.getmtime)
    
    # Get next episode number
    episode_number = get_next_episode_number()
    print(f"📺 Next episode number: {episode_number}")
    
    # Process the file
    if process_word_file(latest_file, episode_number):
        print("\n✅ Vocabulary content generation completed!")
        print(f"📚 Episode: {episode_number}")
        print(f"📄 Word file: {latest_file}")
    else:
        print("\n❌ Content generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()