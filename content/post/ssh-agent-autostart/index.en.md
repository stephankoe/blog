---
title: "Auto-Start of SSH agent on headless servers"
description: "Explanation of the functionality of the SSH agent program from OpenSSH as well as configurations for automatically starting the associated background service"
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

# How to Auto-Start the SSH Agent

Headless[^headless] servers usually do not have an SSH agent service pre-installed. To keep SSH keys in memory for convenience while working on the server, an SSH agent must be started by the user manually. However, the lifespan of the SSH agent is not tied to the current session, so the process remains active even after the user session ends. The connection parameters, on the other hand, are lost after the session if only stored in environment variables. Additionally, using multiple instances of agent may be undesirable as each instance may have different keys loaded into memory, requiring multiple password inputs.

[^headless]: Servers without graphical user interfaces

In this article, I explain how the SSH agent can be used on a headless server without needing to start a new instance manually with each new session.

In my previous article "[Tips and Tricks: SSH](../ssh)", I give more details on configuring SSH with cryptographic keys.

## Usage Modes of `ssh-agent`

The command `ssh-agent` starts the ssh agent service. This command usually offers two usage modes:

- `ssh-agent` starts a permanently running background service, prints the connection parameter on the console and terminates.
- `ssh-agent command [arg ...]` starts an SSH agent in the background and runs the command `command` with the given arguments. This started child process receives the connection parameters from its parent. The SSH agent terminates as soon as the child process terminates.

### Usage of `ssh-agent` as Background Service

The following session protocol shows that `ssh-agent` starts a background process with the same name, prints the connection parameters and returns the control flow back to the user.

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

According to the [manual](https://www.man7.org/linux/man-pages/man1/ssh-agent.1.html), this mode is for login sessions. The output of `ssh-agent` is valid shell code and can be evaluated with the builtin `eval`, whereby the connection parameter are made available to the current session as environment variables.

### Usage of `ssh-agent` as Parent Process

This mode is usually used as parent process for an X session. When `ssh-agent` receives positional arguments, it will start an SSH agent in the background, setups the environment with the connection parameters and executes the command with the given arguments as a child process. This child process will inherit the environment of its parent process, so it also receives the environment variables with the connection parameters.

The following session protocol visualizes this behaviour. Since the command `ssh-agent` is started with the argument `bash`, a new interactive shell opens. Therefore, the process IDs differ before and after the execution of `ssh-agent bash`. Within this interactive shell, the necessary connection parameters are available and the SSH agent process is running in the background. After the user exits the session, the user returns to the original session, the environment variables with the connection parameters are empty and the SSH agent terminated as well.

```bash
user@server:~ $ echo $$  # Process ID of current session
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

## System Configuration

This chapter contains a few possible system configurations that

- start the SSH agent in the background without user intervention, and
- only start at most one SSH agent per user/session.

### Script to start an instance of `ssh-agent`

The basic idea is to store the connection parameter of `ssh-agent` in a file and load this file every time a new session is opened. Since the connection parameters could be out-of-date or invalid, a few checks are required. The following code block contains a possible implementation.

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

This code reads the connection parameters of the SSH agent from the file `~/.local/state/ssh/ssh_agent_env`. If this file does not exist or the given process ID is invalid, a new agent process is started and the file content is overwritten by the new connection parameters. Finally, the configured keys are loaded automatically in memory if the value of the `AddKeysToAgent` setting is not `yes`.

To automatically start an SSH agent in the background, this script can be loaded in `~/.bashrc`, so the current configuration parameters are available in every new command line session.

The configuration `AddKeysToAgent yes` in the user or system configuration (cf. "[SSH-Client Configuration](../ssh/index.en.md#Configuration)") results in automatically loading the key in the agent when it is used. In this case, `ssh-add` does not has to be executed in advance.

### SSH Agent as System Service

Instead starting `ssh-agent` with the [above-mentioned script](#script-to-start-an-instance-of-1), it can also be started and maintained with [systemd](https://systemd.io). systemd is a system program that is, among others, responsible for the administration of background services in the majority of current Linux distributions.

Services in systemd are registered with a configuration file. These configuration files are usually stored by the system administrator in the directory `/etc/systemd/system`. Regular users who usually do (should) not have write permissions in `/etc` can also define their own services by storing configuration files in `~/.config/systemd/user`. If this directory does not yet exist, it must be created first. 

The following shell code sets up an SSH agent service with systemd:

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

Here, the service `ssh-agent` is provided with an uniquely determined path for the socket. `%t` stands for the directory where runtime data for the current user is stored. This corresponds to the value of the environment variable `$XDG_RUNTIME_DIR`. When the user logs in, the service is started automatically and the runtime of the background service can be manually controlled with the usual systemd commands.

Next, the user has to manually configure the value of the environment variable `$SSH_AUTH_SOCK`, so the SSH clients in the new sessions can connect to the SSH agent background process. One possibility to configure this is:

```bash
env_dir="${XDG_CONFIG_HOME:-"${HOME}/.config"}/environment.d"
mkdir -p "${env_dir}"
cat >> "${env_dir}/ssh_auth_socket.conf" <<EOF
SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.socket"
EOF
```

The files in the directory [environment.d](https://www.man7.org/linux/man-pages/man5/environment.d.5.html) contain definitions of environment variables and will be loaded by systemd during startup. After reloading the systemd services, the new service can be enabled:

```bash
systemctl --user enable --now ssh-agent
```

This solution was proposed in [StackExchange Unix&Linux](https://unix.stackexchange.com/a/390631).

## IT Security Considerations

To minimize the possibility of misuse, it is recommended to configure a timeout for the keys. The applications `ssh-agent` and `ssh-add` offer the option `-t` with which the user can set a time in seconds that the unlocked keys should remain in memory.
