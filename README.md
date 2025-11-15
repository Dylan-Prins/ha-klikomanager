# ha-klikomanager

Home Assistant custom component voor [Klikomanager](https://klikomanager.com).  
Deze integratie zet de ophaaldagen van je afvalkalender in een Home Assistant-agenda.

## Installatie (als custom component)

- **Stap 1**: Kopieer de map `custom_components/klikomanager` uit deze repository naar de `custom_components` map van je Home Assistant-installatie.
  - Voorbeeld pad: `/config/custom_components/klikomanager`
- **Stap 2**: Herstart Home Assistant.
- **Stap 3**: Ga in Home Assistant naar **Instellingen → Apparaten & Diensten → Integraties → + Integratie toevoegen**.
- **Stap 4**: Zoek naar **Klikomanager** en volg de stappen in de UI (kaartnummer + wachtwoord invullen).

> Let op: de integratie logt in bij klikomanager.com met jouw kaartnummer + wachtwoord en haalt daar de afvalkalender op.

## Ontwikkel-notities

- De integratie maakt een **calendar entity** aan met de naam “Klikomanager Afvalkalender”.
- De data wordt opgehaald via een `DataUpdateCoordinator` in `__init__.py` die:
  - inlogt met kaartnummer + wachtwoord,
  - de afvalkalender ophaalt via de Klikomanager API,
  - en deze omzet naar Home Assistant kalender-events.
