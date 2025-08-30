import requests
import time
import logging
import hmac
import hashlib
import json
from functools import lru_cache
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# -------------------------------
# Sentiment Analysis Helpers
# -------------------------------

# Pre-defined models with their specific result parsing logic
SENTIMENT_MODELS = [
    {
        "name": "siebert/sentiment-roberta-large-english",
        "parser": "positive_negative"  # Returns POSITIVE/NEGATIVE labels
    },
    {
        "name": "distilbert-base-uncased-finetuned-sst-2-english", 
        "parser": "positive_negative"  # Returns POSITIVE/NEGATIVE labels
    },
    {
        "name": "nlptown/bert-base-multilingual-uncased-sentiment",
        "parser": "star_rating"  # Returns 1-5 star ratings
    }
]

def analyze_sentiment(text):
    """
    Analyze the sentiment of the given text using Hugging Face models.
    Falls back to keyword analysis if API calls fail.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        float: Sentiment score between 0.0 (negative) and 1.0 (positive)
    """
    if not text or len(text.strip()) < 10:  # Increased minimum length for meaningful analysis
        logger.warning("Text too short for meaningful sentiment analysis")
        return 0.5  # Neutral default

    # Check if Hugging Face API is configured
    if not Config.HUGGING_FACE_API_KEY or Config.HUGGING_FACE_API_KEY.startswith("your_actual"):
        logger.warning("Hugging Face API key not configured, using keyword-based analysis")
        return keyword_based_sentiment(text)

    headers = {"Authorization": f"Bearer {Config.HUGGING_FACE_API_KEY}"}

    for model_info in SENTIMENT_MODELS:
        model_name = model_info["name"]
        api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        logger.info(f"Attempting sentiment analysis with model: {model_name}")

        for attempt in range(3):  # Retry up to 3 times per model
            try:
                response = requests.post(api_url, headers=headers, json={"inputs": text}, timeout=15)

                if response.status_code == 503:
                    # Model is loading, wait and retry
                    wait_time = response.json().get('estimated_time', 10)
                    logger.info(f"Model {model_name} is loading. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()  # Raise exception for 4xx/5xx responses

                result = response.json()
                score = parse_sentiment_result(model_info, result)
                
                if score is not None:
                    logger.info(f"Successfully analyzed sentiment with {model_name}: {score:.3f}")
                    return score
                else:
                    logger.warning(f"Could not parse result from model {model_name}")
                    break  # Try next model

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout with {model_name} (attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error with {model_name}: {e}")
                if attempt == 2:  # Last attempt
                    break
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error with {model_name}: {e}")
                break

    logger.warning("All sentiment models failed, falling back to keyword-based analysis")
    return keyword_based_sentiment(text)

def parse_sentiment_result(model_info, result):
    """
    Parse the raw API response based on the model type.
    
    Args:
        model_info (dict): Model configuration containing name and parser type
        result: Raw response from Hugging Face API
        
    Returns:
        float: Normalized sentiment score between 0.0 and 1.0, or None if parsing fails
    """
    if not isinstance(result, list) or not result:
        return None

    data = result[0]
    parser_type = model_info["parser"]

    if parser_type == "positive_negative":
        # Models that return POSITIVE/NEGATIVE labels
        scores = {}
        for item in data:
            label = item.get('label', '').upper()
            score = item.get('score', 0)
            scores[label] = score
        
        positive_score = scores.get('POSITIVE', 0)
        negative_score = scores.get('NEGATIVE', 0)
        
        if positive_score + negative_score > 0:
            return positive_score / (positive_score + negative_score)
        return 0.5

    elif parser_type == "star_rating":
        # Models that return 1-5 star ratings
        star_scores = {}
        for item in data:
            label = item.get('label', '')
            score = item.get('score', 0)
            if 'star' in label and label[0].isdigit():
                stars = int(label[0])
                star_scores[stars] = score
        
        if star_scores:
            total_score = sum(stars * score for stars, score in star_scores.items())
            total_weight = sum(star_scores.values())
            return total_score / (5 * total_weight)  # Normalize to 0-1

    return None

@lru_cache(maxsize=1000)
def keyword_based_sentiment(text):
    """
    Fallback sentiment analysis using keyword matching.
    Results are cached for performance.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        float: Sentiment score between 0.0 and 1.0
    """
    positive_keywords = {
        'good': 0.7, 'great': 0.8, 'excellent': 0.9, 'amazing': 0.9,
        'happy': 0.8, 'joy': 0.8, 'love': 0.9, 'wonderful': 0.85,
        'excited': 0.75, 'pleased': 0.7, 'content': 0.6, 'grateful': 0.8,
        'optimistic': 0.7, 'bliss': 0.9, 'calm': 0.65, 'peaceful': 0.7,
        'relaxed': 0.65, 'thankful': 0.75, 'appreciative': 0.75,
        'serene': 0.7, 'delighted': 0.8, 'blissful': 0.85, 'ecstatic': 0.9
    }

    negative_keywords = {
        'bad': 0.3, 'terrible': 0.1, 'awful': 0.1, 'horrible': 0.1,
        'sad': 0.2, 'angry': 0.2, 'hate': 0.1, 'dislike': 0.3,
        'upset': 0.3, 'frustrated': 0.25, 'disappointed': 0.3,
        'anxious': 0.25, 'depressed': 0.1, 'stressed': 0.25,
        'worried': 0.3, 'fear': 0.2, 'scared': 0.2, 'dread': 0.15,
        'miserable': 0.1, 'heartbroken': 0.1, 'lonely': 0.2,
        'annoyed': 0.3, 'furious': 0.1, 'devastated': 0.1
    }

    text_lower = text.lower()
    positive_score = 0
    negative_score = 0

    for word, weight in positive_keywords.items():
        if word in text_lower:
            positive_score += weight

    for word, weight in negative_keywords.items():
        if word in text_lower:
            negative_score += (1 - weight)  # Invert negative weights

    total_score = positive_score + negative_score
    
    if total_score > 0:
        return positive_score / total_score
    return 0.5

def recommend_meditation(sentiment_score, emotion=None):
    """
    Recommend a meditation based on sentiment score and optional emotion label.
    
    Args:
        sentiment_score (float): Score from 0.0 to 1.0
        emotion (str, optional): Emotion label from journal entry
        
    Returns:
        dict: Meditation recommendation with file and name
    """
    # If we have a specific emotion, use it for more precise recommendations
    if emotion:
        emotion_lower = emotion.lower()
        if any(e in emotion_lower for e in ['anxious', 'stress', 'worry', 'overwhelm']):
            return {"file": "anxiety_relief.mp3", "name": "Anxiety Relief Meditation"}
        elif any(e in emotion_lower for e in ['sad', 'depress', 'grief', 'heartbreak']):
            return {"file": "gratitude.mp3", "name": "Gratitude Practice"}
        elif any(e in emotion_lower for e in ['tired', 'exhaust', 'sleep', 'fatigue']):
            return {"file": "sleep.mp3", "name": "Sleep Meditation"}
        elif any(e in emotion_lower for e in ['anger', 'frustrat', 'annoy', 'furious']):
            return {"file": "relaxation.mp3", "name": "Deep Relaxation"}
        elif any(e in emotion_lower for e in ['focus', 'concentrate', 'distract', 'attention']):
            return {"file": "focus.mp3", "name": "Focus Enhancement"}

    # Fallback to sentiment-based recommendations
    if sentiment_score < 0.3:
        return {"file": "gratitude.mp3", "name": "Gratitude Practice"}
    elif sentiment_score < 0.45:
        return {"file": "breathing.mp3", "name": "Calming Breath Work"}
    elif sentiment_score < 0.7:
        return {"file": "focus.mp3", "name": "Mindful Focus"}
    else:
        return {"file": "morning_energy.mp3", "name": "Energy Boost"}

# -------------------------------
# IntaSend Payment Helpers
# -------------------------------

def verify_webhook_signature(payload, signature):
    """Verify IntaSend webhook signature (already well-implemented)"""
    if not Config.INTASEND_SECRET_KEY or Config.INTASEND_SECRET_KEY.startswith("your_actual"):
        logger.error("IntaSend secret key not configured")
        return False

    try:
        secret = Config.INTASEND_SECRET_KEY.encode('utf-8')
        expected_signature = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False

# The initiate_intasend_payment and verify_intasend_payment functions are already excellent