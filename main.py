from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd
import os

app = FastAPI()

# Enable CORS (for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
API_KEY = os.getenv("API_KEY")

# News fetching logic
def fetch_news():
    if not API_KEY:
        raise ValueError("❌ API_KEY is missing in environment variables.")

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=India&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize=100&"
        f"apiKey={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(f"NewsAPI Error: {data.get('message')}")

    articles = data.get("articles", [])
    if not articles:
        return pd.DataFrame()

    df = pd.DataFrame(articles)
    expected_columns = ['title', 'description', 'url']
    available_columns = [col for col in expected_columns if col in df.columns]

    if not available_columns:
        return pd.DataFrame()

    df = df[available_columns]
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

# Category tagging
def assign_category(row):
    text = (row.get('title', '') + " " + row.get('description', '')).lower()

    if any(word in text for word in ['modi', 'election', 'bjp', 'parliament', 'congress']):
        return 'Politics'
    elif any(word in text for word in ['economy', 'gdp', 'inflation', 'budget', 'bank']):
        return 'Economy'
    elif any(word in text for word in ['ai', 'space', 'isro', 'tech', 'nasa', 'quantum']):
        return 'Science & Tech'
    elif any(word in text for word in ['climate', 'pollution', 'environment', 'green']):
        return 'Environment'
    elif any(word in text for word in ['us', 'china', 'pakistan', 'russia', 'un']):
        return 'International Affairs'
    elif any(word in text for word in ['governance', 'bureaucracy', 'reform']):
        return 'Governance'
    else:
        return 'Miscellaneous'

# API endpoint
@app.get("/news")
def get_categorized_news():
    try:
        df = fetch_news()

        if df.empty:
            return {"news": []}

        df['category'] = df.apply(assign_category, axis=1)
        return {"news": df.to_dict(orient="records")}

    except Exception as e:
        print("❌ Server Error:", str(e))
        return {"error": "Internal Server Error", "details": str(e)}
