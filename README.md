# ha-klikomanager

Home Assistant custom component for [Klikomanager](https://klikomanager.com).  
This integration exposes the Dutch Klikomanager household waste collection schedule as a Home Assistant calendar and can optionally sync pickups into an existing calendar (for example an iCloud/CalDAV calendar).

## Installation (as custom component)

- **Step 1**: Install the integration via HACS (Custom repository) or copy the `custom_components/klikomanager` folder from this repository into the `custom_components` folder of your Home Assistant installation.  
  - Example path: `/config/custom_components/klikomanager`
- **Step 2**: Restart Home Assistant.
- **Step 3**: In Home Assistant go to **Settings → Devices & Services → Integrations → Add integration**.
- **Step 4**: Search for **Klikomanager** and follow the UI steps:
  - enter your Klikomanager **card number** and **password**;
  - optionally select a **target calendar** (e.g. `calendar.afval_kalender`) where waste pickup events will be created.

> Note: Klikomanager is a Dutch container / household waste management system.  
> This integration logs in to klikomanager.com with your card number + password and retrieves the waste collection calendar from their API.

## Development notes

- The integration creates a **calendar entity** named “Klikomanager Afvalkalender”.
- Data is fetched via a `DataUpdateCoordinator` in `__init__.py` that:
  - logs in with card number + password,
  - retrieves the waste calendar from the Klikomanager API,
  - and exposes it as Home Assistant calendar events.
- The coordinator refreshes **once per day**.
- When a target calendar is configured:
  - upcoming Klikomanager pickup dates (up to 60 days ahead) are created as events in that calendar via `calendar.create_event`;
  - for each combination of **date + fraction** only a single event is created (keys are stored in the config entry options to avoid duplicates).


