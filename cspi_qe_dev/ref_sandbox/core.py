from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from cspi_qe_dev.ci_operator.api import (
    CiOperatorApi,
    OpenshiftReleaseSource,
    Ref,
    RefNotFoundError,
)
from cspi_qe_dev.ci_operator.enum import ImageSourceType

import random
import os
import subprocess as sp
import uuid
import json
import click

OPENSHIFT_CI_OP_DIR_NAME = "ci-operator"
BUILD_DIR = "/tmp/sandbox"
CONFIG_DIR = os.getenv("HOME", "~") + "/.ref-ref_sandbox"

MOCKED_VAULT_DIR = CONFIG_DIR + "/mocked-vault"
MOCKED_SECRETS_DIR = CONFIG_DIR + "/secrets"
SECRETSYNC_TARGET_NAME = "secretsync/target-name"
SECRETSYNC_TARGET_NAMESPACE = "secretsync/target-namespace"

UID_MIN = 10_000
UID_MAX = 10_100

BUILD_ID_START = 9_900_000_000_000_000_000
BUILD_ID_END = 9_990_000_000_000_000_000
BUILD_ID = f"{random.randint(BUILD_ID_START, BUILD_ID_END)}"

NAMESPACE = f"ci-op-{str(uuid.uuid4())[:8]}"

LATEST_CLI_IST = "registry.ci.openshift.org/ocp/4.14:cli"
INJECT_OC_CMD = f"COPY --from={LATEST_CLI_IST} /usr/bin/oc /usr/bin/oc"

GLOBAL_ENV = {
    "KUBECONFIG": "/var/run/secrets/ci.openshift.io/multi-stage/kubeconfig",
    "KUBECONFIGMINIMAL": "/var/run/secrets/ci.openshift.io/multi-stage/kubeconfig-minimal",
    "KUBEADMIN_PASSWORD_FILE": "/var/run/secrets/ci.openshift.io/multi-stage/kubeadmin-password",
    "CLUSTER_PROFILE_DIR": "/var/run/secrets/ci.openshift.io/cluster-profile",
    "SHARED_DIR": "/var/run/secrets/ci.openshift.io/multi-stage",
    "ARTIFACT_DIR": "/logs/artifacts",
    "NAMESPACE": NAMESPACE,
    "BUILD_ID": BUILD_ID,
}

GLOBAL_VOLUME_MOUNTS = {
    "logs": "/logs",
    "tools": "/tools",
    "home": "/alabama",
    "cluster-profile": "/var/run/secrets/ci.openshift.io/cluster-profile",
    "shared_dir": GLOBAL_ENV["SHARED_DIR"],
    "artifact_dir": GLOBAL_ENV["ARTIFACT_DIR"],
}


@dataclass
class RefSandbox:
    ref_dir: Path
    _ci_op = CiOperatorApi
    _ref: Ref = None
    _built_image_hash = None
    _build_dir: Path = None
    _ref_base_image: str = None
    _container_uid: int = None
    _copy_src_dst: Iterator[Iterator[str]] = None
    _volume_mounts: dict = None
    _build_env: dict = None
    _credential_mounts: list = None
    _mocked_vault_dir: Path = None
    _mocked_vault_creds: dict = None
    _mocked_secret_paths: dict = None
    _mocked_secrets_dir: Path = None

    def __post_init__(self):
        for p in self.ref_dir.parents:
            if p.parent.name == OPENSHIFT_CI_OP_DIR_NAME:
                self._ci_op = CiOperatorApi(OpenshiftReleaseSource(p.parent.parent))
        if not self._copy_src_dst:
            self._copy_src_dst = []
        if not self._credential_mounts:
            self._credential_mounts = []

    @property
    def ref(self):
        if not self._ref:
            r = self.ref_dir.glob("*-ref.yaml")
            try:
                r = next(r)
            except StopIteration:
                raise RefNotFoundError(f'No ref found at "{self.ref_dir.absolute()}"')
            self._ref = Ref(r)
        return self._ref

    @property
    def ref_base_image(self):
        if not self._ref_base_image:
            img = self.ref.image
            if img.source_type == ImageSourceType.IMAGE_STREAM_TAG:
                self._ref_base_image = self.ref.image.pull_str
            else:
                local_img_name = "localhost/" + img.name
                res = sp.run(
                    [
                        "podman",
                        "images",
                        "--format={{.Repository}}",
                        "--noheading",
                        f"{local_img_name}",
                    ],
                    capture_output=True,
                )
                res = res.stdout.decode().split()
                if local_img_name in res:
                    self._ref_base_image = local_img_name
                else:
                    raise LookupError(f'unable to find local image: "{local_img_name}"')
        return self._ref_base_image

    @property
    def container_uid(self):
        if not self._container_uid:
            self._container_uid = random.randint(UID_MIN, UID_MAX)
        return self._container_uid

    @property
    def copy_cmd(self):
        res = ""
        for src, dst in self._copy_src_dst:
            src = Path(src)
            (self.build_dir / src.name).write_bytes(src.read_bytes())
            res += f"COPY --chown={self.container_uid}:0 --chmod=555 {src.name} {dst}\n"
        return res

    @property
    def credential_mounts(self):
        if not self._credential_mounts:
            self._credential_mounts = self.ref.credentials
        return self._credential_mounts

    @property
    def volume_mounts(self):
        if not self._volume_mounts:
            d = {}
            d.update(GLOBAL_VOLUME_MOUNTS)
            for c in self.credential_mounts:
                d.update({c["name"]: c["mount_path"]})
            self._volume_mounts = d.copy()
        return self._volume_mounts

    @property
    def build_env(self):
        if not self._build_env:
            d = {}
            d.update(GLOBAL_ENV)
            d.update({d["name"]: d.get("default", "") for d in self.ref.yaml.env})
            self._build_env = d.copy()
        return self._build_env

    @property
    def mocked_secret_paths(self):
        d = {}
        for _, v in self.mocked_vault_creds.items():
            n = v[SECRETSYNC_TARGET_NAME]
            ns = v[SECRETSYNC_TARGET_NAMESPACE]
            p: Path = self.mocked_secrets_dir / ns / n
            p.mkdir(exist_ok=True, parents=True)
            d[n] = p
            for _k, _v in v.items():
                if _k in (SECRETSYNC_TARGET_NAME, SECRETSYNC_TARGET_NAMESPACE):
                    continue
                (p / _k).write_text(_v)
        self._mocked_secret_paths = d.copy()
        return self._mocked_secret_paths

    def prompt_for_missing_secret(self, target_name):
        _yes = click.prompt(
            f"Mocked vault secret was not found for {target_name}. Create one now? | (y/N)",
            default=False,
            show_default=False,
        )
        if _yes:
            f: Path = self.mocked_vault_dir / target_name
            j = json.dumps(
                {
                    "secret_key": "secret_value",
                    "secretsync/target-name": target_name,
                    "secretsync/target-namespace": "test-credentials",
                },
                indent=2,
            )
            f.write_text(j)
            click.edit(filename=f.as_posix(), editor="code", require_save=True)
            click.prompt(
                "ENTER when finished editing", default=True, show_default=False
            )

    def build(self, skip_secret_prompt=False):
        if cf := self.ref.commands_file.path:
            entrypoint = "/tmp/entrypoint-wrapper/entrypoint-wrapper"
            self._copy_src_dst.append((cf, entrypoint))
        else:
            entrypoint = "bash"
        for m in self.credential_mounts:
            d = self.mocked_secret_paths.get(m["name"])
            if not d:
                if skip_secret_prompt:
                    continue
                self.prompt_for_missing_secret(m["name"])
            d = self.mocked_secret_paths.get(m["name"])
            if not d:
                continue
            for p in d.iterdir():
                self._copy_src_dst.append((p, m["mount_path"]))

        p = self.build_dir / "latest.yaml"
        p.write_text(
            f"""
            FROM {self.ref_base_image}
            {INJECT_OC_CMD if self.ref.cli == "latest" else ""}
            VOLUME {" ".join(v for _, v in self.volume_mounts.items())}
            USER {self.container_uid}:0
            RUN id
            {self.copy_cmd}
            ENTRYPOINT {entrypoint}
        """
        )

        args = [
            "--tag=ref_sandbox:latest",
            "--cap-drop=ALL",
            "--security-opt=label=level:s0:c66,c35",
        ]

        if self.build_env:
            env = " ".join([f"{k}={v}" for k, v in self.build_env.items()])
            args.append(f"--env={env}")

        cmd = ["podman", "build", *args, f"--file={p.as_posix()}"]
        res = sp.run(cmd, capture_output=True).stdout.split()
        self._built_image_hash = res[-1] if res else None
        return res

    @property
    def build_dir(self) -> Path:
        if not self._build_dir:
            self._build_dir = Path(BUILD_DIR)
            self._build_dir.mkdir(parents=True, exist_ok=True)
        return self._build_dir

    @property
    def mocked_vault_dir(self) -> Path:
        if not self._mocked_vault_dir:
            self._mocked_vault_dir = Path(MOCKED_VAULT_DIR)
            self._mocked_vault_dir.mkdir(parents=True, exist_ok=True)
        return self._mocked_vault_dir

    @property
    def mocked_secrets_dir(self) -> Path:
        if not self._mocked_secrets_dir:
            self._mocked_secrets_dir = Path(MOCKED_SECRETS_DIR)
            self._mocked_secrets_dir.mkdir(parents=True, exist_ok=True)
        return self._mocked_secrets_dir

    @property
    def mocked_vault_creds(self) -> dict:
        d = {}
        for p in self.mocked_vault_dir.rglob("*"):
            if p.is_dir():
                continue
            try:
                d[p.name] = json.loads(p.read_text())
            except json.JSONDecodeError:
                print(f"error parsing json in {p.as_posix()}")
                continue
        self._mocked_vault_creds = d.copy()
        return self._mocked_vault_creds

    def run(self, shell=False):
        args = [
            "--privileged=false",
            "--cap-drop=ALL",
            "--security-opt=label=level:s0:c66,c35",
            "--image-volume=tmpfs",
            "--rmi",
        ]

        if self.build_env:
            env = " ".join([f"{k}={v}" for k, v in self.build_env.items()])
            for e in env.split(" "):
                args.append(f"--env={e}")

        container_name = (
            self._built_image_hash if self._built_image_hash else "ref_sandbox:latest"
        )

        if shell:
            args.append("-it")
            args.append("--entrypoint=bash")

        cmd = ["podman", "run", *args, container_name]

        sp.run(cmd)
