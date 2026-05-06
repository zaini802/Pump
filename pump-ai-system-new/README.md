# ⚙️ AI-Assisted Pump Design & Selection Platform

A professional industrial-grade pump engineering system.

## 🚀 Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🤖 AI Advisor (Free)
1. Get a free Groq API key at https://console.groq.com
2. Enter it in the sidebar → AI Advisor section

## 📁 Project Structure
```
pump-ai-system/
├── app.py                  ← Main dashboard (run this)
├── requirements.txt
├── config/settings.py      ← 10 themes + constants + fluid DB
├── modules/                ← Pump models (centrifugal/recip/plunger/gear)
├── calculations/           ← Head, power, losses, NPSH
├── graphs/                 ← Plotly performance curves
├── ai/                     ← Groq AI advisor
├── theory/                 ← Engineering knowledge base
├── ui/                     ← Theme CSS + sidebar
└── utils/                  ← Validators + unit converters
```

## Standards
API 610 / API 674 / API 676 · ANSI/HI 1.1-6.5 · ISO 5199 · Perry's 9th Ed.
