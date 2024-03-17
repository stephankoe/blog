---
title: "Kommunikationsmuster"
description: "Beschreibung häufig genutzter Kommunikationsmuster im verteilten Rechnen"
date: 2024-03-03T12:56:52+08:00
image: cover.jpg
math: true
categories:
  - distributed-computing
  - machine-learning
weight: 1
---

# Kommunikationsmuster

Beim verteilten Rechnen werden häufig wiederkehrende Muster verwendet, um Daten zwischen den teilnehmenden Prozessen auszutauschen und zu synchronisieren. Im Folgenden werden einige solche Kommunikationsmuster[^MPI] erläutert, die die Grundlage für die Implementierung verteilten maschinellen Lernens bilden [@nielsenIntroductionHPCMPI2016]. Für die Analyse und das Verständnis der Prozesse im verteilten maschinellen Lernens sind diese Muster unabdingbar.

[^MPI]: Die erläuterten Kommunikationsmuster werden auf Basis des *Message Passing Interface* (MPI) definiert. Dies ist ein Standard zur Kommunikation in parallelen Rechnerarchitekturen. Beispiele für Implementierungen von MPI sind [Intel MPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/mpi-library.html) und [Open MPI](https://www.open-mpi.org/).

## Beschreibung der Kommunikationsmuster

### Broadcast

Beim Broadcast sendet ein Prozess seine Daten an alle anderen Prozesse, welche jeweils ihre lokalen Daten mit den erhaltenen Werten überschreiben. Nach der Operation hat also jeder Prozess die Daten des sendenden Prozesses im Speicher.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einem Datum x_i abgebildet. Das Datum von Prozess 1 ist vor der Operation x_1, die Daten der anderen Prozesse sind jeweils mit x_2 bis x_n angegeben. Von Prozess 1 aus der mit vorher beschrifteten Reihe aus zeigen drei gestrichelte Linien auf die Prozesse der unteren, mit nachher beschrifteten Reihe. Die Linie ist mit Broadcast beschriftet. Die Daten aller in der unteren Reihe dargestellten Prozesse ist mit dem von Prozess 1 in der oberen Reihe identisch, und zwar x_1.](img/mpi-broadcast.svg)

: Beispiel einer Broadcast-Operation: Prozess 1 sendet sein Datum $x_1$ an alle anderen Prozesse, welche jeweils ihre eigenen Daten mit diesem Datum $x_1$ überschreiben.

### Reduce

Bei einer *Reduce*-Operation senden alle teilnehmenden Prozesse ihre Daten an einen bestimmten Zielprozess, welcher anschließend die Daten aller Prozesse anhand einer Reduktionsoperation auf jeweils einen Wert reduziert. Häufig verwendete Reduktionsoperationen sind Addition und Maximum. Nach der Reduktion erhält der Zielprozesses das Ergebnis der Reduktion der Daten aller Prozesse, wohingegen der Speicherinhalt aller anderen Prozesse unverändert bleibt.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einem Datum $x_i$ abgebildet. Von allen Prozessen aus der oberen Reihe führt jeweils eine gestrichelte Linie zu Prozess 1 in der unteren, mit nachher beschrifteten Reihe. Der dortige Speicherinhalt von Prozess 1 ist mit (x_1 + x_2 + ... + x_n) angegeben. Die Daten der anderen Prozesse sind im Vergleich mit der oberen Zeile unverändert.](img/mpi-reduce.svg)

: Beispiel einer Reduce-Operation: Alle Prozesse senden ihre Daten an Prozess 1, welcher die Summe aller erhaltenen Daten berechnet. Der ursprüngliche Speicherinhalt von Prozess 1 wird mit der Summe überschrieben. Die Speicherinhalte der anderen Prozesse bleiben unverändert.

### All-Reduce

Beim *All-Reduce* werden ähnlich wie bei der *[Reduce](#Reduce)*-Operation die Daten der teilnehmenden Prozesse auf jeweils ein Datum reduziert, allerdings erhalten alle Prozesse das Ergebnis.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einem Datum $x_i$ abgebildet. Von allen Prozessen aus der oberen Reihe führt jeweils eine gestrichelte Linie zu allen anderen Prozessen in der unteren, mit nachher beschrifteten Reihe. Der dortige Speicherinhalt aller Prozesse ist mit (x_1 + x_2 + ... + x_n) angegeben.](img/mpi-all-reduce.svg)

: Beispiel einer All-Reduce-Operation: Alle Prozesse tauschen untereinander ihre Daten aus und summieren sie auf. Jedes Prozesses erhält anschließend das gleiche Ergebnis.

### Barrier

Eine *Barrier* (Barriere) ist ein Mechanismus zur zeitlichen Synchronisation von Prozessen. Beim Erreichen einer Barriere wird die Ausführung des Programms so lange pausiert, bis alle anderen Prozesse ebenfalls dieselbe Barriere erreicht haben.

### Gather

Vor der Operation hat jeder Prozess jeweils ein Datum $x_i$ im Speicher. Im Zuge einer *Gather*-Operation werden die Daten aller $n$ Prozesse bei einem bestimmten Zielprozess gesammelt. Anschließend verfügt dieser Zielprozess über die Daten aller Prozesse $(x_1, ..., x_n)$.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einem Wert x_i abgebildet. Von allen Prozessen aus der oberen Reihe führt jeweils eine gestrichelte Linie zum Prozess 1 in der unteren, mit nachher beschrifteten Reihe. Der dortige Prozess 1 ist mit einer Liste von Werten x_1 bis x_n abgebildet. Die Werte aller anderen Prozesse der unteren Reihe sind identisch mit der oberen Reihe.](img/mpi-gather.svg)

: Beispiel einer *Gather*-Operation: Prozess 1 sammelt die Daten aller $n$ Prozesse und legt sie in einer Liste ab. Der Speicherinhalt der anderen Prozesse bleibt unverändert.

### All-Gather

Bei einer *All-Gather*-Operation werden die Daten $x_i$ aller $n$ Prozesse auf allen Prozessen gesammelt. Dadurch erhalten alle teilnehmenden Prozesse jeweils Zugriff auf die Daten aller Prozesse in Form einer Liste $(x_1, ..., x_n)$.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einem Wert x_i abgebildet. Von allen Prozessen aus der oberen Reihe führt jeweils eine gestrichelte Linie zu allen Prozessen in der unteren, mit nachher beschrifteten Reihe. Die dortigen Prozesse sind mit jeweils einer Liste abgebildet, welche die Daten x_1 bis x_m beinhaltet.](img/mpi-all-gather.svg)

: Beispiel einer All-Gather-Operation: Jeder Prozess erhält jeweils eine Kopie der Daten aller anderen Prozesse.

### Scatter

Im Zuge der *Scatter*-Operation verteilt ein Prozess die Daten $(x_1, ..., x_n)$ so auf alle $n$ teilnehmenden Prozesse (einschließlich des Senders), dass jeder Prozess exakt ein Datum aus der Liste erhält. Konkret erhält der $i$-te Prozess den $i$-ten Wert $x_i$. *Scatter* ist damit die Umkehrung der *[Gather](#gather)*-Operation.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse abgebildet. In der oberen Reihe ist neben Prozess 1 eine Liste mit n Elementen x_1 bis x_n abgebildet. Von diesem Prozess aus führt jeweils eine gestrichelte Linie zu allen Prozessen in der unteren, mit nachher beschrifteten Reihe. Die dortigen Prozesse sind mit jeweils einem Datum aus der obigen Liste abgebildet: Prozess 1 mit x_1, Prozess 2 mit x_2, usw.](img/mpi-scatter.svg)

: Beispiel einer Scatter-Operation: Die Werte in einer Liste $(x_1, ..., x_n)$ in Prozess 1 werden gleichmäßig auf alle Prozesse verteilt. Nach der Operation hat jeder der Prozesse jeweils einen Wert aus der Liste erhalten.

### All-to-All

Im Vorfeld der *All-to-All*-Operation haben alle $n$ Prozesse jeweils eine Liste mit $n$ Elementen. Alle Prozesse verteilen ihre Daten im Zuge der *All-to-All*-Operation jeweils auf alle anderen Prozesse (siehe *[Scatter](#scatter)*). Jene Prozesse sammeln wiederum alle empfangenen Werte und speichern sie in einer Liste der Größe $n$ ab (siehe *[Gather](#gather)*). Diese Operation ist vergleichbar mit dem Transponieren einer zweidimensionalen Matrix, deren Spalten auf mehrere Prozesse verteilt sind.

![Es sind zwei Reihen zu sehen. Die obere ist mit vorher und die untere mit nachher beschriftet. In jeder Reihe sind n Prozesse mit jeweils einer Liste abgebildet. Die Listen verschiedener Prozesse enthalten verschiedene Daten -- die Liste von Prozess i enthält die Daten x_i,1 bis x_i,n. Von allen Prozessen aus der oberen Reihe führt jeweils eine gestrichelte Linie zu allen Prozessen in der unteren, mit nachher beschrifteten Reihe. Die dortigen Prozesse sind ebenfalls mit jeweils einer Liste abgebildet, dessen Daten sich allerdings von der oberen Reihe unterscheiden: Die Liste von Prozess i in der unteren Reihe enthält nun die Daten x_1,i bis x_n,i.](img/mpi-all-to-all.svg)

: Beispiel einer *All-to-All*-Operation: Jeder Prozess verteilt seine lokalen Daten so auf alle anderen Prozesse, dass jeder Prozess $i$ das $i$-te Datum erhält. Gleichzeitig sammeln alle Prozesse die erhaltenen Daten in einer Liste. Beispielsweise sind in der Liste von Prozess 1 nach der Operation die ursprünglich ersten Werte aller Prozesse gespeichert.

## Zusammenfassung

- **Broadcast**: Ein bestimmter Prozess sendet seine Daten an alle anderen Prozesse.
- **Reduce**: Die Daten aller Prozesse werden in einem bestimmten Prozess zusammengefasst.
- **All-Reduce**: Die Daten aller Prozesse werden in allen Prozessen zusammengefasst.
- **Barrier**: Aller Prozesse pausieren solange bis alle Prozesse die Barriere erreicht haben.
- **Gather**: Die einzelnen Werte aller Prozesse werden in einem bestimmten Prozess gesammelt.
- **All-Gather**: Die einzelnen Werte aller Prozesse werden in allen Prozessen gesammelt.
- **Scatter**: Die Daten eines Prozesses werden gleichmäßig auf alle Prozesse verteilt.
- **All-to-All**: Die Daten aller Prozesse werden gleichmäßig auf alle Prozesse verteilt, während gleichzeitig jeder Prozess die erhaltenen Daten in einer Liste sammelt.

## PyTorch Distributed

Da die oben beschriebenen Kommunikationsmuster die Grundlage für die Implementierung verteilter KI-Architekturen bilden, wurden sie in Form des Pakets *PyTorch Distributed* in die im maschinellen Lernen beliebte Bibliothek PyTorch integriert. In diesem Kapitel erläutere ich die Verwendung dieser Muster mittels der von PyTorch bereitgestellten Funktionen.

PyTorch Distributed bildet das Fundament für wichtige Bausteine des parallelen Lernens in PyTorch, wie PyTorch DDP [@liPyTorchDistributedExperiences2020] und PyTorch FSDP [@zhaoPyTorchFSDPExperiences2023]. @liPyTorchDistributedOverview2024 erläutert detailliert die Implementierung datenparallelen Trainings-Aufbaus mit PyTorch. Die [offizielle PyTorch-Dokumentation](https://pytorch.org/docs/stable/distributed.html) bietet zudem Detailinformationen zu den bereitgestellten Funktionen. 

Die hier beschriebenen Kommunikationsmuster sind relativ low-level, das heißt ein ML-Ingenieur wird bei der Parallelisierung eines Modells mit PyTorch normalerweise nicht die oben beschriebenen Methoden verwenden, sondern kann auf abstraktere Werkzeuge wie PyTorch DDP oder FSDP zurückgreifen.

Beim Start der verteilten Anwendung muss PyTorch Distributed zunächst initialisiert werden. Dabei wird eine Gruppe erstellt, die alle an der Berechnung teilnehmenden Prozesse umfasst – die sog. "*default group*". Die Initialisierung erfolgt mittels der Methode [`torch.distributed.init_process_group`](https://pytorch.org/docs/stable/distributed.html#torch.distributed.init_process_group), welche die Konfiguration standardmäßig aus Umgebungsvariablen ausliest. Die wichtigsten Umgebungsvariablen hierbei sind:

- `RANK`: der globale Rang des aktuellen Prozesses, vergleichbar mit einer globalen Prozess-ID,
- `LOCAL_RANK`: der lokale Rang des aktuellen Prozesses auf dem jeweiligen Rechner, vergleichbar mit einer rechnerlokalen Prozess-ID,
- `WORLD_SIZE`: die Anzahl aller teilnehmenden Prozesse,
- `MASTER_ADDR`: die Adresse des Hauptprozesses, der die Verwaltung der Prozesse übernimmt, und
- `MASTER_PORT`: der zugehörige Port des Hauptprozesses.

Alternativ können diese Daten auch als Argumente an [`torch.distributed.init_process_group`](https://pytorch.org/docs/stable/distributed.html#torch.distributed.init_process_group) übermittelt werden.

```python
import torch
import torch.distributed as dist

dist.init_process_group()
```

Im Folgenden verwende ich für eine kompaktere Darstellung konsequent die Abkürzung `dist` für `torch.distributed`. PyTorch unterstützt mehrere Backends zur Inter-Prozess-Kommunikation (IPC) wie MPI, GLOO oder [NCCL](https://developer.nvidia.com/nccl). In diesem Beispiel verwende ich GLOO als Backend, welches sich für das Testen am lokalen PC eignet. Die NVIDIA Collective Communications Library (NCCL) erfordert mindestens eine NVidia-GPU pro Prozess und für die Nutzung von MPI muss PyTorch zunächst mit MPI-Unterstützung kompiliert werden. Details zu den Backends kann man in [diesem Tutorial](https://pytorch.org/tutorials/intermediate/dist_tuto.html#communication-backends) nachlesen.

Für eine kompaktere Darstellung verwende ich im Folgenden die Methode `create_data`, welche einen Tensor mit Daten in Abhängigkeit des aktuellen Rangs initialisiert und ggf. auf eine GPU transferiert. Bei der Verwendung von GPUs mittels CUDA muss beachtet werden, dass zwei miteinander über NCCL kommunizierende Prozesse auch unterschiedliche GPUs verwenden müssen.

```python
def create_data(worker_id: int = None, dim: int = 4) -> torch.Tensor:
    worker_id = worker_id if worker_id is not None else dist.get_rank()
    data = torch.arange(dim) + worker_id * dim
    if dist.get_backend() == "nccl":
        data = data.to(f"cuda:{worker_id}")
    return data
```

Die Methode `dist.broadcast` initiiert einen Broadcast der übergebenen Daten vom Prozess `src` aus auf alle anderen Prozesse. `src` bestimmt den Rang des sendenden Prozesses, in diesem Beispiel Prozess 0. Jeder Prozess alloziert zunächst einen Tensor `data` gleicher Größe. Der sendende Prozess wird den Inhalt dieses Tensors an alle anderen Prozesse senden und die empfangenden Prozesse werden dessen Inhalt mit den erhaltenen Daten überschreiben. Nach Abschluss der Operation hat `data` in allen Prozessen den gleichen Inhalt.

```python
data = create_data()
dist.broadcast(data, src=0)
```

Eine Reduktion findet mittels der Methode `dist.reduce` statt. Wie bei der Broadcast-Methode haben alle Prozesse bereits einen Tensor `data` alloziert, dessen Inhalt sie an Prozess 0 schicken. Der Zielprozess wird mittels des Arguments `dst` angegeben. Mittels des Arguments `op` lässt sich die Form die Reduktionsoperation bestimmen.

```python
data = create_data()
dist.reduce(data, dst=0, op=dist.ReduceOp.SUM)
```

Ein All-Reduce wird analog mittels der Methode `dist.all_reduce` durchgeführt, doch entfällt hier das Argument `dst`.

```python
data = create_data()
dist.all_reduce(data, op=dist.ReduceOp.SUM)
```

Zum Sammeln von Daten in einem Zielprozess ist die Methode `dist.gather` vorgesehen. Diese nimmt als Eingabe wiederum einen bereits allozierten Tensor `data`, den Rang des Zielprozesses `dst`, sowie eine Liste von bereits in passender Größe allozierten Tensoren `gather_list`, in welche die von den anderen Prozessen erhaltenen Tensoren gespeichert werden. `gather_list` ist nur verpflichtend für den Zielprozess, alle anderen Prozesse brauchen dieses Argument nicht angeben.

```python
data = create_data()
result = ([torch.zeros_like(data) for _ in range(dist.get_world_size())] 
          if dist.get_rank() == 0 
          else None)
dist.gather(data, dst=0, gather_list=result)
```

Mittels `dist.all_gather` wird analog zu `dist.gather` eine All-Gather-Operation durchgeführt. Es entfällt wieder das Argument `dst`.

```python
data = create_data()
result = [torch.zeros_like(data) for _ in range(dist.get_world_size())]
dist.all_gather(result, data)
```

Eine Scatter-Operation wird mittels `dist.scatter` durchgeführt. Hierbei übergibt der sendende Prozess, hier 0, der Methode eine Liste mit jeweils einen Tensor für jeden Prozess. Dabei wird der Prozess mit dem Rang $i$ den Tensor `data[i]` erhalten. Zunächst muss jeder Prozess einen Tensor passender Größe allozieren, hier `result`, in den die empfangenen Daten geschrieben werden. Die Angabe des zweiten Argumentes ist nur für den sendenden Prozess notwendig.

```python
dim = 4
data = ([create_data(worker_id=i, dim=dim) for i in range(dist.get_world_size())]
        if dist.get_rank() == 0
        else None)
result = torch.zeros(dim)
dist.scatter(result, data)
```

`dist.all_to_all` funktioniert analog zur Scatter-Operation, wobei allerdings jeder der $n$ Prozesse der Methode eine Liste der Länge $n$ mit zu sendenden Tensoren übergibt. Leider unterstützen nicht alle Backends diese Operation.

```python
dim = 4
data = [create_data(dim=dim) + i / dist.get_world_size()
        for i in range(dist.get_world_size())]
result = [torch.zeros(dim)]
dim.all_to_all(result, data)
```

Die Methode `dist.barrier()` blockiert den ausführenden Prozess solange, bis alle anderen Prozesse an derselben Stelle im Quellcode angelangt sind.

```python
dist.barrier()
```

Standardmäßig kommunizieren die oben beschriebenen Methoden mit allen anderen Prozessen. Allerdings ist es nicht immer notwendig, alle Prozesse in die Kommunikation mit einzubeziehen. Mittels Angabe einer Gruppe von Prozessen über das Argument `group` kann die Anzahl der durch eine Operation angesprochenen Prozesse eingeschränkt werden. Dazu muss zunächst eine Gruppe mit Hilfe von `dist.new_group()` definiert werden. Dies erfordert allerdings die Beteiligung *aller* Prozesse, denn die Methode `dist.new_group()` wird solange die Ausführung pausieren, bis alle Prozesse an dieser Stelle im Code angelangt sind. Der folgende Code erzeugt eine Gruppe mit allen Prozessen, deren Ränge gerade Zahlen sind:

```python
even_ranks = {i for i in range(dist.get_world_size()) if i % 2 == 0}
group = dist.new_group(ranks=even_ranks)
```

Anschließend kann diese Gruppe verwendet werden, um eine lokale Synchronisation durchzuführen:

```python
if dist.get_rank() % 2 == 0:  # only group needs to participate
    data = create_data()
	dist.reduce(data, op=dist.ReduceOp.SUM, group=group)
```

Hierbei ist natürlich nicht mehr die Beteiligung aller Prozesse erforderlich, sondern nur noch der Prozesse in der verwendeten Gruppe.

Ein Skript, welches PyTorch Distributed verwendet, wird üblicherweise mit [`torchrun`](https://pytorch.org/docs/stable/elastic/run.html#launcher-api) oder [`python -m torch.distributed.launch`](https://pytorch.org/docs/stable/distributed.html#launch-utility) (veraltet) gestartet. Diese Befehle ermöglichen es, gleich mehrere Prozesse auf einem Rechner oder mehreren Rechnern zu starten, wodurch die manuelle Erstellung von Prozessen entfällt. Zudem bieten sie Kommandozeilenoptionen an, um die nötigen Umgebungsvariablen zu konfigurieren. So wird beispielsweise mit `--nnodes` die Anzahl der teilnehmenden Rechner bestimmt, `--nproc-per-node` gibt die Anzahl der Prozesse pro Rechner an und `--master-addr` dient der Angabe der Hauptprozessadresse (z.B. IP-Adresse oder Domain-Name).

Zur Demonstration der Konzepte habe ich [dieses Skript](https://github.com/stephankoe/blog/tree/main/content/post/communication-pattern/demo.py) geschrieben. Es führt die oben angesprochenen Methoden mit Beispieldaten hintereinander aus und protokolliert ausführlich die ausgeführten Operationen sowie die Ein- und Ausgabedaten. Ich habe es auf einem Laptop mit Ubuntu 23.10, Python 3.11 und PyTorch 2.0.1 getestet. Es kann einfach mittels 

```bash
torchrun --nproc-per-node=4 demo.py
```

 gestartet werden.

## Referenzen

{{bibliography}}
