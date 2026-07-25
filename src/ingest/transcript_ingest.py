"""Handles transcript ingestion."""

def ingest_transcript(url, ticker, date):
    import requests
    from bs4 import BeautifulSoup
    html = requests.get(url).text
    text = BeautifulSoup(html, "html.parser").get_text()
    return {"ticker": ticker, "date": date, "text": text}
