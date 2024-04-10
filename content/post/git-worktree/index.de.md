---
title: "Parallele Arbeit an mehreren Branches desselben Repositories"
description: ""
date: 2024-04-10T17:33:14+08:00
image: 
math: false
categories:
  - programming
  - version management
keywords:
  - git
  - Versionskontrolle
  - Programmierung
weight: 1
---

# Parallele Arbeit an mehreren Zweigen desselben Repositories

## Problem

Wenn man in Git an einem Zweig bereits Aenderungen vorgenommen hat, aber gleichzeitig auch an einem anderen Zweig arbeiten moechte, dann ist ein Wechsel des aktiven Zweigs notwendig. 
Dies kann im Arbeitsalltag z.B. auftreten, wenn man an mehreren Features gleichzeitig arbeitet, einer Kollegin oder einem Kollegen bei einer Frage oder einem Problem unterstuetzen moechte, 
oder kurz einen Fehler in einem vor kurzem fertiggestellten Feature beheben muss.

Bei (noch) nicht von Git getrackten Dateien ist der Wechsel zwar direkt moeglich, aber in einigen Situationen kann der Wechsel zum Verlust dieser Dateien fuehren.
Bei bereits von Git getrackten Dateien jedoch blockiert der Client den Wechsel, sodass man die Aenderungen zunachst zuruecksetzen muss, d.h. es muss zunaechst das Arbeitsverzeichnis 
bereinigt werden (engl.: *clean working tree*).

Der gaengige Weg das Arbeitsverzeichnis in Git zu bereinigen ist, ohne die Aenderungen zu verlieren, ist `git stash`. 
Dieser Befehl verschiebt die Aenderungen in einen lokalen Zwischenspeicher, von wo sie spaeter mittels `git stash apply` einfach wieder zurueckgeholt werden koennen.

Eine Alternative ist es, die noch unfertigen Aenderungen direkt zu committen und sie spaeter mittels `git commit --amend` zu erweitern.

Nervig, nur nacheinander, Risiko von Fehlern (z.B. Mergen von Commits, Merges bei stage apply)🚧

Die dritte Moeglichkeit ist das erneute Klonen des Repositories. Dieser Klon ist allerdings vollstaendig unabhaengig von den anderen Kopien, d.h. er muss auch getrennt von anderen Klonen 
aktualisiert werden und lokale Zweige sowie Stashes sind nicht verfuegbar. Zudem speichern alle Klone jeweils die gesamte Versionshistorie, was zusaetzlich Speicher kostet.

## Loesung

Einen Mittelweg bietet der Befehl `git worktree`. Dieser Befehl erlaubt es, mehrere Zweige desselben Repositories auf einem Rechner gleichzeitig auszuchecken, wobei die jeweiligen Kopien
sich den gleichen Zustand teilen.

Um einen anderen Zweig auszuchecken, fuehrt man vom Arbeitsverzeichnis des bereits geklonten Repositories den folgenden Befehl aus:

```bash
git worktree add ../project-1_branch-2 branch-2
```

Dieser Befehl erzeugt eine Kopie des Repositories im Verzeichnis `../project-1_branch-2` (der Pfad ist beliebig waehlbar) und wechselt in dieser Kopie in den Zweig `branch-2`. 
Dieses Verzeichnis kann anschliessend einfach in einer IDE oder einem Code-Editor geoeffnet und bearbeitet werden.
Falls `branch-2` noch nicht existiert, wird das Argument `-b` benoetigt, um diesen Zweig zu erzeugen.

Dieses neue Verzeichnis ist allerdings abhaengig vom urspruenglichen Klon. Dies ist daran zu erkennen, dass sich darin statt eines Verzeichnisses `.git` lediglich eine Datei mit diesem Namen findet.
Diese Datei ist ein Verweis auf den urspruenglichen Klon, welcher weiterhin die Ground-Truth bildet.🚧 Das heisst, der Originalklon sollte nicht geloescht werden.

Um ein zusaetzliches Arbeitsverzeichnis wieder zu entfernen, bietet Git den Befehl:

```bash
git worktree remove ../project-1_branch-2
```

Hier gibt man wiederum den Pfad zum zusaetzlichen Arbeitsverzeichnis an, in diesem Beispiel `../project-1_branch-2`. 
Git wird daraufhin dieses Verzeichnis unwiderruflich loeschen, es sei denn, es gibt darin noch Aenderungen, die nicht committed worden sind.

Es koennen ein Zweig zur gleichen Zeit nicht in mehreren Arbeitsverzeichnissen ausgecheckt werden.🚧

Laut [Dokumentation](https://git-scm.com/docs/git-worktree) ist der `git worktree`-Befehl in der aktuellen Version 2.44.0 noch experimentell.
Vor allem ist die Unterstuetzung von Submodulen noch nicht vollstaendig und es wird dazu geraten, bei "Superprojekten" diese Funktionalitaet nicht zu verwenden.

## Referenzen

- https://git-scm.com/docs/git-worktree
