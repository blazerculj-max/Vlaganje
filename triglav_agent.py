import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
from datetime import datetime

# --- KONFIGURACIJA ---
OPENAI_API_KEY = "TVOJ_API_KLJUČ"
URL_TECAJNICA = "https://www.triglavinvestments.si/tecajnica/"

class TriglavAIAsistent:
    def __init__(self):
        self.letni_donos_ocena = 0.07 

    def nalozi_zgodovinske_podatke(self, pot_do_datoteke):
        """
        Prebere CSV datoteko, ki si jo prenesel s Triglavove strani.
        Predpostavljamo stolpca: 'Datum' in 'Vrednost enote premoženja (VEP)'.
        """
        try:
            df = pd.read_csv(pot_do_datoteke, sep=';', decimal=',')
            df['Datum'] = pd.to_datetime(df['Datum'], dayfirst=True)
            df = df.sort_values(by='Datum')
            return df
        except Exception as e:
            print(f"Napaka pri branju CSV: {e}")
            return None

    def izracunaj_preteklost_proti_danes(self, df, datum_zacetka, vlozek):
        """
        Izračuna, koliko bi imel danes, če bi vložil na specifičen datum.
        """
        datum_zacetka = pd.to_datetime(datum_zacetka)
        
        # Poiščemo najbližji razpoložljiv datum v preteklosti
        start_row = df.iloc[(df['Datum'] - datum_zacetka).abs().argsort()[:1]]
        vep_start = start_row['VEP'].values[0]
        vep_danes = df.iloc[-1]['VEP'] # Zadnja vrstica v tabeli
        
        st_enot = vlozek / vep_start
        vrednost_danes = st_enot * vep_danes
        donos_v_procentih = ((vep_danes / vep_start) - 1) * 100
        
        return {
            "vlozek": vlozek,
            "vrednost_danes": round(vrednost_danes, 2),
            "donos_pct": round(donos_v_procentih, 2),
            "datum_vstopa": start_row['Datum'].values[0]
        }

    def izracunaj_izgubo_zaradi_cakanja(self, mesecni_vlozek, let, zamuda_leta):
        """
        Primerjava: Začetek danes vs. začetek čez X let.
        """
        r = self.letni_donos_ocena / 12
        
        def fv(n_meseci):
            return mesecni_vlozek * (((1 + r)**n_meseci - 1) / r) * (1 + r)

        danes_fv = fv(let * 12)
        zamuda_fv = fv((let - zamuda_leta) * 12)
        
        return {
            "danes": round(danes_fv, 2),
            "zamuda": round(zamuda_fv, 2),
            "razlika": round(danes_fv - zamuda_fv, 2)
        }

    def generiraj_ai_porocilo(self, podatki):
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Uporabnik je v preteklosti vložil {podatki['vlozek']} EUR. 
        Danes je ta naložba vredna {podatki['vrednost_danes']} EUR ({podatki['donos_pct']}% donos).
        
        Glede na trenutne novice v letu 2026 (npr. stabilizacija obrestnih mer, rast tech sektorja), 
        kaj bi mu svetoval za naslednjih 10 let? Bodi kritičen do tveganj.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "Si oster finančni analitik."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# --- TESTIRANJE ---
if __name__ == "__main__":
    bot = TriglavAIAsistent()
    
    # 1. Scenarij: Izguba zaradi čakanja
    izguba = bot.izracunaj_izgubo_zaradi_cakanja(200, 15, 3)
    print(f"Če čakaš 3 leta, izgubiš: {izguba['razlika']} EUR!")

    # 2. Scenarij: Zgodovina (če imaš CSV)
    # df = bot.nalozi_zgodovinske_podatke('triglav_sklad.csv')
    # if df is not None:
    #     zgodovina = bot.izracunaj_preteklost_proti_danes(df, '2015-01-01', 10000)
    #     print(f"Vložek 10k leta 2015 bi bil danes: {zgodovina['vrednost_danes']} EUR")
