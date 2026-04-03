from flask import Flask, jsonify
from dotenv import load_dotenv

from database import initialize_db, get_user, filter_new_articles, mark_articles_sent
from fetcher import fetch_articles
from summarizer import summarize_articles
from emailer import send_briefing

load_dotenv()

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run_briefing():
    """Main pipeline endpoint — triggered daily by n8n."""
    try:
        # 1. Load user preferences from SQLite
        user = get_user(user_id=1)
        if not user:
            return jsonify({"error": "No user found"}), 404

        # 2. Fetch articles based on user interests
        articles = fetch_articles(user["interests"])
        if not articles:
            return jsonify({"message": "No articles found"}), 200

        # 3. Filter out already-sent articles
        new_articles = filter_new_articles(user["id"], articles)
        if not new_articles:
            return jsonify({"message": "No new articles today"}), 200

        # 4. Summarize with GPT
        summary = summarize_articles(new_articles, user["interests"])

        # 5. Send email
        send_briefing(user["email"], summary)

        # 6. Mark articles as sent
        mark_articles_sent(user["id"], new_articles)

        return jsonify({
            "status": "success",
            "articles_sent": len(new_articles)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Simple health check so n8n can verify the app is alive."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
