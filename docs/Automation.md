# Punkt 4 – Automatisierung der Testfälle und Gütemessung

## Ziel

Der Evaluationsprozess soll so gestaltet werden, dass Testfälle wiederholt, konsistent und effizient ausgeführt werden können.

Automatisierung ist insbesondere relevant, um verschiedene Systemiterationen objektiv vergleichen zu können.

---

## 1. Motivation für Automatisierung

Manuelle Tests sind:

- zeitaufwendig
- schwer reproduzierbar
- anfällig für subjektive Bewertung

Automatisierung ermöglicht:

- schnelle Regressionstests
- objektivere Vergleichbarkeit
- Skalierung auf größere Testmengen

---

## 2. Automatisierbare Bereiche

---

### A – Testausführung

Fragen aus einer strukturierten Testdatenbank werden automatisiert an den Tutor gesendet.

**Nutzen:**  
Wiederholbare Tests über mehrere Systemversionen hinweg.

---

### B – Antwortspeicherung

Antworten werden systematisch erfasst:

- Testfall-ID
- Systemversion
- Antworttext
- Quellenangabe
- Antwortzeit

---

### C – Metrikberechnung

Automatische Berechnung von:

- Trefferquote
- Antwortzeit
- Quellenquote
- Scope-Erkennung
- Ablehnungsrate

---

### D – Vergleich mit Referenzantworten

Antworten werden gegen Ground Truth geprüft.

Mögliche Verfahren:

- semantische Ähnlichkeit
- Keyword-Matching
- LLM-as-a-Judge

---

## 3. Nicht vollständig automatisierbare Bereiche

Qualitative Aspekte erfordern ergänzend menschliche Bewertung:

- Verständlichkeit
- didaktische Qualität
- Praxisnähe
- Erklärungstiefe

Daher wird ein hybrides Evaluationsmodell verfolgt.

---

## 4. Automatisierungskonzept für den BI-Tutor

### Geplante Toolchain

- Testfälle als CSV / JSON
- API / Benutzerinterface des Tutors
- Python-Skript zur Testausführung
- Excel / Dashboard zur Auswertung

---

### Geplanter Workflow

1. Testfälle laden  
2. Automatisch an den Tutor senden  
3. Antworten speichern  
4. Metriken berechnen  
5. Bericht generieren

---

## 5. Beispielhafte Bewertungsregeln

---

### Quellenprüfung

Wenn eine Antwort einen Quellenhinweis enthält → bestanden

---

### Scope-Test

Wenn irrelevante Fragen korrekt abgelehnt werden → bestanden

---

### Antwortzeit

Unter 5 Sekunden → bestanden

---

### Referenznähe

Ähnlichkeit zur Musterantwort größer als definierter Schwellenwert → bestanden

---

## 6. Nutzen für das Projekt

Die Automatisierung ermöglicht:

- schnelle Tests bei neuen Versionen
- systematische Identifikation von Schwächen
- datenbasierte Nachweise von Verbesserungen

Damit wird der Entwicklungsprozess effizienter und nachvollziehbarer.

---

## Ergebnis

Es wurde ein hybrides Evaluationskonzept definiert, bei dem quantitative Kriterien automatisiert geprüft und qualitative Kriterien ergänzend manuell bewertet werden.
