from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import current_user, login_required
from extensions import db
from models import User
from datetime import datetime
import requests
import hmac
import hashlib
import json
from config import Config

premium_bp = Blueprint('premium_bp', __name__)  # Consistent _bp naming

@premium_bp.route('/premium')
@login_required
def premium():
    """
    Render the premium membership page with feature comparison.
    """
    free_features = [
        {"icon": "fas fa-headphones", "text": "2 Basic Meditation Sessions"},
        {"icon": "fas fa-book", "text": "Limited Journal History (Last 5 entries)"},
        {"icon": "fas fa-chart-line", "text": "Basic Mood Tracking"}
    ]

    premium_features = [
        {"icon": "fas fa-crown", "text": "6 Exclusive Premium Sessions"},
        {"icon": "fas fa-database", "text": "Unlimited Journal History"},
        {"icon": "fas fa-chart-pie", "text": "Advanced Mood Analytics & Insights"},
        {"icon": "fas fa-lightbulb", "text": "Personalized AI Recommendations"},
        {"icon": "fas fa-ad", "text": "Ad-Free Experience"},
        {"icon": "fas fa-bolt", "text": "Priority Support"}
    ]

    # Check if the payment gateway is properly configured
    payment_configured = not (
        Config.INTASEND_PUBLIC_KEY.startswith(("your_actual", "test_")) or
        Config.INTASEND_SECRET_KEY.startswith(("your_actual", "test_")) or
        not Config.INTASEND_PUBLIC_KEY or
        not Config.INTASEND_SECRET_KEY
    )

    return render_template(
        'premium.html',
        free_features=free_features,
        premium_features=premium_features,
        payment_configured=payment_configured, # Pass this to the template
        user_is_premium=current_user.is_premium # Also pass explicitly
    )


@premium_bp.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    """
    Initiate a payment with IntaSend. Redirects user to payment gateway.
    """
    # Check if user is already premium
    if current_user.is_premium:
        flash('You are already a Premium Member! Thank you for your support. 💚', 'info')
        return redirect(url_for('dashboard_bp.dashboard'))

    # Check payment configuration
    if not current_app.config.get('PAYMENT_CONFIGURED', False):
        flash('Payment system is currently undergoing maintenance. Please try again later.', 'warning')
        return redirect(url_for('premium_bp.premium'))

    amount = request.form.get('amount', '5.00')  # Default amount

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
            "first_name": current_user.first_name or current_user.username, # Use more specific field if available
            "last_name": current_user.last_name or "",
            "redirect_url": url_for('premium_bp.payment_success', _external=True),
            "callback_url": url_for('premium_bp.payment_webhook', _external=True),
            "metadata": { # Add metadata to track user in webhook
                "user_id": current_user.id,
                "email": current_user.email
            }
        }

        # Remove empty fields to avoid API errors
        payload = {k: v for k, v in payload.items() if v}

        response = requests.post(
            "https://payment.intasend.com/api/v1/checkout/",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses

        payment_data = response.json()
        payment_url = payment_data.get("url")

        if not payment_url:
            raise ValueError("No payment URL received from IntaSend")

        return redirect(payment_url)

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Payment initiation failed (Network/API Error): {e}")
        flash('We couldn\'t connect to the payment service. Please check your connection and try again.', 'danger')
    except ValueError as e:
        current_app.logger.error(f"Payment initiation failed (Invalid Response): {e}")
        flash('Received an invalid response from the payment service. Please try again.', 'danger')
    except Exception as e:
        current_app.logger.error(f"Payment initiation failed (Unexpected Error): {e}")
        flash('An unexpected error occurred. Please try again or contact support if the problem persists.', 'danger')

    return redirect(url_for('premium_bp.premium'))


@premium_bp.route('/payment-success')
@login_required
def payment_success():
    """
    Handle successful payment redirect from IntaSend.
    This is a secondary confirmation; the webhook is the primary source of truth.
    """
    if not current_user.is_premium:
        # The webhook should handle this, but this is a fallback
        current_user.is_premium = True
        current_user.premium_since = datetime.utcnow()
        db.session.commit()
        current_app.logger.info(f"User {current_user.id} upgraded via success-redirect fallback.")

    flash('🎉 Welcome to Mindful Minutes Premium! Your subscription is now active. Enjoy exclusive content and features.', 'success')
    return redirect(url_for('dashboard_bp.dashboard'))


@premium_bp.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """
    Process payment webhook from IntaSend. This is the primary source of truth for payment status.
    """
    # Verify webhook signature
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get("X-IntaSend-Signature")

        if not signature:
            current_app.logger.warning("Webhook received without signature. Rejecting.")
            abort(403)

        # Compute expected signature
        secret = Config.INTASEND_SECRET_KEY.encode('utf-8')
        expected_signature = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()

        # Compare signatures securely
        if not hmac.compare_digest(signature, expected_signature):
            current_app.logger.error("Webhook signature verification failed. Potential fraud.")
            abort(403)

        # Parse payload
        data = json.loads(payload)

    except (ValueError, json.JSONDecodeError) as e:
        current_app.logger.error(f"Invalid webhook JSON payload: {e}")
        return "Invalid payload", 400
    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {e}")
        return "Server error", 500

    # Process the event
    if data.get("state") == "COMPLETE":
        try:
            customer_email = data.get("email")
            if not customer_email:
                current_app.logger.error("Webhook missing customer email")
                return "Email required", 400

            # Find user by email from webhook data
            user = User.query.filter_by(email=customer_email).first()
            if not user:
                current_app.logger.error(f"Webhook for unknown email: {customer_email}")
                return "User not found", 404

            # Upgrade user if not already premium
            if not user.is_premium:
                user.is_premium = True
                user.premium_since = datetime.utcnow()
                db.session.commit()
                current_app.logger.info(f"User {user.id} ({user.email}) successfully upgraded via webhook.")
            else:
                current_app.logger.info(f"Webhook received for already premium user: {user.email}")

            return "", 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to process webhook for {data.get('email')}: {e}")
            return "Processing failed", 500

    else:
        # Log other states for debugging (e.g., "PENDING", "FAILED")
        current_app.logger.info(f"Webhook received with state: {data.get('state')} for {data.get('email')}")
        return "", 200