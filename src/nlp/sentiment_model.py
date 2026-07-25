"""Sentiment analysis wrapper."""

def get_sentiment(text):
    from transformers import pipeline
    classifier = pipeline("sentiment-analysis")
    result = classifier(text[:512])[0]
    return result
