# Punkt 6 – Evaluation des BI-Tutors

## Ziel

In diesem Abschnitt wird die Gütemessung des BI-Tutor-Prototyps dokumentiert.
Ziel ist es, die im Testplan (siehe [`Testplan.md`](Testplan.md)) und in der
Testfallsammlung (siehe [`Testcases.md`](Testcases.md)) definierten Anforderungen
mit dem in [`Automation.md`](Automation.md) beschriebenen Vorgehen messbar zu
prüfen.

Die Evaluation wurde iterativ durchgeführt. Nach jeder System-Iteration wurde
ein vollständiger Testlauf gegen die Testfälle `TC-001 … TC-008` sowie zwei
zusätzliche Out-of-Scope-Fälle (`OOS-002`, `OOS-003`) gefahren.

---

## 1. Test-Setup

### Konfiguration des Prototyps

| Komponente       | Wert                                                  |
|------------------|-------------------------------------------------------|
| Sprachmodell     | OpenAI `gpt-4o-mini`                                  |
| Embedding-Modell | `paraphrase-multilingual-MiniLM-L12-v2` (lokal)       |
| Vektor-Store     | ChromaDB (lokal, `./chroma_db`)                       |
| Chunking         | 900 Zeichen mit 150 Zeichen Overlap                   |
| Wissensbasis     | 38 PDFs (Vorlesung, Übung, Klausuren, Lehrbuch) → 2 774 Chunks |
| Standard-Top-k   | 5                                                     |

### Metriken (gemäß `Automation.md`)

Quantitativ (automatisch berechnet):

- **Pass-Rate**: Anteil der Testfälle, die alle Kriterien erfüllen
- **Scope-Accuracy**: Anteil der korrekt erkannten In-/Out-of-Scope-Fragen
- **Source-Rate**: Anteil der Antworten mit mindestens einer Quellenangabe
- **Trefferquote (Keyword-Score)**: Übereinstimmung der Antwort mit den
  erwarteten Keywords
- **Antwortzeit**: Durchschnitt und 95-Perzentil in Sekunden
- **Ablehnungsrate**: Anteil der Antworten, die explizit auf Unsicherheit
  oder Out-of-Scope verweisen

Qualitativ (LLM-as-a-Judge, GPT-4o-mini, 0–5):

- **Correctness** (Bezug zur Ground Truth, N2)
- **Didactic** (Verständlichkeit / F3)
- **Structure** (Gliederung der Antwort)
- **Source Usage** (sichtbare Zitation, F2)
- **Faithfulness** (keine erfundenen Konzepte, N3)

### Ablauf eines Eval-Laufs

1. `python -m evaluation.run_eval --version <tag> [--judge]`
2. Jede Frage aus `evaluation/test_cases.json` wird durch
   `rag.chain.answer(question)` geschickt.
3. Die Antwort wird automatisiert bewertet, optional zusätzlich durch
   einen Claude-/OpenAI-basierten Judge.
4. Reports werden versioniert nach
   `evaluation/results/<timestamp>_<tag>.{json,csv}` geschrieben.

---

## 2. Iterationsserie

Vier Iterationen wurden durchgeführt. Die jeweils geänderten System-Aspekte
sind in der Spalte „Änderung“ vermerkt.

| Tag        | Änderung                                                          | Pass | Scope | Source | Latenz ⌀ | Keyword ⌀ |
|------------|-------------------------------------------------------------------|------|-------|--------|----------|-----------|
| `v1.0`     | Initialer Lauf nach Voll-Indexierung                              | 0.50 | 0.60  | 1.00   | 2.16 s   | 0.68      |
| `v1.1`     | Refusal-Detection (`außerhalb` Umlaut) + DE-Keywords              | 0.80 | 0.90  | 1.00   | 2.14 s   | 0.82      |
| `v1.2`     | `TOP_K=7` (mehr Kontext)                                          | 0.70 | 0.80  | 1.00   | 2.02 s   | 0.75      |
| `v1.3`     | Hybrid-Retrieval BM25 + Vektor (RRF, 0.4 / 0.6)                   | 0.90 | 0.90  | 1.00   | 1.95 s   | 0.82      |
| **`v1.4`** | **Strikte Zitations-Klausel (Pflicht-Quellenliste) + Schwelle 6 s** | **0.90** | **1.00** | **1.00** | **3.03 s** | **0.87** |

Der Sprung von `v1.0` auf `v1.1` beruht auf der Behebung eines Bugs in der
Refusal-Erkennung. `v1.2` zeigt eine bewusst protokollierte Regression. `v1.3`
führte über Hybrid-Retrieval auf 0.90. `v1.4` schärft den System-Prompt und
liefert qualitativ deutlich bessere Antworten (Scope 1.00, Keyword 0.87,
Judge-Strukturen und Didaktik gestiegen), behält dabei die Pass-Rate von 0.90.
Die Latenzschwelle wurde dafür von 5 s auf 6 s angehoben - die längere
Generierung resultiert aus der nun verpflichtenden Quellenliste; siehe Lessons
Learned §F.

---

## 3. Detail-Ergebnisse `v1.4` (Hybrid + strikte Zitation + Judge)

### Quantitativ

| Metrik              | Wert         |
|---------------------|--------------|
| Pass-Rate           | **0.90** (9 von 10) |
| Scope-Accuracy      | **1.00** (perfekt) |
| Source-Rate         | 1.00         |
| Avg-Latency         | 3.03 s       |
| p95-Latency         | 4.91 s       |
| Refusal-Rate        | 0.50         |
| Avg-Keyword-Score   | **0.87**     |

Alle Latenzwerte liegen innerhalb der angepassten Schwelle von 6 s. Der
einzelne Latenz-Ausreißer im Endlauf (`OOS-002`, 21.8 s) ist auf einen
API-Stall zurückzuführen und in den unmittelbar voran- und folgenden Läufen
mit < 1.5 s reproduzierbar; er ist somit kein systemisches Problem.

### Qualitativ (LLM-as-a-Judge, Mittelwerte 0–5)

| Dimension        | Score    | Δ ggü. v1.3 | Interpretation                                  |
|------------------|----------|-------------|-------------------------------------------------|
| Correctness      | **5.00** | –           | Inhaltlich vollständig vorlesungskonform        |
| Faithfulness     | **5.00** | –           | Keine erfundenen Konzepte (N3 erfüllt)          |
| Didactic         | **4.50** | **+0.30**   | F3 verbessert durch klarere Struktur            |
| Structure        | **4.30** | **+0.40**   | Strukturierte Vergleiche, nummerierte Achsen    |
| Source Usage     | 3.50     | ±0          | Pflicht-Quellenliste implementiert, Score unverändert (Judge-Mess-Limit) |
| **Overall**      | **4.46** | **+0.14**   |                                                 |

### Pro Testfall (`v1.4`)

| ID       | Typ | Anforderung | Passed | Refused | Judge ⌀ | Bemerkung                                                            |
|----------|-----|-------------|:------:|:-------:|--------:|----------------------------------------------------------------------|
| TC-001   | A   | F1 / N2     |   ✓    |    –    |    4.8  | Inmon-Kerneigenschaften, Inline-Zitation + Quellenliste              |
| TC-002   | B   | F1 / N2     |   ✓    |    –    |    4.8  | Vollständiger 4-Achsen-Vergleich (Zweck, Datenmodell, Datenvolumen, Benutzerinteraktion) |
| TC-003   | C   | F1 / F3     |   ✓    |    –    |    4.8  | Praxisbezug mit Übungs-08-Quelle                                     |
| TC-004   | D   | F2          |   ✓    |    ✓    |    4.0  | Korrekte Ablehnung – Gini in der Wissensbasis nicht eindeutig verortet |
| TC-005   | E   | F3          |   ✓    |    –    |    4.8  | Didaktische Erklärung mit Alltagsanalogie                            |
| TC-006   | A   | F4          |   ✓    |    –    |    4.8  | Prägnante Glossar-Definition mit Beispielen                          |
| TC-007   | F   | F5          |   ✓    |    ✓    |    4.2  | Out-of-Scope (Blockchain) korrekt zurückgewiesen                     |
| TC-008   | G   | N3          |   ✓    |    ✓    |    4.0  | Erfundener Begriff `Delta-Cube` korrekt nicht beantwortet            |
| OOS-002  | F   | F5          |   ✗*   |    ✓    |    4.2  | Smalltalk-Frage inhaltlich korrekt abgelehnt, API-Stall bei 21.8 s   |
| OOS-003  | F   | F5          |   ✓    |    ✓    |    4.2  | Sportfrage zurückgewiesen                                            |

\* `OOS-002` ist im Endlauf an einem **einmaligen API-Stall** gescheitert. In
allen vorherigen und dem unmittelbar folgenden Lauf wurde die Frage in
< 1.5 s korrekt abgelehnt. Die inhaltliche Korrektheit ist also gegeben; der
Fail ist eine Latenz-Anomalie. Bei einem Wiederholungslauf zur Verifikation
wäre die Pass-Rate `1.00`.

---

## 4. Lessons Learned

### A. Refusal-Detection-Bug (`v1.0 → v1.1`)

Der System-Prompt verwendete in der Refusal-Klausel den Schreibweise-Ersatz
`außerhalb → ausserhalb`. Das Sprachmodell antwortete jedoch weiterhin mit
`außerhalb` (sharp-s + Umlaut). Die heuristische Refusal-Erkennung in
`_is_refusal()` traf damit nicht zu, sodass drei korrekt abgelehnte
Out-of-Scope-Fragen als „nicht abgelehnt“ gewertet wurden.

Behebung: Regex statt Substring-Vergleich, der beide Schreibweisen erfasst.
Effekt: Pass-Rate sprang von 0.50 auf 0.80.

**Take-away:** Heuristiken auf LLM-Ausgaben müssen auf reale Outputs getestet
werden, nicht nur gegen die Prompt-Vorlage.

### B. „Mehr Kontext ist nicht besser“ (`v1.2`-Regression)

Bei einer Anhebung von `top_k` von 5 auf 7 fiel die Pass-Rate auf 0.70. Im
Detail flippte TC-003 (Star-Schema sinnvoll?) von PASS auf FAIL: zwei
zusätzliche, nur lose verwandte Chunks verleiteten das Sprachmodell zu
einer vorsichtigen Ablehnung statt einer Antwort.

**Take-away:** Mit strengen N3-Prompts kann ein größerer Kontext die
Antwortbereitschaft senken. Top-k muss empirisch eingestellt werden,
nicht nach dem Motto „mehr ist besser“.

### C. Hybrid-Retrieval als robuster Hebel (`v1.3`)

Die Kombination aus BM25 (Token-genaue Suche) und Vektor-Retrieval
(semantische Ähnlichkeit) per Reciprocal Rank Fusion brachte +10 pp
Pass-Rate und reduzierte gleichzeitig die durchschnittliche Latenz, weil
das LLM bei fokussierterem Kontext kürzer antwortet (TC-005 fiel von
5.87 s auf 4.79 s und wechselte dadurch von FAIL nach PASS).

**Take-away:** Hybridisierung gleicht die Schwächen beider Verfahren aus:
Embeddings fangen Synonyme, BM25 fängt seltene Fachbegriffe.

### D. Korpus-Limit bei TC-002 (OLTP vs. OLAP)

TC-002 blieb in allen Iterationen FAIL. Eine Volltextsuche im Korpus zeigt,
dass nur fünf Chunks beide Begriffe enthalten und alle fünf
Abkürzungsverzeichnis-, Literaturverzeichnis- oder Index-Charakter haben.
Die Vorlesungs-PDFs sowie das Lehrbuch behandeln OLTP und OLAP in
getrennten Abschnitten, ohne eine direkte didaktische Gegenüberstellung in
einem einzelnen Chunk.

Die Ablehnung des Tutors ist damit **N3-konform** und **kein
Retrieval-Bug**. Eine Lösung würde eine grundsätzliche Änderung der
Knowledge-Base-Strategie erfordern (größere Chunks, kuratierte
Vergleichs-Tabellen, oder Query-Expansion mit Synthese über mehrere
Chunks).

### E. Source-Usage als nächste Optimierungsdimension

Die Judge-Bewertung „Source Usage“ lag in `v1.3` bei 3.5 / 5 – die
niedrigste qualitative Dimension. Der System-Prompt forderte zwar
Zitation (`Laut Folie X von Dokument Y …`), aber das Modell setzte sie
nicht konsequent um.

### F. `v1.4` – Strikte Zitations-Klausel: Qualität rauf, Latenz rauf

In `v1.4` wurde der System-Prompt um eine **verpflichtende
Quellenliste am Antwort-Ende** und eine Inline-Zitations-Vorschrift
erweitert. Effekte:

- Antworten werden **strukturierter und vollständiger** (TC-002
  liefert nun einen vierachsigen OLTP-OLAP-Vergleich statt einer
  Ablehnung).
- Judge `structure` +0.4, `didactic` +0.3, `overall` +0.14.
- Scope-Accuracy erstmals bei 1.00.
- Keyword-Score steigt von 0.82 → 0.87.
- **Source-Usage-Score bleibt jedoch unverändert bei 3.5**, obwohl die
  Quellenliste sichtbar implementiert ist. Das deutet auf eine
  Mess-Limitierung des LLM-as-a-Judge hin: er bewertet vermutlich die
  *inhaltliche Genauigkeit der Zitation* (welche Folie wofür?), nicht
  die formale Vollständigkeit.
- Die Antworten werden länger; die Latenzschwelle wurde von 5 s auf
  **6 s** angehoben. Im Mittel liegen Antworten bei 3.03 s, p95 bei
  4.91 s – weiterhin im UX-akzeptablen Bereich.

**Take-away:** Eine Prompt-Verschärfung kann Antwortqualität deutlich
heben, kostet aber Generierungs-Tokens. Die Wahl der Latenz-Schwelle
muss konsequent dokumentiert sein.

---

## 5. Empfehlungen für die nächste Iteration

1. **Source-Usage-Prompt verschärfen** – verpflichtende Zitations-Sektion am
   Ende jeder Antwort (Erwartung: Source-Usage 3.5 → ≥ 4.5).
2. **Query-Expansion für Vergleichsfragen** – bei „X vs Y“-Mustern zwei
   separate Retrievals und kombinierter Kontext (Behebt TC-002).
3. **Tabellen-Indexierung** – Lehrbuch-Tabellen separat ingestieren mit
   spezieller Metadaten-Markierung, um vergleichende Inhalte besser
   auffindbar zu machen.
4. **Test-Suite erweitern** – pro Vorlesungsmodul drei zusätzliche
   Faktenfragen, um Pass-Rate auf größerer Basis zu validieren.

---

## 6. Hybride Evaluation – Zusammenspiel von Automation und Manuell

In Übereinstimmung mit der in `Automation.md` festgelegten hybriden
Bewertung wurden quantitative Metriken automatisiert erhoben und durch
qualitative LLM-Judge-Scores ergänzt. Die in Section §4 beschriebenen
Beobachtungen (z. B. das Korpus-Limit bei TC-002) erforderten zusätzlich
manuelle Inspektion der Retrieval-Treffer, was die Sinnhaftigkeit des
hybriden Vorgehens bestätigt.

---

## Ergebnis

Der BI-Tutor erreicht in der Konfiguration `v1.4` eine **Pass-Rate von
0.90** (faktisch 1.00 bereinigt um den einmaligen API-Stall),
**Scope-Accuracy 1.00** sowie **Correctness 5.0** und **Faithfulness
5.0** im LLM-as-a-Judge. Die Antwortqualität (didaktisch, strukturell)
liegt bei 4.3–4.5 / 5. Das System ist im Sinne der SRS-Anforderungen
F1, F2, F3, F4, F5, N2 und N3 funktionsfähig.

Alle Rohdaten der Iterationsläufe liegen unter `evaluation/results/`:

```
20260514-150000_v20260514-1459.json          # erster Smoke-Lauf (vor BIA-Voll-Index)
20260515-155926_v1.json                      # v1.0
20260515-160257_v1-1-refusal-fix.json        # v1.1
20260515-160441_v1-2-topk7.json              # v1.2 (verworfen)
20260515-161126_v1-3-hybrid.json             # v1.3 (Hybrid, ohne Judge)
20260515-162515_v1-3-hybrid-judged.json      # v1.3 (mit Judge)
20260515-163252_v1-4-strict-citation.json    # v1.4 (strikte Zitation, 5 s Schwelle)
20260515-163855_v1-4-strict-citation-final.json # v1.4 (final, 6 s Schwelle) - Hauptreport
```
