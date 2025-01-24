import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ========== Ρυθμίσεις Γλώσσας ==========
LANGUAGES = {
    "en": {
        "title": "💱 Ultimate Currency Converter",
        "amount": "Amount",
        "from_curr": "From Currency",
        "to_curr": "To Currency",
        "convert": "Convert",
        "result": "Converted Amount",
        "history": "Historical Rates (1 Year)",
        "error": "Error fetching data. Please try again later.",
        "switch_lang": "Switch to Greek"
    },
    "el": {
        "title": "💱 Εξαιρετικός Μετατροπέας Συναλλάγματος",
        "amount": "Ποσό",
        "from_curr": "Από Νόμισμα",
        "to_curr": "Σε Νόμισμα",
        "convert": "Μετατροπή",
        "result": "Μετατρεπμένο Ποσό",
        "history": "Ιστορικές Ισοτιμίες (1 Έτος)",
        "error": "Σφάλμα φόρτωσης δεδομένων. Δοκιμάστε ξανά αργότερα.",
        "switch_lang": "Αλλαγή σε Αγγλικά"
    }
}

# ========== Λήψη Δεδομένων ==========
@st.cache_data(ttl=3600)  # Cache για 1 ώρα
def fetch_data():
    try:
        # FIAT από ECB
        ecb_response = requests.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")
        ecb_data = ecb_response.text
        fiat_rates = {"EUR": 1.0}
        
        for line in ecb_data.split("\n"):
            if 'currency="' in line and 'rate="' in line:
                currency = line.split('currency="')[1].split('"')[0]
                rate = line.split('rate="')[1].split('"')[0]
                fiat_rates[currency] = float(rate)
        
        # Crypto από CoinGecko
        crypto_response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,eur")
        crypto_data = crypto_response.json()
        crypto_rates = {
            "BTC": crypto_data["bitcoin"]["eur"],
            "ETH": crypto_data["ethereum"]["eur"]
        }
        
        return {**fiat_rates, **crypto_rates}, None
    except Exception as e:
        return None, str(e)

# ========== Ιστορικά Δεδομένα ==========
def get_historical_data(base_currency, target_currency):
    symbol = f"{base_currency}{target_currency}=X" if base_currency != "BTC" and base_currency != "ETH" else f"{target_currency}-{base_currency}"
    data = pd.DataFrame()
    try:
        data = yf.download(symbol, period="1y")["Close"].reset_index()
    except:
        pass
    return data

# ========== Κύρια Εφαρμογή ==========
def main():
    # Αρχικοποίηση γλώσσας
    if "lang" not in st.session_state:
        st.session_state.lang = "el"
    
    # Λήψη δεδομένων
    rates, error = fetch_data()
    lang = LANGUAGES[st.session_state.lang]
    
    # ===== UI =====
    st.set_page_config(page_title=lang["title"], layout="centered")
    st.title(lang["title"])
    
    # Κουμπί αλλαγής γλώσσας
    if st.button(lang["switch_lang"]):
        st.session_state.lang = "en" if st.session_state.lang == "el" else "el"
        st.experimental_rerun()
    
    # Εμφάνιση σφάλματος αν υπάρχει
    if error:
        st.error(f"{lang['error']}: {error}")
        return
    
    # Μετατροπέας
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(lang["amount"], min_value=0.0, value=1.0, step=0.1)
            from_curr = st.selectbox(lang["from_curr"], list(rates.keys()), index=0)
        with col2:
            to_curr = st.selectbox(lang["to_curr"], list(rates.keys()), index=1)
        
        if st.button(lang["convert"], use_container_width=True):
            converted = (amount / rates[from_curr]) * rates[to_curr]
            st.success(f"**{lang['result']}**: {converted:.4f} {to_curr}")
    
    # Ιστορικά δεδομένα
    st.subheader(lang["history"])
    historical_data = get_historical_data(from_curr, to_curr)
    if not historical_data.empty:
        fig = px.line(historical_data, x="Date", y="Close", labels={"Close": f"{from_curr}/{to_curr}"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(lang["error"])

if __name__ == "__main__":
    main()
