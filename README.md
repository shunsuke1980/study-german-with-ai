# Study German with AI

A Jekyll-based blog that documents a German language learning journey to A2 level using AI-generated content. This project automatically generates daily German texts with vocabulary tracking and provides explanations in both Japanese and English.

## 🎯 Project Overview

This blog helps German learners by:
- Generating daily A2-level German texts (300 words) on various everyday topics
- Tracking vocabulary progress towards the A2 goal of 1,500 words
- Providing detailed explanations in Japanese and English
- Ensuring vocabulary diversity and systematic learning progression

## 🚀 Features

- **Daily Content Generation**: Automated GitHub Actions workflow creates new German learning content every day
- **Vocabulary Management**: Smart tracking system that monitors word usage and ensures diverse vocabulary exposure
- **Bilingual Support**: Each German text comes with detailed explanations in both Japanese and English
- **Progress Tracking**: Monitors learning progress towards A2 vocabulary goals (1,500 words in ~120 days)
- **Topic Rotation**: Covers 24 different A2-level topics to ensure comprehensive learning

## 📚 Content Structure

Each daily post includes:
- 300-word German text at A2 level
- Vocabulary statistics and progress tracking
- Links to Japanese and English explanation articles
- New A2 vocabulary words learned that day
- Estimated completion time for A2 vocabulary goals

## 🛠️ Technical Details

### Built With
- **Jekyll**: Static site generator
- **GitHub Actions**: Automated daily content generation
- **Claude API**: AI-powered German text generation
- **Python**: Vocabulary management and content processing

### Workflow
The GitHub Actions workflow (`generate-content.yml`) runs daily and:
1. Generates A2-level German text using Claude API
2. Tracks and manages vocabulary usage
3. Creates bilingual explanation articles
4. Commits new content to the repository
5. Publishes via GitHub Pages

## 📊 Vocabulary Tracking

The system tracks:
- Total unique words learned
- A2 vocabulary progress (words learned out of 1,500 target)
- Daily learning pace
- Estimated completion time
- Word frequency to avoid overuse

## 🌐 Deployment

This site is designed for GitHub Pages deployment. Simply push to the main branch, and GitHub Pages will automatically build and deploy the Jekyll site.

## 📝 License

This project is open source and available for everyone to use.

## ☕ Support

If you find this project helpful and would like to support its continued development:

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="BuyMeACoffee" width="100">](https://www.buymeacoffee.com/shunsuke1980)

## 📧 Contact

Created by shunsuke1980 - [shunsuke1980@gmail.com](mailto:shunsuke1980@gmail.com)