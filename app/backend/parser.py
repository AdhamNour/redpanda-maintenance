import re
from typing import Any, Dict, List, Optional, Tuple


def parse_brokers(output: str) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Parses the BROKERS section from Redpanda `rpk cluster info` output.

    Returns:
        tuple: (list of broker dicts, main/controller broker dict or None)
    """
    brokers = []
    main_broker = None

    if not output:
        return brokers, main_broker

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

                broker_info: Dict[str, Any] = {
                    "id": broker_id,
                    "host": host,
                    "port": port,
                    "is_main": is_main,
                    "raw_id": raw_id,
                    "rack": parts[3] if len(parts) > 3 else "N/A",
                    "maintenance_state": "ACTIVE", # Will be updated with maintenance status
                    "draining": False,
                    "finished": False,
                }

                brokers.append(broker_info)
                if is_main:
                    main_broker = broker_info

    return brokers, main_broker


def parse_maintenance_status(output: str) -> List[Dict[str, Any]]:
    """
    Parses the output of `rpk cluster maintenance status`.
    Actual rpk columns: NODE-ID  ENABLED  FINISHED  ERRORS  PARTITIONS  ELIGIBLE  TRANSFERRING  FAILED

    Interpretation:
      - enabled=true,  finished=true   → node has finished draining, fully IN MAINTENANCE
      - enabled=true,  finished=false  → node is actively DRAINING partitions
      - enabled=false                  → node is ACTIVE (not in maintenance)
    """
    results = []
    if not output:
        return results

    lines = output.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.upper().startswith("NODE") or line.startswith("=") or line.startswith("-"):
            continue

        parts = line.split()
        if len(parts) >= 2:
            try:
                node_id = int(parts[0])
            except ValueError:
                continue

            enabled_str = parts[1].lower() if len(parts) > 1 else "false"
            finished_str = parts[2].lower() if len(parts) > 2 else "false"
            errors_str = parts[3] if len(parts) > 3 else "none"

            enabled = enabled_str in ("true", "yes", "1")
            finished = finished_str in ("true", "yes", "1")

            # finished=true means draining completed → node is fully IN MAINTENANCE
            # enabled=true, finished=false means still redistributing partitions
            if enabled and finished:
                status_label = "IN MAINTENANCE"
            elif enabled and not finished:
                status_label = "DRAINING"
            else:
                status_label = "ACTIVE"

            results.append({
                "node_id": node_id,
                "enabled": enabled,
                "draining": enabled and not finished,
                "finished": finished,
                "status": status_label,
                "errors": errors_str,
            })

    return results


def parse_cluster_health(output: str) -> Dict[str, Any]:
    """
    Parses the output of `rpk cluster health`.
    Extracts healthy status, under-replicated partitions, leaderless partitions, etc.
    """
    health_info: Dict[str, Any] = {
        "is_healthy": True,
        "status_text": "HEALTHY",
        "under_replicated_partitions": 0,
        "leaderless_partitions": 0,
        "offline_partitions": 0,
        "all_nodes_healthy": True,
        "raw_output": output or ""
    }

    if not output:
        return health_info

    # Search for common patterns in rpk cluster health output
    if re.search(r'Cluster health\s*:\s*(\w+)', output, re.IGNORECASE):
        match = re.search(r'Cluster health\s*:\s*(\w+)', output, re.IGNORECASE)
        status = match.group(1).upper() if match else "HEALTHY"
        health_info["status_text"] = status
        health_info["is_healthy"] = (status == "HEALTHY" or status == "OK")

    # Under-replicated partitions
    urp_match = re.search(r'Under-replicated partitions\s*:\s*(\d+)', output, re.IGNORECASE)
    if urp_match:
        val = int(urp_match.group(1))
        health_info["under_replicated_partitions"] = val
        if val > 0:
            health_info["is_healthy"] = False
            health_info["status_text"] = "DEGRADED"

    # Leaderless partitions
    leaderless_match = re.search(r'Leaderless partitions\s*:\s*(\d+)', output, re.IGNORECASE)
    if leaderless_match:
        val = int(leaderless_match.group(1))
        health_info["leaderless_partitions"] = val
        if val > 0:
            health_info["is_healthy"] = False
            health_info["status_text"] = "DEGRADED"

    # Offline partitions
    offline_match = re.search(r'Offline partitions\s*:\s*(\d+)', output, re.IGNORECASE)
    if offline_match:
        val = int(offline_match.group(1))
        health_info["offline_partitions"] = val
        if val > 0:
            health_info["is_healthy"] = False
            health_info["status_text"] = "CRITICAL"

    return health_info
