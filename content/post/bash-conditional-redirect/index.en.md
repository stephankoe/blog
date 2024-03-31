---
title: "Conditional Redirection in Bash Scripts"
description: "How to route the output of a command in Bash into a file only when a condition is met?"
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

# Conditional Redirect in Bash Scripts

## Problem

Today, a colleague of mine approached me with a question: 

> How to route the output of a command into a file only when a condition is met?

Specifically, when the value of the environment variable `$PDEBUG` is true, the output (stdout) and error streams (stderr) should not only be printed onto the terminal, but additionally be stored in two different files `run.log` and `run.err`, respectively.

The challenge hereby is that the redirection operator `>` cannot simply be appended to the command with a variable because Bash would then treat it as an input argument to the command. An if-else statement would require to either repeat the command or to encapsulate it in a function. And a solution with `eval` introduces additional complexity due to quoting issues together with possible shell injection vulnerabilities, if used improperly.

## Solution

For reproducibility and easier testing, I will represent the command in question with the function `my_command`:

```bash
function my_command {
    echo "This goes to stdout"
    echo "This goes to stderr" >&2
}
```

We can achieve a conditional redirection of the command output by introducing a function `write_log` that forwards the contents from its standard input (stdin) to its stdout while simultaneously storing a copy of the contents in a file if `$PDEBUG` is truthy. This function requires the path to the output file. Then, we put this function to use by simply piping `my_command`'s output into `write_log`:

```bash
my_command | write_log run.log
```

To use `write_log` for stderr, we first have to redirect the error stream into the stdin of a subshell with `2> >(...)`[^expl]. Inside the subshell, we simply launch `write_log run.err` and redirect the output of it again back to stderr with `>&2`. This redirection is needed because the error stream from `my_command` is routed into the stdin of the subshell, which in turn is forwarded to its stdout by `write_log`. So, with `>&2` we avoid mixing stdout and stderr. As a result, the invocation of `my_command` looks as follows:

```bash
my_command \
    2> >(write_log run.err >&2) \
    | write_log run.log
```

[^expl]: `2>` redirects stderr, `(...)` creates a new sub-shell that runs `...` and the second `>` redirects the input into the stdin of the sub-shell.

To achieve conditional redirection within `write_log`, we use `tee` in combination with parameter expansion of Bash arrays. We first initiate an empty Bash array `$tee_args` and append the file path if `$PDEBUG` is truthy. Then, we run `tee "${tee_args[@]}"`. `"${tee_args[@]}"` expands the array contents and ensures proper quoting of each array element, so filenames with spaces and even Bash code don't pose problems.

Putting it all together, the final code looks as follows:

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

## Key Points

- Encapsulate the condition in a function and pipe the output of `my_command` into this function.
- `tee` stores a copy of the stream contents in a file and simultaneously writes them to stdout.
- Bash array expansion with `"${args[@]}"` helps to safely handle a variable number of arguments at runtime.
- Redirect stderr to `write_log`'s stdin and back to stderr with `2> >(write_log run.err >&2)`.
