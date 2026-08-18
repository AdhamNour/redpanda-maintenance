#!/usr/bin/env python3
import paramiko

# Configuration
HOST = "10.109.116.20"       # Replace with your server IP / hostname
PORT = 22
USERNAME = "anhassan"   # Replace with your SSH username
PASSWORD = "TRqRZnDhj111af00YR55"   # Replace with your SSH password
COMMAND = "rpk cluster info -X user=EjadaDataManagment -X pass='ecgtZSdmR@B8!GgT' -X sasl.mechanism=SCRAM-SHA-256"

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

        if errors:
            print("\n--- Errors ---")
            print(errors)

    finally:
        ssh.close()

if __name__ == "__main__":
    main()
