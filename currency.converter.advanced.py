import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
import requests
import numpy as np
from sklearn.linear_model import LinearRegression
import yfinance as yf
import os
from dotenv import load_dotenv
from alpha_vantage.foreignexchange import ForeignExchange

load_dotenv()

# -------- Ρυθμίσεις ----------
LANGUAGES = {
    "en": {
        "title": "🚀 Advanced Currency Analytics",
        "convert": "Convert",
        "historical": "Historical Trends",
        "alerts": "Rate Alerts",
        "predict": "Predictions",
        "api_mode": "Use Alpha Vantage API (Advanced)",
        "no_api_warning": "Using free ECB/CoinGecko data (limited)"
    },
    "el": {
        "title": "🚀 Προηγμένος Μετρητής & Ανάλυση Νομισμάτων",
        "convert": "Μετατροπή",
        "historical": "Ιστορικά Δεδομένα",
        "alerts": "Ειδοποιήσεις",
        "predict": "Προβλέψεις",
        "api_mode": "Χρήση Alpha Vantage API (Για προχωρημένους)",
        "no_api_warning": "Χρήση δωρεάν δεδομένων ECB/CoinGecko (περιορισμένα)"
    }
}

# -------- API Functions ----------
def fetch_rates(use_alpha_vantage=False):
    """Λήψη δεδομένων ανάλογα με την επιλογή API"""
    rates = {}
    
    # Προσθήκη δεδομένων από ECB
    try:
        ecb_data = requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml").text
        for line in ecb_data.split("\n"):
            if 'currency=' in line and 'rate=' in line:
                currency = line.split('currency="')[1].split('"')[0]
                rate = line.split('rate="')[1].split('"')[0]
                rates[currency] = float(rate)
        rates["EUR"] = 1.0
    except:
        pass
    
    # Προσθήκη δεδομένων από Alpha Vantage (αν επιλεγεί)
    if use_alpha_vantage and os.getenv("ALPHA_VANTAGE_API_KEY"):
        try:
            av = ForeignExchange(key=os.getenv("ALPHA_VANTAGE_API_KEY"))
            av_rates, _ = av.get_currency_exchange_rate(from_currency="USD", to_currency="EUR")
            rates["USD"] = float(av_rates["5. Exchange Rate"])
        except:
            pass
    
    # Προσθήκη κρυπτονομισμάτων από CoinGecko
    try:
        crypto_data = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,eur").json()
        rates["BTC"] = crypto_data["bitcoin"]["usd"]
        rates["ETH"] = crypto_data["ethereum"]["usd"]
    except:
        pass
    
    return rates

# -------- Main App ----------
def main():
    st.set_page_config(layout="wide")
    lang = LANGUAGES["el"] if st.session_state.get("lang", "el") == "el" else LANGUAGES["en"]

    # Sidebar ρυθμίσεις
    with st.sidebar:
        st.button("ΕΛ/EN", on_click=lambda: st.session_state.update(lang="en" if st.session_state.get("lang") == "el" else "el"))
        use_alpha_vantage = st.checkbox(lang["api_mode"])
        if not use_alpha_vantage:
            st.warning(lang["no_api_warning"])
        
    # Καρτέλες
    tab1, tab2, tab3, tab4 = st.tabs([lang["convert"], lang["historical"], lang["alerts"], lang["predict"]])

    with tab1:
        # Μετατροπέας
        rates = fetch_rates(use_alpha_vantage)
        if not rates:
            st.error("Δεν βρέθηκαν δεδομένα!")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Ποσό", min_value=0.0, value=1.0)
            from_curr = st.selectbox("Από", list(rates.keys()))
        with col2:
            to_curr = st.selectbox("Σε", list(rates.keys()))
        
        if st.button(lang["convert"]):
            converted = (amount / rates[from_curr]) * rates[to_curr]
            st.success(f"**Αποτέλεσμα:** {converted:.2f} {to_curr}")

    with tab2:
        # Ιστορικά γραφήματα
        currency_pair = st.selectbox("Επιλογή νομίσματος", ["EUR/USD", "EUR/GBP", "BTC/USD"])
        data = yf.download(f"{currency_pair.replace('/', '')}=X", period="1y")
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'])])
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Ειδοποιήσεις
        st.info("Αυτή η λειτουργικότητα απαιτεί API Key (ενεργοποιήστε το Alpha Vantage)")

    with tab4:
        # Προβλέψεις ML
        days = st.slider("Ημέρες για πρόβλεψη", 1, 30, 7)
        if st.button("Πρόβλεψη EUR/USD"):
            prediction = predict_future_rates("EURUSD", days)
            st.metric("Προβλεπόμενη τιμή", f"{prediction:.2f}")

if __name__ == "__main__":
    main()