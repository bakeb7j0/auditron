from utils.parsing import parse_rpm_verify


def test_parse_rpm_verify_basic():
    out = "SM5DLUGT. /etc/foo.conf\n..5...... /bin/bar\n"
    rows = parse_rpm_verify(out)
    assert rows[0][0].startswith("SM5DLUGT")
    assert rows[0][1] == "/etc/foo.conf"
