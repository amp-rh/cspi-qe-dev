from dataclasses import dataclass
from cspi_qe_dev.ci_operator.abc import PathWrapperABC
from cspi_qe_dev.ci_operator.yaml_config import ConfigYaml


@dataclass
class Repo(PathWrapperABC):
    @property
    def yaml_configs(self):
        for config in self.path.glob("*.yaml"):
            yield ConfigYaml(config)
