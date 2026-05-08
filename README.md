
# Target Verdeling & Commissie Tool

Deze tool helpt om de jaartarget van Marcel te verdelen over de maanden en om kwartaalcommissie te simuleren.

## Installatie

Open een terminal in deze map en voer uit:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Functionaliteiten

- Omzet 2025 van Marcel is ingebouwd
- Werkelijke omzet 2026 t.e.m. april is ingebouwd
- Instelbaar groeipercentage
- Automatische berekening van jaartarget
- Maandtargets handmatig aanpasbaar
- Kwartaalcontrole met minimum en maximum aandeel per kwartaal
- Instelbaar commissiepercentage, bijvoorbeeld 2%
- Commissie wordt enkel berekend op omzet boven het kwartaaltarget
- Export naar CSV en Excel

## Commissieformule

Commissie per kwartaal = max(0, werkelijke kwartaalomzet - kwartaaltarget) × commissiepercentage
