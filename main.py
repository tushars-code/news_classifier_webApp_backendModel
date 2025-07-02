from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd

API_KEY = "855647b8d4ec4d6da6de98ee2c9368e5"

app = FastAPI()

# Allow React frontend access (for local or deployed app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use ["http://localhost:3000"] for React dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Your original model logic reused here --
def fetch_news():
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

    if data["status"] != "ok":
        return pd.DataFrame()

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

# -- Expose your logic via API endpoint --
@app.get("/news")
def get_categorized_news():
    df = fetch_news()

    if df.empty:
        return {"news": []}

    df['category'] = df.apply(assign_category, axis=1)
    return {"news": df.to_dict(orient="records")}
