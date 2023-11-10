from dataclasses import dataclass
from typing import Iterator

from cspi_qe_dev.ci_operator.abc import PathWrapperABC
from cspi_qe_dev.ci_operator.org import Org
from cspi_qe_dev.ci_operator.ref import Ref


@dataclass
class Config(PathWrapperABC):
    @property
    def orgs(self) -> Iterator[Org]:
        for d in self.path.iterdir():
            if d.is_dir():
                yield Org(d)


@dataclass
class StepRegistry(PathWrapperABC):
    @property
    def refs(self) -> Iterator[Ref]:
        for p in self.path.glob("**/*-ref.yaml"):
            yield Ref(p)


@dataclass
class CiOperator(PathWrapperABC):
    @property
    def config(self):
        return Config(self.path / "config")

    @property
    def step_registry(self):
        return StepRegistry(self.path / "step-registry")
