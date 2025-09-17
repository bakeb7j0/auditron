from utils.parsing import parse_rpm_verify, parse_ss_listen

def test_parse_rpm_verify_basic():
    out = "SM5DLUGT. /etc/foo.conf\n..5...... /bin/bar\n"
    rows = parse_rpm_verify(out)
    assert rows[0][0].startswith("SM5DLUGT")
    assert rows[0][1] == "/etc/foo.conf"

def test_parse_ss_listen_basic():
    line = 'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:((\\"sshd\\",pid=123,fd=3))'
    tup = parse_ss_listen(line)
    assert tup[0] == 'tcp'
    assert ':22' in tup[1]
