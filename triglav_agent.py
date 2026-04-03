import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
from datetime import datetime

# --- KONFIGURACIJA ---
OPENAI_API_KEY = "TVOJ_API_KLJUČ_TUKAJ"
URL_TECAJNICA = "https://www.triglavinvestments.si/tecajnica/"

class TriglavAIAsistent:
    def __init__(self):
        self.sklad_ime = "Triglav World" # Primer sklada
        self.letni_donos_ocena = 0.07    # 7% pričakovan donos (konzervativno)

    def pridobi_live_podatke(self):
        """Scrape trenutnih tečajev s spletne strani."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = requests.get(URL_TECAJNICA, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Iskanje tabele s tečaji - Triglav ima specifično strukturo
            podatki = {}
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ime = cols[0].text.strip()
                    cena = cols[1].text.strip().replace(' €', '').replace(',', '.')
                    try:
                        podatki[ime] = float(cena)
                    except ValueError:
                        continue
            return podatki
        except Exception as e:
            return f"Napaka pri pridobivanju podatkov: {e}"

    def izracunaj_nalozbo(self, mesecni_vlozek, let_varcevanja, zamuda_leta=0):
        """Matematični model za izračun donosa in izgube zaradi čakanja."""
        r = self.letni_donos_ocena / 12
        n = (let_varcevanja - zamuda_leta) * 12
        
        # Formula za prihodnjo vrednost periodičnih vplačil
        fv = mesecni_vlozek * (((1 + r)**n - 1) / r) * (1 + r)
        total_vlozek = mesecni_vlozek * n
        profit = fv - total_vlozek
        
        return {
            "koncna_vrednost": round(fv, 2),
            "vlozeno": round(total_vlozek, 2),
            "profit": round(profit, 2)
        }

    def ai_komentar_trga(self, rezultat):
        """AI Agent analizira rezultat in doda 'live' kontekst o svetu."""
        if not OPENAI_API_KEY or "TVOJ" in OPENAI_API_KEY:
            return "Dodaj API ključ za AI analizo."

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Analiziraj naslednji finančni scenarij:
        Vlagatelj vlaga {rezultat['vlozeno']} EUR, končni znesek po varčevanju je {rezultat['koncna_vrednost']} EUR.
        
        Upoštevaj trenutno globalno situacijo v letu 2026 (AI boom, energetska tranzicija, geopolitične napetosti).
        Podaj 2 kritična plusa in 2 minusa za takšno naložbo v prihodnosti. Bodi kratek in oster.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "Si finančni strateg za sklade Triglav."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# --- IZVEDBA ---
if __name__ == "__main__":
    bot = TriglavAIAsistent()
    
    print("--- 1. PRIDOBIVANJE PODATKOV LIVE ---")
    tečaji = bot.pridobi_live_podatke()
    for k, v in list(tečaji.items())[:5]: # Izpis prvih 5
        print(f"{k}: {v} €")

    print("\n--- 2. ANALIZA SCENARIJEV (Primer: 200€/mesec, 15 let) ---")
    danes = bot.izracunaj_nalozbo(200, 15)
    čez_3_leta = bot.izracunaj_nalozbo(200, 15, zamuda_leta=3)
    
    izguba = danes['koncna_vrednost'] - čez_3_leta['koncna_vrednost']
    
    print(f"Če začneš danes: {danes['koncna_vrednost']} €")
    print(f"Če začneš čez 3 leta: {čez_3_leta['koncna_vrednost']} €")
    print(f"KRITIČNA IZGUBA ZARADI ČAKANJA: {round(izguba, 2)} €")

    print("\n--- 3. AI STRATEŠKI POGLED ---")
    print(bot.ai_komentar_trga(danes))
