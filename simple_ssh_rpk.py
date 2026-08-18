#!/usr/bin/env python3
import re
import paramiko

# Configuration
HOST = "10.109.116.20"       # Replace with your server IP / hostname
PORT = 22
USERNAME = "anhassan"   # Replace with your SSH username
PASSWORD = "TRqRZnDhj111af00YR55"   # Replace with your SSH password
COMMAND = "rpk cluster info -X user=EjadaDataManagment -X pass='ecgtZSdmR@B8!GgT' -X sasl.mechanism=SCRAM-SHA-256"


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
    # Initialize SSH Client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {USERNAME}@{HOST}...")
        ssh.connect(
            hostname=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD
        )

        print(f"Running command: {COMMAND}")
        stdin, stdout, stderr = ssh.exec_command(COMMAND)

        # Fetch and display output
        output = stdout.read().decode()
        errors = stderr.read().decode()

        if output:
            print("\n--- Output ---")
            print(output)

            # Parse and display broker information
            brokers, main_broker = parse_brokers(output)

            print("\n" + "=" * 50)
            print("PARSED BROKERS SUMMARY")
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

        if errors:
            print("\n--- Errors ---")
            print(errors)

    finally:
        ssh.close()


if __name__ == "__main__":
    main()

