"""
Auto-discovery utilities for finding ExtModel subclasses and Flask Blueprints.

Uses only the Python standard library (importlib, pkgutil).
"""

import importlib
import logging
import pkgutil
from typing import List, Type

from .models import ExtModel

logger = logging.getLogger(__name__)


def discover_models(package_name: str) -> List[Type[ExtModel]]:
    """Import all modules in *package_name* and collect ExtModel subclasses.

    Args:
        package_name: Dotted package path, e.g. ``"my_extension.models"``.

    Returns:
        List of ExtModel subclass types found in the package.
        Empty list if the package does not exist.
    """
    models: List[Type[ExtModel]] = []

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        logger.debug("Models package %r not found, skipping.", package_name)
        return models

    models.extend(_collect_models_from_module(package))

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return models

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        full_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_name)
            models.extend(_collect_models_from_module(module))
        except Exception as exc:
            logger.warning("Failed to import model module %r: %s", full_name, exc)

    logger.info(
        "Discovered %d model(s) from %r: %s",
        len(models),
        package_name,
        [m.__name__ for m in models],
    )
    return models


def discover_blueprints(package_name: str) -> list:
    """Import all modules in *package_name* and collect Flask Blueprint instances.

    Args:
        package_name: Dotted package path, e.g. ``"my_extension.controllers"``.

    Returns:
        List of Blueprint instances. Empty list if the package does not exist.
    """
    from flask import Blueprint

    blueprints: list = []

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        logger.debug("Controllers package %r not found, skipping.", package_name)
        return blueprints

    blueprints.extend(_collect_blueprints_from_module(package, Blueprint))

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return blueprints

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        full_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_name)
            blueprints.extend(_collect_blueprints_from_module(module, Blueprint))
        except Exception as exc:
            logger.warning("Failed to import controller module %r: %s", full_name, exc)

    logger.info(
        "Discovered %d blueprint(s) from %r: %s",
        len(blueprints),
        package_name,
        [bp.name for bp in blueprints],
    )
    return blueprints


# ------------------------------------------------------------------ #
# Internal helpers                                                      #
# ------------------------------------------------------------------ #


def _collect_models_from_module(module) -> List[Type[ExtModel]]:
    """Find all ExtModel subclasses *defined* in *module*."""
    found = []
    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if (
            isinstance(obj, type)
            and issubclass(obj, ExtModel)
            and obj is not ExtModel
            and obj.__module__ == module.__name__
        ):
            found.append(obj)
    return found


def _collect_blueprints_from_module(module, blueprint_cls) -> list:
    """Find all Flask Blueprint instances defined in *module*."""
    found = []
    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if isinstance(obj, blueprint_cls):
            found.append(obj)
    return found
