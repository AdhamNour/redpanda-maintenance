import shlex
import threading
from typing import Any, Callable, Dict, Optional, Tuple
import paramiko


class SSHClientManager:
    """Manages Paramiko SSH connections and command execution for Redpanda."""

    def __init__(self):
        self._client: Optional[paramiko.SSHClient] = None
        self._current_profile: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._is_executing = False

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    def connect(self, profile: Dict[str, Any]) -> Tuple[bool, str]:
        """Connects to remote host using profile configuration."""
        with self._lock:
            self.disconnect()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            host = profile.get("host", "")
            port = int(profile.get("port", 22))
            username = profile.get("ssh_user", "")
            auth_type = profile.get("ssh_auth_type", "password")

            try:
                if auth_type == "key" and profile.get("ssh_key_path"):
                    key_path = profile.get("ssh_key_path", "")
                    client.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        key_filename=key_path,
                        timeout=10
                    )
                else:
                    password = profile.get("ssh_password", "")
                    client.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        password=password,
                        timeout=10
                    )

                self._client = client
                self._current_profile = profile
                return True, "Connected successfully."
            except Exception as e:
                self._client = None
                self._current_profile = None
                return False, f"SSH Connection failed: {str(e)}"

    def disconnect(self) -> None:
        """Closes the active SSH connection."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._current_profile = None

    def get_sasl_flags(self, profile: Optional[Dict[str, Any]] = None) -> str:
        """Constructs SASL flags for rpk commands."""
        prof = profile or self._current_profile or {}
        sasl_user = prof.get("sasl_user", "")
        sasl_pass = prof.get("sasl_password", "")
        sasl_mech = prof.get("sasl_mechanism", "SCRAM-SHA-256")

        flags = []
        if sasl_user:
            flags.append(f"-X user={shlex.quote(sasl_user)}")
        if sasl_pass:
            flags.append(f"-X pass={shlex.quote(sasl_pass)}")
        if sasl_mech:
            flags.append(f"-X sasl.mechanism={shlex.quote(sasl_mech)}")

        return " ".join(flags)

    def execute_command(
        self,
        command: str,
        on_stdout_line: Optional[Callable[[str], None]] = None,
        on_stderr_line: Optional[Callable[[str], None]] = None,
        timeout: Optional[float] = None
    ) -> Tuple[int, str, str]:
        """
        Executes a command synchronously over SSH.
        Optionally streams stdout/stderr lines as they arrive.
        """
        if not self.is_connected or not self._client:
            return -1, "", "Not connected to any SSH host."

        try:
            self._is_executing = True
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)

            out_lines = []
            err_lines = []

            # Read stdout
            for line in stdout:
                out_lines.append(line)
                if on_stdout_line:
                    on_stdout_line(line.rstrip("\r\n"))

            # Read stderr
            for line in stderr:
                err_lines.append(line)
                if on_stderr_line:
                    on_stderr_line(line.rstrip("\r\n"))

            exit_status = stdout.channel.recv_exit_status()
            out_str = "".join(out_lines)
            err_str = "".join(err_lines)
            return exit_status, out_str, err_str

        except Exception as e:
            return -1, "", str(e)
        finally:
            self._is_executing = False

    def execute_async(
        self,
        command: str,
        on_complete: Callable[[int, str, str], None],
        on_stdout_line: Optional[Callable[[str], None]] = None,
        on_stderr_line: Optional[Callable[[str], None]] = None,
        timeout: Optional[float] = None
    ) -> threading.Thread:
        """Executes a command in a background thread and calls on_complete when finished."""
        def worker():
            exit_code, out, err = self.execute_command(
                command,
                on_stdout_line=on_stdout_line,
                on_stderr_line=on_stderr_line,
                timeout=timeout
            )
            on_complete(exit_code, out, err)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
