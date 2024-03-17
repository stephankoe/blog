---
title: "Communication Patterns"
description: "Description of frequently used communication patterns in distributed maschine learning"
date: 2024-03-03T12:56:52+08:00
image: cover.jpg
math: true
categories:
  - distributed-computing
  - machine-learning
weight: 1
---

# Communication Patterns

When distributing a compute task over multiple processes, common communication patterns are used to exchange data between the participating processes. In this article, I explain some of these communication patterns[^MPI] that lay the foundation for the implementation of distributed machine learning tasks [@nielsenIntroductionHPCMPI2016]. Knowledge on these patterns is essential when analysing and understanding the processes in distributed machine learning in detail.

[^MPI]: These communication patterns are defined based on the *Message Passing Interface* (MPI). This is a standard for the communication in parallel computer architectures. Examples for implementations of MPI are [Intel MPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/mpi-library.html) and [Open MPI](https://www.open-mpi.org/).

## Description of the Communication Patterns

### Broadcast

A process sends (*broadcasts*) its data to all other processes and the receiving processes overwrite their local data with the received data. Hence, after the operation, every process has access to the data of the sending process.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. Three dashed lines from process 1 in the above row point to each process in the below row. The lines are labeled with Broadcast. The data of all processes in the below row is identical to the data of process 1 in the above row, that is x_1.](img/mpi-broadcast.svg "The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. Three dashed lines from process 1 in the above row point to each process in the below row. The lines are labeled with Broadcast. The data of all processes in the below row is identical to the data of process 1 in the above row, that is x_1.")

: Example for a broadcast operation: Process 1 sends a datum $x_1$ to all other processes, which in turn overwrite their own datum with $x_1$.

### Reduce

In a *Reduce* operation, all participating processes send their data to a certain target process, which subsequently reduces the data of all processes with a reduce operation to a single value. Commonly used reduction operations are addition and maximum. After the reduction, the target process has access to the result of the reduced data from each process, whereas the memory content of all other processes remains unchanged.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to process 1 in the below row. The lines are labeled with Reduce_sum. The data of process 1 in the below row is x_1 + x_2 + ... + x_n. The data of all other processes in the below row is identical to their value in the above row.](img/mpi-reduce.svg "The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to process 1 in the below row. The lines are labeled with Reduce_sum. The data of process 1 in the below row is x_1 + x_2 + ... + x_n. The data of all other processes in the below row is identical to their value in the above row.")

: Example for a Reduce operation: All processes send their data to process 1, which computes the sum of the data from all processes. Process 1 replaces its datum with the computed sum, while the data of all other processes remain unchanged.

### All Reduce

During the course of an *All Reduce* operation, every process sends its data to every other process. Then, upon receiving the data from all other processes, every process applies a reduction operation to the data of all processes, including its own data, and overwrite their respective previous datum with the result of this operation. After the operation, every process stores the same data.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to every process in the below row. The lines are labeled with AllReduce_sum. The data of every process in the below row is x_1 + x_2 + ... + x_n.](./img/mpi-all-reduce.svg)

: Example for an All Reduce operation: All processes exchange their data and sum them up individually. After the operation, every process has the same result in memory.

### Barrier

A *Barrier* is a mechanism to synchronise multiple processes in time. When the program pointer of a process arrives at a barrier, it will stop until all other processes arrive at the same barrier as well.

### Gather

Before the operation, each process stores a datum $x_i$. While performing the *Gather* operation, every of the $n$ processes sends its data to a certain target process. The target process in turn collects all data and stores it in a list $(x_1, ..., x_n)$.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to process 1 in the below row. The lines are labeled with Gather. The data of process 1 in the below row is a list (x_1, x_2, ..., x_n). The data of all other processes in the below row is identical to their value in the above row.](img/mpi-gather.svg "The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to process 1 in the below row. The lines are labeled with Gather. The data of process 1 in the below row is a list (x_1, x_2, ..., x_n). The data of all other processes in the below row is identical to their value in the above row.")

: Example for a *Gather* operation: Process 1 gathers the data of all $n$ processes and stores them in a list. Meanwhile, the memory of the other processes does not change.

### All-Gather

In contrast to the *Gather* operation, during an *All Gather* operation, every process individually gathers the data of every process. As a result, every process has a list $(x_1, ..., x_n)$ of data from every process.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a datum x_i each. The datum of process 1 is x_1 before the operation, the data of the other processes is given with x_2 to x_n. There is a dashed line from each process in the above row to each one in the below row. The lines are labeled with AllGather. The data of each process in the below row is a list (x_1, x_2, ..., x_n).](img/mpi-all-gather.svg)

: Example of an *All Gather*  operation: Every process receives a copy of the data from every other process and stores them in a list.

### Scatter

During a *Scatter* operation, a process distributes the data from a list $(x_1, ..., x_n)$ over all $n$ processes, including itself. Thereby, every process receives exact one entry from that list. Specifically, the $i$th process receives the $i$th value $x_i$. *Scatter* is therefore the reverse operation to the *[Gather](#gather)* operation.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes. Next to process 1 is a list of values (x_1, x_2, ..., x_n). There is a dashed line from process 1 in the above row to every process in the below row. The lines are labeled with Scatter. The data of process 1 in the below row is x_1, the data of process 2 is x_2, and so on. Hence, every process in the below row received a value from the list held by process 1.](img/mpi-scatter.svg)

: Example of a *Scatter*  operation: The entries of a list $(x_1, ..., x_n)$ are distributed evenly across all processes. After the operation, every process stores an entry from that list.

### All-to-All

All $n$ processes has allocated a list with $n$ elements each. When performing the *All-to-All* operation, every process individually distributes the entries of its list to all other processes (cf. *[Scatter](#scatter)*). At the same time, every process gather the received data and store them in a list of size $n$ (cf. *[Gather](#gather)*). This operation is comparable to transposing a 2D matrix, whose columns are distributed onto multiple processes.

![The image shows two rows. The above one is labeled with before, the below one with after. Every row contains n processes with a list of n values (x_i,1, ..., x_i,n) each. There is a dashed line from each process in the above row to each process in the below row. The lines are labeled with All-to-all. The data of each process i in the below row is a list (x_1,i, x_2,i, ..., x_n,i).](img/mpi-all-to-all.svg)

: Example for an *All-to-All* operation: Every process distributes its local data to all processes in a way that process $i$ receives the $i$th entry of that list. In turn, every process gathers the received data into a list. For example, as a result of the operation, the list of process 1 contains the respective first elements from the original lists of every process.

## Summary

- **Broadcast**: A certain process sends its data to all other processes.
- **Reduce**: The data of all processes is reduced to a single value by a certain process.
- **All-Reduce**: The data of all processes is reduced to a single value by all processes.
- **Barrier**: The process pauses until all other processes arrived at the same barrier.
- **Gather**: The data of every process is gathered by a certain process and stored in a list.
- **All-Gather**: The data of every process is gathered by all processes and stored in a list.
- **Scatter**: The data of a certain process is distributed evenly across all processes.
- **All-to-All**: The data of every process is distributed evenly across all processes, while every process gathers the received data into a list.

## PyTorch Distributed

Since the communication patterns described above are the foundation for the implementation of distributed AI architectures, they are integrated into the popular machine learning library *PyTorch* in the form of the package *PyTorch Distributed*. In this capter, I explain how to use these patterns with the methods provided by PyTorch.

PyTorch Distributed is the basis for important building blocks of parallel learning in PyTorch, such as PyTorch DDP [@liPyTorchDistributedExperiences2020] and PyTorch FSDP [@zhaoPyTorchFSDPExperiences2023]. @liPyTorchDistributedOverview2024 describes the implementation of data parallel training in PyTorch in detail. Moreover, the [official PyTorch documentation](https://pytorch.org/docs/stable/distributed.html) offers detailed information on the available methods.

These communication patterns are relatively low-level and hence, a typical ML engineer is usually not required to use them to parallelize a PyTorch model. Instead, PyTorch offers more abstract tools like PyTorch DDP or FSDP.

To start a distributed application, PyTorch Distributed first must be initialised. During initialisation, it creates a group (*default group*) that contains all participating processes. To this end, the programmer calls the method  [`torch.distributed.init_process_group`](https://pytorch.org/docs/stable/distributed.html#torch.distributed.init_process_group), which reads the configuration from environment variables by default. The most important environment variables are:

- `RANK`: the global rank of the process, comparable to a worker ID,
- `LOCAL_RANK`: the local rank of the process on the current host, comparable to a host-local worker ID,
- `WORLD_SIZE`: the number of participating processes,
- `MASTER_ADDR`: the address of the main process used for coordination, and
- `MASTER_PORT`: the respective port of the main process.

Alternatively, this data can also be supplied to [`torch.distributed.init_process_group`](https://pytorch.org/docs/stable/distributed.html#torch.distributed.init_process_group) as arguments.

```python
import torch
import torch.distributed as dist

dist.init_process_group()
```

In the following, I will use the abbreviation `dist` for `torch.distributed` for a more concise presentation. PyTorch supports multiple backends for inter-process communication (IPC) such as MPI, GLOO or [NCCL](https://developer.nvidia.com/nccl). In this example, I use GLOO as a backend which is suitable for local testing on a PC. The NVIDIA Collective Communications Library (NCCL) requires at least one NVIDIA GPU per process and in order to be able to use MPI, PyTorch must first be compiled with MPI support. More details on backends is provided in [this tutorial](https://pytorch.org/tutorials/intermediate/dist_tuto.html#communication-backends).

For a concise presentation, I introduce the method `create_data` that creates a tensor with data depending on the rank of the current process, and moves it to a GPU if required. When using GPUs with CUDA, one must note that two processes that communicate over NCCL must also allocate two different GPUs.

```python
def create_data(worker_id: int = None, dim: int = 4) -> torch.Tensor:
    worker_id = worker_id if worker_id is not None else dist.get_rank()
    data = torch.arange(dim) + worker_id * dim
    if dist.get_backend() == "nccl":
        data = data.to(f"cuda:{worker_id}")
    return data
```

The method `dist.broadcast` initiates a broadcast of the provided data from process `src` to all other processes. The argument `src` determines the rank of the sending process, in this example 0. Every process allocates a tensor `data` of equal size in beforehand. The sending process will send the contents of this tensor to all other processes and the receiving processes will overwrite the contents of their `data`  tensor with the received data. After the operation completed, the contents of `data` is the same in every process.

```python
data = create_data()
dist.broadcast(data, src=0)
```

A reduction is initiated with the method `dist.reduce`. Similar to the broadcast method, all process first allocate a tensor `data` of equal size. The contents of this tensor is sent to process 0. The argument `dst` defines the destination process and the argument `op` the reduction operation.

```python
data = create_data()
dist.reduce(data, dst=0, op=dist.ReduceOp.SUM)
```

Similarly, an All Reduce is performed with the method `dist.all_reduce`. However, the programmer does not need to specify `dst`.

```python
data = create_data()
dist.all_reduce(data, op=dist.ReduceOp.SUM)
```

To gather data in a certain process, PyTorch provides the method `dist.gather`. This method takes as input an already allocated tensor `data`, the rank of the destination process `dst`, as well as a list containing suitably sized tensors `gather_list`. The data received from each process is stored in `gather_list`, so it has to contain as many pre-allocated tensors as there are processes participating in the operation. `gather_list`, however, is only required for the destination process, all other processes do not have to specify this argument.

```python
data = create_data()
result = ([torch.zeros_like(data) for _ in range(dist.get_world_size())] 
          if dist.get_rank() == 0 
          else None)
dist.gather(data, dst=0, gather_list=result)
```

With the method `dist.all_gather`, an All Gather operation is performed. The usage of this method is similar to `dist.gather`. As with All Reduce, the argument `dst` is dropped.

```python
data = create_data()
result = [torch.zeros_like(data) for _ in range(dist.get_world_size())]
dist.all_gather(result, data)
```

A scatter operation is done with `dist.scatter`, whereby the sending process – in this example, process 0 – inputs a list `data` with one tensor for every process. The process with the rank $i$ will receive the tensor `data[i]`. First, every process must allocate a suitably sized tensor, here `result`, into which `dist.scatter` can write the received data. The second argument is only required for the sending process and can be omitted on the other processes.

```python
dim = 4
data = ([create_data(worker_id=i, dim=dim) for i in range(dist.get_world_size())]
        if dist.get_rank() == 0
        else None)
result = torch.zeros(dim)
dist.scatter(result, data)
```

`dist.all_to_all` works analogous to the scatter operation, but every of the $n$ processes must provide the method with a list of size $n$ and appropriately sized tensors. Unfortunately, not all backends support this operation.

```python
dim = 4
data = [create_data(dim=dim) + i / dist.get_world_size()
        for i in range(dist.get_world_size())]
result = [torch.zeros(dim)]
dim.all_to_all(result, data)
```

The method `dist.barrier()` blocks the running process until all processes arrived at the same location in their code.

```python
dist.barrier()
```

By default, the above-mentioned methods communicate with all processes. However, not always is it necessary that all processes participate in the communication. When given a group of processes via the argument `group`, only a certain subset of nodes will synchronise, while all other nodes will continue to compute independently. First, a new group must be initialized with the `dist.new_group()` method. However, this requires the participation of *all* processes because this method will wait until all processes arrived at the same location in the code. The following code creates a group with all processes with an evenly numbered rank:

```python
even_ranks = {i for i in range(dist.get_world_size()) if i % 2 == 0}
group = dist.new_group(ranks=even_ranks)
```

Subsequently, this group can be used to synchronise processes locally:

```python
if dist.get_rank() % 2 == 0:  # only group needs to participate
    data = create_data()
	dist.reduce(data, op=dist.ReduceOp.SUM, group=group)
```

Of course, this does not require all processes to participate, but only those within the group. Therefore, those processes with an unevenly numbered rank can skip this operation.

A script using PyTorch Distributed can usually be launched with [`torchrun`](https://pytorch.org/docs/stable/elastic/run.html#launcher-api) or [`python -m torch.distributed.launch`](https://pytorch.org/docs/stable/distributed.html#launch-utility) (deprecated). These commands allow to run multiple processes on a single computer or even multiple computers (nodes). They automatically create the required number of processes and additionally offer command-line options to configure the necessary environment variables. For example, `torchrun` allows to specify the number of participating nodes with `--nnodes` and the number of processes per node with `--nproc-per-node`. `--master-addr` specifies the address of the main node (e.g., IP address or domain name).

To demonstrate the concepts, I wrote [this script](https://github.com/stephankoe/blog/tree/main/content/post/communication-pattern/demo.py). It runs the above-mentioned methods with example data in sequence and prints a detailed protocol of the executed operations and their inputs and outputs. I tested it on a laptop with Ubuntu 23.10, Python 3.11 and PyTorch 2.0.1. It can be simply run with 

```bash
torchrun --nproc-per-node=4 demo.py
```

## References

{{bibliography}}
