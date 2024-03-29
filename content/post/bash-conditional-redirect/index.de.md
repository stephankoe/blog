---
title: "Bedingte Umleitung der Kommando-Ausgabe in Bash-Skripten"
description: "Wie kann man die Ausgabe eines Kommandos in Bash in eine Datei umleiten, wenn eine Bedingung erfüllt ist?"
date: 2024-03-27T17:42:52+08:00
image: 
math: false
categories:
  - bash
  - programming
  - linux
keywords:
  - Bash
  - Redirection
  - Redirect
  - Parameter expansion
  - Shell
  - Routing
  - stdout
  - stdin
  - stderr
  - Condition
  - If-else statement
  - Tee
weight: 1
---

# Bedingte Umleitung der Kommando-Ausgabe in Bash-Skripten

## Problem

Heute kam ein Kollege mit folgender Frage auf mich zu:

> Wie kann ich die Ausgabe meines Kommandos in Bash in eine Datei umleiten, wenn eine Bedingung erfüllt ist?

Konkret möchte er mittels einer Umgebungsvariable `$PDEBUG` die Ausgabe des Kommandos steuern. Wenn diese Variable den Wert `true` enthält, sollen die Standardausgabe- (stdout) und Standardfehler-Streams (stderr) nicht nur auf der Konsole ausgegeben werden, sondern zusätzlich in jeweils einer Datei `run.log` und `run.err` gespeichert werden.

Die Herausforderung ist hierbei, dass der Umleitungsoperator `>` nicht einfach an den Befehl mittels einer Variable angehängt werden kann, da er ansonsten als Eingabeargument interpretiert werden würde. Bei Verwendung von If-Else müsste der Befehl entweder wiederholt oder in eine Funktion gekapselt werden. Und eine Lösung mittels `eval` führt zu weiterer Komplexität, da auf das korrekte Quoting und auf mögliche Angriffsflächen durch Shell-Injection geachtet werden muss.

## Lösung

## Kernpunkte