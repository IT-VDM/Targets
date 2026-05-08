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


## Aangepast in v9

- Opgelost: bij kwartaalcontrole werd het Streamlit `DeltaGenerator` object zichtbaar.
- Oorzaak: `st.success(...) if ... else st.error(...)` stond als losse expressie in de app.
- Oplossing: vervangen door een gewone `if/else`, zodat alleen de statusmelding zichtbaar blijft.
