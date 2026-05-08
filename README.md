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


## Aangepast in v11

Toegevoegd bovenop de huidige versie:

- Maandprogress bars
- Kwartaalprogress bars
- Nog te behalen bedrag per maand en per kwartaal
- Commissie preview per kwartaal
- Duidelijke targetstatus:
  - Target niet gehaald
  - Target gehaald
  - Commissie actief
- Extra Excel-tabblad: Maandprogress

Visuele logica:
Targetverdeling = plannen · Progress bars = opvolgen · Commissieoverzicht = resultaat


## Aangepast in v12

Toegevoegd:

- Admin-tab **Omzetcijfers**
  - Omzet 2025 aanpasbaar
  - Effectieve omzet 2026 aanpasbaar
- Admin-tab **Prognose**
  - Prognose aan/uit
  - Startmaand prognose
  - Prognosegroei per maand
- Lege toekomstige maanden kunnen automatisch aangevuld worden met prognoseomzet.
- Prognosewaarden worden in de tool aangeduid als **Prognose** en in tekst cursief weergegeven.
- Commissie-preview en progress bars kunnen nu rekenen met effectieve omzet + prognose.
- Excel-export bevat de type-aanduiding Effectief / Prognose.


## Aangepast in v13

- Prognoselogica aangepast:
  - De ingestelde maand is nu de **referentiemaand**.
  - De prognose start vanaf de maand **na** de referentiemaand.
  - Voorbeeld: referentiemaand maart + 10% groei:
    - april = maart × 1,10
    - mei = april × 1,10
    - juni = mei × 1,10
- Teksten in de Admin-tab zijn aangepast naar **Referentiemaand voor prognose**.
