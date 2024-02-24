---
title: "Auto-Start des SSH-Agenten auf Headless-Servern"
description: "Erläuterung der Funktionsweise des SSH-Agenten-Programms von OpenSSH sowie Konfigurationen zum automatischen Starten des zugehörigen Hintergrunddienstes"
url: ssh-agent-autostart
date: 2024-02-21 17:52:37+0800
toc: true
categories:
  - system-administration
  - it-security
keywords:
  - ssh
  - it-security
  - commandline
  - system-administration
  - ssh-agent
  - headless-server
weight: 1
---

# SSH-Agenten auf Headless-Servern automatisch starten

Auf Headless-Servern[^headless] ist üblicherweise kein SSH-Agent vorinstalliert. Wer SSH-Schlüssel bei der Arbeit am Server im Arbeitsspeicher vorhalten möchte, muss daher den SSH-Agenten manuell starten. Die Lebenszeit des SSH-Agenten ist allerdings nicht an die Zeit der aktuellen Sitzung gebunden, das heißt, er besteht nach Beenden der Sitzung fort. Die Verbindungsdaten hingegen gehen bei naiver Verwendung nach der Sitzung verloren, wenn sie lediglich in Umgebungsvariablen gespeichert wurden. Des weiteren ist die Verwendung mehrerer Instanzen des SSH-Agenten ggf. unerwünscht, da jede Instanz ggf. unterschiedliche Schlüssel in den Speicher geladen hat und eine Passworteingabe mehrfach vonnöten ist.

[^headless]: Ein Server ohne graphische Oberfläche

In diesem Artikel erläutere ich daher wie der SSH-Agent auf einem Headless-Server verwendet werden kann, ohne bei jeder neuen Sitzung manuell eine neue Instanz starten zu müssen.

Die Konfiguration von SSH mit kryptographischen Schlüsseln erläutere ich näher in meinem Artikel [Tipps und Tricks: SSH](../ssh).

## Benutzungsmodi von `ssh-agent`

Der SSH-Agent wird mit dem Befehl `ssh-agent` gestartet. Generell bietet die Anwendung zwei Nutzungsvarianten:

- `ssh-agent` startet einen permanent laufenden Hintergrunddienst, gibt die Verbindungsparameter auf der Konsole aus und terminiert.
- `ssh-agent command [arg ...]` startet einen SSH-Agenten im Hintergrund und führt den Befehl `command` mit den gegebenen Argumenten aus. Dieser gestartete Kindprozess erhält die die zur Verbindungsaufnahme nötigen Umgebungsvariablen. Der SSH-Agent terminiert, sobald `command` terminiert.

### Nutzung von `ssh-agent` als Hintergrunddienst

Wie im folgenden Sitzungsprotokoll zu sehen, startet `ssh-agent` den SSH-Agenten-Dienst im Hintergrund, gibt `ssh-agent` die Verbindungsparameter auf der Kommandozeile aus und gibt den Kontrollfluss sofort wieder dem Benutzer zurück.

```bash
user@server:~ $ ssh-agent
SSH_AUTH_SOCK=/tmp/ssh-C0jytHtSL6qw/agent.294541; export SSH_AUTH_SOCK;
SSH_AGENT_PID=294542; export SSH_AGENT_PID;
echo Agent pid 294542;

user@server:~ $ ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
...
user      294528  0.0  0.0   8192  1840 ?        Ss   18:10   0:00 ssh-agent
...
```

Dieser Modus ist laut dem [Handbuch](https://www.man7.org/linux/man-pages/man1/ssh-agent.1.html) für Login-Sitzungen gedacht. Die Ausgabe von `ssh-agent` ist valider Shell-Code und kann mittels des Builtin `eval` ausgeführt werden, wodurch die Verbindungsparameter als Umgebungsvariablen der aktuellen Sitzung zur Verfügung gestellt werden.

### Nutzung von `ssh-agent` als Elternprozess

Für die Verwendung als Elternprozess einer X-Sitzung gedacht ist die Verwendung von `ssh-agent` mit Argumenten. Wird dem Befehl ein Argument übergeben, so startet `ssh-agent` einen SSH-Agenten im Hintergrund, setzt die zur Verbindungsaufnahme nötigen Parameter als Umgebungsvariablen und führt `ssh-agent` das übergebene Programm aus. Das als Kindprozess von `ssh-agent` gestartete Programm kann auf die Umgebungsvariablen mit den Verbindungsparametern zugreifen. 

Dieses Verhalten wird aus folgendem Sitzungsprotokoll ersichtlich. Da der Befehl `ssh-agent` mit dem Programm `bash` gestartet wird, öffnet sich eine neue interaktive Shell. Deshalb unterscheiden sich die Prozess-IDs vor und nach der Ausführung von `ssh-agent bash`. Innerhalb dieser interaktiven Shell sind die nötigen Verbindungsparameter des SSH-Agenten verfügbar und der Prozess des SSH-Agenten ist aktiv. Nach dem Schließen dieser Sitzung befindet sich der Nutzer wieder in der ursprünglichen Sitzung, die Umgebungsvariablen mit den Verbindungsparametern sind nicht mehr verfügbar und auch der SSH-Agenten ist terminiert.

```bash
user@server:~ $ echo $$  # Prozess-ID der aktuellen Sitzung
294449

user@server:~ $ ssh-agent bash

user@server:~ $ echo $$
298358

user@server:~ $ echo $SSH_AGENT_PID $SSH_AGENT_SOCK
298359 /tmp/ssh-C0jytHtSL6qw/agent.298359

user@server:~ $ ps aux | grep ssh-agent
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
...
user      298359  0.0  0.0   8192  1840 ?        Ss   19:06   0:00 ssh-agent bash
...

user@server:~ $ exit

user@server:~ $ echo $$
294449

user@server:~ $ echo $SSH_AGENT_PID $SSH_AGENT_SOCK

user@server:~ $ ps aux | grep ssh-agent
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
```

## Systemkonfiguration

In diesem Kapitel möchte ich mögliche Systemkonfigurationen vorstellen, die

- den SSH-Agenten ohne Zutun im Hintergrund starten, und
- pro Benutzer/Sitzung maximal einen einzigen SSH-Agenten-Prozess verwenden.

### Skript zum Starten einer Instanz von `ssh-agent`

Die grundlegende Idee des Skriptes ist es die Verbindungsdaten für den SSH-Hintergrunddienst in einer Datei abzuspeichern und beim Öffnen einer neuen Sitzung diese Datei zunächst zu überprüfen. Da die darin enthaltenen Sitzungsdaten u.U. ungültig sein können, sind einige Überprüfungen nötig. Der folgende Code-Block enthält eine mögliche Implementierung dieser Idee.

```bash
#!/usr/bin/env bash

XDG_STATE_HOME="${XDG_STATE_HOME:-"${HOME}/.local/state"}"
SSHAF="$XDG_STATE_HOME/ssh/ssh_agent_env"
[ -f "$SSHAF" ] && . "$SSHAF"

if [ -z "$SSH_AGENT_PID" ]; then
  # SSH_AGENT_PID not set, but user has a service already running
  SSH_AGENT_PID="$(pgrep -u "$USER" ssh-agent | head -1)"
elif ! kill -0 "$SSH_AGENT_PID" >/dev/null 2>&1; then
  # User doesn't own SSH_AGENT_PID or no such process
  SSH_AGENT_PID=
elif [ "$(ps "$SSH_AGENT_PID" | tail -1 | awk '{print $NF}')" != "ssh-agent" ]; then
  # Process isn't SSH agent
  SSH_AGENT_PID=
fi

if [ -z "$SSH_AGENT_PID" ]; then
  mkdir -p "$(dirname "$SSHAF")"
  ssh-agent >"$SSHAF"
  chmod 600 "$SSHAF"
  . "$SSHAF"
  if grep -qE 'AddKeysToAgent +yes' "${HOME}/.ssh/config" >/dev/null 2>&1; then
    # If AddKeysToAgent is not set or no
    ssh-add
  fi
fi
```

Dieser Code liest die Verbindungsdaten des SSH-Agenten standardmäßig aus der Datei `~/.local/state/ssh/ssh_agent_env` aus. Falls diese Datei nicht existiert oder die darin angegebene Prozess-ID des SSH-Agenten ungültig ist, wird ein neuer Agenten-Prozess gestartet und die Verbindungsdaten in obiger Datei abgelegt. Abschließend werden die konfigurierten Schlüssel geladen, falls der Wert der Einstellung `AddKeysToAgent` nicht `yes`ist. 

Es empfiehlt sich, diesen Code in einem Shell-Skript abzuspeichern und in `~/.bashrc` zu laden, damit der SSH-Agent in jedem Kommandozeilensitzung vorhanden ist.

Die Konfiguration `AddKeysToAgent yes` in der Benutzer- oder Systemkonfiguration (siehe "[Konfiguration des SSH-Clients](../ssh/index.de.md#Konfiguration)") bewirkt ein automatisches Laden eines Schlüssel in den Agenten, sobald dieser verwendet wird. In dem Falle ist die vorherige Ausführung von `ssh-add` nicht mehr vonnöten.

### SSH-Agent als System-Dienst

Anstatt `ssh-agent` mit dem [oben beschriebenen Skript](#skript-zum-starten-einer-instanz-von-1) in der `~/.bashrc` zu laden, kann der SSH-Agent auch mittels [systemd](https://systemd.io/) gestartet und verwaltet werden. systemd ist ein Systemprogramm, welches bei der Mehrheit der aktuellen Linux-Distributionen u.a. die Verwaltung von Hintergrunddiensten übernimmt.

Die Registrierung eines Dienstes bei systemd erfolgt mittels einer Konfigurationsdatei. Systemdienste werden üblicherweise vom Systemverwalter im Verzeichnis `/etc/systemd/system` abgelegt. Da einfache Benutzer auf dem System üblicherweise keine Schreibrechte auf Systemverzeichnisse haben (sollten), können sie alternativ die Konfigurationsdatei im Verzeichnis `~/.config/systemd/user` speichern. Dieses Verzeichnis muss ggf. zunächst erstellt werden.

Der folgende Shell-Code konfiguriert einen SSH-Agenten als systemd-Dienst:

```bash
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-"${HOME}/.config"}"
mkdir -p "${XDG_CONFIG_HOME}/systemd/user"
chmod 700 "${XDG_CONFIG_HOME}"
cat > "${XDG_CONFIG_HOME}/systemd/user/ssh-agent.service" <<EOF
[Unit]
Description=SSH key agent

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a $SSH_AUTH_SOCK

[Install]
WantedBy=default.target
EOF
```

Hierin wird dem Dienst `ssh-agent` ein eindeutig bestimmter Pfad für den Socket übergeben. `%t` wird dabei durch das Verzeichnis ersetzt, in dem dem Benutzer zugehörige Laufzeitdateien abgelegt werden. Dieses entspricht dem Wert der Umgebungsvariable `$XDG_RUNTIME_DIR`. Der Dienst wird automatisch bei Anmeldung des Benutzers gestartet und die Laufzeit des Hintergrunddienstes kann mittels der durch systemd zur Verfügung gestellten Befehle gesteuert werden. 

Anschließend muss der Benutzer manuell den Wert von `$SSH_AUTH_SOCK` setzen, damit SSH-Clients die Verbindung zum Agenten aufnehmen können. Eine Möglichkeit hierzu ist: 

```bash
env_dir="${XDG_CONFIG_HOME:-"${HOME}/.config"}/environment.d"
mkdir -p "${env_dir}"
cat >> "${env_dir}/ssh_auth_socket.conf" <<EOF
SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.socket"
EOF
```

Die Dateien im Verzeichnis [environment.d](https://www.man7.org/linux/man-pages/man5/environment.d.5.html) enthalten Definition von Umgebungsvariablen und werden von systemd beim Start eingelesen. Nach einem Neuladen der systemd-Dienste kann der neue Dienst gestartet werden:

```bash
systemctl --user enable --now ssh-agent
```

Diese Lösung wurde  [StackExchange Unix&Linux](https://unix.stackexchange.com/a/390631) vorgestellt.

## Sicherheit

Um die Wahrscheinlichkeit eines Missbrauchs zu reduzieren, empfiehlt es sich, einen Timeout für die Schlüssel zu setzen. Die Anwendungen `ssh-agent` und `ssh-add` bieten hierzu die Option `-t`, mit welcher eine Zeit in Sekunden definiert werden kann, die die entsperrten Schlüssel maximal im Speicher verweilen können.
