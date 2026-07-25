"""FastAPI service exposing signal endpoints."""

from fastapi import FastAPI
from src.nlp.sentiment_model import get_sentiment

app = FastAPI(title="EchoFoundry API")

@app.get("/")
def root():
    return {"message": "EchoFoundry API running"}

@app.get("/signal")
def signal_endpoint(ticker: str, text: str):
    sentiment = get_sentiment(text)
    return {"ticker": ticker, "sentiment": sentiment}
