# Technical Guide

## Architecture

The application uses a Flask backend with SQLAlchemy for database operations. The frontend uses vanilla HTML/CSS/JS with Chart.js for visualizations.

## API Integrations

- Hugging Face for sentiment analysis
- IntaSend for payment processing

## Database Schema

- Users: id, username, email, password_hash, is_premium, created_at
- JournalEntries: id, content, sentiment_score, emotion, created_at, user_id

## Deployment

The application can be deployed on platforms like Heroku, Render, or DigitalOcean. Set environment variables for production.