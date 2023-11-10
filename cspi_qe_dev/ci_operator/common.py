from dataclasses import dataclass


from dataclasses import dataclass
from cspi_qe_dev.ci_operator.abc import PathWrapperABC
from cspi_qe_dev.ci_operator.ci_operator import CiOperator


@dataclass
class OpenshiftReleaseSource(PathWrapperABC):
    @property
    def ci_operator(self):
        return CiOperator(self.path / "ci-operator")
