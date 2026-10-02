# Punkt 5 – Knowledge Base Design und Quellenstrategie

## Ziel

Die Knowledge Base bildet das fachliche Fundament des BI-Tutors.

Sie soll sicherstellen, dass Antworten auf verlässlichen, vorlesungsspezifischen Inhalten basieren und nicht auf allgemeinem Internetwissen.

Damit wird fachliche Konsistenz gewährleistet und das Risiko von Halluzinationen reduziert.

---

## 1. Rolle der Knowledge Base

Die Knowledge Base dient als zentrale Wissensquelle für das Retrieval-Augmented Generation (RAG)-System.

Ihre Hauptfunktionen sind:

- Bereitstellung relevanter Inhalte für Nutzeranfragen
- Sicherstellung von Quellenbezug und Nachvollziehbarkeit
- Unterstützung der Antwortgenerierung auf Basis valider Informationen

---

## 2. Anforderungen an die Knowledge Base

Die Wissensbasis muss:

- fachlich korrekt sein
- inhaltlich vollständig für den definierten Themenbereich sein
- strukturiert und maschinenlesbar vorliegen
- mit Metadaten angereichert sein
- regelmäßig überprüfbar und erweiterbar sein

---

## 3. Quellenstrategie

---

### Primäre Quellen

Die primäre Wissensbasis besteht aus:

- Vorlesungsfolien der Veranstaltung *Business Intelligence & Analytics*
- offizielle Übungsunterlagen
- bereitgestellte Skripte / Reader
- Musterlösungen und Fallbeispiele

Diese Quellen bilden die verbindliche fachliche Grundlage.

---

### Sekundäre Quellen

Zur Ergänzung können genutzt werden:

- wissenschaftliche Lehrbücher
- frei zugängliche Fachartikel
- seriöse Online-Ressourcen

Sekundäre Quellen werden nur eingesetzt, wenn sie mit der Lehrmeinung kompatibel sind.

---

## 4. Strukturmodell der Knowledge Base

Die Inhalte werden in semantisch sinnvolle Wissenseinheiten zerlegt.

Jede Einheit enthält:

- eigentlichen Textinhalt
- Themenkategorie
- Quelle
- Kapitel / Vorlesungseinheit
- Seitennummer / Foliensatz
- Schlagwörter

---

### Beispielstruktur

| Feld | Inhalt |
|---|---|
| Text | Definition von Data Warehouse |
| Kategorie | Data Warehousing |
| Quelle | Vorlesung 3 |
| Seite | Folie 12 |
| Keywords | DWH, Inmon, Architektur |

---

## 5. Technische Aufbereitung

Die Dokumente werden verarbeitet durch:

- PDF-Extraktion
- Textbereinigung
- Chunking in geeignete Abschnitte
- Metadatenanreicherung
- Speicherung in Vektor- oder Dokumentdatenbank

---

## 6. Qualitätskriterien der Wissensbasis

Die Knowledge Base wird anhand folgender Kriterien bewertet:

- Abdeckung relevanter Vorlesungsinhalte
- Präzision der extrahierten Informationen
- Konsistenz der Metadaten
- Retrieval-Qualität bei Suchanfragen

---

## 7. Strategischer Nutzen

Eine gut strukturierte Wissensbasis ermöglicht:

- höhere Antwortqualität
- präzisere Quellenangaben
- bessere Nachvollziehbarkeit
- effizientere Testfallgenerierung

Sie ist damit ein zentraler Erfolgsfaktor des Systems.

---

## Ergebnis

Es wurde ein strukturiertes Design für die Knowledge Base definiert, das sowohl die inhaltliche Qualität als auch die technische Nutzbarkeit für den BI-Tutor sicherstellt.
