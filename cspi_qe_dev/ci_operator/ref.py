from dataclasses import dataclass
from cspi_qe_dev.ci_operator.enum import ImageSourceType
from cspi_qe_dev.ci_operator.abc import PathWrapperABC
from cspi_qe_dev.ci_operator.yaml_config import StepRegistryRefYaml


@dataclass
class RefImage:
    source_type: ImageSourceType = ImageSourceType.NONE
    name: str = None
    namespace: str = None
    tag: str = None
    registry: str = "registry.ci.openshift.org"

    @classmethod
    def from_ref_yaml(cls, ref: dict):
        if img := ref.get("from"):
            return cls(ImageSourceType.PIPELINE_IMAGE, name=img)
        if img := ref.get("from_image"):
            return cls(ImageSourceType.IMAGE_STREAM_TAG, **img)

    @property
    def pull_str(self):
        if self.source_type is ImageSourceType.IMAGE_STREAM_TAG:
            return f"{self.registry}/{self.namespace}/{self.name}:{self.tag}"
        raise NotImplementedError


@dataclass
class RefCommands:
    inner: list[str]

    @classmethod
    def from_ref_yaml(cls, ref: dict):
        if inner := ref.get("commands"):
            return cls(inner)


@dataclass
class RefCommandsFile(PathWrapperABC):
    ...


@dataclass
class Ref(PathWrapperABC):
    _yaml: StepRegistryRefYaml = None
    _image: RefImage = None
    _commands: RefCommands = None
    _commands_file: RefCommandsFile = None
    name: str = None

    def __post_init__(self):
        self.name = self.path.name.removesuffix("-ref.yaml")

    @property
    def yaml(self):
        if not self._yaml:
            self._yaml = StepRegistryRefYaml(self.path)
        return self._yaml

    @property
    def image(self):
        if not self._image:
            self._image = RefImage.from_ref_yaml(self.yaml.ref)
        return self._image

    @property
    def commands(self):
        if not self._commands:
            self._commands = RefCommands.from_ref_yaml(self.yaml.ref)
        return self._commands

    @property
    def commands_file(self):
        if not self._commands_file:
            p = self.path.parent.joinpath(self.commands.inner)
            if p.is_file():
                self._commands_file = RefCommandsFile(p)
        return self._commands_file

    @property
    def credentials(self):
        return self.yaml.credentials

    @property
    def cli(self):
        return self.yaml.cli

    @property
    def linked_configs(self):
        raise NotImplementedError
