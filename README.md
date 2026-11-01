# 🥗 AI Meal & Fitness Planner

A Streamlit app that creates a personalized 7-day meal plan, workout plan, and grocery list using the Groq API.

## Features
- Calculates BMI, maintenance calories, and a daily calorie target (Mifflin-St Jeor formula)
- Goals: lose weight, maintain, gain muscle
- Supports Pakistani/Desi cuisine, budget in PKR, allergies, and diet types
- Workout plan matched to level, equipment, and workout days
- Weekly grocery list and daily habits
- Download the full plan as Markdown

## Run locally
```bash
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"   # Windows: set GROQ_API_KEY=your_key_here
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app (main file: `app.py`).
3. In **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
4. Deploy.

Get a free API key at [console.groq.com](https://console.groq.com).

## Disclaimer
This app gives general guidance only and is not medical advice. Consult a doctor or registered dietitian for health conditions, pregnancy, or if you are under 18.
