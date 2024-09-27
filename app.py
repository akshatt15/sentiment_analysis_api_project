from flask import Flask, request, jsonify
import pandas as pd
import requests
import io

app = Flask(__name__)

GROQ_API_URL = "https://api.groq.com/sentiment"  # Example Groq API endpoint
GROQ_API_KEY = "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"  # Replace with your actual API key


# Define a route for the root URL
@app.route('/')
def home():
    return "<h1>Welcome to the Sentiment Analysis API</h1><p>Use the /analyze endpoint to perform sentiment analysis on customer reviews.</p>"


def analyze_sentiment_with_groq(review):
    response = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"text": review}
    )

    if response.status_code == 200:
        result = response.json()
        sentiment = result.get("sentiment", "neutral")
        return sentiment
    else:
        return "error"


@app.route('/analyze', methods=['POST'])
def analyze_reviews():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(file.read()))
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
        else:
            return jsonify({"error": "Invalid file format. Only XLSX or CSV allowed."}), 400

        if 'Review' not in df.columns:
            return jsonify({"error": "Column 'Review' not found in the file."}), 400

        reviews = df['Review'].dropna().tolist()[:50]
        total_reviews = len(reviews)

        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for review in reviews:
            sentiment = analyze_sentiment_with_groq(review)
            if sentiment == "positive":
                sentiment_counts["positive"] += 1
            elif sentiment == "negative":
                sentiment_counts["negative"] += 1
            elif sentiment == "neutral":
                sentiment_counts["neutral"] += 1

        sentiment_scores = {
            "positive": round((sentiment_counts['positive'] / total_reviews) * 100, 2),
            "negative": round((sentiment_counts['negative'] / total_reviews) * 100, 2),
            "neutral": round((sentiment_counts['neutral'] / total_reviews) * 100, 2)
        }

        return jsonify(sentiment_scores)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
