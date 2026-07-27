# Architecture Notes

# Why src/ was removed

The original src/ folder contained prototype code for ingestion, sentiment, API serving, and correlation analysis. It was useful as a rough sketch, but it mixed research logic, API code, and signal evaluation too early. As such, SRC has been removed.

EchoFoundry will use a clearer structure:

- ingest/ — data collection from SEC, transcripts, calendars, and prices
- eatures/ — sentiment, novelty, and topic-surprise feature engineering
- models/ — predictive models and modeling utilities
- acktests/ — event windows, backtest engine, and metrics
- pp/ — FastAPI service code
- config/ — configuration files
- 
otes/ — research notes, dev logs, and threat models
- scripts/ — runnable project commands

The goal is to keep reusable logic separate from scripts and to keep research code separate from production API code.
