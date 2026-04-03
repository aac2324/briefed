import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_briefing(to_email: str, summary: str):
    """
    Sends the daily briefing email.
    
    Args:
        to_email: recipient email address
        summary: the formatted summary string from summarizer.py
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📰 Your Daily Briefed Digest"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email

    # Plain text version
    text_body = f"""
Your Daily Briefed Digest
--------------------------

{summary}

--------------------------
Briefed — your personal AI news agent
    """

    # HTML version (cleaner in email clients)
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

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f"✅ Briefing sent to {to_email}")


# Quick test
if __name__ == "__main__":
    from fetcher import fetch_articles
    from summarizer import summarize_articles

    interests = "artificial intelligence, European economics"
    articles = fetch_articles(interests)
    summary = summarize_articles(articles, interests)
    send_briefing(GMAIL_ADDRESS, summary)
