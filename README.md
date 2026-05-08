# Target Verdeling & Commissie Tool - Marcel v8

## Starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Admin login

Login: admin  
Wachtwoord: vdlx1234

## Aangepast in v8

- Aparte pagina: **Config / Admin**
- Afgeschermde instellingen:
  - Groei % t.o.v. 2025
  - Commissiepercentage
  - Minimum aandeel per kwartaal
  - Maximum aandeel per kwartaal
- Target tool toont deze instellingen alleen als vaste waarden.
- Uitlegtekst over commissie gebruikt automatisch het ingestelde commissiepercentage.


## Aangepast in v10

- Standaardverdeling bij eerste opening staat nu op **gelijk verdeeld over 12 maanden**.
- De knop **Verdeel volgens 2025-seizoen** blijft beschikbaar als alternatief.
- De DeltaGenerator-weergave in kwartaalcontrole blijft gecorrigeerd.
