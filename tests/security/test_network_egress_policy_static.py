from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_egress_policy_scripts_exist():
    assert Path("infra/security/apply-egress-policy.sh").exists()
    assert Path("infra/security/remove-egress-policy.sh").exists()
    assert Path("infra/security/egress-policy.env.example").exists()


def test_egress_policy_uses_docker_user_chain():
    text = read("infra/security/apply-egress-policy.sh")

    assert "DOCKER-USER" in text
    assert "VATRANSCRIBE-EGRESS" in text
    assert "iptables -N" in text
    assert "iptables -I" in text or "insert_once DOCKER-USER" in text


def test_egress_policy_blocks_private_and_metadata_ranges():
    text = read("infra/security/apply-egress-policy.sh")

    for cidr in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "169.254.169.254/32",
    ):
        assert cidr in text


def test_egress_policy_allows_only_required_internal_dependencies():
    text = read("infra/security/apply-egress-policy.sh")

    assert "--dport 5432" in text
    assert "--dport 6379" in text
    assert "--dports 80,443" in text
    assert "VATRANSCRIBE_EGRESS_STRICT" in text


def test_egress_policy_remove_script_cleans_chain():
    text = read("infra/security/remove-egress-policy.sh")

    assert "DOCKER-USER" in text
    assert "iptables -D" in text
    assert "iptables -F" in text
    assert "iptables -X" in text


def test_egress_policy_readme_documents_ipv6_gap():
    text = read("infra/security/README-egress-policy.md")

    assert "IPv6" in text
    assert "ip6tables" in text or "nftables" in text
    assert "169.254.169.254" in text
