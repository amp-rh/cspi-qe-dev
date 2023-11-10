from dataclasses import dataclass
from abc import ABC
from pathlib import Path
import yaml
import yaml.scanner


@dataclass
class PathWrapperABC(ABC):
    path: Path

    def __post_init__(self):
        if not isinstance(self.path, Path):
            self.path = Path(self.path)


@dataclass
class YamlWrapperABC(ABC):
    path: Path
    _yaml: dict = None

    def __post_init__(self):
        try:
            self._yaml = yaml.safe_load(self.path.read_text())
        except yaml.scanner.ScannerError:
            self._yaml = yaml.safe_load(self.path.read_text().replace("\t\n", "\n"))


@dataclass
class YamlPathWrapperABC(YamlWrapperABC, PathWrapperABC, ABC):
    ...
