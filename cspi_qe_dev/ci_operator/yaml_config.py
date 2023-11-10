from dataclasses import dataclass


from dataclasses import dataclass
from cspi_qe_dev.ci_operator.abc import YamlPathWrapperABC

import re

REF_RE = re.compile(r"ref: (.+)")


@dataclass
class ConfigYaml(YamlPathWrapperABC):
    @property
    def refs(self):
        yield from REF_RE.findall(self.path.read_text())


@dataclass
class StepRegistryRefYaml(YamlPathWrapperABC):
    _ref: dict = None

    @property
    def ref(self):
        if not self._ref:
            self._ref = self._yaml["ref"]
        return self._ref

    @property
    def env(self):
        return self.ref.get("env", [])

    @property
    def credentials(self):
        return self.ref.get("credentials", [])

    @property
    def commands(self):
        return self.ref["commands"]
    
    @property
    def cli(self):
        return self.ref.get("cli", None)
