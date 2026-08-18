#!/usr/bin/env python3
import argparse
import re
import shlex
import sys
import paramiko


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SSH into a Redpanda host and fetch broker information via 'rpk cluster info'."
    )
    parser.add_argument(
        "-H", "--host",
        dest="host",
        required=True,
        help="SSH Remote host IP or hostname ([IP_ADDRESS])."
    )
    parser.add_argument(
        "-P", "--port",
        dest="port",
        type=int,
        default=22,
        help="SSH port (default: 22)."
    )
    parser.add_argument(
        "-u", "--ssh-user",
        dest="ssh_user",
        required=True,
        help="SSH username ([SSH_USERNAME])."
    )
    parser.add_argument(
        "-p", "--ssh-password",
        dest="ssh_password",
        required=True,
        help="SSH password ([SSH_PASSWORD])."
    )
    parser.add_argument(
        "--sasl-user",
        dest="sasl_user",
        required=True,
        help="Redpanda SASL username ([SASL_USERNAME])."
    )
    parser.add_argument(
        "--sasl-password",
        dest="sasl_password",
        required=True,
        help="Redpanda SASL password ([SASL_PASSWORD])."
    )
    parser.add_argument(
        "--sasl-mechanism",
        dest="sasl_mechanism",
        default="SCRAM-SHA-256",
        help="SASL mechanism (default: SCRAM-SHA-256)."
    )
    return parser.parse_args()


def parse_brokers(output: str):
    """
    Parses the BROKERS section from Redpanda `rpk cluster info` output.

    Returns:
        tuple: (list of broker dicts, main/controller broker dict or None)
    """
    brokers = []
    main_broker = None

    # Match everything under the BROKERS header until the next section header (e.g. TOPICS)
    section_match = re.search(r'BROKERS\s*\n=+\s*\n(.*?)(?=\n\s*[A-Z]+\s*\n=+|\Z)', output, re.DOTALL)
    if not section_match:
        section_match = re.search(r'BROKERS\s*\n(.*?)(?=\n\s*[A-Z]+|\Z)', output, re.DOTALL)

    if section_match:
        section_lines = section_match.group(1).strip().splitlines()
        for line in section_lines:
            line = line.strip()
            if not line or line.upper().startswith("ID"):
                continue

            # Format: ID (e.g. 0 or 0*), HOST, PORT, (optional RACK, etc.)
            parts = line.split()
            if len(parts) >= 3:
                raw_id = parts[0]
                is_main = "*" in raw_id
                broker_id_str = raw_id.replace("*", "")

                try:
                    broker_id = int(broker_id_str)
                except ValueError:
                    broker_id = broker_id_str

                host = parts[1]
                try:
                    port = int(parts[2])
                except ValueError:
                    port = parts[2]

                broker_info = {
                    "id": broker_id,
                    "host": host,
                    "port": port,
                    "is_main": is_main,
                    "raw_id": raw_id,
                }
                if len(parts) > 3:
                    broker_info["rack"] = parts[3]

                brokers.append(broker_info)
                if is_main:
                    main_broker = broker_info

    return brokers, main_broker


def main():
    args = parse_arguments()

    # Safely escape parameters for the remote bash command
    command = (
        f"rpk cluster info "
        f"-X user={shlex.quote(args.sasl_user)} "
        f"-X pass={shlex.quote(args.sasl_password)} "
        f"-X sasl.mechanism={shlex.quote(args.sasl_mechanism)}"
    )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=args.host,
            port=args.port,
            username=args.ssh_user,
            password=args.ssh_password
        )

        stdin, stdout, stderr = ssh.exec_command(command)

        output = stdout.read().decode("utf-8")
        errors = stderr.read().decode("utf-8")

        if errors and not output:
            print(f"Error executing command: {errors}", file=sys.stderr)
            sys.exit(1)

        brokers, main_broker = parse_brokers(output)

        if not brokers:
            print("No brokers found in the cluster output.", file=sys.stderr)
            if errors:
                print(f"Stderr: {errors}", file=sys.stderr)
            sys.exit(1)

        print("=" * 50)
        print("BROKERS SUMMARY")
        print("=" * 50)
        for b in brokers:
            marker = " [MAIN / CONTROLLER *]" if b["is_main"] else ""
            print(f" - Broker ID: {b['id']:<3} | Host: {b['host']:<15} | Port: {b['port']}{marker}")

        if main_broker:
            print("\n[*] Main Broker Identified (marked with *):")
            print(f"    Broker ID : {main_broker['id']}")
            print(f"    Host      : {main_broker['host']}")
            print(f"    Port      : {main_broker['port']}")
        else:
            print("\n[!] No main broker marked with '*' found in output.")

    finally:
        ssh.close()


if __name__ == "__main__":
    main()


