"""Every advertised plugin must load through garak's own loader.

A plugin that lists but fails to instantiate is worse than one that is absent,
because a suite would skip it mid-run. These tests prove the bootstrap makes
each class loadable via ``garak._plugins.load_plugin`` -- the exact path the
harness uses -- and that the probe/detector wiring resolves.
"""

from __future__ import annotations

import pytest

from garak_pwnzz import bootstrap


@pytest.fixture(scope="module", autouse=True)
def _installed():
    bootstrap.install()


def test_specs_enumerate():
    specs = bootstrap.plugin_specs()
    assert specs["generators"], "no generators found"
    assert specs["probes"], "no probes found"
    assert specs["detectors"], "no detectors found"


def test_all_detectors_load():
    from garak._plugins import load_plugin

    for spec in bootstrap.plugin_specs()["detectors"]:
        det = load_plugin(spec)
        assert det is not None, spec
        assert hasattr(det, "detect")


def test_all_probes_load_and_reference_valid_detectors():
    from garak._plugins import load_plugin

    detector_specs = set(bootstrap.plugin_specs()["detectors"])
    for spec in bootstrap.plugin_specs()["probes"]:
        probe = load_plugin(spec)
        assert probe is not None, spec
        assert probe.prompts, f"{spec} has no prompts"
        assert probe.goal, f"{spec} has no goal"
        # primary detector must be loadable
        primary = probe.primary_detector
        assert primary, f"{spec} has no primary_detector"
        load_plugin(f"detectors.{primary}")


def test_generators_construct_without_network():
    # Construction must not touch the network -- only sending a prompt should.
    from garak._plugins import load_plugin

    for spec in bootstrap.plugin_specs()["generators"]:
        gen = load_plugin(spec)
        assert gen is not None, spec
        assert gen.base_url.startswith("http://127.0.0.1") or "localhost" in gen.base_url


def test_probe_target_generator_pairs_are_consistent():
    from garak.probes.pwnzz import PROBE_TARGET_GENERATOR
    from garak_pwnzz import suites

    for suite in suites.SUITES.values():
        for task in suite.tasks:
            probe_cls = task.probe.split(".")[-1]
            gen_cls = task.generator.split(".")[-1]
            expected = PROBE_TARGET_GENERATOR.get(probe_cls)
            if expected:
                assert gen_cls in expected, (
                    f"suite {suite.name} task {task.label}: "
                    f"{probe_cls} expects one of {expected}, got {gen_cls}"
                )
