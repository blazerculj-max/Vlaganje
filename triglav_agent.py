import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai
from datetime import datetime, timedelta
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Naložimo okoljske spremenljivke (za lokalno testiranje)
load_dotenv()

# Nastavitve strani
st.set_page_config(page_title="Triglav AI Investicijski Asistent", layout="wide")

# --- FUNKCIJE ---

def get_live_prices():
    """Pridobi trenutne tečaje s Triglavove strani."""
    url = "https://www.triglavinvestments.si/tecajnica/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        podatki = []
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                ime = cols[0].text.strip()
                cena = cols[1].text.strip().replace(' €', '').replace(',', '.')
                try:
                    podatki.append({"Sklad": ime, "Cena (VEP)": float(cena)})
                except: continue
        return pd.DataFrame(podatki)
    except:
        return pd.DataFrame(columns=["Sklad", "Cena (VEP)"])

def ai_analiza(donos, znesek, obdobje):
    """Generira AI komentar glede na trenutno leto 2026."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ OpenAI API ključ ni nastavljen v .env ali Streamlit Secrets."
    
    client = openai.OpenAI(api_key=api_key)
    prompt = f"Investitor je v {obdobje} letih ustvaril {donos}% donosa in ima {znesek}€. Piši kot oster finančni strateg v letu 2026. Upoštevaj AI boom in inflacijo. Bodi kratek."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "Si finančni analitik za sklade."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "AI storitev trenutno ni na voljo."

# --- STRAN (UI) ---

st.title("📈 Triglav AI Investicijski Asistent")
st.markdown("Analiza skladov v realnem času s pomočjo umetne inteligence.")

# Stranska vrstica za vnose
st.sidebar.header("Parametri naložbe")
vlozek = st.sidebar.number_input("Mesečni vložek (€)", value=200, step=10)
leta = st.sidebar.slider("Obdobje varčevanja (let)", 1, 30, 15)
pripricakovan_donos = st.sidebar.slider("Pričakovan letni donos (%)", 1.0, 15.0, 7.0) / 100

# 1. LIVE PODATKI
st.subheader("🌐 Trenutni tečaji (Live Scraping)")
df_live = get_live_prices()
if not df_live.empty:
    st.dataframe(df_live, use_container_width=True)
else:
    st.warning("Ni bilo mogoče pridobiti podatkov v živo. Preveri povezavo.")

st.divider()

# 2. KALKULATOR IZGUBE ZARADI ČAKANJA
st.subheader("⏳ Izguba zaradi čakanja (Cost of Delay)")
col1, col2 = st.columns(2)

def izracun_fv(v, r, t):
    return v * (((1 + r/12)**(t*12) - 1) / (r/12)) * (1 + r/12)

fv_danes = izracun_fv(vlozek, pripricakovan_donos, leta)
fv_zamuda = izracun_fv(vlozek, pripricakovan_donos, leta - 3)
izguba = fv_danes - fv_zamuda

with col1:
    st.metric("Vrednost (začni danes)", f"{fv_danes:,.2f} €")
    st.metric("Vrednost (čez 3 leta)", f"{fv_zamuda:,.2f} €")

with col2:
    st.error(f"Izguba zaradi 3-letnega čakanja: {izguba:,.2f} €")
    st.info("To je moč obrestno-obrestnega računa, ki ga zamujaš.")

# 3. ZGODOVINSKA ANALIZA (CSV)
st.divider()
st.subheader("📜 Zgodovinska simulacija (iz /data mape)")

# Poskusimo naložiti CSV
csv_path = "data/triglav_podatki.csv"
if os.path.exists(csv_path):
    df_hist = pd.read_csv(csv_path, sep=';', decimal=',')
    df_hist['Datum'] = pd.to_datetime(df_hist['Datum'], dayfirst=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist['Datum'], y=df_hist['VEP'], mode='lines', name='Vrednost enote'))
    st.plotly_chart(fig, use_container_width=True)
    
    # AI Komentar
    if st.button("Generiraj AI strateški komentar"):
        with st.spinner("AI analizira trg..."):
            komentar = ai_analiza(round(pripricakovan_donos*100, 1), round(fv_danes, 2), leta)
            st.write(komentar)
else:
    st.info("Za zgodovinski graf naloži CSV datoteko v mapo `data/` na GitHubu.")
