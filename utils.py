import requests
import time
import logging
import hmac
import hashlib
import json
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# Sentiment Analysis Helpers
# -------------------------------

SENTIMENT_MODELS = [
    "siebert/sentiment-roberta-large-english",
    "distilbert-base-uncased-finetuned-sst-2-english",
    "nlptown/bert-base-multilingual-uncased-sentiment"
]

def analyze_sentiment(text):
    if not text or len(text.strip()) < 3:
        logger.warning("Text too short for sentiment analysis")
        return 0.5

    if not Config.HUGGING_FACE_API_KEY or Config.HUGGING_FACE_API_KEY.startswith("your_actual"):
        logger.warning("Hugging Face API key not configured, using keyword-based analysis")
        return keyword_based_sentiment(text)

    headers = {"Authorization": f"Bearer {Config.HUGGING_FACE_API_KEY}"}

    for model in SENTIMENT_MODELS:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        logger.info(f"Trying sentiment model: {model}")

        for attempt in range(3):
            try:
                response = requests.post(api_url, headers=headers, json={"inputs": text}, timeout=30)

                if response.status_code == 503:
                    wait_time = response.json().get('estimated_time', 10)
                    logger.warning(f"Model {model} is loading, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    logger.error(f"Error {response.status_code} from {model}: {response.text}")
                    break

                result = response.json()
                logger.debug(f"Model {model} response: {result}")

                score = parse_sentiment_result(model, result)
                if score is not None:
                    logger.info(f"Successfully analyzed sentiment with {model}: {score}")
                    return score

                break

            except requests.exceptions.Timeout:
                logger.error(f"Timeout with {model} (attempt {attempt+1})")
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error with {model} (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error with {model}: {e}")
                break

    logger.warning("All sentiment models failed, falling back to keyword-based analysis")
    return keyword_based_sentiment(text)

def parse_sentiment_result(model, result):
    if not isinstance(result, list) or len(result) == 0:
        return None

    sentiment_data = result[0]

    if model in ["siebert/sentiment-roberta-large-english", "distilbert-base-uncased-finetuned-sst-2-english"]:
        scores = {item['label'].upper(): item['score'] for item in sentiment_data}
        return scores.get("POSITIVE", 0.5)

    elif model == "nlptown/bert-base-multilingual-uncased-sentiment":
        star_ratings = {}
        for item in sentiment_data:
            if 'star' in item['label']:
                stars = int(item['label'][0])
                star_ratings[stars] = item['score']

        if star_ratings:
            total_score = sum(stars * score for stars, score in star_ratings.items())
            total_weight = sum(star_ratings.values())
            return total_score / (5 * total_weight)

    return None

def keyword_based_sentiment(text):
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'happy', 'joy', 'love', 'wonderful',
        'excited', 'pleased', 'content', 'grateful', 'optimistic', 'bliss', 'calm',
        'peaceful', 'relaxed', 'thankful', 'appreciative', 'serene', 'delighted'
    ]

    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'sad', 'angry', 'hate', 'dislike',
        'upset', 'frustrated', 'disappointed', 'anxious', 'depressed', 'stressed',
        'worried', 'fear', 'scared', 'dread', 'miserable', 'heartbroken', 'lonely'
    ]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > 0 or neg_count > 0:
        total = pos_count + neg_count
        sentiment = pos_count / total if total > 0 else 0.5

        if pos_count > neg_count:
            return min(0.9, 0.5 + (pos_count - neg_count) * 0.1)
        elif neg_count > pos_count:
            return max(0.1, 0.5 - (neg_count - pos_count) * 0.1)

    return 0.5

def recommend_meditation(sentiment_score):
    if sentiment_score < 0.3:
        return {"file": "gratitude.mp3", "name": "Gratitude Meditation"}
    elif sentiment_score < 0.7:
        return {"file": "breathing.mp3", "name": "Breathing Exercise"}
    else:
        return {"file": "focus.mp3", "name": "Focus Meditation"}

# -------------------------------
# IntaSend Payment Helpers
# -------------------------------

def verify_webhook_signature(payload, signature):
    if not Config.INTASEND_SECRET_KEY or Config.INTASEND_SECRET_KEY.startswith("your_actual"):
        logger.error("IntaSend secret key not configured")
        return False

    secret = Config.INTASEND_SECRET_KEY.encode('utf-8')
    expected_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

def initiate_intasend_payment(amount, email, first_name, last_name, redirect_url, callback_url):
    if (not Config.INTASEND_PUBLIC_KEY or Config.INTASEND_PUBLIC_KEY.startswith("your_actual") or
        not Config.INTASEND_SECRET_KEY or Config.INTASEND_SECRET_KEY.startswith("your_actual")):
        logger.error("IntaSend API keys not configured")
        return None

    url = "https://payment.intasend.com/api/v1/checkout/"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Config.INTASEND_SECRET_KEY}'
    }

    payload = {
        "public_key": Config.INTASEND_PUBLIC_KEY,
        "amount": amount,
        "currency": "KES",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "redirect_url": redirect_url,
        "callback_url": callback_url
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Payment initiated successfully: {data.get('invoice', {}).get('id')}")
        return data.get("url")

    except requests.exceptions.RequestException as e:
        logger.error(f"Payment initiation failed: {e}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response error: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during payment initiation: {e}")
        return None

def verify_intasend_payment(invoice_id):
    if not Config.INTASEND_SECRET_KEY or Config.INTASEND_SECRET_KEY.startswith("your_actual"):
        logger.error("IntaSend secret key not configured")
        return False

    url = f"https://payment.intasend.com/api/v1/checkout/{invoice_id}/"
    headers = {
        'Authorization': f'Bearer {Config.INTASEND_SECRET_KEY}'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        status = data.get("state", "").upper()
        logger.info(f"Payment verification for {invoice_id}: {status}")
        return status == "COMPLETE"

    except requests.exceptions.RequestException as e:
        logger.error(f"Payment verification failed: {e}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response error: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during payment verification: {e}")
        return False
