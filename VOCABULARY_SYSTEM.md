# German Vocabulary Learning System

This system automatically generates German vocabulary blog posts and podcast episodes from word lists.

## Features

- **Automated Content Generation**: Processes German word lists to create comprehensive learning content
- **Etymology & Memory Techniques**: AI-generated word origins and Japanese phonetic memory aids
- **Multi-Speed Audio**: Slow, normal, and fast pronunciation practice
- **SSML Audio Generation**: High-quality text-to-speech with language switching
- **Podcast Integration**: Automatic RSS feed updates for podcast distribution
- **File Monitoring**: Watches for new word files and auto-generates content

## Quick Start

### 1. Setup Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export AZURE_SPEECH_KEY="your_azure_speech_key"
export AZURE_SPEECH_REGION="your_azure_region"
```

### 3. Add Word File

Create a text file in `data/words/` with German words (one per line):

```
data/words/my_words.txt
```

Example content:
```
lernen
verstehen
sprechen
hören
lesen
```

### 4. Generate Content

**Manual Generation:**
```bash
python generate_vocab_content.py
```

**Automatic Monitoring:**
```bash
python watch_words.py
```

## Output Files

### Blog Posts
- **Location**: `_posts/YYYY-MM-DD-german-vocab-episode-X.md`
- **Format**: Jekyll-compatible markdown with front matter
- **Content**: Vocabulary entries with etymology, memory techniques, examples, and quiz

### Audio Files
- **Location**: `assets/audio/episode-X.mp3`
- **Format**: MP3 with Japanese/German language switching
- **Features**: Multiple speaking speeds, pronunciation practice, quiz section

### SSML Files (Debug)
- **Location**: `data/ssml/episode-X-ssml.xml`
- **Purpose**: Debug SSML markup for TTS generation

## Content Structure

Each vocabulary entry follows this format:

```markdown
## 単語1: lernen

**意味**: 学ぶ
**語源**: 中高ドイツ語の「lernen」から派生...
**覚え方**: 「レルネン」→「レール音」→電車のレール音を聞いて学ぶ

**ゆっくり**: lernen... lernen... lernen
**普通**: lernen, lernen, lernen
**早口**: lernen-lernen-lernen

**例文トレーニング**:
1. Ich möchte Deutsch lernen. (ドイツ語を学びたいです。)
2. Kinder lernen schnell. (子供たちは早く学びます。)
3. Wir lernen jeden Tag etwas Neues. (私たちは毎日何か新しいことを学びます。)

**ゆっくり**: lernen... lernen... lernen
**普通**: lernen, lernen, lernen
**早口**: lernen-lernen-lernen
```

## SSML Features

The audio generation uses advanced SSML markup:

- **Language Switching**: `<lang xml:lang="ja-JP">` and `<lang xml:lang="de-DE">`
- **Speaking Rates**: Slow (0.75), Normal (1.0), Fast (1.25)
- **Breaks**: Strategic pauses for comprehension
- **Quiz Timing**: 3-second pauses for quiz answers

Example SSML:
```xml
<speak>
  <lang xml:lang="ja-JP">今日のドイツ語単語は</lang>
  <lang xml:lang="de-DE">lernen</lang>
  <lang xml:lang="ja-JP">です。</lang>
  <break time="1s"/>
  <lang xml:lang="ja-JP">ゆっくり：</lang>
  <prosody rate="0.75">
    <lang xml:lang="de-DE">lernen</lang>
  </prosody>
</speak>
```

## GitHub Actions Integration

The system includes automated workflows:

### vocabulary-pipeline.yml
- **Trigger**: Push to `data/words/*.txt`
- **Actions**: 
  1. Generate vocabulary content
  2. Create audio files
  3. Update podcast RSS
  4. Auto-commit changes

### Environment Secrets Required
- `ANTHROPIC_API_KEY`: For content generation
- `AZURE_SPEECH_KEY`: For audio generation
- `AZURE_SPEECH_REGION`: Azure region for Speech Services

## File Watcher

The `watch_words.py` script provides real-time monitoring:

- Watches `data/words/` directory
- Processes new `.txt` files automatically
- Generates content and audio
- Auto-commits to git (optional)

### Usage
```bash
python watch_words.py
```

Features:
- File change detection
- Duplicate processing prevention
- Error handling and retry logic
- Environment validation

## Podcast RSS Integration

The system automatically updates `podcast.rss` with:
- Vocabulary episodes
- Regular German learning content
- iTunes-compatible metadata
- Episode numbering and descriptions

## Directory Structure

```
/
├── data/
│   ├── words/           # Word list files (.txt)
│   └── ssml/           # Generated SSML files (debug)
├── _posts/             # Generated blog posts
├── assets/
│   └── audio/          # Generated MP3 files
├── .github/
│   └── workflows/
│       └── vocabulary-pipeline.yml
├── generate_vocab_content.py    # Main content generator
├── watch_words.py              # File watcher
├── requirements.txt            # Python dependencies
└── podcast.rss                 # Updated RSS feed
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify `ANTHROPIC_API_KEY` is set
   - Check API key permissions

2. **Audio Generation Fails**
   - Verify `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` are set
   - Check Azure Speech Services subscription status

3. **File Watcher Not Responding**
   - Check file permissions in `data/words/`
   - Verify required directories exist

4. **Empty Audio Files**
   - Check SSML syntax in debug files
   - Verify Azure Speech Services quotas and limits

### Debug Commands

```bash
# Test content generation
python generate_vocab_content.py

# Check environment
python -c "import os; print('ANTHROPIC_API_KEY' in os.environ)"

# Test Azure Speech Services setup
python -c "import azure.cognitiveservices.speech as speechsdk; print('Azure Speech Services ready')"
```

## Customization

### Modify Content Format
Edit `format_vocabulary_content()` in `generate_vocab_content.py`

### Adjust Audio Settings
Modify voice selection and audio config in `generate_audio_file()`

### Change File Patterns
Update glob patterns in `watch_words.py` and workflow files

## Performance Notes

- **Rate Limits**: Built-in delays between API calls
- **File Size**: Audio files typically 1-3MB per episode
- **Generation Time**: ~2-3 minutes per 5-word episode
- **Concurrent Processing**: Single-threaded to respect API limits

## Contributing

1. Test changes with small word files first
2. Verify SSML output in debug files
3. Check audio quality before committing
4. Update documentation for new features