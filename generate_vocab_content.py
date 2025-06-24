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
import azure.cognitiveservices.speech as speechsdk
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
    """Create SSML content for Azure Speech Services with Florian Multilingual voice"""
    # Build SSML as a string for better control
    ssml_parts = []

    ssml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    ssml_parts.append('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="de-DE">')
    ssml_parts.append('<voice name="de-DE-FlorianMultilingualNeural">')

    # Introduction in German (the multilingual voice should handle mixed content better)
    ssml_parts.append("Heute lernen wir deutsche Wörter.")
    ssml_parts.append('<break time="1s"/>')

    # Process each word
    for i, (word, data) in enumerate(words_data.items(), 1):
        # Word announcement
        ssml_parts.append(f"Wort {i}: <prosody rate='medium'>{word}</prosody>")
        ssml_parts.append('<break time="0.5s"/>')

        # Meaning in German
        ssml_parts.append(f"{data['meaning']}")
        ssml_parts.append('<break time="1s"/>')

        # Slow pronunciation
        ssml_parts.append("Langsam:")
        for j in range(3):
            ssml_parts.append(f'<prosody rate="x-slow">{word}</prosody>')
            if j < 2:
                ssml_parts.append('<break time="0.5s"/>')

        ssml_parts.append('<break time="0.5s"/>')

        # Normal speed
        ssml_parts.append("Normal:")
        for j in range(3):
            ssml_parts.append(f'<prosody rate="medium">{word}</prosody>')
            if j < 2:
                ssml_parts.append('<break time="0.3s"/>')

        ssml_parts.append('<break time="0.5s"/>')

        # Fast speed
        ssml_parts.append("Schnell:")
        for j in range(3):
            ssml_parts.append(f'<prosody rate="fast">{word}</prosody>')
            if j < 2:
                ssml_parts.append('<break time="0.1s"/>')

        ssml_parts.append('<break time="1s"/>')

        # Example sentences
        ssml_parts.append("Beispielsätze:")
        ssml_parts.append('<break time="0.5s"/>')

        for j, sentence in enumerate(data['sentences'], 1):
            ssml_parts.append(f"Beispiel {j}:")
            ssml_parts.append(f'<prosody rate="x-slow">{sentence["german"]}</prosody>')
            ssml_parts.append('<break time="1s"/>')
            ssml_parts.append(f'<prosody rate="x-slow">{sentence["german"]}</prosody>')
            ssml_parts.append('<break time="1s"/>')
            ssml_parts.append(f"{sentence['japanese']}")
            ssml_parts.append('<break time="1s"/>')

        # Practice repetition
        ssml_parts.append("Noch einmal üben:")
        ssml_parts.append('<break time="0.5s"/>')

        # Repeat all speeds
        for speed_name, rate in [("Langsam", "x-slow"), ("Normal", "medium"), ("Schnell", "fast")]:
            ssml_parts.append(f"{speed_name}:")
            for k in range(3):
                ssml_parts.append(f'<prosody rate="{rate}">{word}</prosody>')
                if k < 2:
                    ssml_parts.append('<break time="0.3s"/>')
            ssml_parts.append('<break time="0.5s"/>')

        ssml_parts.append('<break time="2s"/>')

    # Quiz section
    ssml_parts.append("Jetzt kommt das Quiz. Hören Sie das deutsche Wort und denken Sie an die Bedeutung.")
    ssml_parts.append('<break time="1s"/>')

    for i, (word, data) in enumerate(words_data.items(), 1):
        ssml_parts.append(f"Frage {i}:")
        ssml_parts.append(f'<prosody rate="medium">{word}</prosody>')
        ssml_parts.append('<break time="3s"/>')
        ssml_parts.append(f"Die Antwort war: {data['meaning']}")
        ssml_parts.append('<break time="1s"/>')

    # Closing
    ssml_parts.append("Das war die heutige Wortschatzübung. Vergessen Sie nicht zu wiederholen. Viel Erfolg!")

    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')

    # Join all parts with spaces
    ssml_string = ' '.join(ssml_parts)

    # Parse back to XML element for consistency with the rest of the code
    from xml.etree.ElementTree import fromstring
    return fromstring(ssml_string)

def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_audio_file(ssml_content, output_path):
    """Generate MP3 audio file using Microsoft Azure Speech Services"""
    # Check for Azure credentials
    if 'AZURE_SPEECH_KEY' not in os.environ or 'AZURE_SPEECH_REGION' not in os.environ:
        print("❌ Azure Speech credentials not found, skipping audio generation")
        return False

    try:
        # Convert SSML to string
        ssml_text = ET.tostring(ssml_content, encoding='unicode')

        # Configure Azure Speech Service
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ['AZURE_SPEECH_KEY'],
            region=os.environ['AZURE_SPEECH_REGION']
        )

        # Set the voice to Florian Multilingual
        speech_config.speech_synthesis_voice_name = "de-DE-FlorianMultilingualNeural"

        # Set output format to MP3
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )

        # Create synthesizer with file output
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Generate audio from SSML
        print(f"🔊 Generating audio with Azure Speech Services...")
        result = synthesizer.speak_ssml_async(ssml_text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"✅ Audio saved: {output_path}")
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"❌ Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"❌ Error details: {cancellation_details.error_details}")
            return False
        else:
            print(f"❌ Unexpected result: {result.reason}")
            return False

    except Exception as e:
        print(f"❌ Error generating audio with Azure: {e}")
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

    # Generate audio file (only if Azure Speech credentials are available)
    if 'AZURE_SPEECH_KEY' in os.environ and 'AZURE_SPEECH_REGION' in os.environ:
        audio_dir = Path("assets/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"episode-{episode_number}.mp3"
        if generate_audio_file(ssml_content, audio_path):
            print(f"✅ Audio generated: {audio_path}")
        else:
            print("⚠️  Audio generation failed")
    else:
        print("ℹ️  Azure Speech credentials not found, skipping audio generation")

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