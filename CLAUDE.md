# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jekyll-based blog for documenting German language learning from A2 to C2 level using AI-generated content. The blog combines German texts with Japanese explanations of grammar and vocabulary.

## Architecture

Jekyll static site with:
- `_posts/`: Blog posts in Jekyll format (YYYY-MM-DD.md, YYYY-MM-DD-jp.md, YYYY-MM-DD-en.md)
- `_config.yml`: Site configuration
- `data/`: Vocabulary tracking and progress data
- `assets/audio/`: Generated German audio files (MP3)
- Posts use YAML front matter and contain German text with Japanese/English explanations
- Theme: minima (Jekyll default)

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

### Creating New Posts
Posts are automatically created in `_posts/` with filename format: 
- `YYYY-MM-DD.md` (main German content)
- `YYYY-MM-DD-jp.md` (Japanese explanation)  
- `YYYY-MM-DD-en.md` (English explanation)

Each post requires front matter:
```yaml
---
layout: post
title: "Post Title"
date: YYYY-MM-DD
categories: [german, learning]
---
```

## Post Structure

Posts typically contain:
1. German text (A2-C2 level)
2. Japanese vocabulary explanations
3. Grammar notes in Japanese
4. Optional audio references in `assets/audio/`

## GitHub Pages Deployment

This site appears designed for GitHub Pages deployment, which will automatically build the Jekyll site when pushed to the repository.