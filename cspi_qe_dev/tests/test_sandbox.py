import cspi_qe_dev.ref_sandbox.api as _api
from cspi_qe_dev.ref_sandbox.core import RefSandbox, MOCKED_SECRETS_DIR, MOCKED_VAULT_DIR
from pathlib import Path
import json
import pytest

MOCKED_VAULT_SECRET_NAMESPACE = "_test-credentials"
MOCKED_VAULT_SECRET_NAME = "test-cred-a"
MOCKED_VAULT_SECRET_TARGET_NAME = "xyz"
MOCKED_VAULT_SECRET_JSON_STR = json.dumps(
    {
        "my-secret": "abc123",
        "secretsync/target-name": MOCKED_VAULT_SECRET_TARGET_NAME,
        "secretsync/target-namespace": MOCKED_VAULT_SECRET_NAMESPACE,
    }
)


@pytest.fixture
def sb_from_firewatch(firewatch_ref_dir) -> RefSandbox:
    yield _api.get_ref_sandbox_from_path(firewatch_ref_dir)


@pytest.fixture
def mocked_vault_secret() -> Path:
    p = Path(MOCKED_VAULT_DIR) / MOCKED_VAULT_SECRET_NAME
    p.parent.mkdir(exist_ok=True, parents=True)
    p.write_text(MOCKED_VAULT_SECRET_JSON_STR)
    yield p
    p.unlink()
    ns = Path(MOCKED_SECRETS_DIR) / MOCKED_VAULT_SECRET_NAMESPACE
    tn = ns / MOCKED_VAULT_SECRET_TARGET_NAME
    for p in tn.rglob("./*"):
        if p.is_file():
            p.unlink()
    if tn.is_dir():
        tn.rmdir()
    if ns.is_dir():
        ns.rmdir()

@pytest.fixture
def sb(sb_from_firewatch, mocked_vault_secret) -> RefSandbox:
    yield sb_from_firewatch


def test_init_ref_sandbox_from_path(sb_from_firewatch):
    assert isinstance(
        sb_from_firewatch,
        RefSandbox,
    )


def test_get_firewatch_ref_image_from_ref_sandbox(sb_from_firewatch):
    exp = "registry.ci.openshift.org/cspi-qe/firewatch"
    actual = sb_from_firewatch.ref.image.pull_str
    assert actual.startswith(exp)


def test_build_sandbox_container_image(sb):
    assert not sb._built_image_hash
    sb.build(skip_secret_prompt=True)
    assert sb._built_image_hash


def test_run_sandbox_container(sb):
    sb.build(skip_secret_prompt=True)
    sb.run()


def test_get_mocked_vault_secret_entry(sb):
    exp = "abc123"
    actual = sb.mocked_vault_creds.get(MOCKED_VAULT_SECRET_NAME)["my-secret"]
    assert exp == actual


def test_get_mocked_secret_file(sb):
    exp = "abc123"
    actual = (sb.mocked_secret_paths["xyz"] / "my-secret").read_text()
    assert exp == actual
