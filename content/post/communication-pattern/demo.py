"""Demonstration of inter-process communication in PyTorch"""
from argparse import ArgumentParser
import os
import time
from typing import Callable, Iterable, Sequence, Optional

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

_DIM = 12
_COLORS = tuple(
    f"\033[0{h};{c}m"
    for h in range(3)  # light
    for c in range(31, 37)  # hue
)
_RESET_COLOR = "\033[00m"
_BACKEND = "gloo"  # nccl for CUDA


def print_dist(message: str,
               ranks: Optional[Iterable[int]] = None,
               worker_id: Optional[int] = None,
               ) -> None:
    """
    Print the given message, so it doesn't conflict with
    other processes and is easily identifiable
    :param message: text to print
    :param ranks: if not None, only these ranks will print
    :param worker_id: current worker ID (if group not initialized yet)
    """
    rank = (dist.get_rank()
            if worker_id is None
            else worker_id)
    if ranks is not None and rank not in ranks:
        return
    print(f"[RANK {rank}] {message}")


def sleep(worker_id: int) -> int:
    """
    Pause the execution of given worker based on worker_id
    and print the amount in seconds the worker is going to
    pause
    :param worker_id: worker ID
    :return: number of seconds
    """
    timeout = worker_id * 2
    if timeout:
        print_dist(f"Worker {worker_id} is going to do some "
                   f"processing which will take {timeout} seconds",
                   worker_id=worker_id)
        time.sleep(timeout)


def create_array(dim: int = _DIM) -> torch.Tensor:
    """
    Create an array with values depending on the current worker's rank
    :param dim: array dimension
    :return: array
    """
    # If using NCCL as backend, this tensor must be on the
    # GPU. Different processes cannot share one GPU.
    data = torch.arange(dim) + dist.get_rank() * dim
    if dist.get_backend() == "nccl":
        data = data.to(f"cuda:{dist.get_rank()}")
    return data


def print_array(arr: torch.Tensor,
                when: str,
                op: str,
                what: str = "array",
                ) -> None:
    """
    Print the contents of the given array
    :params arr: array
    :params when: before or after the operation
    :params op: name of the operation
    :params what: name of the array
    """
    print_dist(f"{what.title()} on worker {dist.get_rank()} {when} "
               f"the {op} operation: {arr}")


def demonstrate_broadcast() -> None:
    """Demonstrate broadcast"""
    # Broadcast (worker 0)
    values = create_array()
    sleep(dist.get_rank())
    print_array(arr=values, when="before", op="broadcast")
    print_dist("BROADCAST...", ranks=[0])
    dist.broadcast(values, src=0)
    print_array(arr=values, when="after", op="broadcast")


def demonstrate_reduce() -> None:
    """Reduce (worker 0)"""
    values = create_array()
    sleep(dist.get_rank())
    print_array(arr=values, when="before", op="reduce")
    print_dist("REDUCE...", ranks=[0])
    dist.reduce(values, dst=0)
    print_array(arr=values, when="after", op="reduce")


def demonstrate_all_reduce() -> None:
    """AllReduce"""
    values = create_array()
    sleep(dist.get_rank())
    print_array(arr=values, when="before", op="all-reduce")
    print_dist("ALL REDUCE...", ranks=[0])
    dist.all_reduce(values, op=dist.ReduceOp.SUM)
    print_array(arr=values, when="after", op="all-reduce")

def demonstrate_gather() -> None:
    """Gather (worker 0)"""
    dest_id = 0
    values = create_array()
    sleep(dist.get_rank())
    if dist.get_rank() == dest_id:
        output_arrays = [torch.zeros_like(values)
                         for _ in range(dist.get_world_size())]
    else:  # other processes don't need output_arrays
        output_arrays = None
    print_array(arr=values, when="before", op="gather")
    print_dist("GATHER...", ranks=[0])
    dist.gather(values,
                dst=dest_id,
                gather_list=output_arrays)
    print_array(arr=values, when="after", op="gather", what="values")
    print_array(arr=output_arrays, when="after", op="gather", what="gathered data")


def demonstrate_all_gather() -> None:
    """All-Gather"""
    values = create_array()
    sleep(dist.get_rank())
    output_arrays = [torch.zeros_like(values)
                     for _ in range(dist.get_world_size())]
    print_array(arr=values, when="before", op="all-gather")
    print_dist("ALL GATHER...", ranks=[0])
    dist.all_gather(output_arrays, values)
    print_array(arr=values, when="after", op="all-gather", what="values")
    print_array(output_arrays, "after", op="all-gather", what="gathered data")


def demonstrate_scatter() -> None:
    """Scatter (worker 0)"""
    src_id = 0
    sleep(dist.get_rank())
    if dist.get_rank() == src_id:
        values = [create_array()
                  for _ in range(dist.get_world_size())]
    else:
        values = None
    output_array = torch.zeros(_DIM, dtype=int)
    print_array(arr=values, when="before", op="scatter", what="values")
    print_array(arr=output_array, when="before", op="scatter", what="output")
    print_dist("SCATTER...", ranks=[0])
    dist.scatter(output_array, values)
    print_array(arr=output_array, when="after", op="scatter", what="output")


def demonstrate_all_to_all() -> None:
    """All-to-All"""
    if dist.get_backend() == "gloo":  # doesn't support all-to-all
        print_dist(f"Skip all-to-all: not supported by {dist.get_backend()}")
        return

    sleep(dist.get_rank())
    values = [create_array()
              for _ in range(dist.get_world_size())]
    output_arrays = [torch.zeros_like(array)
                     for array in values]
    print_array(arr=values, when="before", op="all-to-all", what="values")
    print_array(arr=output_arrays, when="before", op="all-to-all", what="output")
    print_dist("ALL TO ALL...", ranks=[0])
    dist.all_to_all(output_arrays, values)
    print_array(arr=values, when="after (values)", op="all-to-all", what="values")
    print_array(arr=output_arrays, when="after", op="all-to-all", what="output")


def demonstrate_group() -> None:
    """
    Create a group containing all workers with even IDs
    All workers must participate in group creation, even
    those not part of the new group; blocks until all
    processes reach the dist.new_group(...) call
    """
    sleep(dist.get_rank())
    print_dist(f"Worker {dist.get_rank()} creates group 'even'")
    group_workers = {i for i in range(dist.get_world_size()) if i % 2 == 0}
    group = dist.new_group(ranks=group_workers)

    # Synchronize values only among the processes in our newly
    # created process group
    values = create_array()
    print_array(arr=values, when="before", op="group-local all-reduce")
    if dist.get_rank() in group_workers:
        dist.all_reduce(values, op=dist.ReduceOp.SUM, group=group)
    print_array(arr=values, when="after", op="group-local all-reduce")


if __name__ == "__main__":
    parser = ArgumentParser("PyTorch distributed demo script")
    parser.add_argument("--backend", default="gloo",
                        choices=("gloo", "nccl", "mpi"),
                        help="Communication backend")
    args = parser.parse_args()

    rank = int(os.getenv("RANK"))
    world_size = int(os.getenv("WORLD_SIZE"))

    print(f"Start worker {rank}/{world_size}")
    sleep(rank)

    # Must be called first by all processes to initialize
    # the default process group containing all workers; block
    # until all processes reach this line
    print_dist(f"Worker {rank} is waiting for process group",
               worker_id=rank)
    master_addr = os.getenv("MASTER_ADDR")
    master_port = os.getenv("MASTER_PORT")
    dist.init_process_group(backend=args.backend)
    print_dist(f"Worker {dist.get_rank()} successfully initialized process group")

    demonstrate_broadcast()
    demonstrate_reduce()
    demonstrate_all_reduce()
    demonstrate_gather()
    demonstrate_all_gather()
    demonstrate_scatter()
    demonstrate_all_to_all()
    demonstrate_group()

    # Wait until all processes reach this point, we don't want
    # processes to leave early
    dist.barrier()
    print_dist(f"Worker {dist.get_rank()} terminates")
