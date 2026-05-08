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
    start = time.time()
    run_id = f"run-{int(start)}"
    stage = "start"

    logging.info("[%s] STEP 0: /run called", run_id)

    try:
        stage = "load_user"
        logging.info("[%s] STEP 1: %s", run_id, stage)
        user = get_user(user_id=1)
        if not user:
            return jsonify({"status": "error", "run_id": run_id, "stage": stage, "error": "No user found"}), 404

        stage = "fetch_articles"
        logging.info("[%s] STEP 2: %s", run_id, stage)
        articles = fetch_articles(user["interests"])
        if not articles:
            return jsonify({"status": "ok", "run_id": run_id, "stage": stage, "message": "No articles found"}), 200

        stage = "filter_new"
        logging.info("[%s] STEP 3: %s", run_id, stage)
        new_articles = filter_new_articles(user["id"], articles)
        if not new_articles:
            return jsonify({"status": "ok", "run_id": run_id, "stage": stage, "message": "No new articles today"}), 200

        stage = "summarize"
        logging.info("[%s] STEP 4: %s", run_id, stage)
        summary = summarize_articles(new_articles, user["interests"])

        stage = "send_email"
        logging.info("[%s] STEP 5: %s", run_id, stage)
        send_briefing(user["email"], summary)

        stage = "mark_sent"
        logging.info("[%s] STEP 6: %s", run_id, stage)
        mark_articles_sent(user["id"], new_articles)

        dur_ms = int((time.time() - start) * 1000)
        return jsonify({
            "status": "success",
            "run_id": run_id,
            "articles_sent": len(new_articles),
            "duration_ms": dur_ms
        }), 200

    except Exception as e:
        logging.exception("[%s] FAILED at stage=%s", run_id, stage)
        return jsonify({"status": "error", "run_id": run_id, "stage": stage, "error": str(e)}), 500

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
