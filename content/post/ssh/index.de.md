---
title: "Tipps und Tricks: SSH"
description: "Eine Zusammenfassung nützlicher Funktionen von SSH, die die Arbeit an entfernten Rechnern erleichtern"
url: ssh
date: 2024-02-18 18:41:11+0800
toc: true
categories:
   - distributed-computing
   - system-administration
   - it-security
keywords:
   - distributed-computing
   - ssh
   - it-security
   - commandline
   - system-administration
weight: 1
---

# Tipps und Tricks: SSH

SSH (**S**ecure **Sh**ell, deutsch: *sichere Shell*) ist ein beliebtes Werkzeug, um Konsolensitzungen auf entfernten Rechnern zu öffnen. Dabei werden die übertragenen Daten im Gegensatz zu herkömmlichen Fernwartungswerkzeugen wie *telnet* oder *rsh* verschlüsselt, sodass sie auf dem Übertragungsweg weder eingesehen noch manipuliert werden können. Damit hat sich SSH als das de-facto Standardwerkzeug für das Arbeiten an entfernten Rechnern etabliert und ist ein fester Bestandteil des Werkzeug-Repertoires vieler Systemadministratoren und (Web-)Entwickler.

In diesem Artikel stelle ich Funktionen von SSH vor, die die Benutzung von SSH im Alltag erleichtern. Dabei gehe ich zunächst kurz auf die Benutzung und Konfiguration des SSH-Clients ein. Anschließend erläutere ich die Erzeugung und Benutzung von Schlüsseln für eine sichere passwortlose Anmeldung an entfernten Rechnern und abschließend gehe ich auf Jump Hosts, Git und der parallelen Ausführung von Kommandos auf mehreren Rechnern ein. Mein Hauptaugenmerk liegt in diesem Artikel auf unixoiden Betriebssystemen (Linux, BSD, MacOS), gehe allerdings auch kurz auf Windows ein.

Der Großteil dieses Artikels basiert auf dem Vortrag "[Besser leben mit SSH](https://media.ccc.de/v/gpn20-8-besser-leben-mit-ssh)" von @leyrerBesserLebenMit2022, gehalten auf der Gulaschprogrammiernacht 20 am 21.05.2022.

## Benutzung

Der SSH-Client ist auf vielen unixoiden Systemen vorinstalliert. Auf der Kommandozeile kann mittels des `ssh`-Befehls eine Verbindung zu einem entfernten Rechner aufgenommen werden, insofern auf ihm ein SSH-Server aktiv ist. Dabei wird dem Befehl die Adresse des Zielrechners übergeben, ggf. mitsamt Anmeldeinformationen. Werden keine Anmeldeinformationen übergeben, so verwendet der SSH-Client standardmäßig den Benutzernamen des aktuell angemeldeten Benutzers. 

Beispielsweise kann man sich mittels des Befehls

```bash
ssh root@ssh-server.example.com
```

als Root-Nutzer[^root] am Rechner mit der Domain `ssh-server.example.com` anmelden. Alternativ können natürlich auch IP-Adressen verwendet werden. Bei der Anmeldung wird üblicherweise ein Passwort abgefragt.

[^root]: Auf einigen Systemen ist zur Sicherheit die Anmeldung mit dem Nutzer `root` blockiert. Generell wird von der direkten Nutzung des root-Accounts abgeraten.

## Konfiguration

Die Konfiguration des SSH-Clients kann per 

1. Kommandozeilen-Option,
2. Benutzerkonfiguration (standardmäßig in `~/.ssh/config`) oder
3. Systemkonfiguration (standardmäßig in `/etc/ssh/ssh_config`)

erfolgen. Mittels der Kommandozeilenoption `-f` können diese Konfigurationen allerdings auch aus anderen Dateien ausgelesen werden. Alternativ kann die `ssh`-Konfiguration auch auf mehrere Dateien in dem Verzeichnis `~/.ssh/conf.d` verteilt werden. Diese werden, falls vorhanden, in alphabetischer Reihenfolge eingelesen. Dies ist nützlich, wenn die Benutzerkonfiguration durch zu viele Einträge unübersichtlich wird oder Konfigurationen nach bestimmten Kriterien getrennt werden sollen (z.B. pro Kunde).

Ein Beispiel für die einfache Konfiguration eines Zielrechners (Host) ist: 

```
Host ssh-server
  HostName ssh-server.example.com
  User root
```

Das Schlüsselwort `Host` leitet die Konfiguration für einen Zielrechner mit den angegebenen Namen ein. Die Namen der Zielrechner folgen dem Schlüsselwort `Host`. Der SSH-Client ermittelt die für die aktuelle Verbindungsanfrage anzuwendende Konfiguration anhand dieser Namen. Innerhalb der Konfiguration wird mit `HostName` die Adresse angegeben (IP-Adresse oder Domain), mit der sich der Client verbinden soll, und mittels `User` der zu verwendende Benutzer (in diesem Beispiel `root`)[^root].

Obige Konfiguration erlaubt die Anmeldung am entfernten Rechner mittels

```bash
ssh ssh-server  # äquivalent zu `ssh root@ssh-server.example.com`
```

In der Konfiguration können auch Platzhalter verwendet werden. Die Liste der Platzhalter ist in der [Dokumentation von ssh_config](https://man.openbsd.org/ssh_config.5#TOKENS) einzusehen. So wird beispielsweise der Platzhalter `%h` durch den in der ersten Zeile angegebenen Namen des Hosts ersetzt. Der Stern `*` steht für beliebige Zeichenketten. Beispielsweise wird die folgende Konfiguration für alle Adressen verwendet, die mit ".example.com" enden:

```
Host *.example.com
  HostName %h
  User root
```

Vor einem Verbindungsaufbau wird die Konfigurationsdatei von oben nach unten eingelesen und der Eintrag des ersten passenden Hostnamens wird verwendet. Es ist daher empfehlenswert, dass spezifische Einträge (wie z.B. `ssh-server.example.com`) vor generischen Einträgen (wie `*.example.com`) stehen.

Mittels der Eigenschaft `SendEnv` können im Zielsystem Umgebungsvariablen gesetzt werden[^sendenv]. Die Konfiguration von `IdentitiesOnly: yes` bewirkt, dass der SSH-Client nur die für den angegebenen Host konfigurierten Identitäten zur Anmeldung verwendet, anstatt alle konfigurierten Identitäten auszuprobieren. Hilfreich für getaktete Verbindungen oder Verbindungen mit hoher Latenz ist eine Komprimierung der Datenübertragung, die mit `Compression: yes` erreicht werden kann.

[^sendenv]: Die Variablennamen müssen allerdings zunächst in der Konfiguration des SSH-Servers authorisiert werden.

## Schlüsselverwaltung

Standardmäßig erfordert die Anmeldung an einem entfernten Rechner ein Passwort. SSH ermöglicht allerdings auch die Anmeldung per kryptographischem Schlüssel, wodurch eine Anmeldung ohne die manuelle Eingabe eines Passwortes ermöglicht wird. Dieser Schlüssel ist eine einzigartige Zeichenkette, mit welcher sich der Anmeldende am entfernten Rechner ausweisen kann.

### Schlüssel erzeugen

Zur Schlüsselerzeugung wird auf dem Client-Rechner der Befehl `ssh-keygen` verwendet. Beispielsweise erzeugt der Befehl

```bash
ssh-keygen -t ed25519 -a 420 -f ~/.ssh/demo.ed25519 -C "Kommentar"
```

einen Schlüssel mittels des kryptographischen Verfahrens [ed25519](https://de.wikipedia.org/wiki/Curve25519). Welche Verfahren unterstützt werden, kann dem Handbuch[^man-ssh-keygen] entnommen werden. Dieser Schlüssel wird in der mit `-f` angegebenen Datei `~/.ssh/demo.ed25519` abgelegt. `-f` ist optional und standardmäßig `~/.ssh/id_${cryptographic_method}`[^dateiname]. Der mittels der Kommandozeilenoption `-C` angegebene Kommentar kann zur Dokumentation des Schlüssels verwendet werden, z.B kann der Erzeuger hier seinen Namen hinterlegen, sodass dieser auf dem Zielsystem einem Besitzer zugeordnet werden kann. Die Option `-a` gibt die Anzahl der Runden an, die bei der Generierung des Schlüssels verwendet werden. Eine höhere Zahl schützt besser vor Brute-Force-Attacken, aber führt zu einem langsameren Entsperren des Schlüssels.

[^man-ssh-keygen]: `man ssh-keygen`

[^dateiname]: Hierbei wird `${cryptographic_method}` durch den Namen des mittels `-t` gewählte kryptographische Verfahren ersetzt. In diesem Beispiel ist dies `ed25519`.

Bei der Erzeugung des Schlüssels wird `ssh-keygen` ein Passwort abfragen. Das hier angegebene Passwort kann frei gewählt werden und wird später der Entsperrung des Schlüssels dienen. Die Eingabe ist zwar optional, aber empfehlenswert, da ein (starkes) Passwort vor Diebstahl und Missbrauch durch Unberechtigte schützen kann[^breach].

[^breach]: Kryptographische Schlüssel sind häufig ein beliebtes Ziel von Hackern beim Einbruch in fremde Computersysteme. So kam 2023 beispielsweise [bei Microsoft ein Signierungs-Schlüssel](https://www.microsoft.com/en-us/security/blog/2023/07/14/analysis-of-storm-0558-techniques-for-unauthorized-email-access/) abhanden, durch den die Hacker Zugang zu den E-Mails verschiedener Regierungsorganisationen erlangten.

`ssh-keygen` erzeugt zwei Dateien: 

- `~/.ssh/demo.ed25519` ist der *private* Schlüssel zur Authentifizierung der Identität auf dem Zielsystem, und
- `~/.ssh/demo.ed25519.pub` ist der *öffentliche* Schlüssel, der auf dem Zielsystem zur Authentifizierung benutzt wird.

Bei der Anmeldung am Zielrechner verschlüsselt der SSH-Server zur Authentifizierung des Anmeldenden eine zufällige Zeichenkette mit dem öffentlichen Schlüssel, welche nur mittels des zugehörigen privaten Schlüssels wieder entschlüsselt werden kann. Daher ist es notwendig, dass der private Schlüssel in jedem Fall geheim bleibt. Konkret heißt dies, er wird *nicht* auf das Zielsystem kopiert und sollte auch unter keinen Umständen in Code-Repositories oder Docker-Images[^docker] gespeichert werden [@mikehanleyWeUpdatedOur2023].

[^docker]: Die naive Verwendung von Geheimnissen wie Passwörter oder Schlüsseln in Docker-Images ist riskant, da aufgrund der Unveränderlichkeit (*immutability*) der Schichten in Docker-Images selbst gelöschte Inhalte tieferer Schichten auch nachträglich noch einsehbar sein können. Zur Speicherung von Geheimnissen in Docker-Images sind *[Docker secrets](https://docs.docker.com/engine/swarm/secrets/)* vorgesehen. Diese Thematik werde ich in einem kommenden Artikel erläutern.

Um den Einfluss eines versehentlich abhanden gekommenen Schlüssels abzuschwächen, empfiehlt es sich, für verschiedene Domänen (Kunden, Dienste, Server) verschiedene Schlüssel zu verwenden.

### Schlüsselverteilung

Damit das Zielsystem die Authentifizierung vornehmen kann, benötigt es den öffentlichen Schlüssel (`*.pub`). Dieser wird auf auf dem Host üblicherweise in der Datei `~/.ssh/authorized_keys` abgelegt.

Mittels `ssh-copy-id` kann der Schlüssel einfach vom Client-Rechner aus auf die Zielrechner verteilt werden:

```bash
ssh-copy-id -i ~/.ssh/demo.ed25519.pub ssh-server
```

kopiert den öffentlichen Schlüssel in `~/.ssh/demo.ed25519.pub` auf den mit `ssh-server` identifizierten Rechner (siehe Abschnitt „[Konfiguration](#konfiguration)“). Dabei muss noch das Benutzerpasswort eingegeben werden. 

### Schlüsselverwendung

Mittels der Kommandozeilenoption `-i` kann `ssh` bei der Anmeldung angewiesen werden, anstatt eines Passwortes den geheimen Schlüssel aus der angegebenen Datei zu verwenden: 

```bash
ssh -i ~/.ssh/demo.ed25519 alias1
```

Das dabei abgefragte Passwort ist nun nicht mehr das des Nutzers am Zielrechner, sondern das Entsperr-Passwort des geheimen Schlüssels (falls konfiguriert). Alternativ kann der Schlüssel auch in der Benutzerkonfiguration spezifiziert werden:

```
   Host ssh-server
     HostName ssh-server.example.com
     User root
     PreferredAuthentications publickey
     IdentityFile ~/.ssh/demo.ed25519
```

Der Schlüssel `PreferredAuthentications` gibt eine Liste der bevorzugten Authentifizierungsmethoden an, in diesem Falle wird das `publickey`-Verfahren gewählt. Der Schlüssel `IdentityFile` gibt den Pfad zum geheimen Schlüssel an.

Bei der erfolgreichen Konfiguration wird beim nächsten `ssh ssh-server` lediglich das bei der Schlüsselerzeugung angegebene Passwort für den geheimen Schlüssel abgefragt. 

Hiermit gelingt zwar die Anmeldung am Zielrechner ohne Eingabe eines Passworts, der Nutzer muss allerdings weiterhin ein Passwort zur Entsperrung des Schlüssels angeben. Für eine wirklich passwortlose Anmeldung kann der [Schlüsselpasswort-Cache](#schlüsselpasswort-cache) verwendet werden.

### Schlüsselpasswort-Cache

Ein mit Passwort geschützter geheimer Schlüssel benötigt normalerweise bei der Verwendung die Eingabe des Passworts. Um dennoch eine passwortlose Anmeldung zu ermöglichen, kann ein Schlüsselpasswort-Cache verwendet werden. Bei aktuellen Desktop-Systemen wie GNOME oder KDE sind solche Passwort-Caches üblicherweise bereits vorhanden (GNOME Keyring, Kwallet, ...). Beim Entsperren des Schlüssels erscheint ein Fenster zur Passworteingabe, wonach das Passwort für einen gewissen Zeitraum im Arbeitsspeicher vorgehalten wird. Auf Systemen ohne native Passwort-Caches, wie Headless-Server, ist allerdings die Kommandozeilenanwendung `ssh-agent` nützlich. Diese wird im Folgenden näher erläutert.

Wenn mittels `ssh-agent` ein Passwort im Arbeitsspeicher vorgehalten werden soll, muss zunächst der gleichnamige Hintergrunddienst gestartet werden. Dieser kommuniziert über einen UNIX-Socket mit dem SSH-Subsystem, welches geheime Schlüssel entsperrt. Nachdem der Hintergrunddienst gestartet wurde, kann man mittels `ssh-add` die Passwörter privater Schlüssel in den Speicher laden. Folgender Code startet einen SSH-Agenten-Prozess und lädt anschließend alle konfigurierten Schlüssel in den Speicher:

```bash
eval $(ssh-agent)  # wertet den durch ssh-agent ausgegebenen Skript-Code aus
ssh-add  # alle konfigurierten Schlüssel entsperren (erforder Passworteingabe)
```

Wenn die Anwendung `ssh-agent` ausgeführt wird, startet sie den gleichnamigen Hintergrunddienst und gibt anschließend den Shell-Code auf der Kommandozeile aus, der zur Verbindungsaufnahme notwendig ist. Konkret werden hierin die Umgebungsvariablen `SSH_AUTH_SOCK` (UNIX-Socket) und `SSH_AGENT_PID` (Prozess-ID) gesetzt. Deshalb wird im obigen Beispiel mittels des Builtin `eval` die Ausgabe von `ssh-agent` ausgewertet und damit der aktuellen Sitzung zur Verfügung gestellt.

Bei jedem Aufruf von `ssh-agent` wird ein neuer SSH-Agenten-Dienst im Hintergrund gestartet, der nicht an die Lebensdauer der aktuellen Sitzung gebunden ist. Gleichzeitig ist die obige automatische Konfiguration mittels `eval` nur für eine Kommandozeilen-Sitzung gültig. Würde obiger Code in Konfigurationsdateien wie `.profile` oder `.bashrc` verwendet, würden mehrere verschiedene Instanzen des SSH-Agenten mit verschiedenen Speicherständen gestartet. Eine Konfiguration ohne dieses Verhalten beschreibe ich in meinem Artikel "[SSH-Agenten auf Headless-Servern automatisch starten](../ssh-agent-autostart)".

Mittels `AddKeysToAgent yes` in der [SSH-Client-Konfiguration](#konfiguration) kann der SSH-Client angewiesen werden, die Schlüssel automatisch nach Entsperrung dem SSH-Agenten zu übermitteln. Damit müssen die Schlüssel nicht mehr vorzeitig mittels `ssh-add` in den Speicher geladen werden, sondern erst bei Benutzung.

### Windows

Auf Windows gibt es verschiedene Werkzeuge, die die Verwendung von SSH ermöglichen, wie z.B. [PuTTY](https://putty.org/). PuTTY bietet mit `puttygen` (`ssh-keygen`), `pagent` (`ssh-agent`) und `putty` (`ssh`) entsprechende Funktionalitäten zu den Werkzeugen aus OpenSSH mit einer graphischen Oberfläche. Die mit PuTTY generierten Schlüssel verwenden allerdings ein anderes Format als OpenSSH, sodass sie ggf. konvertiert werden müssen, bevor sie auf unixoiden Systemen verwendet werden können.

Neuere Versionen von Windows bieten SSH-Funktionalität auch nativ in der PowerShell an. Alternativ kann OpenSSH mittels Werkzeugen wie [cygwin](https://cygwin.com/), [git bash](https://git-scm.com/downloads) oder [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/de-de/windows/wsl/install) auch direkt auf Windows verwendet werden.

### GNOME

Auch der Linux-Desktop GNOME bietet eine graphische Oberfläche für das Schlüsselmanagement mit dem vorinstallierten Programm [GNOME Keyring](https://wiki.gnome.org/Projects/GnomeKeyring/) (deutsch: "Passwörter und Verschlüsselung"). Mit dieser Anwendung können SSH-Schlüssel erzeugt und deren Passwörter im Speicher vorgehalten werden.

## Jump Host

Ein Jump-Host oder *bastion* ist ein Rechner, der den Zugang zu anderen Rechnern hinter einer Firewall ermöglicht. Um sich mit dem Zielhost hinter der Firewall mit nur einem Befehl zu verbinden, bietet der SSH-Client die Kommandozeilenoption `-J`: 

```bash
ssh -J bastion target.local
```

Dieser Befehl bewirkt, dass sich der SSH-Client zunächst mit dem Host `bastion` verbindet und anschließend automatisch von dort aus eine Verbindung mit `target.local` aufbaut.

Analog kann diese indirekte Verbindung auch in die [Konfigurationsdatei](#konfiguration) eingetragen werden: 

```
Host bastion
  HostName ssh.example.com
  User root
  PreferredAuthentication publickey
  IdentityFile ~/.ssh/demo.ed25519
  
Host internal
  HostName target.local
  ProxyJump bastion
  User root
  PreferredAuthentication publickey
  IdentityFile ~/.ssh/demo.ed25519
```

In dieser Konfigurationsdatei wird zunächst der Jump-Host mit dem Alias `bastion` konfiguriert, anschließend der eigentliche Zielrechner `internal`. Bei der Konfiguration von `internal` wird mittels der Einstellung `ProxyJump` angegeben, dass die Verbindung indirekt über `bastion` erfolgt. Diese Konfiguration ermöglicht eine direkte Verbindung mit dem Zielsystem mittels `ssh internal`.

Bei älteren SSH-Clients ohne Unterstützung von `-J` oder `ProxyJump` kann man eine direkte Verbindung erreichen, indem man einen SSH-Befehl an den Jump-Host sendet: 

```bash
ssh -o ProxyCommand="ssh -W %h:%p bastion" target.local
```

Die Funktion "*Agent forwarding*" (`-A`) gilt inzwischen als unsicher und sollte nicht mehr verwendet werden.

## Git über SSH

Git-Server ermöglichen ebenfalls eine Anmeldung über SSH. Daher kann das oben beschriebene Verfahren zur passwortlosen Anmeldung auch für Git verwendet werden. Dazu wird zunächst der öffentliche Schlüssel (d.h. der Inhalt der `*.pub`-Datei) auf dem Git-Server hinterlegt[^git-key]. Anschließend trägt man den jeweiligen Schlüssel für den Server in der [Konfigurationsdatei](#konfiguration) ein. Danach kann das Git-Repository mittels *ssh* geklont werden (Achtung: nicht *https* verwenden). Bei bereits mittels *https* geklonte Repositories kann die Adresse des Remote-Repositories mit Hilfe von `git remote set-url` neu eingerichtet werden.

[^git-key]: Das Verfahren zum Hinterlegen des Schlüssels bei Git-Diensten ist abhängig vom Dienst (z.B. [GitHub](https://docs.github.com/de/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account), [GitLab]()) und wird hier daher nicht näher erläutert.

## Parallele Ausführung von Kommandos auf mehreren Rechnern

Zur gleichzeitigen Ausführung von Kommandos auf mehreren Rechnern kann das Kommandozeilentool [`pdsh`](https://github.com/chaos/pdsh) verwendet werden, welches üblicherweise nachinstalliert werden muss. Folgendes Kommando sendet den Befehl `echo ` an drei Server zur Ausführung:

```bash
pdsh -R ssh -w 192.168.2.100,192.168.2.101,192.168.2.102 'echo "Hallo, die aktuelle Zeit ist: $(date)"'  # mit IP-Adressen
pdsh -R ssh -w server1,server2,server3 'echo "Hallo, die aktuelle Zeit ist: $(date)"'  # mit Aliasen
```

Standardmäßig verwendet `pdsh` das Remote-Command-Modul (rcmd) `rsh`, aber mittels der Option `-R` kann auch `ssh` ausgewählt werden[^rcmd]. Mittels der Option `-w` wird eine kommagetrennte Liste der Rechner-Adressen an `pdsh` übergeben, auf denen der Befehl ausgeführt werden soll. Wenn in der [SSH-Konfigurationsdatei](#konfiguration) den Zielrechnern Namen zugeordnet wurden, können sie auch hier verwendet werden.

Damit die Anmeldung am Zielrechner gelingt, muss eine passwortlose Anmeldung eingerichtet werden. Wie eine sichere passwortlose Anmeldung eingerichtet werden kann, habe ich im Kapitel [Schlüsselverwaltung](#schlsselverwaltung) beschrieben.

[^rcmd]: Alternativ zur Option `-R` kann ssh auch mittels der Umgebungsvariable `PDSH_RCMD_TYPE` ausgewählt werden. Dies ist hilfreich, wenn ssh zur Standard-Methode zur Verbindung mittels `pdsh` gemacht werden soll.

## Referenzen

{{bibliography}}
