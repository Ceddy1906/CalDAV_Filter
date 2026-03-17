# CalDAV Filter Calendar

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant Custom Component, das CalDAV/Nextcloud-Kalender nach Schlüsselwörtern filtert und die gefilterten Ereignisse als `CalendarEntity`-Instanzen bereitstellt – ideal als **Kalender-Trigger in Automationen**.

---

## Funktionsweise

```
CalDAV-Server (z. B. Nextcloud)
    └── Koordinator pollt alle N Minuten
         └── Filtert Ereignisse nach Titel- und/oder Beschreibungs-Schlüsselwort
              └── Erstellt eine CalendarEntity pro Filter
                   └── Nutzbar als Trigger in HA-Automationen
```

Pro konfiguriertem Filter entsteht **eine eigene Kalender-Entität**. Mehrere Filter können auf denselben Kalender zeigen, mit unterschiedlichen Schlüsselwörtern.

---

## Voraussetzungen

- Home Assistant (getestet auf Home Assistant OS)
- Zugang zu einem CalDAV-Server (z. B. Nextcloud, Radicale, Baikal)
- Python-Paket `caldav >= 0.9` (wird automatisch von HA installiert)

---

## Installation

### Manuell

1. Ordner `caldav_filter` in `config/custom_components/` kopieren.
2. Home Assistant neu starten.

### HACS (Custom Repository)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL des Repositories eingeben, Kategorie „Integration" wählen.
3. Integration installieren und HA neu starten.

---

## Einrichtung

### Schritt 1 – Verbindung

**Einstellungen → Geräte & Dienste → Integration hinzufügen → CalDAV Filter Calendar**

| Feld | Beschreibung |
|------|-------------|
| CalDAV URL | Vollständige URL zum CalDAV-Endpunkt, z. B. `https://nextcloud.example.com/remote.php/dav/principals/users/meinuser/` |
| Benutzername | CalDAV-Benutzername |
| Passwort | CalDAV-Passwort |
| Abrufintervall (Minuten) | Wie oft der Server abgefragt wird (Standard: 15 Min.) |

Nach erfolgreicher Verbindung werden die verfügbaren Kalender automatisch erkannt.

### Schritt 2 – Ersten Filter anlegen

| Feld | Beschreibung |
|------|-------------|
| Entitätsname | Anzeigename der Kalender-Entität in HA |
| Kalender | Kalender aus dem Dropdown auswählen |
| Icon | MDI-Icon (z. B. `mdi:calendar-star`) |
| Titel-Schlüsselwort *(optional)* | Nur Ereignisse, deren **Titel** dieses Wort enthält |
| Beschreibungs-Schlüsselwort *(optional)* | Nur Ereignisse, deren **Beschreibung** dieses Wort enthält |

Beide Schlüsselwörter können kombiniert werden (AND-Verknüpfung). Leer lassen bedeutet „kein Filter".

---

## Filter verwalten

Über **Einstellungen → Geräte & Dienste → CalDAV Filter Calendar → Konfigurieren**:

- **Filter hinzufügen** – neuen Filter/Entität erstellen
- **Filter bearbeiten** – Namen, Kalender, Icon oder Schlüsselwörter ändern
- **Filter löschen** – Entität entfernen
- **Verbindungseinstellungen** – Abrufintervall anpassen

Jede Änderung lädt die Integration automatisch neu.

---

## Nutzung in Automationen

Die erzeugten Kalender-Entitäten erscheinen unter `calendar.*` und können direkt als **Kalender-Trigger** verwendet werden:

```yaml
automation:
  trigger:
    - platform: calendar
      event: start
      entity_id: calendar.mein_filter
  action:
    - service: notify.mobile_app
      data:
        message: "Ereignis beginnt: {{ trigger.calendar_event.summary }}"
```

---

## Technische Details

| Eigenschaft | Wert |
|-------------|------|
| Domain | `caldav_filter` |
| Plattform | `calendar` |
| IoT-Klasse | `cloud_polling` |
| Vorausschau | 60 Tage |
| Mindestanforderung | `caldav >= 0.9` |

### Zeitzonen

- Ganztägige Ereignisse (`date`) und naive `datetime`-Werte werden normalisiert.
- Alle Zeiten werden intern in UTC verarbeitet.
- Wiederkehrende Ereignisse (RRULE) werden vom CalDAV-Server expandiert.

---


## Unterstützte Sprachen

- Englisch
- Deutsch
- Spanisch
- Französisch

---

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.
