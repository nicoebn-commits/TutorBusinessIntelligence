# Systematische Anforderungserhebung

## Ziel

Die Anforderungen an den BI-Tutor wurden systematisch erhoben, um eine belastbare Grundlage für die Entwicklung und Evaluation des Systems zu schaffen.

Die Erhebung orientiert sich an einem strukturierten Vorgehen aus Stakeholderanalyse, Problemidentifikation und Anforderungsableitung.

---

## 1. Vorgehensmodell

Die Anforderungserhebung erfolgte in vier Schritten:

1. **Analyse des Nutzungskontexts**  
   Untersuchung typischer Lernsituationen im Kontext der Vorlesung *Business Intelligence & Analytics*.

2. **Identifikation relevanter Stakeholder**  
   Definition der Hauptnutzergruppen und ihrer Bedürfnisse.

3. **Ableitung von Anforderungen**  
   Überführung der identifizierten Probleme und Ziele in funktionale und nicht-funktionale Anforderungen.

4. **Priorisierung und Validierung**  
   Bewertung der Anforderungen hinsichtlich Relevanz, Umsetzbarkeit und Projektnutzen.

---

## 2. Datengrundlage der Erhebung

Die Anforderungen basieren auf:

- Analyse der Kursaufgabe und Projektziele
- Reflexion typischer Lernprobleme von Studierenden
- Vergleich mit bestehenden Standard-Chatbots
- fachlichen Anforderungen aus dem Vorlesungskontext

---

## 3. Ergebnis der Erhebung

Die systematische Analyse führte zu einem priorisierten Anforderungskatalog, der als Grundlage der folgenden Software Requirements Specification dient.

# Software Requirements Specification (SRS)

---

## 1. Systemkontext

Der BI-Tutor ist ein LLM-basierter Chatbot, der Studierende bei Verständnisfragen, Wiederholung und Prüfungsvorbereitung im Fachgebiet Business Intelligence unterstützt.

Das System basiert auf einer vorlesungsspezifischen Wissensbasis und soll fachlich konsistente, nachvollziehbare und verständliche Antworten liefern.

---

## 2. Zielgruppe

### Primäre Zielgruppe

- Studierende der Wirtschaftsinformatik / Betriebswirtschaft
- Teilnehmende der Vorlesung *Business Intelligence & Analytics*

---

### Sekundäre Zielgruppe

- Tutorinnen und Tutoren
- Lehrende zur Generierung von Übungsfragen oder Lernmaterialien

---

## 3. Stakeholder

| Stakeholder | Interesse |
|---|---|
| Studierende | verständliche, korrekte Lernunterstützung |
| Lehrende | fachlich konsistente Antworten |
| Projektteam | technische Umsetzbarkeit und Evaluierbarkeit |

---

## 4. Problemstellung

Studierende stehen häufig vor folgenden Herausforderungen:

- umfangreiche und komplexe Vorlesungsunterlagen
- abstrakte Konzepte mit hoher Einstiegshürde
- fehlendes individuelles Feedback außerhalb der Lehrveranstaltung
- inkonsistente Antworten allgemeiner LLM-Systeme ohne Bezug zur Vorlesung

Ein spezialisierter Tutor adressiert diese Defizite durch kontextbezogene Unterstützung.

---

## 5. Funktionale Anforderungen

---

### F1 – Dokumentenbasierte Antworten

Das System muss Antworten auf Basis der hinterlegten Vorlesungsunterlagen generieren.

---

### F2 – Quellenangabe

Jede Antwort soll nachvollziehbare Quellenhinweise enthalten.

---

### F3 – Adaptive Erklärung

Das System soll Inhalte auf unterschiedlichem Verständlichkeitsniveau erklären können.

---

### F4 – Glossarfunktion

Fachbegriffe sollen präzise und schnell definiert werden können.

---

### F5 – Themenfokus

Das System soll auf BI-relevante Inhalte beschränkt bleiben und fachfremde Anfragen abgrenzen.

---

## 6. Nicht-funktionale Anforderungen

---

### N1 – Benutzerfreundlichkeit

Die Interaktion soll intuitiv und niedrigschwellig sein.

---

### N2 – Korrektheit

Antworten müssen fachlich korrekt und vorlesungskonform sein.

---

### N3 – Faithfulness

Das System darf keine Inhalte erfinden und muss Unsicherheiten transparent machen.

---

### N4 – Performance

Antworten sollen in angemessener Zeit bereitgestellt werden.

---

### N5 – Skalierbarkeit

Die Wissensbasis soll erweiterbar und wartbar sein.

---

## 7. Priorisierung der Anforderungen

| ID | Anforderung | Priorität |
|---|---|---|
| F1 | Dokumentenbasierung | Hoch |
| F2 | Quellenangabe | Hoch |
| F3 | Adaptive Erklärung | Mittel |
| F4 | Glossarfunktion | Mittel |
| F5 | Themenfokus | Hoch |
| N2 | Korrektheit | Hoch |
| N3 | Faithfulness | Hoch |

---

## 8. Erfolgskriterien

Das System gilt als erfolgreich, wenn:

- relevante BI-Fragen korrekt beantwortet werden
- Quellen nachvollziehbar angegeben werden
- Halluzinationen minimiert werden
- Studierende einen erkennbaren Lernmehrwert erhalten

---

## Ergebnis

Die Anforderungen wurden systematisch erhoben und in einer strukturierten SRS dokumentiert.

Diese bildet die Grundlage für die weitere Entwicklung, Evaluation und Iteration des BI-Tutors.
