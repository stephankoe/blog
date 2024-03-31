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

Die Herausforderung ist hierbei, dass der Umleitungsoperator `>` nicht einfach an den Befehl mittels einer Variable angehängt werden kann, da er ansonsten als Eingabeargument interpretiert werden würde. Bei Verwendung von If-Else müsste der Befehl entweder wiederholt oder in eine Funktion gekapselt werden. Und eine Lösung mittels `eval` führt zu weiterer Komplexität, da auf das korrekte Quoting und Shell-Injection geachtet werden muss.

## Lösung

Im Folgenden soll `my_command` den Befehl repräsentieren, dessen Ausgabe umgeleitet werden soll. Dieser ist wie folgt definiert:

```bash
function my_command {
    echo "This goes to stdout"
    echo "This goes to stderr" >&2
}
```

Die bedingte Umleitung der Kommandoausgabe lässt sich einer Funktion `write_log` erreichen, welche den Inhalt der Standardeingabe (stdin) einliest und ihn sofort wieder auf stdout schreibt. Dabei wird, sofern `$PDEBUG` wahr ist, gleichzeitig die Eingabe in eine Datei geschrieben. Diese Funktion benötigt dazu den Pfad der Ausgabedatei. Anschließend kann die Standardausgabe von `my_command` einfach mit einer Pipe an `write_log` weitergeleitet werden:

```bash
my_command | write_log run.log
```

Um `write_log` auch zur Umleitung von stderr zu verwenden, muss stderr zunächst mit `2> >(...)`[^erkl] in die Standardeingabe einer Subshell geleitet werden. Innerhalb der Subshell verwenden wir `write_log run.err`, um den Inhalt von stderr in Abhängigkeit von `$PDEBUG` in die Datei `run.err` zu schreiben. Da allerdings `write_log` auf stdout schreibt, müssen wir mittels `>&2` die Standardausgabe an die Standardfehlerausgabe der Subshell weiterleiten, um eine Vermischung von stdout und stderr zu verhindern. Der Aufruf von `my_command` sieht anschließend wie folgt aus:

```bash
my_command \
    2> >(write_log run.err >&2) \
    | write_log run.log \
```

[^erkl]: `2>` leitet stderr um, `(...)` erzeugt eine neue Subshell, welche `...` ausführt und der zweite `>` leitet die Eingabe an den stdin der Subshell weiter.

Um nun eine bedingte Umleitung innerhalb von `write_log` zu erreichen, verwenden wir `tee`[^tee] in Kombination mit Parameterexpansion von Bash-Arrays. Zunächst initialisieren wir ein leeres Bash-Array `$tee_args` und fügen den Pfad der Ausgabedatei hinzu, falls `$PDEBUG` wahr ist. Anschließend führen wir `tee "${tee_args[@]}"` aus. `"${tee_args[@]}"` wandelt jedes Element des Arrays in jeweils ein Argument um und stellt dabei das korrekte Quoting sicher. Dadurch werden Probleme mit Leerzeichen oder gar Bash-Code in Dateinamen vermieden.

[^tee]: Der Name `tee` leitet sich vom T-Stück einer Rohrleitung ab. Analog zu diesem T-Stück leitet `tee` die Eingabe an zwei Ziele weiter. Üblicherweise, aber nicht notwendigerweise, sind dies eine Datei und die Standardausgabe.

Der endgültige Code sieht wie folgt aus:

```bash
PDEBUG="${PDEBUG:-"$1"}"  # debug-mode on/off

function write_log {
    filepath="${1?"File path required!"}"
    tee_args=()
    if "${PDEBUG}"; then
        tee_args+=("${filepath}")
    fi
    tee "${tee_args[@]}"
}

my_command \
    2> >(write_log run.err >&2) \
    | write_log run.log
```

## Kernpunkte

- Die bedingte Weiterleitung in eine Datei wird in einer Funktion gekapselt und die Ausgabe von `my_command` in diese Log-Funktion umgeleitet.
- `tee` speichert eine Kopie der Stream-Inhalte in eine Datei und schreibt sie gleichzeitig auf die Standardausgabe.
- Die Expansion von Bash-Arrays mit `"${args[@]}"` ermöglicht die sichere Handhabung einer variablen Anzahl von Argumenten zur Laufzeit.
- Die Standardfehlerausgabe des Befehls wird mittels `2> >(write_log run.err >&2)` an die Log-Funktion weitergeleitet ohne dabei stderr und stdout zu vermischen.