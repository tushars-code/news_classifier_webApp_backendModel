from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import pandas as pd

app = FastAPI()

# Enable CORS (allow all origins - change in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Hardcoded API Key (⚠️ only for testing)
API_KEY = "855647b8d4ec4d6da6de98ee2c9368e5"

# Fetch news articles
def fetch_news():
    if not API_KEY:
        raise Exception("❌ API_KEY not found.")

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=India&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize=100&"
        f"apiKey={API_KEY}"
    )

    response = requests.get(url)

    print("🌐 HTTP Status Code:", response.status_code)
    print("📝 Raw Response Text:", response.text[:300])  # print first 300 chars

    if response.status_code != 200:
        raise Exception(f"❌ NewsAPI error {response.status_code}: {response.text}")

    try:
        data = response.json()
    except Exception as e:
        raise Exception("❌ Failed to decode JSON from NewsAPI.") from e

    if data.get("status") != "ok":
        raise Exception(f"❌ NewsAPI returned status: {data.get('status')}")

    articles = data.get("articles", [])
    if not articles:
        print("⚠️ No articles found.")
        return pd.DataFrame()

    df = pd.DataFrame(articles)
    expected_columns = ['title', 'description', 'url']
    df = df[[col for col in expected_columns if col in df.columns]]
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# Categorize each article
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
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "details": str(e)},
        )
