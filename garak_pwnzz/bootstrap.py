"""Make this project's plugins loadable by Garak under the ``pwnzz`` name.

Garak resolves a plugin spec such as ``probes.pwnzz.CouponExtraction`` by
importing ``garak.probes.pwnzz``. Its loader is a plain ``importlib`` call
against the ``garak`` package namespace, so third-party plugins are only
findable if that namespace can see them.

Rather than copy files into ``site-packages/garak`` -- which would make the
install stateful and easy to get wrong on a fresh machine -- this module
appends our plugin directories to the relevant ``__path__`` lists at import
time. ``garak.probes`` is a regular package, so extending its ``__path__``
makes ``garak.probes.pwnzz`` resolve to our file on disk with normal import
semantics: no ``sys.modules`` surgery, no shadowing of stock plugins, and
nothing written outside this repository.

Call :func:`install` before invoking garak. :mod:`garak_pwnzz.runner` does this
for you.
"""

from __future__ import annotations

import importlib
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent / "garak_plugins"

#: Garak plugin categories this project extends, mapped to our directory names.
_CATEGORIES = ("generators", "probes", "detectors")

#: The modules each category contributes, under the names they take inside the
#: garak namespace -- ``garak.probes.pwnzz``, ``garak.detectors.pwnzz_judge``,
#: and so on. Detectors are split in two because the two kinds answer different
#: questions: ``pwnzz`` scores against ground truth read from the pinned
#: application source, ``pwnzz_judge`` asks a model for an opinion. Keeping them
#: in separate specs means a run, a report, or a reader can tell them apart
#: without knowing the class names.
PLUGIN_MODULES: dict[str, tuple[str, ...]] = {
    "generators": ("pwnzz",),
    "probes": ("pwnzz",),
    "detectors": ("pwnzz", "pwnzz_judge"),
}

#: Set once :func:`install` has extended the garak namespace in this process.
#: Mutable process state, not a constant, so it keeps a lower-case name.
_installed: bool = False  # pylint: disable=invalid-name


def install(force: bool = False) -> None:
    """Make ``garak.*.pwnzz`` importable *and* discoverable by garak's tooling.

    Two steps:

    1. Append our plugin directories to ``garak.{category}.__path__`` so
       ``importlib`` -- and therefore ``garak._plugins.load_plugin`` and the
       harness -- resolves ``garak.probes.pwnzz`` to our file on disk.
    2. Register our classes in garak's plugin *cache*, which is what
       ``enumerate_plugins`` (and hence the stock CLI's ``--probes`` spec
       parser and ``--list_probes``) reads. The cache is otherwise built by
       scanning only garak's own package directory, so without this our plugins
       load but cannot be named on the command line.

    Idempotent. Safe to call from any process that will invoke garak, including
    the worker processes garak spawns for parallel attempts.
    """

    # Module-level flag: idempotence has to survive across every caller in the
    # process, including the workers garak forks for parallel attempts.
    global _installed  # pylint: disable=global-statement
    if _installed and not force:
        return

    for category in _CATEGORIES:
        package = importlib.import_module(f"garak.{category}")
        our_dir = str(PLUGIN_ROOT / category)
        if not (PLUGIN_ROOT / category).is_dir():
            raise RuntimeError(f"missing plugin directory: {our_dir}")
        if our_dir not in package.__path__:
            package.__path__.append(our_dir)

    _register_in_cache()
    _installed = True


def _runnable_classes(category: str, module_name: str) -> list[tuple[str, type]]:
    """Return the concrete plugin classes one of our modules contributes.

    Filters out anything a run could not sensibly select: names imported from
    elsewhere, garak's own base classes, private names, classes flagged
    ``_abstract_base``, and -- where the module declares ``__all__`` -- anything
    it did not export.
    """

    module = importlib.import_module(f"garak.{category}.{module_name}")
    base = importlib.import_module(f"garak.{category}.base")
    base_names = {name for name in dir(base) if isinstance(getattr(base, name), type)}
    exported = set(getattr(module, "__all__", []))

    classes: list[tuple[str, type]] = []
    for name in dir(module):
        obj = getattr(module, name)
        if not isinstance(obj, type):
            continue
        if obj.__module__ != module.__name__:
            continue
        if name.startswith("_") or name in base_names:
            continue
        # Read ``_abstract_base`` off the class itself, not through the MRO: a
        # concrete plugin inherits the flag from the abstract base it extends,
        # and an inherited True would hide every real plugin in the module.
        if obj.__dict__.get("_abstract_base", False):
            continue
        if exported and name not in exported:
            continue
        classes.append((f"{category}.{module_name}.{name}", obj))
    return classes


def _register_in_cache() -> None:
    """Add our plugin classes to garak's in-memory plugin cache.

    ``enumerate_plugins`` reads ``PluginCache.instance()[category]``. We import
    each of our modules, take every concrete plugin class it defines, and add a
    cache entry built by garak's own ``plugin_info`` so the metadata shape
    matches exactly what the CLI expects.
    """

    # Imported here rather than at module scope: importing garak._plugins costs
    # a full plugin scan, and callers that only need plugin_specs() should not
    # pay for it.
    from garak._plugins import PluginCache

    # PluginCache declares instance()/plugin_info() without a `self` parameter,
    # so they are class-level callables despite lacking @staticmethod. Type
    # checkers read them as unbound instance methods; the calls are correct.
    cache = PluginCache.instance()  # type: ignore[attr-defined]
    for category in _CATEGORIES:
        for module_name in PLUGIN_MODULES[category]:
            for key, obj in _runnable_classes(category, module_name):
                if key in cache.get(category, {}):
                    continue
                info = PluginCache.plugin_info(obj)  # type: ignore[attr-defined]
                cache.setdefault(category, {})[key] = info


def plugin_specs() -> dict[str, list[str]]:
    """Return the plugin classes this project contributes, by category.

    Used by the CLI's ``list`` command and by the tests that assert every
    advertised plugin actually loads.
    """

    install()
    found: dict[str, list[str]] = {}
    for category in _CATEGORIES:
        names = [
            key
            for module_name in PLUGIN_MODULES[category]
            for key, _ in _runnable_classes(category, module_name)
        ]
        found[category] = sorted(names)
    return found
