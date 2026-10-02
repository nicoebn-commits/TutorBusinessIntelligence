# Punkt 3 – Sammlung konkreter Testfälle

## Ziel

Auf Basis der definierten Testfalltypen wird eine erste Sammlung konkreter Testfälle erstellt.

Diese Testfälle dienen als Grundlage für die Evaluation des Systems und werden im Projektverlauf kontinuierlich erweitert und verbessert.

Die Testfälle werden für wiederholbare Gütemessungen über verschiedene Systemiterationen hinweg genutzt.

---

## 1. Struktur eines Testfalls

Jeder Testfall wird nach einem standardisierten Schema dokumentiert:

- **Testfall-ID**
- **Kategorie / Typ**
- **Eingabefrage**
- **Erwartetes Verhalten / Ground Truth**
- **Bewertungskriterien**
- **Priorität**

---

## 2. Konkrete Testfälle für den BI-Tutor

---

### TC-001

**Kategorie:** Faktenfrage  
**Eingabefrage:**  
„Was ist ein Data Warehouse?“

**Erwartetes Verhalten / Ground Truth:**  
Definition gemäß Vorlesungsunterlagen, inklusive Kerneigenschaften wie subject-oriented, integrated, time-variant und non-volatile.

**Bewertungskriterien:**  
Korrektheit, Vollständigkeit

**Priorität:** Hoch

---

### TC-002

**Kategorie:** Vergleichsfrage  
**Eingabefrage:**  
„Was ist der Unterschied zwischen OLTP und OLAP?“

**Erwartetes Verhalten / Ground Truth:**  
Strukturierter Vergleich hinsichtlich Zweck, Datenmodell, Nutzungskontext und Abfragecharakteristik.

**Bewertungskriterien:**  
Korrektheit, Strukturierung

**Priorität:** Hoch

---

### TC-003

**Kategorie:** Anwendungsfrage  
**Eingabefrage:**  
„Wann ist ein Star-Schema sinnvoll?“

**Erwartetes Verhalten / Ground Truth:**  
Praxisnahe Erklärung mit Bezug auf analytische Datenmodelle und Performancevorteile.

**Bewertungskriterien:**  
Praxisbezug, Transferleistung

**Priorität:** Mittel

---

### TC-004

**Kategorie:** Quellen-/Grounding-Test  
**Eingabefrage:**  
„In welcher Vorlesungseinheit wurde der Gini-Koeffizient behandelt?“

**Erwartetes Verhalten / Ground Truth:**  
Korrekte Quellenangabe mit Modul-/Kapitelbezug.

**Bewertungskriterien:**  
Groundedness, Transparenz

**Priorität:** Hoch

---

### TC-005

**Kategorie:** Adaptive Erklärung  
**Eingabefrage:**  
„Erkläre ETL so, dass es ein Erstsemester versteht.“

**Erwartetes Verhalten / Ground Truth:**  
Didaktisch reduzierte Erklärung ohne unnötige Fachsprache.

**Bewertungskriterien:**  
Verständlichkeit, Zielgruppenanpassung

**Priorität:** Hoch

---

### TC-006

**Kategorie:** Glossar  
**Eingabefrage:**  
„Was bedeutet Slicing & Dicing?“

**Erwartetes Verhalten / Ground Truth:**  
Kurze und präzise Definition mit Bezug auf multidimensionale Analyse.

**Bewertungskriterien:**  
Prägnanz, Korrektheit

**Priorität:** Mittel

---

### TC-007

**Kategorie:** Out-of-Scope  
**Eingabefrage:**  
„Wie funktioniert Blockchain Mining?“

**Erwartetes Verhalten / Ground Truth:**  
Höfliche Ablehnung oder Hinweis auf Themenfokus.

**Bewertungskriterien:**  
Scope Control

**Priorität:** Hoch

---

### TC-008

**Kategorie:** Halluzinationstest  
**Eingabefrage:**  
„Erkläre das Delta-Cube-Modell aus der Vorlesung.“

**Erwartetes Verhalten / Ground Truth:**  
Erkennung, dass dieses Konzept nicht Teil der Wissensbasis ist.

**Bewertungskriterien:**  
Faithfulness, Unsicherheitskommunikation

**Priorität:** Hoch

---

## 3. Nutzung für Gütemessungen

Die Testfälle werden für verschiedene Entwicklungsiterationen wiederholt eingesetzt.

Dadurch lassen sich:

- Leistungsverbesserungen messen
- Regressionen erkennen
- Schwächen systematisch dokumentieren

---

## 4. Erweiterbarkeit

Die Testfallsammlung wird im Verlauf des Projekts erweitert:

- zusätzliche Fragen pro Themengebiet
- unterschiedliche Schwierigkeitsstufen
- Variationen derselben Fragestellung

Ziel ist eine robuste und repräsentative Test-Suite.

---

## Ergebnis

Es wurde eine erste strukturierte Testfallsammlung erstellt, die als Basis für Evaluation, Vergleich und Weiterentwicklung des BI-Tutors dient.
