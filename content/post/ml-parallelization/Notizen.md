# Notizen

- Parameterserver
- Balanced PP (BPipe)
- Generalization gap, problem of large batch sizes
- Analyse des Trainingsprozesses mit Blick auf Parallelisierung (Forward, Backward, SGD)
- The efficiency of parallel training is largely influenced by communication and can be much improved by optimiyation of communication patterns. However, since this article is about distributed training architectures, the optimization of communication will be explored in a future article.
- Achieving super-linearity in NN training, e.g., ZeRO

## Statischer Speicher

Gegeben: 

- $V$: Vokabular
- $L$: Anzahl der Schichten
- $H_a$: Dimension des Attention-Mechanismus (hidden size)
- $H_f$: Dimension des FFNN
- $S$: Sequenzlänge
- $N_t$: Tensor-Shards
- $N_p$: Pipeline-Shards

Dann: 

- Word embedding table: $W = \frac{V \cdot H_a}{N_t \cdot N_p}$
- POS embedding: $P = \frac{S H_a}{N_p}$
- Attention layer norm: $\frac{2 H_a L}{N_p}$
- QKVA-Gewicht: $\frac{4 H_a^2 L}{N_t N_p}$
- QKV-Bias: $\frac{3 H_a L}{N_t N_p}$
- A-Bias: $\frac{HL}{N_p}$
- FFNN layer norm: $\frac{2 H_a L}{N_p}$
- F weight size: $\frac{H_a H_f L}{N_t N_p}$
- F1 bias: $\frac{H_f L}{N_t N_p}$
- F2 bias: $\frac{H L}{N_p}$

Modellgrößen:

- GPT: $W$ + pos embedding + attention layer norm + QKVA-Gewicht + QKV-Bias + A-Bias + FFNN Laer norm + F weight + F1 bias + F2 bias
- Llama: $W$ + pos embedding + attention layer norm + QKVA-Gewicht + FFNN layer norm + 3  * F weight