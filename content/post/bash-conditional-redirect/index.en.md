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

```bash
PDEBUG="${PDEBUG:-"$1"}"  # debug-mode on/off
LOG_DIR="${LOG_DIR:-"log"}"

function write_log {
    filename="${1?"Filename required!"}"
    tee_args=()
    if "${PDEBUG}"; then
        mkdir -p "${LOG_DIR}"
        tee_args+=("${LOG_DIR}/${filename}")
    fi
    tee "${tee_args[@]}"
}

my_command \
    2> >(write_log run.err >&2) \
    | write_log run.log
```
