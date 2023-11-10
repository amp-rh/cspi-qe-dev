from cspi_qe_dev.ci_operator.ci_operator import StepRegistry
from cspi_qe_dev.ci_operator.common import CiOperator, OpenshiftReleaseSource
from cspi_qe_dev.ci_operator.ref import Ref
from cspi_qe_dev.ci_operator.yaml_config import ConfigYaml
from dataclasses import dataclass
from pathlib import Path


class RefNotFoundError(BaseException):
    ...


@dataclass
class CiOperatorApi:
    _src: OpenshiftReleaseSource
    _ci_op: CiOperator = None
    _step_registry: StepRegistry = None

    def __post_init__(self):
        self._ci_op = self._src.ci_operator
        self._step_registry = self._ci_op.step_registry
        self._config = self._ci_op.config

    def _wrap_ref(self, ref):
        @dataclass
        class RefWrapper:
            _ref: Ref
            _api = self

            @property
            def linked_configs(self):
                yield from self._api.get_linked_configs_for_ref(self._ref)

        return RefWrapper(ref)

    def _wrap_config(self, config):
        @dataclass
        class ConfigWrapper:
            _config: ConfigYaml
            _api = self

        return ConfigWrapper(config)

    def get_step_registry_ref(self, ref_name: str):
        res = next(filter(lambda x: x.name == ref_name, self._step_registry.refs), None)
        if res:
            return self._wrap_ref(res)
        raise RefNotFoundError(f'"{ref_name}" not found in step registry')

    def get_linked_configs_for_ref(self, ref: Ref):
        for conf in self._iter_all_configs():
            if ref.name in conf.refs:
                yield conf

    def _iter_all_configs(self):
        for o in self._config.orgs:
            for r in o.repos:
                for y in r.yaml_configs:
                    yield y


def from_src_root(p: str):
    return CiOperatorApi(OpenshiftReleaseSource(Path(p)))
