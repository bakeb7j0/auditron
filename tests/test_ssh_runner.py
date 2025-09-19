"""Unit tests for SSH runner utilities."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from utils.ssh_runner import SSHClient, SSHResult


class TestSSHResult:
    """Test SSHResult class."""

    def test_ssh_result_init(self):
        """Test SSHResult initialization."""
        result = SSHResult(rc=0, out="success", err="")
        assert result.rc == 0
        assert result.out == "success"
        assert result.err == ""

    def test_ssh_result_with_error(self):
        """Test SSHResult with error."""
        result = SSHResult(rc=1, out="", err="command failed")
        assert result.rc == 1
        assert result.out == ""
        assert result.err == "command failed"


class TestSSHClient:
    """Test SSHClient class."""

    def test_ssh_client_init(self, sample_host):
        """Test SSHClient initialization."""
        client = SSHClient(sample_host)
        assert client.host == sample_host
        assert client.timeout == 60
        assert client._which_cache == {}

    def test_ssh_client_with_custom_timeout(self, sample_host):
        """Test SSHClient with custom timeout."""
        client = SSHClient(sample_host, timeout=30)
        assert client.timeout == 30

    @patch("utils.ssh_runner.subprocess.run")
    def test_which_command_available(self, mock_run, sample_host):
        """Test which() when command is available."""
        # Mock successful which command
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "/usr/bin/ls\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        result = client.which("ls")

        assert result is True
        assert client._which_cache["ls"] is True
        mock_run.assert_called_once()

    @patch("utils.ssh_runner.subprocess.run")
    def test_which_command_not_available(self, mock_run, sample_host):
        """Test which() when command is not available."""
        # Mock failed which command
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "command not found"
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        result = client.which("nonexistent")

        assert result is False
        assert client._which_cache["nonexistent"] is False

    def test_which_uses_cache(self, sample_host):
        """Test that which() uses cache on subsequent calls."""
        client = SSHClient(sample_host)
        client._which_cache["ls"] = True

        # Should return cached result without calling subprocess
        with patch("utils.ssh_runner.subprocess.run") as mock_run:
            result = client.which("ls")
            assert result is True
            mock_run.assert_not_called()

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_basic_command(self, mock_run, sample_host):
        """Test running a basic command."""
        # Mock successful command execution
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        result = client.run("ls -la")

        assert isinstance(result, SSHResult)
        assert result.rc == 0
        assert result.out == "command output"
        assert result.err == ""

        # Verify SSH command was constructed correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]  # First positional argument

        assert "ssh" in ssh_cmd
        assert "-o" in ssh_cmd
        assert "BatchMode=yes" in ssh_cmd
        assert "-p" in ssh_cmd
        assert "22" in ssh_cmd
        assert f"root@{sample_host['ip']}" in ssh_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_ssh_key(self, mock_run, sample_host):
        """Test running command with SSH key."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        client.run("uptime")

        # Verify SSH key was included
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        assert "-i" in ssh_cmd
        assert sample_host["ssh_key_path"] in ssh_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_sudo(self, mock_run, sample_host):
        """Test running command with sudo."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        client.run("cat /etc/shadow", use_sudo=True)

        # Verify sudo was used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        remote_cmd = ssh_cmd[-1]  # Last argument is the remote command
        assert "sudo -n bash -lc" in remote_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_without_sudo_when_disabled(self, mock_run, sample_host):
        """Test running command without sudo when explicitly disabled."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        client.run("whoami", use_sudo=False)

        # Verify sudo was not used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        remote_cmd = ssh_cmd[-1]
        assert "sudo" not in remote_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_custom_port(self, mock_run, sample_host):
        """Test running command with custom SSH port."""
        sample_host["ssh_port"] = 2222
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        client.run("date")

        # Verify custom port was used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        port_idx = ssh_cmd.index("-p") + 1
        assert ssh_cmd[port_idx] == "2222"

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_different_user(self, mock_run, sample_host):
        """Test running command with different SSH user."""
        sample_host["ssh_user"] = "admin"
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        client.run("whoami")

        # Verify correct user was used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        user_host = f"admin@{sample_host['ip']}"
        assert user_host in ssh_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_hostname_fallback(self, mock_run):
        """Test running command using hostname when IP is not set."""
        host_config = {
            "hostname": "test-server.example.com",
            "ip": None,
            "ssh_user": "root",
            "ssh_key_path": "/tmp/key",
            "ssh_port": 22,
            "use_sudo": 1,
        }

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(host_config)
        client.run("uptime")

        # Verify hostname was used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        assert "root@test-server.example.com" in ssh_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_command_failure(self, mock_run, sample_host):
        """Test handling command failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Permission denied"
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        result = client.run("cat /etc/shadow")

        assert result.rc == 1
        assert result.out == ""
        assert result.err == "Permission denied"

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_check_flag_success(self, mock_run, sample_host):
        """Test running command with check=True when command succeeds."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "success"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        result = client.run("ls", check=True)

        assert result.rc == 0
        assert result.out == "success"

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_with_check_flag_failure(self, mock_run, sample_host):
        """Test running command with check=True when command fails."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "command failed"
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)

        with pytest.raises(RuntimeError, match="SSH failed rc=1"):
            client.run("false", check=True)

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_timeout_handling(self, mock_run, sample_host):
        """Test handling of command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 30)

        client = SSHClient(sample_host, timeout=30)
        result = client.run("sleep 60")

        assert result.rc == 124  # Standard timeout exit code
        assert result.out == ""
        assert "timeout after 30s" in result.err

    @patch("utils.ssh_runner.subprocess.run")
    def test_run_without_ssh_key(self, mock_run):
        """Test running command without SSH key."""
        host_config = {
            "hostname": "test-host",
            "ip": "192.168.1.100",
            "ssh_user": "root",
            "ssh_key_path": None,
            "ssh_port": 22,
            "use_sudo": 1,
        }

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(host_config)
        client.run("whoami")

        # Verify no SSH key was used
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        assert "-i" not in ssh_cmd

    @patch("utils.ssh_runner.subprocess.run")
    def test_command_quoting(self, mock_run, sample_host):
        """Test that commands with special characters are properly quoted."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = SSHClient(sample_host)
        command_with_quotes = 'echo "hello world" && ls'
        client.run(command_with_quotes, use_sudo=True)

        # Verify command was properly quoted for sudo
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        remote_cmd = ssh_cmd[-1]
        # The command should be quoted when passed to sudo
        assert command_with_quotes in remote_cmd
