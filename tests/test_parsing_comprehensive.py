"""Comprehensive unit tests for parsing utilities."""

from utils.parsing import parse_rpm_verify, parse_ss_listen


class TestRpmVerifyParsing:
    """Test RPM verify output parsing."""

    def test_parse_rpm_verify_basic(self):
        """Test basic RPM verify parsing."""
        out = "SM5DLUGT. /etc/foo.conf\n..5...... /bin/bar\n"
        rows = parse_rpm_verify(out)
        assert len(rows) == 2
        assert isinstance(rows[0], tuple)
        assert rows[0][0] == "SM5DLUGT."
        assert rows[0][1] == "/etc/foo.conf"
        assert rows[1][0] == "..5......"
        assert rows[1][1] == "/bin/bar"

    def test_parse_rpm_verify_with_config_files(self, rpm_verify_output):
        """Test parsing RPM verify output with config file markers."""
        rows = parse_rpm_verify(rpm_verify_output)
        assert len(rows) == 4

        # Config file should have 'c' marker stripped
        config_row = next(row for row in rows if "/etc/ssh/sshd_config" in row[1])
        assert config_row[0] == "SM5DLUGT."
        assert config_row[1] == "/etc/ssh/sshd_config"

    def test_parse_rpm_verify_with_directory_files(self):
        """Test parsing RPM verify output with directory markers."""
        out = "SM5DLUGT. d /var/log\n..5...... d /tmp/test\n"
        rows = parse_rpm_verify(out)
        assert len(rows) == 2
        assert rows[0][1] == "/var/log"
        assert rows[1][1] == "/tmp/test"

    def test_parse_rpm_verify_empty_output(self):
        """Test parsing empty RPM verify output."""
        rows = parse_rpm_verify("")
        assert rows == []

    def test_parse_rpm_verify_whitespace_lines(self):
        """Test parsing RPM verify output with whitespace."""
        out = "SM5DLUGT. /etc/file1\n\n   \n..5...... /bin/file2\n"
        rows = parse_rpm_verify(out)
        assert len(rows) == 2
        assert rows[0][1] == "/etc/file1"
        assert rows[1][1] == "/bin/file2"

    def test_parse_rpm_verify_malformed_lines(self):
        """Test parsing RPM verify output with malformed lines."""
        out = "SM5DLUGT.\n..5...... /bin/valid\nmalformed_line"
        rows = parse_rpm_verify(out)
        assert len(rows) == 1  # Only valid line should be parsed
        assert rows[0][1] == "/bin/valid"

    def test_parse_rpm_verify_special_characters_in_paths(self):
        """Test parsing paths with special characters."""
        out = "SM5DLUGT. /path/with spaces/file\n..5...... /path/with-dashes_and.dots\n"
        rows = parse_rpm_verify(out)
        assert len(rows) == 2
        assert rows[0][1] == "/path/with spaces/file"
        assert rows[1][1] == "/path/with-dashes_and.dots"


class TestSsListenParsing:
    """Test ss listen output parsing."""

    def test_parse_ss_listen_basic(self):
        """Test basic ss listen parsing."""
        line = 'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=123,fd=3))'
        result = parse_ss_listen(line)

        assert result is not None
        proto, local, state, pid, proc = result
        assert proto == "tcp"
        assert local == "0.0.0.0:22"
        assert state == "LISTEN"
        assert pid == 123
        assert proc == "sshd"

    def test_parse_ss_listen_with_multiple_processes(self):
        """Test parsing ss output with multiple processes."""
        line = 'tcp LISTEN 0 80 0.0.0.0:80 0.0.0.0:* users:(("httpd",pid=5678,fd=4),("httpd",pid=5679,fd=4))'
        result = parse_ss_listen(line)

        assert result is not None
        proto, local, state, pid, proc = result
        assert proto == "tcp"
        assert local == "0.0.0.0:80"
        assert state == "LISTEN"
        assert pid == 5678  # Should get first PID
        assert proc == "httpd"

    def test_parse_ss_listen_udp_socket(self):
        """Test parsing UDP socket."""
        line = 'udp UNCONN 0 0 0.0.0.0:53 0.0.0.0:* users:(("systemd-resolve",pid=9012,fd=12))'
        result = parse_ss_listen(line)

        assert result is not None
        proto, local, state, pid, proc = result
        assert proto == "udp"
        assert local == "0.0.0.0:53"
        assert state == "UNCONN"
        assert pid == 9012
        assert proc == "systemd-resolve"

    def test_parse_ss_listen_ipv6_socket(self):
        """Test parsing IPv6 socket."""
        line = 'tcp LISTEN 0 128 [::]:22 [::]:* users:(("sshd",pid=1234,fd=4))'
        result = parse_ss_listen(line)

        assert result is not None
        proto, local, state, pid, proc = result
        assert proto == "tcp"
        assert local == "[::]:22"
        assert state == "LISTEN"
        assert pid == 1234
        assert proc == "sshd"

    def test_parse_ss_listen_no_process_info(self):
        """Test parsing ss output without process information."""
        line = "tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*"
        result = parse_ss_listen(line)

        assert result is not None
        proto, local, state, pid, proc = result
        assert proto == "tcp"
        assert local == "0.0.0.0:22"
        assert state == "LISTEN"
        assert pid is None
        assert proc is None

    def test_parse_ss_listen_empty_line(self):
        """Test parsing empty line."""
        result = parse_ss_listen("")
        assert result is None

    def test_parse_ss_listen_malformed_line(self):
        """Test parsing malformed line gracefully."""
        parse_ss_listen("not a valid ss line")
        # Should handle gracefully and not crash
        # Result may be None or have default values - implementation dependent

    def test_parse_ss_listen_with_full_output(self, ss_listen_output):
        """Test parsing multiple lines of ss output."""
        lines = ss_listen_output.strip().split("\n")
        results = []
        for line in lines:
            result = parse_ss_listen(line)
            if result:
                results.append(result)

        assert len(results) == 4

        # Check SSH entries (both IPv4 and IPv6)
        ssh_results = [r for r in results if r[4] == "sshd"]
        assert len(ssh_results) == 2

        # Check HTTP entry
        http_results = [r for r in results if r[4] == "httpd"]
        assert len(http_results) == 1
        assert http_results[0][1] == "0.0.0.0:80"

        # Check systemd-resolve entry
        resolve_results = [r for r in results if r[4] == "systemd-resolve"]
        assert len(resolve_results) == 1
        assert resolve_results[0][0] == "udp"
        assert resolve_results[0][2] == "UNCONN"
