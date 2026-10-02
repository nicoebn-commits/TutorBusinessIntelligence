# Punkt 2 – Testfalltypen entwickeln

## Ziel

Die Testfalltypen sollen sicherstellen, dass alle funktionalen und nicht-funktionalen Anforderungen aus der SRS überprüfbar sind.

Wir entwickeln damit ein strukturiertes Testmodell, das später mit konkreten Fragen gefüllt wird.

---

## 1. Ableitung aus den Anforderungen

Die Testfalltypen werden direkt aus den definierten Anforderungen abgeleitet.

| Anforderung | Ziel | Passender Testtyp |
|---|---|---|
| F1 Dokumentenbasierung | prüft Wissensabdeckung | Inhaltsfrage |
| F2 Quellenangabe | prüft Nachvollziehbarkeit | Quellentest |
| F3 Adaptive Erklärung | prüft didaktische Qualität | Verständnistest |
| F4 Glossar | prüft Definitionen | Terminologietest |
| F5 Themenfokus | prüft Scope | Grenzfalltest |
| N2 Korrektheit | prüft Faktentreue | Validierungstest |
| N3 Faithfulness | prüft Halluzinationen | Grounding-Test |

---

## 2. Testfalltypen für den BI-Tutor

---

### Typ A – Wissens-/Faktenfragen

**Zweck:**  
Überprüfung fachlicher Korrektheit bei Standardfragen.

**Ziel:**  
Kann der Tutor Inhalte korrekt wiedergeben?

**Beispiele:**  
- „Was ist ein Data Warehouse?“  
- „Definiere OLAP.“

**Bewertete Kriterien:**  
Korrektheit, Relevanz

---

### Typ B – Vergleichsfragen

**Zweck:**  
Prüfung differenzierter Antworten.

**Ziel:**  
Kann das System Konzepte gegeneinander abgrenzen?

**Beispiele:**  
- „Unterschied zwischen Inmon und Kimball?“  
- „OLTP vs. OLAP?“

**Bewertete Kriterien:**  
Korrektheit, Strukturierung

---

### Typ C – Anwendungsfragen

**Zweck:**  
Prüfung von Transferleistung.

**Ziel:**  
Kann Wissen in Kontext gesetzt werden?

**Beispiele:**  
- „Wann nutzt man ein Star-Schema?“  
- „Gib ein Beispiel für einen ETL-Prozess.“

**Bewertete Kriterien:**  
Praxisnähe, Verständlichkeit

---

### Typ D – Quellen-/Grounding-Tests

**Zweck:**  
Prüfung von Nachvollziehbarkeit.

**Ziel:**  
Kann das System Quellen korrekt benennen?

**Beispiele:**  
- „Auf welcher Folie wird Data Mining behandelt?“

**Bewertete Kriterien:**  
Groundedness, Transparenz

---

### Typ E – Adaptive Erklärtests

**Zweck:**  
Prüfung didaktischer Flexibilität.

**Ziel:**  
Kann die Erklärung an Vorwissen angepasst werden?

**Beispiele:**  
- „Erkläre OLAP einfach.“  
- „Erkläre ETL mit einem Praxisbeispiel.“

**Bewertete Kriterien:**  
Verständlichkeit, Personalisierung

---

### Typ F – Out-of-Scope-Tests

**Zweck:**  
Prüfung der Themenbegrenzung.

**Ziel:**  
Lehnt das System irrelevante Fragen korrekt ab?

**Beispiele:**  
- „Wie backe ich Pizza?“  
- „Wer hat die Champions League gewonnen?“

**Bewertete Kriterien:**  
Scope Control, Negative Rejection

---

### Typ G – Halluzinations-/Robustheitstests

**Zweck:**  
Prüfung auf erfundene Inhalte.

**Ziel:**  
Gibt das System Unsicherheit korrekt zu?

**Beispiele:**  
- absichtlich falsche Fachbegriffe  
- nicht vorhandene Vorlesungsinhalte

**Bewertete Kriterien:**  
Faithfulness, Counterfactual Robustness

---

## 3. Übersichtsmatrix

| Typ | Fokus | Beispiel | Bewertete Kriterien |
|---|---|---|---|
| A | Faktenwissen | Was ist OLAP? | Korrektheit |
| B | Vergleich | Inmon vs. Kimball | Struktur |
| C | Anwendung | ETL-Beispiel | Transfer |
| D | Quelle | Welche Folie? | Grounding |
| E | Erklärung | Einfach erklären | Verständlichkeit |
| F | Scope | Off-topic-Frage | Rejection |
| G | Robustheit | Fake-Begriff | Halluzination |

---

## Ergebnis

Es wurde ein systematisches Testfall-Framework entwickelt, das als Grundlage für die Generierung konkreter Testfälle und die spätere Evaluation dient.
