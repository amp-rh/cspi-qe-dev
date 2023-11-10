from dataclasses import dataclass
from typing import Iterator
from cspi_qe_dev.ci_operator.abc import PathWrapperABC
from cspi_qe_dev.ci_operator.repo import Repo


@dataclass
class Org(PathWrapperABC):
    @property
    def repos(self) -> Iterator[Repo]:
        for d in self.path.iterdir():
            if d.is_dir():
                yield Repo(d)
