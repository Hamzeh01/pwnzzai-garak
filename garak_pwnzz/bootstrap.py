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

#: Name our plugin modules take inside the garak namespace, e.g.
#: ``garak.probes.pwnzz``.
PLUGIN_MODULE = "pwnzz"

_installed = False


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

    global _installed
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


def _register_in_cache() -> None:
    """Add our plugin classes to garak's in-memory plugin cache.

    ``enumerate_plugins`` reads ``PluginCache.instance()[category]``. We import
    our module, take every concrete plugin class it defines, and add a cache
    entry built by garak's own ``plugin_info`` so the metadata shape matches
    exactly what the CLI expects.
    """

    from garak._plugins import PluginCache

    cache = PluginCache.instance()  # forces a load if needed; returns the dict
    for category in _CATEGORIES:
        module = importlib.import_module(f"garak.{category}.{PLUGIN_MODULE}")
        base = importlib.import_module(f"garak.{category}.base")
        base_names = {
            name for name in dir(base) if isinstance(getattr(base, name), type)
        }
        for name in dir(module):
            obj = getattr(module, name)
            if not isinstance(obj, type):
                continue
            if obj.__module__ != module.__name__:
                continue
            if name.startswith("_") or name in base_names:
                continue
            if getattr(obj, "_abstract_base", False):
                continue
            key = f"{category}.{PLUGIN_MODULE}.{name}"
            if key in cache.get(category, {}):
                continue
            cache.setdefault(category, {})[key] = PluginCache.plugin_info(obj)


def plugin_specs() -> dict[str, list[str]]:
    """Return the plugin classes this project contributes, by category.

    Used by the CLI's ``list`` command and by the tests that assert every
    advertised plugin actually loads.
    """

    install()
    found: dict[str, list[str]] = {}
    for category in _CATEGORIES:
        module = importlib.import_module(f"garak.{category}.{PLUGIN_MODULE}")
        base = importlib.import_module(f"garak.{category}.base")
        base_names = {
            name for name in dir(base) if isinstance(getattr(base, name), type)
        }
        # Classes explicitly marked abstract via ``__all__`` omission or an
        # ``abstract`` flag are excluded so listings show only runnable plugins.
        exported = set(getattr(module, "__all__", []))
        names = []
        for name in dir(module):
            obj = getattr(module, name)
            if not isinstance(obj, type):
                continue
            if obj.__module__ != module.__name__:
                continue
            if name.startswith("_") or name in base_names:
                continue
            if getattr(obj, "_abstract_base", False):
                continue
            if exported and name not in exported:
                continue
            names.append(f"{category}.{PLUGIN_MODULE}.{name}")
        found[category] = sorted(names)
    return found
