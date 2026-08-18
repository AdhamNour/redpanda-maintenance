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


def display_brokers(brokers):
    print("\n" + "=" * 50)
    print("BROKERS SUMMARY")
    print("=" * 50)
    if not brokers:
        print("No brokers available.")
        return
    for b in brokers:
        marker = " [MAIN / CONTROLLER *]" if b["is_main"] else ""
        print(f" - Broker ID: {b['id']:<3} | Host: {b['host']:<15} | Port: {b['port']}{marker}")


def display_main_broker(main_broker):
    print("\n" + "=" * 50)
    print("MAIN NODE (CONTROLLER)")
    print("=" * 50)
    if main_broker:
        print(f" - Broker ID : {main_broker['id']}")
        print(f" - Host      : {main_broker['host']}")
        print(f" - Port      : {main_broker['port']}")
        if "rack" in main_broker:
            print(f" - Rack      : {main_broker['rack']}")
    else:
        print("[!] No main broker marked with '*' found.")


def handle_enable_maintenance(ssh, sasl_flags, brokers):
    print("\n" + "=" * 50)
    print("ENABLE MAINTENANCE MODE")
    print("=" * 50)
    print("Description: Places a broker into maintenance mode and waits (--wait)")
    print("until partition leader transfers and draining are complete.")
    print("-" * 50)

    if brokers:
        valid_ids = [str(b['id']) for b in brokers]
        print(f"Available Broker IDs: {', '.join(valid_ids)}")

    try:
        node_id_input = input("Enter Node ID to enable maintenance for (or 'c' to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    if not node_id_input or node_id_input.lower() in ("c", "cancel"):
        print("Operation cancelled.")
        return

    try:
        node_id = int(node_id_input)
    except ValueError:
        print(f"[!] Invalid Node ID: '{node_id_input}'. Must be an integer.", file=sys.stderr)
        return

    cmd = f"rpk cluster maintenance enable {node_id} --wait {sasl_flags}"
    print(f"\n[*] Executing: rpk cluster maintenance enable {node_id} --wait ...")
    print("[*] Waiting for broker to safely enter maintenance mode...")

    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8")
    err = stderr.read().decode("utf-8")

    if out:
        print(out.strip())
    if err:
        print(f"Stderr: {err}", file=sys.stderr)


def handle_disable_maintenance(ssh, sasl_flags, brokers):
    print("\n" + "=" * 50)
    print("DISABLE MAINTENANCE MODE")
    print("=" * 50)
    print("Description: Takes a broker out of maintenance mode, returning it")
    print("to active cluster participation.")
    print("-" * 50)

    if brokers:
        valid_ids = [str(b['id']) for b in brokers]
        print(f"Available Broker IDs: {', '.join(valid_ids)}")

    try:
        node_id_input = input("Enter Node ID to disable maintenance for (or 'c' to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    if not node_id_input or node_id_input.lower() in ("c", "cancel"):
        print("Operation cancelled.")
        return

    try:
        node_id = int(node_id_input)
    except ValueError:
        print(f"[!] Invalid Node ID: '{node_id_input}'. Must be an integer.", file=sys.stderr)
        return

    cmd = f"rpk cluster maintenance disable {node_id} {sasl_flags}"
    print(f"\n[*] Executing: rpk cluster maintenance disable {node_id} ...")

    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8")
    err = stderr.read().decode("utf-8")

    if out:
        print(out.strip())
    if err:
        print(f"Stderr: {err}", file=sys.stderr)


def interactive_menu(ssh, sasl_flags, brokers, main_broker):
    info_command = f"rpk cluster info {sasl_flags}"
    health_command = f"rpk cluster health {sasl_flags}"
    maint_command = f"rpk cluster maintenance status {sasl_flags}"

    while True:
        print("\n" + "=" * 50)
        print("COMMAND MENU")
        print("=" * 50)
        print(" [1] List all brokers")
        print(" [2] Identify main node (controller)")
        print(" [3] Get cluster health (rpk cluster health)")
        print(" [4] Check cluster maintenance status (rpk cluster maintenance status)")
        print(" [5] Enable maintenance mode on a node (rpk cluster maintenance enable <NODE_ID> --wait)")
        print(" [6] Disable maintenance mode on a node (rpk cluster maintenance disable <NODE_ID>)")
        print(" [7] Refresh cluster data")
        print(" [8] Exit")
        print("-" * 50)

        try:
            choice = input("Select a command [1-8]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if choice == "1":
            display_brokers(brokers)
        elif choice == "2":
            display_main_broker(main_broker)
        elif choice == "3":
            print("\n" + "=" * 50)
            print("CLUSTER HEALTH")
            print("=" * 50)
            stdin, stdout, stderr = ssh.exec_command(health_command)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            if out:
                print(out.strip())
            elif err:
                print(f"Error executing 'rpk cluster health': {err}", file=sys.stderr)
        elif choice == "4":
            print("\n" + "=" * 50)
            print("CLUSTER MAINTENANCE STATUS")
            print("=" * 50)
            stdin, stdout, stderr = ssh.exec_command(maint_command)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            if out:
                print(out.strip())
            elif err:
                print(f"Error executing 'rpk cluster maintenance status': {err}", file=sys.stderr)
        elif choice == "5":
            handle_enable_maintenance(ssh, sasl_flags, brokers)
        elif choice == "6":
            handle_disable_maintenance(ssh, sasl_flags, brokers)
        elif choice == "7":
            print("\nRefreshing cluster data...")
            stdin, stdout, stderr = ssh.exec_command(info_command)
            out = stdout.read().decode("utf-8")
            err = stderr.read().decode("utf-8")
            new_brokers, new_main = parse_brokers(out)
            if new_brokers:
                brokers, main_broker = new_brokers, new_main
                print(f"[+] Successfully refreshed. Found {len(brokers)} broker(s).")
                display_brokers(brokers)
            else:
                print("[-] Failed to refresh broker list.", file=sys.stderr)
                if err:
                    print(f"Stderr: {err}", file=sys.stderr)
        elif choice in ("8", "exit", "quit", "q"):
            print("Exiting...")
            break
        else:
            print("[!] Invalid option. Please enter a number between 1 and 8.")



def main():
    args = parse_arguments()

    # SASL flags for rpk commands
    sasl_flags = (
        f"-X user={shlex.quote(args.sasl_user)} "
        f"-X pass={shlex.quote(args.sasl_password)} "
        f"-X sasl.mechanism={shlex.quote(args.sasl_mechanism)}"
    )

    info_command = f"rpk cluster info {sasl_flags}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {args.ssh_user}@{args.host}:{args.port}...")
        ssh.connect(
            hostname=args.host,
            port=args.port,
            username=args.ssh_user,
            password=args.ssh_password
        )
        print("[+] Connected successfully.")

        # Initial fetch of cluster info (Brokers)
        stdin, stdout, stderr = ssh.exec_command(info_command)
        info_output = stdout.read().decode("utf-8")
        info_errors = stderr.read().decode("utf-8")

        if info_errors and not info_output:
            print(f"Error executing 'rpk cluster info': {info_errors}", file=sys.stderr)
            sys.exit(1)

        brokers, main_broker = parse_brokers(info_output)

        if not brokers:
            print("No brokers found in the cluster output.", file=sys.stderr)
            if info_errors:
                print(f"Stderr: {info_errors}", file=sys.stderr)
            sys.exit(1)

        # Show initial broker summary & main broker
        display_brokers(brokers)
        display_main_broker(main_broker)

        # Launch interactive menu loop
        interactive_menu(ssh, sasl_flags, brokers, main_broker)

    finally:
        ssh.close()


if __name__ == "__main__":
    main()

