# EchoFoundry

**NLP-Driven Event Signal Research Platform**

EchoFoundry is an applied AI-finance research system that ingests corporate communications — like earnings call transcripts and SEC filings — and extracts quantitative signals using NLP.  
It aims to **bridge text and markets**, identifying relationships between linguistic sentiment, tone, and event-driven market behavior.

## 🔍 Core Capabilities
- **Ingestion Layer** – Scrape and store earnings call transcripts and filings  
- **NLP Pipeline** – Clean, tokenize, and analyze tone/sentiment using pretrained transformers (Hugging Face)  
- **Signal Engine** – Link language metrics to post-event price performance (yfinance + vectorbt)  
- **Backtesting Framework** – Evaluate predictive power of linguistic features  
- **API Layer** – Expose key insights via FastAPI for downstream dashboards or research tools  

## 🧠 Week 1 Deliverables
- Repo setup & environment
- Basic data ingestion pipeline
- Baseline sentiment analysis
- Correlation of sentiment with short-term returns

## ⚙️ Installation
```bash
git clone https://github.com/<your-username>/echo-foundry.git
cd echo-foundry
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

## 🧰 Stack
| Layer | Technology |
|-------|-------------|
| NLP | spaCy, Hugging Face Transformers |
| Data | pandas, numpy, SQLite/Postgres |
| Market Data | yfinance |
| Backtesting | vectorbt |
| API | FastAPI |
| Visualization | matplotlib, seaborn |
| Version Control | GitHub |

## 👤 Author
**Brandon Abegglen**  
UNC Chapel Hill | Physics (Quantitative Finance)  
[LinkedIn](https://www.linkedin.com/in/brandonabegglen/)  
📧 brandonabegglen06@gmail.com
