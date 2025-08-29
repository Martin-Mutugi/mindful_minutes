from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from extensions import db
from models import User
from datetime import datetime
import requests, hmac, hashlib, json
from config import Config

premium_bp = Blueprint('premium', __name__)

@premium_bp.route('/premium')
@login_required
def premium():
    free_features = [
        "Access to 2 basic meditation sessions",
        "Limited journal entries (max 5)",
        "Basic mood tracker"
    ]

    premium_features = [
        "Access to 6 exclusive premium meditation sessions",
        "Unlimited journal entries",
        "Advanced mood analytics",
        "Personalized recommendations",
        "Ad-free experience"
    ]

    return render_template(
        'premium.html',
        free_features=free_features,
        premium_features=premium_features
    )

@premium_bp.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    if current_user.is_premium:
        flash('✅ You are already a premium member!', 'info')
        return redirect(url_for('dashboard.dashboard'))

    if (Config.INTASEND_PUBLIC_KEY.startswith("your_actual") or 
        Config.INTASEND_SECRET_KEY.startswith("your_actual")):
        flash('⚠️ Payment system not configured. Please try again later.', 'danger')
        return redirect(url_for('premium.premium'))

    amount = request.form.get('amount', '5.00')

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.INTASEND_SECRET_KEY}'
        }

        payload = {
            "public_key": Config.INTASEND_PUBLIC_KEY,
            "amount": amount,
            "currency": "KES",
            "email": current_user.email,
            "first_name": current_user.username,
            "last_name": current_user.username,
            "redirect_url": url_for('premium.payment_success', _external=True),
            "callback_url": url_for('premium.payment_webhook', _external=True)
        }

        response = requests.post(
            "https://payment.intasend.com/api/v1/checkout/",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        payment_data = response.json()
        return redirect(payment_data.get("url"))

    except Exception as e:
        print(f"❌ Payment initiation error: {e}")
        flash('Payment initiation failed. Please try again later.', 'danger')
        return redirect(url_for('premium.premium'))

@premium_bp.route('/payment-success')
@login_required
def payment_success():
    if not current_user.is_premium:
        current_user.is_premium = True
        current_user.premium_since = datetime.utcnow()
        db.session.commit()
        print(f"✅ User {current_user.email} upgraded via success redirect")

    flash('🎉 Payment successful! Welcome to Premium. You now have access to exclusive content.', 'success')
    return redirect(url_for('dashboard.dashboard'))

@premium_bp.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    try:
        payload = request.data.decode('utf-8')
        data = json.loads(payload)
    except Exception as e:
        print(f"❌ Invalid webhook payload: {e}")
        return "", 400

    signature = request.headers.get("X-IntaSend-Signature")
    secret = Config.INTASEND_SECRET_KEY.encode("utf-8")
    expected_signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature or "", expected_signature):
        print("⚠️ Webhook signature mismatch!")
        return abort(403)

    if data.get("state") == "COMPLETE":
        email = data.get("email")
        user = User.query.filter_by(email=email).first()

        if user and not user.is_premium:
            user.is_premium = True
            user.premium_since = datetime.utcnow()
            db.session.commit()
            print(f"✅ User {email} upgraded to premium via webhook")

    return "", 200
