#!/usr/bin/env python3
"""
SSH Script to execute Redpanda 'rpk cluster maintenance' commands remotely.
"""

import argparse
import getpass
import os
import sys
import paramiko


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SSH into a remote server and run 'rpk cluster maintenance' commands."
    )
    parser.add_argument(
        "-H", "--host",
        dest="host",
        required=True,
        help="Remote host IP address or hostname."
    )
    parser.add_argument(
        "-P", "--port",
        dest="port",
        type=int,
        default=22,
        help="SSH port (default: 22)."
    )
    parser.add_argument(
        "-u", "--user",
        dest="user",
        required=True,
        help="SSH username."
    )
    parser.add_argument(
        "-p", "--password",
        dest="password",
        default=None,
        help="SSH password. If omitted, will check SSH_PASSWORD env var or prompt securely."
    )
    parser.add_argument(
        "-c", "--command",
        dest="command",
        default="rpk cluster maintenance status",
        help="Command to run (default: 'rpk cluster maintenance status')."
    )
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=30,
        help="Connection and command timeout in seconds (default: 30)."
    )
    return parser.parse_args()


def run_remote_command(host: str, port: int, user: str, password: str, command: str, timeout: int) -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[*] Connecting to {user}@{host}:{port} ...")
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            look_for_keys=False,
            allow_agent=False
        )
        print("[+] Connection established successfully.")
        print(f"[*] Executing remote command: '{command}'\n" + "-" * 50)

        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

        # Read streams
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        exit_status = stdout.channel.recv_exit_status()

        if output:
            print(output.rstrip())
        if error:
            print("[STDERR]", file=sys.stderr)
            print(error.rstrip(), file=sys.stderr)

        print("-" * 50)
        print(f"[*] Command completed with exit code: {exit_status}")
        return exit_status

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Please verify your username and password.", file=sys.stderr)
        return 1
    except paramiko.SSHException as ssh_err:
        print(f"[-] SSH error: {ssh_err}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"[-] Connection timed out connecting to {host}:{port}.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[-] Unexpected error: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


def main():
    args = parse_arguments()

    password = args.password
    if not password:
        password = os.environ.get("SSH_PASSWORD")
    if not password:
        password = getpass.getpass(prompt=f"Enter SSH password for {args.user}@{args.host}: ")

    exit_code = run_remote_command(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        command=args.command,
        timeout=args.timeout
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
