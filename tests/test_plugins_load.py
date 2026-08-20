"""Every advertised plugin must load through garak's own loader.

A plugin that lists but fails to instantiate is worse than one that is absent,
because a suite would skip it mid-run. These tests prove the bootstrap makes
each class loadable via ``garak._plugins.load_plugin`` -- the exact path the
harness uses -- and that the probe/detector wiring resolves.
"""

# Test names carry the intent; a docstring restating the name adds nothing.
# pylint: disable=missing-function-docstring

from __future__ import annotations

from typing import Any

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

    for spec in bootstrap.plugin_specs()["probes"]:
        # load_plugin is declared to return `object`; the contract is duck-typed.
        probe: Any = load_plugin(spec)
        assert probe is not None, spec
        assert probe.prompts, f"{spec} has no prompts"
        assert probe.goal, f"{spec} has no goal"
        # primary detector must be loadable
        primary = probe.primary_detector
        assert primary, f"{spec} has no primary_detector"
        load_plugin(f"detectors.{primary}")
        # ...and so must every extended one. The probewise harness loads these
        # by name at run time and only logs a failure, so a typo would silently
        # drop a detector from the run rather than stopping it.
        for extended in probe.extended_detectors:
            assert load_plugin(
                f"detectors.{extended}", break_on_fail=False
            ), f"{spec} names unloadable extended detector {extended!r}"


def test_every_probe_has_a_stock_detector_for_the_agreement_analysis():
    # detector-agreement.csv pairs each probe's primary detector with its first
    # non-pwnzz one; a probe with no stock detector drops out of that table
    # without any error being raised.
    from garak._plugins import load_plugin

    # The classifier surface answers with a label, not prose, so a
    # refusal-language detector has nothing to say about it. See the probes
    # module docstring.
    exempt = {"probes.pwnzz.SentimentPoisoning"}

    for spec in bootstrap.plugin_specs()["probes"]:
        if spec in exempt:
            continue
        probe: Any = load_plugin(spec)
        stock = [d for d in probe.extended_detectors if not d.startswith("pwnzz")]
        assert stock, f"{spec} has no stock detector to compare against"


def test_every_surface_is_exercised_by_a_suite_task():
    # A generator with no task is an attack surface the assessment silently
    # never touches -- which is how the comment-corpus poisoning path went
    # unmeasured despite having a generator written for it.
    from garak.generators.pwnzz import SURFACES  # pyright: ignore[reportMissingImports]

    from garak_pwnzz import suites

    used = {
        task.generator.split(".")[-1]
        for suite in suites.SUITES.values()
        for task in suite.tasks
    }
    missing = {klass.__name__ for klass in SURFACES} - used
    assert not missing, f"surfaces with no suite task: {sorted(missing)}"


def test_generators_construct_without_network():
    # Construction must not touch the network -- only sending a prompt should.
    from garak._plugins import load_plugin

    for spec in bootstrap.plugin_specs()["generators"]:
        gen: Any = load_plugin(spec)
        assert gen is not None, spec
        assert (
            gen.base_url.startswith("http://127.0.0.1") or "localhost" in gen.base_url
        )


def test_probe_target_generator_pairs_are_consistent():
    # Only importable after bootstrap.install() has grafted our plugins onto the
    # garak namespace, which the module fixture above has done by now.
    from garak.probes.pwnzz import (  # pyright: ignore[reportMissingImports]
        PROBE_TARGET_GENERATOR,
    )

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
