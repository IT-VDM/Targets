
# Target Verdeling & Commissie Tool - Marcel v7

## Starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Aangepast in v7

- Opgelost: bij klikken op "Verdeel gelijk over 12 maanden" worden nu ook de maandinputvelden zelf bijgewerkt.
- Opgelost: bij klikken op "Verdeel volgens 2025-seizoen" worden nu ook de maandinputvelden zelf bijgewerkt.
- Opgelost: bij klikken op "Maak totaal passend" worden nu de huidige manueel ingegeven maandwaarden correct gelezen en aangepast.
- De oorzaak was Streamlit session_state: de number_input widgets bewaren hun eigen key-waarde los van de interne targets.
