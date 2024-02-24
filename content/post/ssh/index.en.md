---
title: "Tips and Tricks: SSH"
description: "A summary of useful SSH features that simplify the work on remote computers"
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

# Tips and Tricks: SSH

SSH (**S**ecure **Sh**ell) is a popular command-line tool to open remote connections to other computers. In contrast to conventional remote tools like *telnet* or *rsh*, SSH encrypts the transferred data, preventing third parties from viewing or manipulating the data. As a result, SSH has become the de-facto standard tool for working on remote computers and is an integral part of the toolset of many system administrators and (web) developers.

In this article, I introduce features of SSH that simplify the day-to-day use of SSH. First, I will briefly describe the usage and configuration of the SSH command-line utility. Then, I will explain the generation and usage of keys for secure passwordless authentication with remote computers. Finally, I discuss the configuration of jump hosts, git and the concurrent execution of commands on multiple remote machines. My main focus in this article is on Unix-like systems (Linux, BSD, MacOS), but I will also briefly cover SSH on Windows.

The majority of this article is based on the talk "[Besser leben mit SSH](https://media.ccc.de/v/gpn20-8-besser-leben-mit-ssh)" (english: "Live Better with SSH") by @leyrerBesserLebenMit2022, presented at the Gulaschprogrammiernacht 20 conference in May 2022.

## Usage

The SSH client is pre-installed on many Unix-like systems. The command-line application `ssh` allows to connect to remote computers provided that an SSH service is running on the remote machine. The command is passed the address of the target host, possibly along with login credentials. If no login credentials are submitted, the SSH client uses the username of the currently logged-in user by default.

For example, with the command

```bash
ssh root@ssh-server.example.com
```

you can login as root user[^root] on the device identified by `ssh-server.example.com`. Alternatively, IP addresses can also be used. The SSH server typically requests the password during login.

[^root]: On some systems, the login with the `root` account is disabled for security reasons. Generally, the direct usage of the `root` account should be avoided.

## Configuration

The SSH client can be configured via

1. a command-line option,
2. a user-specific configuration file (by default in `~/.ssh/config`), or
3. a system-wide configuration file (by default in `/etc/ssh/ssh_config`).

The option `-f` allows to load the configuration from another file. Alternatively, the SSH configuration can be distributed across multiple files in the `~/.ssh/conf.d` directory. These files will then be loaded in alphabetical order. This is useful when the user configuration becomes too cluttered with too many entries or when configurations need to be separated based on specific criteria (e.g., per client).

The simple configuration of a remote computer (host) is:

```
Host ssh-server
  HostName ssh-server.example.com
  User root
```

The keyword `Host` initiates the configuration section for a host with the given name. The names of the host follow the `Host` keyword. The SSH client uses these names to determine the configuration for the current connection request. Within the configuration, `HostName` defines the address (IP address or domain) which the client should connect to, and with the `User` option, the username is defined (in this example, `root`)[^root].

Above configuration allows the login on the configured remote computer with

```bash
ssh ssh-server  # equivalent to `ssh root@ssh-server.example.com`
```

The configuration also allows for placeholders. A list of placeholders can be found in the [documentation of ssh_config](https://man.openbsd.org/ssh_config.5#TOKENS). For example, the placeholder `%h` will be replaced by the given name. The star `*` matches arbitrary strings. Consequently, the following configuration will be used for all addresses that end with ".example.com": 

```
Host *.example.com
  HostName %h
  User root
```

Before establishing the connection, the SSH client reads the configuration file top to bottom and selects the first matching entry. Therefore, it is recommended to write specific entries (like `ssh-server.example.com`) before general (like `*.example.com`) ones.

The option `SendEnv` allows to set environment variables on the host system[^sendenv]. The configuration of `IdentitiesOnly: yes` lets the SSH client only try identities that are configured for a specific host, instead of trying all known identities. The option `Compression: yes` is useful for metered or slow connections.

[^sendenv]: However, the variable names have to be authorised in the SSH server configuration.

## Key Management

The login on a remote computer usually requires entering a password. However, SSH to use cryptographic keys for authentication, enabling passwordless logins. This key is a unique string.

### Key Generation

To generate a key on the client computer, SSH offers the command `ssh-keygen`. For example, the command

```bash
ssh-keygen -t ed25519 -a 420 -f ~/.ssh/demo.ed25519 -C "comment"
```

generates a key using the cryptographic method [ed25519](https://de.wikipedia.org/wiki/Curve25519). The manual[^man-ssh-keygen] usually provides a list of the supported cryptographic methods. The generated key will be stored in the file `~/.ssh/demo.ed25519` that we set with the `-f` option. This option is optional and by default `~/.ssh/id_${cryptographic_method}`[^file-name]. The option `-C` allows the user to add a comment to the generated key -- useful for example for documentation purposes. The option `-a` defines the number of rounds used for the generation of the key. A higher number of rounds protects better against brute-force attacks, but slows down unlocking the key.

[^man-ssh-keygen]: `man ssh-keygen`

[^file-name]: The variable `${cryptographic_method}` is a placeholder for the name of the configured cryptographic method (`-t` option). In this example, it is `ed25519`.

During key generation, `ssh-keygen` will ask for a password. This password can be chosen freely and will be used to unlock the key later. While optional, entering a strong password can protect against theft and misuse by unauthorised individuals[^breach].

[^breach]: Cryptographic keys are a popular target of hackers when breaking into systems. For example, in 2023 hackers stole a [signing key at Microsoft](https://www.microsoft.com/en-us/security/blog/2023/07/14/analysis-of-storm-0558-techniques-for-unauthorized-email-access/) that allowed them to view the e-mail inboxes of various government organizations.

`ssh-keygen` generates two files:

- `~/.ssh/demo.ed25519` is the *private* key used to prove the identity of the client on the host, and
- `~/.ssh/demo.ed25519.pub` is the *public* key used to authenticate the client.

When a client logs in to a host, the host encrypts a random string using the client's public key and sends the cipher to the client. Because the encrypted string can only be decrypted with the private key, the client can prove its identity by responding with the correct clear text. Therefore, it is absolutely necessary to keep the private key secret. Specifically, the private key *must not* be copied onto the host, nor should it be stored in any code repositories or docker images[^docker] [@mikehanleyWeUpdatedOur2023].

[^docker]: Using secrets like passwords or keys naively in docker images is risky because of the immutability of the layers. Even deleted contents can still be accessible later on. To use secrets safely in Docker images, *[docker secrets](https://docs.docker.com/engine/swarm/secrets/)* were introduced. I'm planning to cover this topic in a later article.

To mitigate the impact of a accidentally lost key, it is recommended to use different keys for different domains (e.g., customers, services, servers).

### Key Distribution

Before the host can use the key to authenticate a user, it needs the public key (`*.pub`). This key is normally stored in the file `~/.ssh/authorized_keys`.

The easiest way to distribute keys from the client to hosts is the command `ssh-copy-id`:

```bash
ssh-copy-id -i ~/.ssh/demo.ed25519.pub ssh-server
```

copies the public key in `~/.ssh/demo.ed25519.pub` to the host identified by `ssh-server` (cf. Section "[Configuration](#configuration)"). This still requires entering the user password manually.

### Key Usage

`ssh` can be instructed to use the secret key from the specified file instead of a password during login with the command-line option `-i`:

```bash
ssh -i ~/.ssh/demo.ed25519 alias1
```

The password prompted in this case is no longer the user's password on the host machine, but rather the unlock password of the secret key (if configured). Alternatively, the key can also be specified in the user configuration.

```
   Host ssh-server
     HostName ssh-server.example.com
     User root
     PreferredAuthentications publickey
     IdentityFile ~/.ssh/demo.ed25519
```

The key `PreferredAuthentications` specifies a list of preferred authentication methods, in this case, the `publickey` method is chosen. The key `IdentityFile` indicates the path to the secret key.

Upon successful configuration, the next `ssh ssh-server` command will only prompt for the password specified during key generation for the secret key.

While this allows logging into the host machine without entering a password, the user still needs to provide a password to unlock the key. For a truly passwordless login, the [key password cache](#key-password-cache) can be used.

### Key Password Cache

A password-protected secret key usually requires entering the password when used. To enable passwordless login, a key password cache can be used. On current desktop systems like GNOME or KDE, such password caches are typically already available (GNOME Keyring, Kwallet, …). When unlocking the key, a window for password entry appears, after which the password is kept in memory for a certain period. However, on systems without native password caches, such as headless servers, the command-line application `ssh-agent` is useful. This will be explained further below.

To store a password in memory using `ssh-agent`, the background service with the same name must first be started. This service communicates via a UNIX socket with the SSH subsystem, which unlocks secret keys. After starting the background service, private keys can be loaded into memory with the command `ssh-add`. The following code starts an SSH agent process and then loads all configured keys into memory:

```bash
eval $(ssh-agent)  # evaluates the code printed by ssh-agent
ssh-add  # unlocks all configured keys (requires entering passwords)
```

When the `ssh-agent` application is executed, it starts the background service with the same name and then outputs the shell code on the command line that is necessary for establishing a connection. Specifically, this sets the environment variables `SSH_AUTH_SOCK` (UNIX socket) and `SSH_AGENT_PID` (process ID). Therefore, in the example above, the output of `ssh-agent` is evaluated using the `eval` built-in, making it available to the current session.

Each time `ssh-agent` is called, a new SSH agent service is started in the background. The lifespan of the SSH agent is not bound to the lifespan of the current session, so it will keep running after closing the session. Besides, the above automatic configuration using `eval` is only valid for a the current session. The above code is unsuitable for the use in configuration files like `.profile` or `.bashrc`, because it would lead to multiple instances of the SSH agent with different states. In my article "[Automatically Starting SSH Agents on Headless Servers](../ssh-agent-autostart)", I describe a configuration that avoids redundant instances of the `ssh-agent` service.

By using `AddKeysToAgent yes` in the [SSH client configuration](#configuration), the SSH client can be instructed to automatically pass the keys to the SSH agent after unlocking. This way, the keys no longer need to be loaded into memory befohrehand using `ssh-add`, but only when needed.

### Windows

There are a multitude of commercial and free tools on Windows that allow the use of SSH. A popular, simple and free of these is [PuTTY](https://putty.org/). PuTTY provides functionalities similar to the tools in OpenSSH, including `puttygen` (`ssh-keygen`), `pagent` (`ssh-agent`), and `putty` (`ssh`), but with a graphical interface. However, keys generated with PuTTY use a different format than OpenSSH, so they may need to be converted if necessary when used on Unix-like systems.

Newer versions of Windows also offer SSH functionality natively in PowerShell. Alternatively, OpenSSH can be used directly on Windows with tools like [cygwin](https://cygwin.com/), [git bash](https://git-scm.com/downloads) or [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/de-de/windows/wsl/install).

### GNOME

The Linux desktop GNOME also provides a graphical interface for key management with the pre-installed program [GNOME Keyring](https://wiki.gnome.org/Projects/GnomeKeyring/) ("Passwords and Encryption"). This application allows for the generation of SSH keys and the storage of their passwords in memory.

## Jump Host

A jump host or "*bastion*" is a computer that allows access to other computers behind a firewall. To connect to the target host behind the firewall with just one command, the SSH client offers the command-line option `-J`:

```bash
ssh -J bastion target.local
```

This command causes the SSH client to first connect to the host `bastion` and then automatically establish a connection from there to `target.local`.

Similarly, this indirect connection can also be configured in the [configuration file](#configuration):

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

In this configuration file, the jump host is configured with the alias `bastion` first, followed by the actual target machine `internal`. When configuring `internal`, the `ProxyJump` setting specifies that the connection is made indirectly through `bastion`. This configuration allows for a direct connection to the target system using `ssh internal`.

For older SSH clients without support for `-J` or `ProxyJump`, a direct connection can be achieved by sending an SSH command to the jump host:

```bash
ssh -o ProxyCommand="ssh -W %h:%p bastion" target.local
```

The "*Agent forwarding*" feature (`-A`) is now considered insecure and should no longer be used.

## Git over SSH

Git servers also allow for authentication via SSH. Therefore, the procedure described above for passwordless authentication can also be used for Git. To this end, the public key (i.e., the contents of the `*.pub` file) is first stored on the Git server[^git-key]. Then, the respective key for the server is configured in the [configuration file](#configuration). Finally, the Git repository can be cloned using *ssh* (note: do not use *https*). For repositories already cloned using *https*, the address of the remote repository can be modified using the `git remote set-url` command.

[^git-key]: Git services like [GitHub](https://docs.github.com/de/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) and [GitLab](https://docs.gitlab.com/ee/user/ssh.html#add-an-ssh-key-to-your-gitlab-account) also allow to configure SSH keys in their graphical user interface. However, this procedure depends on the service and is not further explained here.

## Simultaneous Execution of Commands on Multiple Computers

For simultaneous execution of commands on multiple computers, the command-line tool [`pdsh`](https://github.com/chaos/pdsh) can be used, which usually needs to be installed separately. The following command sends the command `echo` to three servers:

```bash
pdsh -R ssh -w 192.168.2.100,192.168.2.101,192.168.2.102 'echo "Hello, the current time is: $(date)"'  # using IP addresses
pdsh -R ssh -w server1,server2,server3 'echo "Hello, the current time is: $(date)"'  # using aliases
```

By default, `pdsh` uses the Remote Command (rcmd) module `rsh`, but the `-R` option can be used to select `ssh` instead[^rcmd]. With the `-w` option, `pdsh` is passed a comma-separated list of the computer addresses, where the command should be executed. If names have been assigned to the target computers in the [SSH configuration file](#configuration), they can also be used here.

To ensure a successful login to the host, passwordless authentication must be set up. The set up procedure for secure passwordless authentication is described in the chapter on [Key Management](https://www.ecosia.org/chat?q=rcmd%20remote%20shell#key-management).

[^rcmd]: In addition to the `-R` option, ssh can also be selected using the environment variable `PDSH_RCMD_TYPE`. This is useful if ssh is to be made the default method for connecting with `pdsh`.

## References

{{bibliography}}

