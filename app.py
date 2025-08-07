# app.py

import os
import re
import pandas as pd
import nltk
import streamlit as st
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from nltk.corpus import stopwords
from textblob import TextBlob
import openai
import httpx

# ---------- SETUP ----------
nltk.download('stopwords', quiet=True)
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    st.error("⚠️ OPENAI_API_KEY not found. Please check your .env file.")
    st.stop()

# Use OpenAI client with disabled SSL verification (if needed)
http_client = httpx.Client(verify=False)
client = openai.OpenAI(api_key=openai_api_key, http_client=http_client)

# ---------- FUNCTIONS ----------

@st.cache_data
def clean_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', str(text).lower())
    words = text.split()
    words = [word for word in words if word not in stopwords.words('english')]
    return " ".join(words)

def get_sentiment(text):
    score = TextBlob(text).sentiment.polarity
    if score > 0.2:
        return 'positive'
    elif score < -0.2:
        return 'negative'
    else:
        return 'neutral'

def generate_summary(reviews):
    try:
        prompt = "Summarize the following customer feedback:\n" + "\n".join(reviews)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

# ---------- STREAMLIT APP ----------

st.set_page_config(page_title="Customer Feedback Analyzer", layout="centered")
st.title("🧠 Smart Customer Feedback Analyzer")
st.markdown("Upload customer reviews, analyze sentiment, and summarize insights using AI.")

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file with a 'reviews.text' column", type="csv")

try:
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("data/sample_reviews.csv")
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# Data cleaning
df = df[df['reviews.text'].notnull()]
df['cleaned_review'] = df['reviews.text'].apply(clean_text)

# Sentiment analysis
df['sentiment'] = df['cleaned_review'].apply(get_sentiment)

# Display metrics
st.subheader("📊 Summary Metrics")
st.write(f"**Total Reviews:** {len(df)}")
st.write(f"**Sentiment Breakdown:**")
st.bar_chart(df['sentiment'].value_counts())

# Generate summary
with st.spinner("Generating AI summary..."):
    summary = generate_summary(df['cleaned_review'].sample(10).tolist())

st.subheader("📝 AI Summary of Feedback")
st.write(summary)