# ha-klikomanager

Home Assistant custom component voor [Klikomanager](https://klikomanager.com).  
Deze integratie zet de ophaaldagen van je afvalkalender in een Home Assistant-agenda.

## Installatie (als custom component)

- **Stap 1**: Kopieer de map `custom_components/klikomanager` uit deze repository naar de `custom_components` map van je Home Assistant-installatie.
  - Voorbeeld pad: `/config/custom_components/klikomanager`
- **Stap 2**: Herstart Home Assistant.
- **Stap 3**: Ga in Home Assistant naar **Instellingen → Apparaten & Diensten → Integraties → + Integratie toevoegen**.
- **Stap 4**: Zoek naar **Klikomanager** en volg de stappen in de UI (postcode + huisnummer invullen).

> Let op: de eerste versie gebruikt nog **dummy-data**. De echte koppeling met klikomanager.com wordt later toegevoegd.

## Ontwikkel-notities

- De integratie maakt een **calendar entity** aan met de naam “Klikomanager Afvalkalender”.
- De data wordt opgehaald via een `DataUpdateCoordinator` in `__init__.py` (nu nog met een voorbeeld-event).
