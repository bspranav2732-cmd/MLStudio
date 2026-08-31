"""
HPC Connection Abstraction
===========================
Provides an abstract base class for remote execution and file transfer,
along with a production SSH/SFTP implementation and an offline Mock implementation.
No university-specific credentials, hosts, or IPs are hardcoded.
"""

import os
import shutil
import tempfile
import subprocess
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any


class HPCConnection(ABC):
    """Abstract base interface for HPC connections."""

    @abstractmethod
    def connect(self, host: str, username: str, **kwargs) -> bool:
        """Establish connection to HPC cluster."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from HPC cluster."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is currently active."""
        pass

    @abstractmethod
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a shell command on the remote host.
        Returns: (exit_code, stdout, stderr)
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a local file to the remote host."""
        pass

    @abstractmethod
    def upload_dir(self, local_dir: str, remote_dir: str) -> None:
        """Upload a local directory to the remote host."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a remote file to the local host."""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> None:
        """Delete a remote file."""
        pass

    @abstractmethod
    def delete_dir(self, remote_dir: str) -> None:
        """Delete a remote directory."""
        pass

    @abstractmethod
    def get_home_dir(self) -> str:
        """Get the user's remote home directory."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get connection metadata."""
        pass

    def test_file_transfer(self) -> Dict[str, Any]:
        """
        Tests safe end-to-end file transfer (Upload -> Remote Verify -> Download -> Content Verify -> Cleanup).
        Operates ONLY inside a uniquely generated temporary directory in the user's home workspace.
        """
        import time
        import uuid

        if not self.is_connected():
            raise ConnectionError("Supercomputer is not connected.")

        unique_id = uuid.uuid4().hex[:8]
        test_dir_name = f"solvosys_hpc_test_{unique_id}"
        test_filename = f"solvosys_test_{unique_id}.txt"
        test_content = f"Solvosys HPC File Transfer Verification Token: {unique_id}\nTimestamp: {time.time()}\n"

        remote_home = self.get_home_dir()
        remote_test_dir = f"{remote_home.rstrip('/')}/{test_dir_name}"
        remote_test_file = f"{remote_test_dir}/{test_filename}"

        steps = {
            "upload": "pending",
            "remote_verify": "pending",
            "download": "pending",
            "content_verify": "pending",
            "cleanup": "pending"
        }

        with tempfile.TemporaryDirectory() as local_temp_dir:
            local_src_file = os.path.join(local_temp_dir, test_filename)
            local_dst_file = os.path.join(local_temp_dir, f"downloaded_{test_filename}")

            with open(local_src_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            try:
                # 1. Upload
                self.upload_file(local_src_file, remote_test_file)
                steps["upload"] = "OK"

                # 2. Remote verification
                exit_code, out, err = self.execute_command(f'test -f "{remote_test_file}" && wc -c "{remote_test_file}"')
                if exit_code != 0:
                    raise RuntimeError(f"Remote file verification failed with exit code {exit_code}: {err or out}")
                steps["remote_verify"] = "OK"

                # 3. Download
                self.download_file(remote_test_file, local_dst_file)
                if not os.path.exists(local_dst_file):
                    raise RuntimeError("Downloaded test file was not found locally.")
                steps["download"] = "OK"

                # 4. Content verification
                with open(local_dst_file, "r", encoding="utf-8") as f:
                    downloaded_content = f.read()

                if downloaded_content != test_content:
                    raise ValueError("Downloaded file content does not match the uploaded test payload.")
                steps["content_verify"] = "OK"

            finally:
                # 5. Targeted Cleanup: Delete ONLY the unique Solvosys test directory
                try:
                    self.delete_dir(remote_test_dir)
                    steps["cleanup"] = "OK"
                except Exception as e:
                    steps["cleanup"] = f"Warning: Cleanup failed for {remote_test_dir}: {str(e)}"

        return {
            "success": all(steps[k] == "OK" for k in ["upload", "remote_verify", "download", "content_verify", "cleanup"]),
            "steps": steps,
            "remote_test_dir": remote_test_dir,
            "message": "File transfer test successful" if steps["content_verify"] == "OK" else "File transfer test failed"
        }


class MockHPCConnection(HPCConnection):
    """
    Mock HPC Connection for local offline testing and development.
    Simulates a remote cluster filesystem and command execution inside a local scratch directory.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._connected = False
        self._host = "mock-dgx.local"
        self._username = "mock_user"
        self._workspace_root = workspace_root or os.path.join(tempfile.gettempdir(), "solvosys_mock_cluster")
        os.makedirs(self._workspace_root, exist_ok=True)

    def connect(self, host: str = "mock-dgx.local", username: str = "mock_user", **kwargs) -> bool:
        self._host = host or "mock-dgx.local"
        self._username = username or "mock_user"
        self._connected = True
        os.makedirs(self._workspace_root, exist_ok=True)
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_workspace_path(self, relative_path: str = "") -> str:
        """Resolve relative path to local mock workspace."""
        if os.path.isabs(relative_path):
            rel = os.path.relpath(relative_path, "/").replace(":", "")
            return os.path.join(self._workspace_root, rel)
        return os.path.join(self._workspace_root, relative_path)

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        if not self._connected:
            return 1, "", "Error: Not connected to HPC host."

        cmd = command.strip()
        if cmd in ('echo "$HOME"', 'echo $HOME'):
            return 0, f"/home/{self._username}\n", ""
        if cmd == "whoami":
            return 0, f"{self._username}\n", ""
        if cmd == "hostname":
            return 0, "mock-login01.local\n", ""
        if cmd.startswith("test -f "):
            path_part = cmd[len("test -f "):].strip().strip('"').strip("'")
            if "&&" in path_part:
                path_part = path_part.split("&&")[0].strip().strip('"').strip("'")
            target = self.get_workspace_path(path_part)
            if os.path.isfile(target):
                size = os.path.getsize(target)
                return 0, f"{size} {path_part}\n", ""
            return 1, "", f"File not found: {path_part}"
        if cmd.startswith("test -d "):
            path_part = cmd[len("test -d "):].strip().strip('"').strip("'")
            target = self.get_workspace_path(path_part)
            if os.path.isdir(target):
                return 0, "", ""
            return 1, "", f"Directory not found: {path_part}"
        if cmd.startswith("rm -rf "):
            path_part = cmd[len("rm -rf "):].strip().strip('"').strip("'")
            target = self.get_workspace_path(path_part)
            if os.path.exists(target):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
            return 0, "", ""

        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self._workspace_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return res.returncode, res.stdout, res.stderr
        except Exception as e:
            return 1, "", str(e)

    def upload_file(self, local_path: str, remote_path: str) -> None:
        if not self._connected:
            raise ConnectionError("Not connected to HPC.")
        target = self.get_workspace_path(remote_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(local_path, target)

    def upload_dir(self, local_dir: str, remote_dir: str) -> None:
        if not self._connected:
            raise ConnectionError("Not connected to HPC.")
        target = self.get_workspace_path(remote_dir)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(local_dir, target)

    def download_file(self, remote_path: str, local_path: str) -> None:
        if not self._connected:
            raise ConnectionError("Not connected to HPC.")
        source = self.get_workspace_path(remote_path)
        if not os.path.exists(source):
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        shutil.copy2(source, local_path)

    def delete_file(self, remote_path: str) -> None:
        if not self._connected:
            raise ConnectionError("Not connected to HPC.")
        target = self.get_workspace_path(remote_path)
        if os.path.exists(target):
            os.remove(target)

    def delete_dir(self, remote_dir: str) -> None:
        if not self._connected:
            raise ConnectionError("Not connected to HPC.")
        target = self.get_workspace_path(remote_dir)
        if os.path.exists(target):
            shutil.rmtree(target)

    def get_home_dir(self) -> str:
        return f"/home/{self._username}"

    def get_info(self) -> Dict[str, Any]:
        return {
            "mode": "mock",
            "connected": self._connected,
            "host": self._host,
            "username": self._username,
            "node": "mock-login01.local",
            "auth_type": "Mock Simulation",
            "workspace": self._workspace_root
        }


class SSHConnection(HPCConnection):
    """
    Production SSH/SFTP Connection for remote Supercomputer clusters.
    Uses user-supplied credentials/SSH keys. No credentials stored or hardcoded.
    """

    def __init__(self):
        self._connected = False
        self._host = None
        self._username = None
        self._client = None
        self._sftp = None
        self._node = None
        self._remote_user = None

    def connect(self, host: str, username: str, port: int = 22, key_filename: Optional[str] = None, **kwargs) -> bool:
        """
        Connect using SSH Key/Agent authentication with strict host key verification.
        Password authentication is strictly prohibited to keep user credentials secure.
        """
        if not host or not str(host).strip() or not username or not str(username).strip():
            raise ValueError("Host and username are required for SSH connection.")

        # Sanitize host, port, username
        host = str(host).strip()
        if host.startswith("ssh://"):
            host = host[6:]
        elif host.startswith("http://") or host.startswith("https://"):
            host = host.split("://", 1)[1]
        if "/" in host:
            host = host.split("/", 1)[0]
        if ":" in host and not host.startswith("["):
            parts = host.split(":")
            if len(parts) == 2 and parts[1].isdigit():
                host = parts[0]
                port = int(parts[1])

        username = str(username).strip()
        port = int(port) if port else 22

        # Explicitly reject any attempts to supply a password
        if "password" in kwargs:
            raise ValueError("Password authentication is disabled for security. Please use SSH keys or SSH agent.")

        try:
            import paramiko
            client = paramiko.SSHClient()
            
            # Strict host key policy - never auto-add unknown host keys
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            
            # Load user's standard known_hosts file and system host keys
            client.load_system_host_keys()
            known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
            if os.path.exists(known_hosts_path):
                client.load_host_keys(known_hosts_path)

            # Auto-discover local SSH private keys from ~/.ssh
            discovered_keys = []
            if key_filename and os.path.isfile(key_filename):
                discovered_keys.append(key_filename)
            else:
                ssh_dir = os.path.expanduser("~/.ssh")
                for kname in ["id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"]:
                    kp = os.path.join(ssh_dir, kname)
                    if os.path.isfile(kp):
                        discovered_keys.append(kp)

            if not discovered_keys:
                raise FileNotFoundError(
                    "No usable SSH key found in ~/.ssh (checked id_ed25519, id_rsa, id_ecdsa). "
                    "Please ensure your SSH key exists locally."
                )
            
            connect_kwargs = {
                "hostname": host,
                "username": username,
                "port": port,
                "timeout": 15,
                "allow_agent": False,
                "look_for_keys": False,
                "key_filename": discovered_keys,
            }
            if "passphrase" in kwargs and kwargs["passphrase"]:
                connect_kwargs["passphrase"] = kwargs["passphrase"]

            client.connect(**connect_kwargs)
            self._client = client
            self._sftp = client.open_sftp()
            self._host = host
            self._username = username
            self._connected = True

            # Harmless verification checks on login node only
            try:
                _, node_out, _ = self.execute_command("hostname")
                self._node = node_out.strip() if node_out else host
            except Exception:
                self._node = host

            try:
                _, who_out, _ = self.execute_command("whoami")
                self._remote_user = who_out.strip() if who_out else username
            except Exception:
                self._remote_user = username

            return True
        except ImportError:
            raise RuntimeError("paramiko is required for SSH connections. Please install paramiko or use Mock mode.")
        except paramiko.ssh_exception.PasswordRequiredException:
            self._connected = False
            raise ConnectionError(
                "The local SSH private key is encrypted with a passphrase. Please enter your SSH key passphrase."
            )
        except paramiko.ssh_exception.AuthenticationException as e:
            self._connected = False
            raise ConnectionError(
                f"SSH key authentication rejected by {host} for user '{username}'. "
                f"Please ensure your public key (e.g. ~/.ssh/id_ed25519.pub) is present in the remote ~/.ssh/authorized_keys."
            )
        except paramiko.ssh_exception.BadHostKeyException:
            self._connected = False
            raise ConnectionError(
                f"Host key verification failed: The host key for {host} does not match the cached key in ~/.ssh/known_hosts."
            )
        except paramiko.ssh_exception.SSHException as e:
            self._connected = False
            err_str = str(e).lower()
            if "encrypted" in err_str or "password required" in err_str:
                raise ConnectionError(
                    "The local SSH private key is encrypted with a passphrase. Please enter your SSH key passphrase."
                )
            elif "invalid key" in err_str or "bad passphrase" in err_str or "passphrase" in err_str:
                raise ConnectionError("SSH key passphrase is incorrect.")
            elif "not found in known_hosts" in err_str or "server" in err_str:
                raise ConnectionError(
                    f"Host key verification failed for {host}. The host key is not in your ~/.ssh/known_hosts file. "
                    f"Please connect once via PowerShell ('ssh {username}@{host}') to verify and record the host key."
                )
            raise ConnectionError(f"SSH connection error: {str(e)}")
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"SSH connection failed to {username}@{host}: {str(e)}")

    def disconnect(self) -> None:
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._connected = False

    def is_connected(self) -> bool:
        if not self._connected or not self._client:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        if not self.is_connected():
            return 1, "", "Error: SSH connection is not active."
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=60)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return exit_code, out, err
        except Exception as e:
            return 1, "", str(e)

    def upload_file(self, local_path: str, remote_path: str) -> None:
        if not self.is_connected() or not self._sftp:
            raise ConnectionError("SSH/SFTP connection is not active.")
        remote_dir = os.path.dirname(remote_path).replace("\\", "/")
        self._ensure_remote_dir(remote_dir)
        self._sftp.put(local_path, remote_path.replace("\\", "/"))

    def upload_dir(self, local_dir: str, remote_dir: str) -> None:
        if not self.is_connected() or not self._sftp:
            raise ConnectionError("SSH/SFTP connection is not active.")
        remote_dir = remote_dir.replace("\\", "/")
        self._ensure_remote_dir(remote_dir)
        for root, _, files in os.walk(local_dir):
            rel = os.path.relpath(root, local_dir).replace("\\", "/")
            curr_remote = remote_dir if rel == "." else f"{remote_dir}/{rel}"
            self._ensure_remote_dir(curr_remote)
            for f in files:
                l_file = os.path.join(root, f)
                r_file = f"{curr_remote}/{f}"
                self._sftp.put(l_file, r_file)

    def download_file(self, remote_path: str, local_path: str) -> None:
        if not self.is_connected() or not self._sftp:
            raise ConnectionError("SSH/SFTP connection is not active.")
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        self._sftp.get(remote_path.replace("\\", "/"), local_path)

    def delete_file(self, remote_path: str) -> None:
        if not self.is_connected() or not self._sftp:
            raise ConnectionError("SSH/SFTP connection is not active.")
        normalized = remote_path.replace("\\", "/")
        try:
            self._sftp.remove(normalized)
        except Exception:
            self.execute_command(f'rm -f "{normalized}"')

    def delete_dir(self, remote_dir: str) -> None:
        """
        Deletes a temporary directory on the remote host.
        STRICT SAFETY: Only allows deleting directories containing 'solvosys_hpc_test_' or 'solvosys_hpc_slurm_test_'.
        """
        if not self.is_connected():
            raise ConnectionError("SSH connection is not active.")

        normalized = remote_dir.replace("\\", "/").rstrip("/")
        # Strict safety check: only delete Solvosys-created test directories
        if (
            "solvosys_hpc_test_" not in normalized
            and "solvosys_hpc_slurm_test_" not in normalized
            and "solvosys_hpc_env_test_" not in normalized
            and "solvosys_hpc_exp_" not in normalized
        ):
            raise ValueError(f"Refusing to delete non-test directory: {remote_dir}")

        code, out, err = self.execute_command(f'rm -rf "{normalized}"')
        if code != 0:
            raise RuntimeError(f"Failed to delete {remote_dir}: {err or out}")

    def get_home_dir(self) -> str:
        """
        Dynamically discover the user's remote home directory from the active session.
        Never assumes or hardcodes university paths.
        """
        if not self.is_connected():
            return f"/home/{self._username}"
        exit_code, out, _ = self.execute_command('echo "$HOME"')
        if exit_code == 0 and out.strip():
            return out.strip().replace("\\", "/")
        return f"/home/{self._username}"

    def _ensure_remote_dir(self, remote_dir: str) -> None:
        if not remote_dir or remote_dir == ".":
            return
        parts = remote_dir.strip("/").split("/")
        path = "" if not remote_dir.startswith("/") else "/"
        for part in parts:
            path = f"{path}/{part}" if path and not path.endswith("/") else f"{path}{part}"
            try:
                self._sftp.stat(path)
            except Exception:
                try:
                    self._sftp.mkdir(path)
                except Exception:
                    pass

    def get_info(self) -> Dict[str, Any]:
        return {
            "mode": "ssh",
            "connected": self.is_connected(),
            "host": self._host,
            "username": self._remote_user or self._username,
            "node": self._node or self._host,
            "auth_type": "SSH Key"
        }
