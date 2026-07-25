"""Correlates sentiment with stock returns."""

def correlate_with_returns(ticker, sentiment_score):
    import yfinance as yf
    import pandas as pd
    data = yf.download(ticker, period="6mo")
    data["return_3d"] = data["Adj Close"].pct_change(3).shift(-3)
    return data["return_3d"].corr(pd.Series([sentiment_score]*len(data)))
