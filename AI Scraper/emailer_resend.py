"""
Drop-in replacement for emailer.py that uses Resend's HTTPS API instead of SMTP.

Use this if the IPv4-patched SMTP version still fails on Render —
that means Render is blocking outbound SMTP entirely on your free tier
and there is no Python-side workaround.

Setup:
  1. Sign up free at https://resend.com (3,000 emails/month, 100/day).
  2. Verify a sender. For a prototype the fastest path is to use
     onboarding@resend.dev as your "From" — no domain verification needed,
     but you can only send to your own verified email. For sending to
     others, verify a domain you own.
  3. Create an API key in the Resend dashboard.
  4. In Render -> Environment, add:
        RESEND_API_KEY=re_xxx...
        SENDER_ADDRESS=onboarding@resend.dev   (or your verified address)
  5. Add `resend` to requirements.txt.
  6. Rename this file to emailer.py (replacing the SMTP version) OR
     change `from emailer import send_briefing` to import from here.
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
    send_briefing(os.getenv("TEST_RECIPIENT", SENDER_ADDRESS), summary)
