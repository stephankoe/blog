---
title: Parallelisierung des Maschinellen Lernens
description: Dieser Artikel beschreibt verschiedene Ansätze zur Parallelisierung von Trainings-Algorithmen im Maschinellen Lernen.
date: 2024-01-28 09:04:28+0800
image: cover.jpg
toc: true
math: true
draft: true
categories:
   - distributed-computing
   - machine-learning
weight: 1
---

# Parallelisierung des Maschinellen Lernens

Jüngste Forschungen über skalierbare Architekturen wie den Transformer [@vaswaniAttentionAllYou2017] haben gezeigt, dass die Leistungsfähigkeit von neuronalen Netzen mit der Anzahl ihrer Parameter korreliert [@kaplanScalingLawsNeural2020] und dabei mit besonders großen Netzwerken beeindruckende Ergebnisse erzielt [@openaiIntroducingChatGPT2022; @openaiGPT4TechnicalReport2023]. Dies führte jüngst zu einem Wettlauf um die größten Modelle und damit verbunden einem drastischen Anstieg der Anforderungen an die Trainings- und Inferenz-Hardware. Diese Architekturen lassen sich zwar quasi beliebig vergrößern, doch sind der Skalierung in der Praxis durch die Hardware Grenzen gesetzt [@narayananEfficientLargescaleLanguage2021]. So hat sich beispielsweise die Zahl der Parameter der größten Modelle von 2018 bis 2021 vertausendfacht, während die Speicherkapazität der populärsten Beschleuniger, Nvidia-Grafikkarten, sich in demselben Zeitraum lediglich verdoppelt hat. Mit der Größe der neuronalen Netze steigt auch die Trainingszeit und die Anzahl der für das Training benötigten Daten stetig an. Um also das Training immer größerer Modelle zu ermöglichen, ist die Verteilung der Rechenleistung auf mehrere Rechenknoten unumgänglich.

![Ein Liniendiagramm, das die Größe der neuronalen Netze in den Jahren von 2018 bis 2021 darstellt. Es sind die folgenden KI-Modelle eingezeichnet: 2018: ELMo (94 Mio.), BERT-L (340 Mio.); 2019: GPT-2 (1,5 Mrd.), Megatron-LM (8,3 Mrd.); 2020: Turing-NLG (17,2 Mrd.), GPT-3 (175 Mrd.). Alle diese Modelle liegen auf einer Geraden in einem logarithmischen Maßstab.](img/neural-network-size.png)
: Größenentwicklung von neuronalen Netzen über die Zeit. Im Zeitraum von 2018 bis 2021 ist die Anzahl der Parameter in modernen neuronalen Netzen exponentiell angestiegen. Quelle: [@narayananEfficientLargescaleLanguage2021].

Dieser Artikel soll eine Einführung in das verteilte Rechnen mit dem Fokus auf das maschinellen Lernen bieten. Zunächst werden die Grundlagen erläutert, anschließend werden mit Daten- und Modellparallelisierung sowie Mixture of Experts verschiedene Formen der Parallelisierung eingeführt, die in der jüngsten Literatur diskutiert werden und in der Praxis bereits rege Anwendung finden.

## Grundlagen

Das Training immer größerer neuronaler Netze stellt die Entwickler vor zwei grundsätzliche Probleme: 

1. die für das Training nötige Rechenzeit steigt mit der Anzahl der zu trainierenden Parameter an,
2. der Speicher aktueller Grafikkarten ist zu klein für die großen Modelle inklusive ihrer Aktivierungen und Gradienten.

Diese Probleme können jeweils durch die Verteilung des Trainings auf mehrere Rechenknoten gelöst werden. Das Training von Modellen der Größe von ChatGPT und GPT-4 wird durch Parallelisierung überhaupt erst möglich gemacht. Doch führt diese Parallelisierung zu einem weiteren Problem:

3. der durch Kommunikation und Synchronisation der Rechenknoten entstehende Mehraufwand steigt mit der Anzahl der Rechenknoten an.

### Scale Out Vs. Scale Up 🚧

- Scale Up nur begrenzt möglich, scale out erlaubt in der Theorie beliebige Skalierungsfaktoren (siehe [unten](#skalierbarkeit)).
- Effizienzsteigerung eine Form von Scle UP?

### Skalierbarkeit

- Ahmdahl: strong scaling🚧
- Gustavson: weak scaling🚧

Soll durch eine Parallelisierung die Rechenzeit verkürzt werden, ist eine Betrachtung des Skalierungsverhaltens des Programms vonnöten. Nicht jedes Programm profitiert gleichermaßen von einer Verteilung auf mehrere Prozesse. Die Beschleunigung $S_p$ (engl.: *Speedup*), die durch die Verteilung auf $p$ Prozesse erreicht wird, ist das Verhältnis zwischen der Rechenzeit[^Latenz] eines einzelnen Prozesses $T_1$ zur Rechenzeit von $p$ Prozessen $T_p$:

$$
S_p = \frac{T_1}{T_p}
$$
Auf Basis der Beschleunigung kann die Effizienz $E_p$ als das Verhältnis der Beschleunigung $S_p$ zur Anzahl der Prozesse $p$ berechnet werden: 

$$
E_p = \frac{S_p}{p} = \frac{T_1}{T_p \cdot p}
$$
Die Effizienz (engl.: *efficiency*) gibt an, inwiefern das betrachtete Programm durch die Verteilung auf $n$ Prozesse profitiert. Bei einer Effizienz von $E_p = 1$ skaliert das Programm *linear*, also eine Erhöhung der Rechenkerne um einen Faktor $f$ führt zu einer Erhöhung der Beschleunigung um den gleichen Faktor. Eine Effizienz von $E_p < 1$ deutet auf ein sub-lineares Skalierungsverhalten hin und eine Effizienz von $E_p > 1$ auf eine super-lineare Skalierung. Das folgende Schaubild verdeutlicht diese Beziehung:

![Speedup](img/scalability.svg)
: Verhältnis der Beschleunigung (Speedup, $S_P$) zur Anzahl der parallelen Prozesse (\#Workers, $P$): Entspricht die Beschleunigung der Erhöhung der parallelen Prozesse ($S_P = P$, blaue Linie), skaliert das Programm linear; ist die Beschleunigung größer als die Anzahl der Prozesse ($S_P > P$, grüner Bereich), liegt eine super-lineare Skalierung vor und im umgekehrten Fall ($S_P < P$, roter Bereich) skaliert das Programm sub-linear.

Zwar gibt es einige Algorithmen, die eine linear oder sogar super-linear skalieren [@aklSuperlinearPerformanceRealTime2004;@ristovSuperlinearSpeedupHPC2016], doch ist in der Praxis eine sub-lineare Skalierung aufgrund durch die Parallelisierung zusätzlich anfallender Aufgaben wie Kommunikation und Synchronisation zwischen den Prozessen die Regel [@mccoolStructuredParallelPrograming2012].

In der Forschung zur Parallelisierung von neuronalen Netzen wird häufig nicht die Rechenzeit als Basis zur Berechnung der Beschleunigung herangezogen, da sich aufgrund der i.d.R. notwendigen Gradientenakkumulierung eine super-lineare Beschleunigung nur schwer erreichen lässt. Beispielsweise berechnen [@rajbhandariZeROMemoryOptimizations2020] die Beschleunigung in Bezug auf die Anzahl der Fließkommazahloperationen pro Sekunde (FLOPs).  🚧

[^Latenz]: Der Fachbegriff für die Rechenzeit ist "Latenz" (engl.: *latency*). 

### Klassifikation von Rechnerarchitekturen🚧

Flynn's taxonomy:

- SISD
- MISD
- SPMD/SIMD/SIMT
- MIMD/MPMD

### Rechnerhardware und Infrastruktur

Matrix-Operationen bilden die Grundlage für das Rechnen mit neuronalen Netzen. Diese lassen sich i.d.R. effizient parallelisieren, wodurch GPUs aufgrund ihrer tausenden von spezialisierten Prozessoren geeigneter für das Rechnen mit neuronalen Netzen sind als CPUs. Moderne Rechencluster setzen daher hauptsächlich auf GPUs oder speziell für die Anwendung im maschinellen Lernen entwickelte Neural Processing Units (NPUs). Beispiele für NPUs sind Googles TPU [@jouppiInDatacenterPerformanceAnalysis2017a; @googleSystemArchitectureCloud2023] und Huaweis Ascend-Plattform [@huaweiAscendComputing2024].

Da der Speicher einzelner GPUs begrenzt ist, aber die Größe moderner neuronaler Netze exponentiell anwächst [@narayananEfficientLargescaleLanguage2021], kommen in der künstlichen Intelligenz vermehrt verteilte Architekturen zum Einsatz.

Ein auf GPUs basierendes Cluster besteht aus mehreren Racks mit mittels Ethernet oder InfiniBand über Netzwerkswitches verbundenen Rechnern, an welchen wiederum über PCIe oder herstellerspezifische Sockets wie SXM mehrere GPUs angeschlossen sind. Die GPUs wiederum können mittels bandbreitenstarker Direktverbindungen und spezialisierter Switches zusätzlich untereinander vernetzt werden, um höhere Bandbreiten bei Übertragungen zwischen den GPUs eines Rechners zu ermöglichen[^NVLink]. Die Verbindungen in den unteren Schichten dieses Baumes haben i.d.R. die höchste Bandbreite, während in den darüber liegenden Schichten die Bandbreite weiter abnimmt.

![Topologie eines GPU-Clusters: Vier Server sind über einen Switch mittels dünner Linien verbunden, unterhalb der Server sind jeweils vier GPUs abgebildet, die mit dem Server über dickere Linien verbunden sind. Zusätzlich sind die vier GPUs jedes Servers über sehr dicke Linien untereinander vernetzt.](img/gpu-cluster-topology.svg)
: Die Netzwerktopologie eines GPU-Clusters. Die Dicke der Verbindungslinien zwischen den Komponenten ist proportional zu deren Bandbreite.

- SuperPOD 🚧 (xPod?) https://docs.nvidia.com/https://docs.nvidia.com/dgx-superpod-reference-architecture-dgx-h100.pdf

Im Gegensatz zur hierarchischen Topologie in GPU-Clustern sind TPUs in einer 2D-Matrix angeordnet. Jede TPU ist selbst netzwerkfähig und über schnelle Direktverbindungen mit jeweils vier anderen TPUs verbunden. Insgesamt bilden die TPUs einen Torus, was u.a. effiziente All-Reduce-Operationen ermöglicht [@jouppiDomainspecificSupercomputerTraining2020].

![Topologie eines TPU-Clusters: Die TPUs sind in einer 2D-Matrix angeordnet und sind horizontal und vertikal miteinander verbunden. Die TPUs an den Rändern der Matrix sind mit den jeweiligen TPUs an den anderen Enden verbunden, sodass die Struktur insgesamt einen Torus bildet.](img/tpu-cluster-topology.svg)
: Die Netzwerktopologie eines TPU-Clusters. Die Farben dienen lediglich der besseren Unterscheidung der Verbindungen.

[^NVLink]: NVIDIA bietet diesbezüglich NVLink und NVSwitch an [@nvidiaNVLinkNVSwitchFastest2023].

## Ansätze

Inspiriert durch die Arbeit von @zhengAlpaAutomatingInter2022 verwende ich in diesem Artikel eine ganzheitliche Sicht auf die Parallelisierung im maschinellen Lernen. Jedes ML-Modell kann in Form eines Graphs dargestellt werden, dessen Knoten entweder Daten (Eingabedaten, Parameter oder Aktivierungen) oder Operationen (Addition, Multiplikation, ...) darstellen. Bei der Verteilung eines Modells werden Teile des Graphs entlang einer oder mehrerer Dimensionen partitioniert und auf verschiedene Geräte verteilt. Die Operationen werden schließlich auf allen Geräten ausgeführt, auf denen ein Teil der Eingabedaten liegt. In der Literatur wird in Abhängigkeit von den partitionierten Daten in Datenparallelisierung, Tensor-Parallelisierung und Pipeline-Parallelisierung unterschieden:

![Es sind vier Graphen zu sehen.](img/parallelism-overview.svg)

: Übersicht über verschiedene gängige Formen der Parallelisierung: Ein Rechengraph (a) kann auf verschiedene Arten verteilt werden. Bei der Datenparallelisierung (b) werden die Daten auf mehrere Knoten verteilt, bei der Tensor-Parallelisierung (c) die Modellparameter und bei der Pipeline-Parallelisierung (d) der Graph selbst. Gegebenenfalls müssen zusätzlich Kommunikationsoperationen durchgeführt werden.

Bei der Datenparallelisierung werden die Eingabedaten sowie Aktivierungen auf mehrere Geräte verteilt, bei der Tensor-Parallelisierung hingegen die Modellparameter und Aktivierungen, während bei der Pipeline-Parallelisierung ganze Teile des Graphs verteilt werden. Diese Formen der Parallelisierung werden im Folgenden näher erläutert. Obwohl sich diese Formen der Parallelisierung gleichermaßen auf die Inference anwenden lassen, liegt der Fokus in den folgenden Ausführungen auf das Training, da der Inference-Prozess der Vorwärtsberechnung beim Training entspricht.

- welche Ansätze ermöglichen strong/weak scaling?🚧

## Datenparallelisierung

Die Datenparallelislierung ist die einfachste und am weitesten verbreitete Form der Parallelisierung im maschinellen Lernen. Beim der Datenparallelisierung werden die Eingabedaten auf mehrere Rechenknoten verteilt, was das Training auf größeren Datensätzen ermöglicht[^spmd]. Jeder Rechenknoten behält dabei das vollständige Modell im Speicher, wodurch die Größe des Modells weiterhin durch den verfügbaren Speicher begrenzt wird [@rajbhandariZeROMemoryOptimizations2020]. Jeder Knoten berechnet unabhängig voneinander die Ausgabe und Gradienten und synchronisiert anschließend die lokalen Gradienten mit den übrigen Knoten mittels einer [All-Reduce](/blog/de/p/kommunikationsmuster/#all-reduce)-Operation. Abschließend aktualisiert jeder Knoten seine lokalen Modellparameter auf Basis der akkumulierten Gradienten. In der nachfolgenden Graphik werden die Eingabedaten entlang der Batch-Dimension auf die verschiedenen Rechenknoten verteilt. Jeder Rechenknoten berechnet anschließend unabhängig voneinander die Ausgabe.

[^spmd]: Datenparallelisierung kann auch als "[Single Program Multiple Data](https://de.wikipedia.org/wiki/Single-Program_Multiple-Data)" (SPMD) betrachtet werden, wobei im maschinellen Lernen das KI-Modell mit seinen Instruktionen und Modellparametern das ausgeführte Programm darstellt.

![SVG image](img/data-parallel.svg)
: Datenparalleles Training von neuronalen Netzen. Das Modell wird auf $n$ Knoten repliziert, während die Trainingsdaten gleichmäßig auf die Rechenknoten verteilt werden. Hier werden die Daten entlang der Batch-Dimension verteilt.

Alternativ zur All-Reduce-Operation können die Modellparameter durch einen Parameter-Server aktualisiert werden [@liScalingDistributedMachine2014]. Die Aufgabe des Parameter-Servers ist die zentrale Aktualisierung der Modell-Parameter auf Basis der Gradienten aller teilnehmenden Prozesse. Da allerdings der Server mit allen Prozessen kommunizieren muss, skaliert er nur begrenzt. In der Praxis wird dieser Ansatz aktuell selten gewählt.

Üblicherweise werden die Daten entlang der Batch-Dimension verteilt, doch können die Daten auch entlang der anderen Dimensionen (z.B. der Sequenzlänge) partitioniert werden. In einigen Domänen wie z.B. der natürlichen Sprachverarbeitung können die Eingabedaten sehr lange Sequenzen enthalten, wie z.B. lange Dokumente oder Audiodaten, was bei einigen Modellarchitekturen zu Speicherproblemen führt. So hat beispielsweise der Transformer [@vaswaniAttentionAllYou2017] eine quadratische Zeit- und Speicherkomplexität in Bezug auf die Eingabelänge [@childGeneratingLongSequences2019]. @liSequenceParallelismLong2022 führen daher die Sequenzparallelisierung ein, bei der die Sprachdaten anhand der Längendimension partitioniert werden. Hierdurch wird das Training auf Datensätzen mit z.T. langen Eingabedokumenten ermöglicht. Es sind jedoch Anpassungen für Modellarchitekturen notwendig, die das gesamte Dokument betrachten. Im Falle des Transformers, der die Ähnlichkeiist er nur begrenzt skalierbarist er nur begrenzt skalierbart jedes Tokens im Eingabedokument mit jedem anderen Token berechnet, schlagen die Autoren *Ring Self Attention* vor, eine Variante des Aufmerksamkeitsmechanismus [@vaswaniAttentionAllYou2017], bei dem die partitionierten Key- und Value-Embeddings zwischen allen Rechenknoten zirkulieren. @jacobsDeepSpeedUlyssesSystem2023 hingegen implementieren in DeepSpeed Ulysses eine andere Form der Sequenzparallelisierung: TODO 🚧

Da beim datenparallelen Training alle Rechenknoten alle Modellparameter mitsamt der zugehörigen Gradienten und Optimierer-Zuständen speichern müssen, ist die Modellgröße durch den verfügbaren Speicher der einzelnen Knoten begrenzt. @rajbhandariZeROMemoryOptimizations2020 stellen deshalb den *Zero Redundancy Optimizer* (ZeRO) vor, der durch die gleichmäßige Verteilung der Optimierer-Zustände, Gradienten und Modellparameter auf alle Rechenknoten den Speicherverbrauch drastisch reduziert. Werden nur die Optimierer-Zustände und Gradienten verteilt, entspricht das Kommunikationsvolumen von ZeRO dem des datenparallelen Trainings. Bei zusätzlicher Partitionierung der Modellparameter erhöht es sich um 50%[^zeropp]. Die Autoren weisen in Experimenten nach, dass das datenparallele Training mit diesem Optimierer in Bezug auf FLOPs super-linear skaliert.

[^zeropp]: In der Praxis kann diese Erhöhung des Kommunikationsvolumens einen nicht-vernachlässigbaren Einfluss auf den Trainingsdurchsatz haben. Daher kombinieren @wangZeROExtremelyEfficient2023 Quantisierung mit einer neuen Platzierungsstrategie, um den Overhead durch die Kommunikation zu reduzieren.

PyTorch unterstützt mit PyTorch DDP [@liPyTorchDistributedExperiences2020a] schon seit längerem datenparalleles Training nativ. Die Unterstützung für die zusätzliche Partitionierung von Optimierer-Zuständen, Gradienten und Modellparametern wurde mit PyTorch FSDP [@zhaoPyTorchFSDPExperiences2023] in PyTorch 2.0 eingeführt.

Sequence-level parallelism for distributed training of long context transformers?? 🚧

## Modellparallelisierung

Bei der Modellparallelisierung werden die Parameter des Modells auf verschiedene Rechenknoten verteilt. Es wird hierbei zwischen Tensor- und Pipeline-Parallelisierung unterschieden.

### Pipeline-Parallelisierung

Bei der Pipeline-Parallelisierung (PP) [@huangGPipeEfficientTraining2019; @narayananPipeDreamGeneralizedPipeline2019; @fanDAPPLEPipelinedData2020] wird das Modell in Abschnitte aufeinander folgender Operatoren zerteilt und diese Abschnitte verschiedenen Rechenknoten zugeordnet. Die Aktivierungen der einzelnen Abschnitte werden mittels Punkt-zu-Punkt-Kommunikation[^sendrecv] auf den Rechenknoten mit dem jeweils folgenden Abschnitt übertragen. Häufig wird das Modell entlang der Schichtengrenzen zerteilt, da das Kommunikationsvolumen hier üblicherweise gering ist. Pipeline-Parallelisierung ist analog zu einem bidirektionalen Staffellauf.

[^sendrecv]: Die zugehörigen Kommunikationsprimitive werden *Send* (senden) und *Recv* (receive, empfangen) genannt.

![Visualisierung der einfachsten Form einer Pipeline-Parallelisierung](img/pp-naive.svg)
: Visualisierung der einfachsten Form einer Pipeline-Parallelisierung: Die Mini-Batches werden nacheinander in das Modell hinein gegeben. Zunächst berechnet der erste Prozess auf GPU 1 die Aktivierungen für die ersten Schichten und leitet sie an den zweiten Prozess weiter, welcher auf der zweiten GPU die Aktivierungen der nachfolgenden Schichten berechnet. Dieser Prozess wiederholt sich, bis die Vorwärtsberechnung für as gesamte Modell abgeschlossen wurde. Anschließend erfolgt die Rückwärtsberechnung entsprechend in umgekehrter Reihenfolge. Nach Abschluss der Rückwärtsberechnung werden auf allen Geräten parallel die Parameter der lokal verfügbaren Schichten auf Basis der lokalen Gradienten aktualisiert. Danach kann die Berechnung des nächsten Mini-Batches gestartet werden.

Diese Form der Parallelisierung ermöglicht prinzipiell ein beliebiges Skalieren der Modelltiefe. Der Vorteil dabei ist das bei geeigneter Wahl der Abschnitte geringe Kommunikationsvolumen und ist damit auch für Netzwerke mit geringerer Bandbreite geeignet. Allerdings führt die Hintereinanderausführung der Abschnitte zu Phasen geringer Rechenlast, die sog. *bubble time*, bei denen nur ein Teil der reservierten Rechenknoten genutzt wird. Ein Hauptziel der Optimierung von pipeline-parallelen Setups ist daher die Minimierung der Bubble-Time.

Durch die Verwendung von Micro-Batches[^micro] [@huangGPipeEfficientTraining2019][^gpipe] kann die Bubble-Zeit verringert werden. Dabei werden die herkömmlichen Mini-Batches in Micro-Batches zerteilt und nacheinander in das Modell eingegeben. Da die Micro-Batches Teil eines Mini-Batches sind, werden die Parameter erst aktualisiert, nachdem die Gradienten aller Micro-Batches vorliegen. Daher können die Rechenknoten gleichzeitig die Vorwärts- und Rückwärtsberechnung für verschiedene Micro-Batches durchführen. Die geringere Berechnungszeit von kleineren Batches und die überlappende Bearbeitung der Micro-Batches durch verschiedene Rechenknoten führt zu einer besseren Auslastung der Rechenknoten. Je höher die Anzahl der Micro-Batches, desto geringer ist der Anteil der Idle-Zeit [@narayananEfficientLargescaleLanguage2021].

[^micro]: Micro-Batches sind konzeptionell äquivalent zu Gradientenakkumulation.
[^gpipe]: GPipe

![](img/pp-microbatches.svg)
: Visualisierung der Ausführung eines Modells (links) mittels Pipeline-Parallelisierung auf vier Beschleunigern. Der Mini-Batch wurde in acht Micro-Batches unterteilt, welche jeweils nacheinander in das Modell eingegeben werden. Nachdem die Rückwärtsberechnung des achten Micro-Batches beendet wurde, werden die Parameter auf Basis der berechneten Gradienten aktualisiert und die nächsten Micro-Batches in das Modell eingegeben.

Allerdings erhöht sich dabei der für die Aktivierungen nötige Speicheraufwand[^activations], denn für jeden Micro-Batch müssen jeweils die Aktivierungen solange gespeichert werden, bis die Vorwärtsberechnung aller Micro-Batches abgeschlossen ist. Das führt bei $B$ Micro-Batches zu einem maximalen Speicherverbrauch für Aktivierungen von $B \cdot M_a$. Der 1F1B-Schedule[^1f1b] [@narayananPipeDreamGeneralizedPipeline2019; @narayananEfficientLargescaleLanguage2021; @fanDAPPLEPipelinedData2021] löst dieses Problem durch die unverzügliche Rückwärtsberechnung eines Micro-Batches, sobald die Vorwärtsberechnung für alle $S$ Pipeline-Abschnitte abgeschlossen ist. Der 1F1B-Schedule operiert in zwei Phasen: In der Aufwärmphase nimmt jeder Knoten zunächst nur Vorwärtsberechnungen, anschließend auch Rückwärtsberechnungen vor. Es kommt hierbei allerdings auch zu Idle-Zeiten. Nachdem die Vorwärtsberechnung der ersten $S$ Micro-Batches abgeschlossen ist, wechselt 1F1B in die Steady-State-Phase, in welcher jeder Knoten jeweils eine Vorwärts- und Rückwärtsberechnung abwechselnd ausführt. Der für die Speicherung der Aktivierungen nötige maximale Speicheraufwand reduziert sich daher auf $S \cdot M_a$, da zu jedem Zeitpunkt maximal $S$ Micro-Batches aktiv berechnet werden. Bei DAPPLE [@fanDAPPLEPipelinedData2021] und PipeDream-Flush [@narayananEfficientLargescaleLanguage2021] werden die Modell-Parameter aller Knoten gleichzeitig aktualisiert, sobald die Rückwärtsberechnung des Mini-Batches abgeschlossen ist (der sog. *Pipeline-Flush*). Hierbei schließt auf die Steady-State-Phase eine Abkühlungsphase an, in welcher die letzten Rückwärtsberechnungen abgeschlossen, aber keine neuen Vorwärtsberechnungen mehr vorgenommen werden. Die Idle-Zeit von 1F1B entspricht der von GPipe.

![](img/pp-1f1b.svg)

: 1F1B-Schedule mit synchroner Parameteraktualisierung nach DAPPLE [@fanDAPPLEPipelinedData2021] und PipeDream-Flush [@narayananEfficientLargescaleLanguage2021].

PipeDream [@narayananPipeDreamGeneralizedPipeline2019] erreicht neben der Speichereinsparung eine Reduktion der Idle-Zeit, indem die Parameteraktualisierung asynchron stattfindet und die Berechnung des nächsten Mini-Batches bereits beginnt, während die Rückwärtsberechnung des aktuellen noch nicht abgeschlossen ist. Dadurch wird zwar die maximale Auslastung beim Übergang zwischen Mini-Batches erreicht, doch muss für jeden Micro-Batch jeweils eine Version der Modellparameter vorgehalten werden. Bei PipeDream-2BW [@narayananEfficientLargescaleLanguage2021] wird die Anzahl der Modellparameter-Versionen auf zwei reduziert, indem die Aktualisierung der Parameter erst nach Abschluss des Mini-Batches erfolgt. Der asynchrone Schedule ist allerdings nicht mathematisch äquivalent zu SGD und dessen Konvergenz daher theoretisch nicht garantiert. Nichtsdestotrotz können @narayananEfficientLargescaleLanguage2021 nachweisen, dass sich die asynchrone Parameteraktualisierung nicht nennenswert auf das Konvergenzverhalten auswirkt.

![Async 1F1B](img/pp-1f1b-async.svg)

: PipeDream-2BW: Asynchroner 1F1B-Schedule mit double buffered weights.

[^1f1b]: 1F1B steht für "*one forward one backward*"
[^activations]: Die Anzahl der nötigen Aktivierungen kann zwar mittels *Activation Checkpointing* reduziert werden, doch müssen die Eingabe-Aktivierungen jeder Modell-Partition weiterhin gespeichert werden. Daher bleibt der Speicheraufwand proportional zur Anzahl der Micro-Batches.

Der verschachtelte (*interleaved*) 1F1B-Schedule [@narayananEfficientLargescaleLanguage2021] ist eine Optimierung des 1F1B-Schedules mit reduzierter Idle-Zeit. Diese Reduktion wird dadurch erreicht, dass ein Rechenknoten für mehrere nicht aufeinander folgende Partitionen des Modells zuständig ist (*model chunks*). Da die Partitionen des Modells nun kleiner sind, können sie schneller berechnet werden. Damit können die Micro-Batches schneller in die Pipelines eingegeben werden. Bei $v$ Modellpartitionen verringert sich die Bubble-Zeit um den Faktor $v$.

![](img/pp-1f1b-interleaved.svg)

@liChimeraEfficientlyTraining2021 erreichen mit Chimera eine bessere Auslastung durch die Verwendung mehrerer paralleler Pipelines. Diese Pipelines verwenden die verfügbaren Rechenknoten in jeweils entgegengesetzter Richtung. Dies führt zwar zu einer Verringerung der Bubble-Time, allerdings ist pro Pipeline jeweils eine Kopie der Modellparameter nötig Chimera kann als Pipeline-Parallelisierung mit Datenparallelisierung auf Ebene der Micro-Batches betrachtet werden. Daher ist neben der P2P-Kommunikation zusätzlich ein All-Reduce zwischen Knoten mit den gleichen Modellschichten nötig, um nach Abschluss der Rückwärtsberechnung die Gradienten zu synchronisieren. Diese zusätzlichen All-Reduce-Operationen können allerdings in den Bubbles am Ende der Mini-Batch-Berechnung eingefügt werden.

![Chimera](img/pp-chimera.svg)

: Chimera mit zwei Pipelines

Bei der Rückwärtsberechnung werden die Ableitungen des Fehlers in Bezug auf die Aktivierungen und Parameter berechnet, doch während erstere zur Rückwärtsberechnung in vorherigen Schichten benötigt werden, werden letztere erst bei der Parameteraktualisierung benötigt (siehe nachfolgende Grafik). Diesen Umstand machen sich @qiZeroBubblePipeline2023 zunutze und zerlegen die Rückwärtsberechnung für einen Micro-Batch in zwei Schritte: der Rückwärtsberechnung für die Aktivierungen, welche möglichst frühzeitig vollzogen werden sollte, und die Rückwärtsberechnung für die Parameter, welche zu einem beliebigen Zeitpunkt zwischen der Rückwärtsberechnung für die Aktivierungen und der Parameteraktualisierung stattfinden kann. Damit kann die Rückwärtsberechnung der vorherigen Schicht bereits beginnen, bevor die komplette Rückwärtsberechnung abgeschlossen ist.

![](img/backward-graph.svg)

: Visualisierung der Vorwärts- und Rückwärtsberechnung. Bei der Rückwärtsberechnung werden jeweils die Ableitungen des Fehlers $E$ in Bezug auf die Parameter $\theta$ und die Aktivierungen $x$ berechnet. Dabei fällt auf, dass nur die Ableitungen in Bezug auf die Aktivierungen während der Rückwärtsberechnung benötigt werden. Die Ableitungen bezüglich der Parameter (Gradienten) werden erst bei der Parameteraktualisierung benötigt.

Dadurch schaffen es die Autoren einen Pipeline-Schedule mit synchronen Parameterupdates zu kreieren, der in der Theorie keine Idle-Zeit beim Übergang zwischen den Mini-Batches aufweist. Durch die zusätzliche Kombination mit einem verschachtelten Schedule[^zero-pp-interleaved], dessen zweiter Teil entgegengesetzt zum ersten Teil verläuft🚧, stellen sie zudem sicher, dass die nur während der Rückwärtsberechnung benötigten Ableitungen bzgl. der Aktivierungen schneller wieder entfernt werden können[^zero-pp-aktiv]. In ihren Experimenten zeigen die Autoren, dass ihr Schedule einen bis zu XX% besseren Durchsatz als 1F1B erreicht.

[^zero-pp-interleaved]: Siehe *interleaved 1F1B*
[^zero-pp-aktiv]: Die erste Iteration des bubble-freien Pipeline-Schedules erforderte einen Speicher von $O(2 p M_a)$, was einen Flaschenhals darstellen kann.

![](img/pp-zero-bubble.svg)

- Token-level parallelism: makes good use of the property of the transformer that long sequences require a longer time to compute [@liangSurveyAutoParallelismLargeScale2023]. Instead of feeding data in the unit of micro-batch to the pipeline, terapipe [@liTeraPipeTokenLevelPipeline2021] splits sequence data along the token axis (i.e., length axis) unevenly and then feeds them in the pipeline where each spit has a similar execution time, orthogonal to TP, helpful in large-scale language models
- Optimize communication: Multiple streams to send/recv [@jiangMegaScaleScalingLarge2024]
- Modellpartitionierung: Möglichst balanciert (Time, memory), geringes Kommunikationsvolumen (Aktivierungen)
- Übersicht: BUbble-Time, Speicher, Kommunikation, async [@liChimeraEfficientlyTraining2021]

### Tensor-Parallelisierung

Bei der Tensor-Parallelisierung werden die Parameter-Tensoren des Modells partitioniert und auf die verschiedenen Rechenknoten verteilt. Gegebenenfalls muss auf die Operation eine Reduktion folgen, um das abschließende Ergebnis zu erhalten. Beispielsweise liegt bei einer verteilten Matrixmultiplikation das Ergebnis erst nach einem All-Reduce vollständig vor.

Megatron-LM [@shoeybiMegatronLMTrainingMultiBillion2020] partitioniert die Parameter der Matrixmultiplikationen im Self-Attention-Block sowie der MLPs spaltenweise. Diese Matrizen benötigen vor allem bei Transformern sehr viel Speicher (quadratisch in der Sequenzlänge), sodass deren Verteilung auf verschiedene Rechenknoten sehr viel Speicher einsparen kann. Allerdings ist durch die nachfolgende Synchronisation das Kommunikationsvolumen bei dieser Form der Parallelisierung sehr hoch, weshalb sie hohe Bandbreiten zwischen den Rechenknoten verlangt, auf denen die Operation ausgeführt wird. Aufgrund des hierarchischen Aufbaus von GPU-Clustern mit bandbreitenstarken Direktverbindungen zwischen den einzelnen GPUs eines einzelnen Rechners und den vergleichsweise langsamen Verbindungen zwischen verschiedenen Rechnern, ist diese Form der Parallelisierung üblicherweise am geeignetsten für die Anwendung zwischen den GPUs eines einzelnen Rechners, deren Bandbreite sie voll ausnutzen kann [@shoeybiMegatronLMTrainingMultiBillion2020].

Grafik: Matrixmultiplikation 🚧

Neben den eindimensionalen spaltenweisen Partitionierungen der Matrixmultiplikationen in Megatron-LM wurden auch andere Arten der Partitionierung vorgestellt, wie z.B. die reihenweise Partitionierung 🚧 oder die mehrdimensionale Partitionierung (2D, 2,5D, 3D) [@xuEfficient2DMethod2021; @bianMaximizingParallelismDistributed2021; @liColossalAIUnifiedDeep2022]. Obwohl sich bei der mehrdimensionalen Partitionierung in der Summe das Kommunikationsvolumen erhöht, skaliert sie besser als die eindimensionale Partitionierung, da bei der eindimensionalen Partitionierung ein All-Reduce über alle Knoten vonnöten ist, während sich bei der höher-dimensionalen Partitionierung durch mehrere voneinander unabhängige All-Reduce-Operationen eine geringere Latenz erreichen lässt 🚧.

Grafik: nd-Partitionierung 🚧

@korthikantiReducingActivationRecomputation2022 schlagen neben der Partitionierung der Matrizen der Matrixmultiplikationen des Transformers zusätzlich die Parallelisierung der LayerNorm- und Dropout-Operatoren vor. Obwohl die Parameter dieser Operatoren im Vergleich zu den Parametern des Aufmerksamkeitsmechanismus und MLPs relativ klein sind, kann durch deren Verteilung der für die Aktivierungen nötiger Speicher merklich reduziert werden. Da im Gegensatz zu den oben genannten Matrixoperationen diese Operationen reihenweise partitioniert werden 🚧, ist ein zusätzlicher Umformungsschritt nötig, um die Daten an den Schnittstellen zum Aufmerksamkeits- und MLP-Modul korrekt umzuwandeln (🚧 welche Primitive?). Sie nennen diese Form der Parallelisierung Sequenzparallelisierung, doch hat diese Methode außer dem Namen keinerlei Gemeinsamkeiten mit der von @liSequenceParallelismLong2022 vorgestellten Sequenzparallelisierung. In der Praxis hat sich die Kombination von spaltenweiser Tensor-Parallelisierung mit Sequenzparallelisierung bewährt, da sie zueinander komplementär sind und der geringere Speicherverbrauch entweder größere Batch-Größen ermöglicht, die wiederum den Durchsatz erhöhen, oder das Training überhaupt erst möglich machen. Zudem lässt sich der durch die zusätzlichen Umformungsschritte entstehende Overhead durch geschickte Verschmelzung mit den nachfolgenden Operationen deutlich reduzieren.🚧

- make full use of bandwidth, communication brought by segmentation is basically efficient collective comm🚧
- SUMMA @vandegeijnSUMMAScalableUniversal1997, 3D matmul @agarwalThreedimensionalApproachParallel1995

## Hybride Parallelisierung

- 3D CNN hybrid parallelism [@oyamaCaseStrongScaling2021 🚧

## Expertenparallelisierung 🚧

Engl.: Expert parallelism, mixture of experts
- @huangHarderTasksNeed2024

## Automatische Parallelisierung

Das manuelle Design von optimalen Parallelisierungsstrategien kann vor allem bei inhomogenen Modellarchitekturen und Rechenclustern zeit- und arbeitsaufwändig sein und erfordert überdies viel Expertenwissen. Dies ist vor allem bei sich verändernden Gegebenheiten oder bei der Verwendung verschieden strukturierter Rechencluster schwer umsetzbar. Daher haben bereits verschiedene Arbeiten Algorithmen zur automatisierten Herleitung von Parallelisierungsstrategien vorgestellt [@jiaDataModelParallelism2018; @wangSupportingVeryLarge2019; @zhengAlpaAutomatingInter2022; @liuColossalAutoUnifiedAutomation2023; @wangImprovingAutomaticParallel2023].  

@jiaDataModelParallelism2018 @wangSupportingVeryLarge2019

Besonders hervorzuheben ist hierbei die Arbeit von @zhengAlpaAutomatingInter2022, welche mit Alpa ein System vorstellen, das auf Basis des statischen Rechengraphs eines Modells sowie der tatsächlichen physischen Gegebenheiten des Rechenclusters eine nahezu optimale Parallelisierungsstrategie unter Einbezug von Inter-Operator- und Intra-Operator-Parallelisierung berechnet. Hierbei bezeichnet Inter-Operator-Parallelisierung das Zerteilen des Rechengraphs entlang der Kanten, während bei der Intra-Operator-Parallelisierung die Operatoren, bzw. die Knoten, des Graphs selbst partitioniert werden. Inter-Operator-Parallelisierung ist damit eine Verallgemeinerung der [Pipeline-Parallelisierung](#pipeline-parallelisierung). Intra-Operator-Parallelisierung hingegen umfasst [Daten](#datenparallelisierung)-, [Tensor](#Tensor-Parallelisierung)- und [Sequenzparallelisierung](#datenparallelisierung), bei denen die einzelnen Elemente des Rechengraphs selbst, nämlich die Tensoren[^tensor] und Rechenoperationen, auf mehrere Rechenknoten verteilt werden.

Das Hauptproblem bei der automatischen Herleitung einer Parallelisierungsstrategie, die sowohl Inter- als auch Intra-Operator-Parallelisierung umfasst, ist der gewaltige Suchraum. Die Autoren von Alpa lösen dieses Problem durch eine zweistufige Herangehensweise: Für jede mögliche Inter-Operator-Konfiguration suchen sie die (nahezu) optimale Intra-Operator-Konfiguration. Bei der Suche eines optimalen Intra-Operator-Parallelisierungsplans wird das Teilnetz des Clusters sowie die Partitionierung des Rechengraphs fest vorgegeben. Die Autoren formulieren die Berechnung des Intra-Operator-Plans als ein Integer-Linear-Programming-Problem, bei dem die Summe der Berechnungs-, Kommunikations- und Resharding-Kosten[^resharding] minimiert wird. Bei der Suche des Inter-Operator-Plans hingegen minimieren sie die maximale Latenz der gesamten Pipeline mittels Dynamic Programming.

Um die Komplexität weiter zu reduzieren, wenden sie zudem einige Heuristiken an wie eine Einschränkung der Submesh-Formen, die Vereinfachung des Rechengraphs, das Clustern von Operationen in Schichten mit ähnlichem Rechenaufwand, oder das frühe Beenden der Suche bei Erreichen einer Maximallatenz.

[^resharding]: *Resharding* bezeichnet eine Neuverteilung bereits verteilter Eingabematrizen, die aufgrund aufeinander folgender Operatoren mit verschiedenen Verteilungsstrategien nötig wird. Angenommen der Operator $o_{i-1}$ produziert eine Matrix, deren Reihen auf mehrere Rechenknoten verteilt sind, doch der Operator $o_i$ erwartet eine Matrix, deren Spalten auf mehrere Rechenknoten verteilt sind. Dann muss mittels einer [All-to-All](../communication-pattern/index.de.md)-Operation diese Matrix zunächst entsprechend der Eingabespezifikationen von $o_i$ neu verteilt werden.
[^tensor]: Eingabe- und Ausgabetensoren sowie die Parameter der Operatoren

@liuColossalAutoUnifiedAutomation2023 stellen mit ColossalAuto eine Strategie zur automatisierten Planung von Intra-Operator-Parallelisierung mit Activation Checkpointing vor. Sie bauen hierbei auf die Arbeit von Alpa auf, jedoch betrachten sie Inter-Operator-Parallelisierung nicht.

- Galvatron-BMW 🚧
- Übersicht 🚧
- PipeDream [@narayananPipeDreamGeneralizedPipeline2019]: Planner für PP 🚧
- DAPPLE [@fanDAPPLEPipelinedData2021]: Planner für PP 🚧

## TODO

- Optimierungsrichtingen, z.B. kommunikation verringern ode verstecken, verteilung für bessere auslastung, lange sequenzen, ...

## Referenzen

{{bibliography}}
[^8]: 
