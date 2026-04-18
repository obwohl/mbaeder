# Analyse der GitHub-Actions Engpässe (Choke-Points)

## Problembeschreibung
Das Problem ist, dass die Abfragen über die GitHub Actions oft nicht, bzw. mit sehr großen zeitlichen Lücken durchgeführt wurden. Die Raw-Daten-CSV-Datei weist Lücken auf. Zuvor wurde als "Trick" in einer stündlichen Action (cron: `7 * * * *`) eine Bash-Schleife mit `sleep 600` implementiert, um den Runner eine Stunde lang offen zu halten und 6 Ausführungen abzuarbeiten.

Dieses Setup verursachte jedoch das Problem, dass die nachfolgenden Action-Runs oftmals gar nicht erst starteten oder von GitHub übersprungen wurden.

## Analyse der Workflow Runs über die GitHub API
Ein Blick auf die letzten Runs der "Scrape SWM Auslastung" Action mittels `gh run list` bzw. der GitHub API verdeutlichte das Problem:

- Run 24560225308: Start: 10:21 Uhr (Update: 11:12)
- Run 24556523735: Start: 08:50 Uhr (Update: 09:41)
- Run 24550683729: Start: 06:10 Uhr (Update: 07:01)
- Run 24546409909: Start: 03:38 Uhr (Update: 04:29)

Das Workflow-File definierte eigentlich den Start zur 7. Minute jeder Stunde. Stattdessen wurden die Runs hochgradig asynchron und mit riesigen Lücken (von teilweise 2-3 Stunden) ausgeführt.

## Die Ursache (Der Choke-Point)

1. **Best-Effort Scheduling von GitHub:** `cron` bei GitHub Actions ist keine Echtzeit-Garantie, sondern "Best-Effort". Wenn ein Repo oder die gesamte GitHub-Plattform unter Last steht, werden Jobs oft verzögert.
2. **Langlaufende Workflows im Free-Tier:** Indem wir die Workflows künstlich 50-60 Minuten lang blockieren (`sleep 600`), beanspruchen wir dauerhaft Runner-Kapazitäten. GitHubs Scheduler registriert, dass der vorherige Workflow noch läuft oder gerade erst beendet wurde, und verzögert (oder ignoriert) den nächsten stündlichen Trigger, um Overlap zu vermeiden und Fair-Use-Ressourcen im Free-Tier zu managen. Das System verhält sich dann wie in einer verstopften Queue.

## Die Lösung

- **Die Schleife entfernen:** Workflows sollten idealerweise so kurz wie möglich sein. Ein Run sollte die Python-Scripte aufrufen und sich direkt beenden.
- **Zwei kurze Runs pro Stunde:** Wir ändern den Cron auf `7,37 * * * *`. Somit läuft der Runner ca. 10 Sekunden lang zur 7. und zur 37. Minute. Dies verringert die Blockade von GitHub Actions enorm, und die Queue wird zuverlässig abgearbeitet.
- **Dauerhaftes Logging im Repo:** Damit wir solche stillschweigenden Ausfälle des Schedulers besser überwachen können, schreiben wir nun Logging-Daten mit Timestamps direkt in eine Datei (z.B. `execution.log` & `scraper.log`), die vom Workflow committet wird. Wenn GitHub Actions nicht rechtzeitig startet, können wir dies später exakt nachvollziehen.

## Erkenntnis und Update zur Zuverlässigkeit von GitHub Cron
Trotz der Entfernung der künstlichen Blockaden hat sich gezeigt, dass GitHubs interner `cron` Queue nach wie vor extrem unzuverlässig ist. Es fallen weiterhin Datenpunkte aus, manchmal fehlen Daten für 1.5 bis 2 Stunden komplett. Das bedeutet, dass wir die GitHub Action `schedule` Queue nicht nutzen können, wenn wir zuverlässige Daten im Halbstunden-Takt benötigen.

### Empfohlene Lösung (Externes Triggering)
Anstatt sich auf den internen GitHub-Scheduler zu verlassen, sollte die Ausführung der Action von **außen** (via GitHub API und `workflow_dispatch`) angetriggert werden.

Dies kann durch einen kostenlosen Service wie [cron-job.org](https://cron-job.org/) erfolgen, der strikt und zuverlässig jede halbe Stunde einen HTTP POST Request absendet. Alternativ kann das Script auch komplett lokal über einen Cronjob ausgeführt werden. Eine genaue Anleitung dazu befindet sich in der Datei `alternative_scheduling_guide.md`.
