import pytest
from pathlib import Path
import subprocess as sp
from dataclasses import dataclass
import pytest

OPENSHIFT_RELEASE_GIT = "https://github.com/openshift/release.git"


@dataclass
class Resources:
    _path: Path = None
    _openshift_src: Path = None

    @property
    def openshift_src(self) -> Path:
        if not self._openshift_src:
            self._openshift_src = self.path / "openshift-release"
            if not self._openshift_src.is_dir():
                sp.run(
                    [
                        "git",
                        "clone",
                        OPENSHIFT_RELEASE_GIT,
                        self._openshift_src.as_posix(),
                    ]
                )
        return self._openshift_src

    @property
    def path(self):
        if not self._path:
            self._path = Path(__file__).parent / "resources"
            self._path.mkdir(exist_ok=True)
        return self._path


@pytest.fixture()
def resources() -> Resources:
    yield Resources()


@pytest.fixture
def openshift_src(resources) -> Path:
    yield resources.openshift_src


@pytest.fixture
def firewatch_ref_dir(openshift_src) -> Path:
    p = openshift_src / "ci-operator/step-registry/firewatch/report-issues"
    assert p.is_dir()
    yield p