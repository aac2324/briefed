import os
import time
import logging
import socket

import requests
from flask import Flask, jsonify
from dotenv import load_dotenv

from database import initialize_db, get_user, filter_new_articles, mark_articles_sent
from fetcher import fetch_articles
from summarizer import summarize_articles
from emailer import send_briefing

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, force=True)


def log_resolve(host: str):
    """Log DNS resolution to quickly spot host-specific network issues."""
    try:
        ip = socket.gethostbyname(host)
        logging.info("DNS OK: %s -> %s", host, ip)
        return ip
    except Exception as e:
        logging.exception("DNS FAIL: %s (%s)", host, e)
        return None


def guess_host(url: str) -> str | None:
    """Extract hostname from a URL-like string (very small helper)."""
    if not url:
        return None
    try:
        # Avoid importing urllib if you want; but it's stdlib and safe:
        from urllib.parse import urlparse
        return urlparse(url).hostname
    except Exception:
        return None


@app.route("/setup", methods=["POST"])
def setup():
    initialize_db()
    user = get_user(user_id=1)
    if not user:
        from database import create_user
        user_id = create_user(
            email=os.getenv("GMAIL_ADDRESS"),
            interests="artificial intelligence, European economics, geopolitics"
        )
        return jsonify({"status": "created", "user_id": user_id}), 200
    return jsonify({"status": "already exists", "user": user}), 200


@app.route("/run", methods=["POST"])
def run_briefing():
    """Main pipeline endpoint — triggered daily by n8n."""
    start = time.time()
    run_id = f"run-{int(start)}"

    logging.info("[%s] STEP 0: /run called", run_id)

    try:
        # --- STEP 1: Load user ---
        logging.info("[%s] STEP 1: load user from SQLite", run_id)
        user = get_user(user_id=1)
        if not user:
            logging.warning("[%s] No user found", run_id)
            return jsonify({"status": "error", "stage": "load_user", "error": "No user found"}), 404

        # --- STEP 2: Fetch NewsAPI ---
        logging.info("[%s] STEP 2: fetch articles (NewsAPI)", run_id)
        log_resolve("newsapi.org")
        articles = fetch_articles(user["interests"])
        logging.info("[%s] STEP 2 DONE: fetched %s articles", run_id, len(articles) if articles else 0)

        if not articles:
            return jsonify({"status": "ok", "message": "No articles found"}), 200

        # --- STEP 3: Dedup/filter ---
        logging.info("[%s] STEP 3: filter new articles", run_id)
        new_articles = filter_new_articles(user["id"], articles)
        logging.info("[%s] STEP 3 DONE: %s new articles", run_id, len(new_articles) if new_articles else 0)

        if not new_articles:
            return jsonify({"status": "ok", "message": "No new articles today"}), 200

        # --- STEP 4: Summarize (Azure OpenAI) ---
        logging.info("[%s] STEP 4: summarize articles (Azure OpenAI)", run_id)
        # If you have AZURE_OPENAI_ENDPOINT in env, we can resolve it:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_BASE_URL")
        azure_host = guess_host(azure_endpoint) if azure_endpoint else None
        if azure_host:
            log_resolve(azure_host)

        summary = summarize_articles(new_articles, user["interests"])
        logging.info("[%s] STEP 4 DONE: summary generated (len=%s)", run_id, len(summary) if summary else 0)

        # --- STEP 5: Email (SMTP) ---
        logging.info("[%s] STEP 5: send email briefing", run_id)
        log_resolve("smtp.gmail.com")
        send_briefing(user["email"], summary)
        logging.info("[%s] STEP 5 DONE: email sent", run_id)

        # --- STEP 6: Mark sent ---
        logging.info("[%s] STEP 6: mark articles as sent", run_id)
        mark_articles_sent(user["id"], new_articles)
        logging.info("[%s] STEP 6 DONE", run_id)

        dur_ms = int((time.time() - start) * 1000)
        logging.info("[%s] DONE in %sms", run_id, dur_ms)

        return jsonify({
            "status": "success",
            "run_id": run_id,
            "articles_sent": len(new_articles),
            "duration_ms": dur_ms
        }), 200

    except Exception as e:
        logging.exception("[%s] FAILED", run_id)
        # Include stage only if you want—right now we log the step markers anyway.
        return jsonify({"status": "error", "run_id": run_id, "error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.get("/net-test")
def net_test():
    r = requests.get("https://example.com", timeout=10)
    return {"status": "ok", "status_code": r.status_code}


if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
