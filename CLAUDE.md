# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jekyll-based blog for documenting German language learning from A2 to C2 level using AI-generated content. The blog combines German texts with Japanese explanations of grammar and vocabulary. Features automated daily content generation through GitHub Actions, vocabulary tracking towards A2 goals (1,500 words), and AI-powered German text generation with bilingual explanations.

## Architecture

Jekyll static site with automated content generation:
- `_posts/`: Blog posts in Jekyll format (YYYY-MM-DD.md, YYYY-MM-DD-jp.md)
- `_config.yml`: Site configuration
- `data/words/`: A2 vocabulary word lists (A2_1.txt, A2_2.txt, etc.)
- `data/ssml/`: SSML files for audio generation
- `assets/audio/`: Generated German audio files (MP3)
- `generate_content.py`: Main content generation script using Anthropic API
- `generate_vocab_content.py`: Vocabulary episode generator with audio synthesis
- `watch_words.py`: File watcher for automatic content generation
- Posts use YAML front matter and contain German text with Japanese/English explanations
- Theme: minima (Jekyll default)
- GitHub Actions workflow for daily automation

## Common Commands

### Build and Serve
```bash
# Install Jekyll (if not present)
gem install jekyll bundler

# Serve locally with auto-regeneration
jekyll serve --watch

# Build site
jekyll build

# Build for production
JEKYLL_ENV=production jekyll build
```

### Python Content Generation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Required environment variables
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export AZURE_SPEECH_KEY="your_azure_speech_key"  # For audio generation
export AZURE_SPEECH_REGION="your_azure_region"

# Generate German learning content
python generate_content.py

# Generate vocabulary episodes with audio
python generate_vocab_content.py

# Watch for new word files and auto-generate content
python watch_words.py
```

### Content Generation Workflow
Content is automatically generated through two main scripts:

1. **Daily German Content** (`generate_content.py`):
   - Creates 300-word A2-level German texts
   - Tracks vocabulary usage and progress
   - Generates bilingual explanations (Japanese/English)
   - Uses Jekyll filename format: `YYYY-MM-DD-topic-title-with-dashes.md`

2. **Vocabulary Episodes** (`generate_vocab_content.py`):
   - Processes word lists from `data/words/`
   - Generates etymology and memory techniques
   - Creates multi-speed audio files with SSML
   - Updates podcast RSS feed automatically

## Post Structure

Posts follow these patterns:
- **German Content**: A2-level text with vocabulary tracking
- **Japanese Explanations**: Grammar notes and word explanations
- **Vocabulary Episodes**: Etymology, memory aids, multi-speed audio
- **Front Matter**: Standard Jekyll YAML with categories `[german, learning]`
- **Audio Integration**: MP3 files in `assets/audio/` with SSML generation

## Automation Features

- **GitHub Actions**: Daily content generation via `.github/workflows/vocabulary-pipeline.yml`
- **File Watching**: `watch_words.py` monitors `data/words/` for new vocabulary files
- **Vocabulary Tracking**: Progress towards A2 goal of 1,500 words
- **Audio Generation**: Azure Cognitive Services for German pronunciation
- **RSS Integration**: Automatic podcast feed updates

## GitHub Pages Deployment

Designed for GitHub Pages with automatic Jekyll builds. The GitHub Actions workflow generates content and commits it to trigger deployment.