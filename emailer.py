"""
Email delivery via Resend's HTTPS API.

We're not using Gmail SMTP because Render's free tier blocks all outbound
SMTP traffic (any port). HTTPS goes through fine, so we use Resend.

Required env vars:
  RESEND_API_KEY  — from https://resend.com/api-keys
  SENDER_ADDRESS  — defaults to onboarding@resend.dev (works without
                    domain verification, but the recipient must be the
                    email you signed up to Resend with)
"""

import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
SENDER_ADDRESS = os.getenv("SENDER_ADDRESS", "onboarding@resend.dev")


def send_briefing(to_email: str, summary: str):
    """Send the daily briefing email via Resend HTTPS API."""
    html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
    <h2 style="color: #333;">📰 Your Daily Briefed Digest</h2>
    <hr style="border: none; border-top: 1px solid #eee;">
    <div style="line-height: 1.8; color: #444;">
      {summary.replace(chr(10), '<br>')}
    </div>
    <hr style="border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">
      Briefed — your personal AI news agent
    </p>
  </body>
</html>
"""

    text_body = (
        "Your Daily Briefed Digest\n"
        "--------------------------\n"
        f"{summary}\n"
        "--------------------------\n"
        "Briefed — your personal AI news agent\n"
    )

    response = resend.Emails.send({
        "from": SENDER_ADDRESS,
        "to": [to_email],
        "subject": "📰 Your Daily Briefed Digest",
        "html": html_body,
        "text": text_body,
    })

    print(f"✅ Briefing sent to {to_email} (resend id: {response.get('id')})")
    return response


if __name__ == "__main__":
    from fetcher import fetch_articles
    from summarizer import summarize_articles

    interests = "artificial intelligence, European economics"
    articles = fetch_articles(interests)
    summary = summarize_articles(articles, interests)
    # In local testing, send to whoever you registered Resend with.
    test_recipient = os.getenv("TEST_RECIPIENT", SENDER_ADDRESS)
    send_briefing(test_recipient, summary)