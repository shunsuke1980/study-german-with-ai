#!/usr/bin/env python3
"""
Enhanced vocabulary generator that creates longer audio by splitting content
"""
import os
from pathlib import Path
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk

def split_words_into_chunks(words_data, words_per_chunk=5):
    """Split word list into smaller chunks to avoid 10-minute limit"""
    items = list(words_data.items())
    chunks = []
    
    for i in range(0, len(items), words_per_chunk):
        chunk_dict = dict(items[i:i + words_per_chunk])
        chunks.append(chunk_dict)
    
    return chunks

def generate_audio_parts(words_data, episode_number):
    """Generate multiple audio parts and combine them"""
    chunks = split_words_into_chunks(words_data, words_per_chunk=5)
    audio_parts = []
    
    for i, chunk in enumerate(chunks):
        # Generate SSML for this chunk
        ssml_content = create_ssml_content(chunk, part_number=i+1, total_parts=len(chunks))
        
        # Generate audio for this part
        part_path = f"temp_part_{i+1}.mp3"
        if generate_audio_file(ssml_content, part_path):
            audio_parts.append(part_path)
    
    # Combine all parts
    if audio_parts:
        combined = AudioSegment.from_mp3(audio_parts[0])
        for part in audio_parts[1:]:
            combined += AudioSegment.from_mp3(part)
        
        # Export final long audio
        output_path = f"assets/audio/episode-{episode_number}-full.mp3"
        combined.export(output_path, format="mp3", bitrate="192k")
        
        # Clean up temp files
        for part in audio_parts:
            os.remove(part)
        
        print(f"✅ Created full audio: {output_path}")
        print(f"   Duration: {len(combined)/1000/60:.1f} minutes")

def create_ssml_content_with_full_repetitions(words_data):
    """Create SSML with ALL repetitions you want - no limits!"""
    ssml_parts = ['<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="de-DE">']
    ssml_parts.append('<voice name="de-DE-FlorianMultilingualNeural">')
    
    # Process each word with FULL repetitions
    for i, (word, data) in enumerate(words_data.items(), 1):
        # Word announcement
        ssml_parts.append(f"Wort {i}: <prosody rate='medium'>{word}</prosody>")
        ssml_parts.append('<break time="0.5s"/>')
        
        # Japanese meaning with proper language tag
        ssml_parts.append(f'<lang xml:lang="ja-JP">{data["meaning"]}</lang>')
        ssml_parts.append('<break time="1s"/>')
        
        # Full repetitions - as many as you want!
        # Slow pronunciation (5 times if you want)
        ssml_parts.append("Langsam:")
        for j in range(5):  # Increased repetitions!
            ssml_parts.append(f'<prosody rate="x-slow">{word}</prosody>')
            if j < 4:
                ssml_parts.append('<break time="0.5s"/>')
        
        ssml_parts.append('<break time="0.5s"/>')
        
        # Normal speed (5 times)
        ssml_parts.append("Normal:")
        for j in range(5):
            ssml_parts.append(f'<prosody rate="medium">{word}</prosody>')
            if j < 4:
                ssml_parts.append('<break time="0.3s"/>')
        
        ssml_parts.append('<break time="0.5s"/>')
        
        # Fast speed (5 times)
        ssml_parts.append("Schnell:")
        for j in range(5):
            ssml_parts.append(f'<prosody rate="fast">{word}</prosody>')
            if j < 4:
                ssml_parts.append('<break time="0.1s"/>')
        
        ssml_parts.append('<break time="1s"/>')
        
        # Example sentences with full repetitions
        ssml_parts.append("Beispielsätze:")
        ssml_parts.append('<break time="0.5s"/>')
        
        for j, sentence in enumerate(data['sentences'], 1):
            ssml_parts.append(f"Beispiel {j}:")
            # Repeat sentence 3 times at slow speed
            for k in range(3):
                ssml_parts.append(f'<prosody rate="x-slow">{sentence["german"]}</prosody>')
                ssml_parts.append('<break time="1s"/>')
            
            ssml_parts.append(f'<lang xml:lang="ja-JP">{sentence["japanese"]}</lang>')
            ssml_parts.append('<break time="1s"/>')
        
        # Additional practice section
        ssml_parts.append("Noch einmal üben:")
        ssml_parts.append('<break time="0.5s"/>')
        
        # Even more practice repetitions!
        for speed_name, rate in [("Langsam", "x-slow"), ("Normal", "medium"), ("Schnell", "fast")]:
            ssml_parts.append(f"{speed_name}:")
            for k in range(5):  # 5 repetitions for practice too!
                ssml_parts.append(f'<prosody rate="{rate}">{word}</prosody>')
                if k < 4:
                    ssml_parts.append('<break time="0.3s"/>')
            ssml_parts.append('<break time="0.5s"/>')
        
        ssml_parts.append('<break time="2s"/>')
    
    # Extended quiz section with more time
    ssml_parts.append("Jetzt kommt das Quiz. Hören Sie das deutsche Wort und denken Sie an die Bedeutung.")
    ssml_parts.append('<break time="2s"/>')  # More time to prepare
    
    for i, (word, data) in enumerate(words_data.items(), 1):
        ssml_parts.append(f"Frage {i}:")
        ssml_parts.append(f'<prosody rate="medium">{word}</prosody>')
        ssml_parts.append('<break time="5s"/>')  # More thinking time
        ssml_parts.append(f'Die Antwort war: <lang xml:lang="ja-JP">{data["meaning"]}</lang>')
        ssml_parts.append('<break time="2s"/>')
    
    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')
    
    return ' '.join(ssml_parts)