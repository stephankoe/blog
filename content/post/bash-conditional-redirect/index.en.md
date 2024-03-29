---
title: "Conditional Redirect in Bash Scripts"
description: ""
date: 2024-03-27T17:42:52+08:00
image: 
math: false
categories:
  - bash
  - programming
  - linux
weight: 1
draft: true
---

# Conditional Redirect in Bash Scripts

Today, a colleague of mine approached me with a question: *How to route the output of a command into a file only if a given condition is met?* 
Specifically, he uses an environment variable `$PDEBUG` to define whether the output of a command should be stored in a file in addition to the output on the terminal.
In that case, the output of the output and error streams should end up in two different files `run.log` and `run.err`, respectively.

For reproducibility and easier testing, I use the function `my_command` as the command in this example.

```bash
function my_command {
    echo "This goes to stdout"
    echo "This goes to stderr"
}
```

We can achieve this behavior by introducing a function `write_log` that takes the input from stdin and `tee`s it into a file if `$PDEBUG` is truthy. This function requires a filepath where it writes the results into. Finally, we simply pipe the result of `my_command` into `write_log`.

To write the text on stderr into another file, we also can use `write_log`, but we have to redirect the error stream with into the stdin of a subshell with `2> >(...)`. Inside the subshell, we simply launch `write_log run.err` and redirect its output again to its error stream. This redirection is needed because the error stream from `my_command` was routed into the stdin of the subshell, which prints the input onto the stdout stream of the subshell via `tee`. So, we need `>&2` to avoid mixing stdout and stderr.

Inside the function `write_log`, we initiate an empty Bash array `$tee_args` and add the file path to it when `$PDEBUG` is truthy. Then, the array `$tee_args` is given to `tee` as argument. The advantage of using an array instead of a simple Bash variable here is that Bash automatically ensures proper quotation and escaping of the content of the array when expanded with "${tee_args[@]}".

The resulting code looks like the following:

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
