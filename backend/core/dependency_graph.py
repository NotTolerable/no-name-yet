"""Deterministic, versioned prerequisite graph for canonical controls.

This module contains product knowledge only. It does not inspect facts, assess
readiness, authorize claims, or participate in the TrustPacket pipeline.
"""

from collections.abc import Iterable
import heapq
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from core.models import (
    ControlCatalog,
    ControlDefinition,
    ControlDependency,
    ControlDependencySet,
    DependencyType,
)


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CONTROL_CATALOG_PATH = DATA_DIRECTORY / "control_catalog.json"
DEFAULT_CONTROL_DEPENDENCIES_PATH = DATA_DIRECTORY / "control_dependencies.json"


class DependencyGraphError(ValueError):
    """Base class for fail-closed dependency graph configuration errors."""


class DependencyGraphLoadError(DependencyGraphError):
    """Static graph data could not be read or validated as a document."""


class DependencyGraphValidationError(DependencyGraphError):
    """Catalog and dependency documents do not form a valid graph."""


class UnknownControlError(DependencyGraphError):
    """A query referenced a control outside the loaded catalog."""


def _load_json_object(path: str | Path, document_name: str) -> dict[str, Any]:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise DependencyGraphLoadError(
            f"Could not read {document_name} at {source}: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise DependencyGraphLoadError(
            f"Invalid JSON in {document_name} at {source}: {error}"
        ) from error

    if not isinstance(payload, dict):
        raise DependencyGraphLoadError(
            f"{document_name} at {source} must contain a JSON object"
        )
    return payload


def load_control_catalog(
    path: str | Path = DEFAULT_CONTROL_CATALOG_PATH,
) -> ControlCatalog:
    """Load and validate a versioned control catalog from human-readable JSON."""

    source = Path(path)
    try:
        return ControlCatalog.model_validate(
            _load_json_object(source, "control catalog")
        )
    except ValidationError as error:
        raise DependencyGraphLoadError(
            f"Invalid control catalog at {source}: {error}"
        ) from error


def load_control_dependencies(
    path: str | Path = DEFAULT_CONTROL_DEPENDENCIES_PATH,
) -> ControlDependencySet:
    """Load and validate the shape of versioned dependency data from JSON."""

    source = Path(path)
    try:
        return ControlDependencySet.model_validate(
            _load_json_object(source, "control dependencies")
        )
    except ValidationError as error:
        raise DependencyGraphLoadError(
            f"Invalid control dependencies at {source}: {error}"
        ) from error


def validate_dependency_graph(
    catalog: ControlCatalog,
    dependency_set: ControlDependencySet,
) -> None:
    """Reject inconsistent versions, invalid edges, ambiguity, and cycles."""

    if catalog.catalog_version != dependency_set.catalog_version:
        raise DependencyGraphValidationError(
            "Catalog version mismatch: control catalog uses "
            f"{catalog.catalog_version}, dependencies use "
            f"{dependency_set.catalog_version}"
        )

    control_ids = {control.id for control in catalog.controls}
    seen_edges: set[tuple[str, str, DependencyType]] = set()
    pair_types: dict[tuple[str, str], DependencyType] = {}
    adjacency: dict[str, list[str]] = {
        control_id: [] for control_id in control_ids
    }

    for dependency in dependency_set.dependencies:
        edge_label = (
            f"{dependency.control_id} -> {dependency.depends_on_control_id} "
            f"({dependency.dependency_type.value})"
        )
        if dependency.control_id not in control_ids:
            raise DependencyGraphValidationError(
                f"Unknown control_id in dependency edge: {edge_label}"
            )
        if dependency.depends_on_control_id not in control_ids:
            raise DependencyGraphValidationError(
                f"Unknown depends_on_control_id in dependency edge: {edge_label}"
            )
        if dependency.control_id == dependency.depends_on_control_id:
            raise DependencyGraphValidationError(
                f"Self-dependency is not allowed: {edge_label}"
            )

        edge_key = (
            dependency.control_id,
            dependency.depends_on_control_id,
            dependency.dependency_type,
        )
        if edge_key in seen_edges:
            raise DependencyGraphValidationError(
                f"Duplicate dependency edge: {edge_label}"
            )
        seen_edges.add(edge_key)

        pair_key = (dependency.control_id, dependency.depends_on_control_id)
        previous_type = pair_types.get(pair_key)
        if previous_type is not None and previous_type is not dependency.dependency_type:
            raise DependencyGraphValidationError(
                "Ambiguous dependency types for "
                f"{dependency.control_id} -> {dependency.depends_on_control_id}: "
                f"{previous_type.value} and {dependency.dependency_type.value}"
            )
        pair_types[pair_key] = dependency.dependency_type
        adjacency[dependency.control_id].append(
            dependency.depends_on_control_id
        )

    _validate_acyclic(adjacency)


def _validate_acyclic(adjacency: dict[str, list[str]]) -> None:
    state: dict[str, int] = {control_id: 0 for control_id in adjacency}
    stack: list[str] = []

    def visit(control_id: str) -> None:
        state[control_id] = 1
        stack.append(control_id)
        for prerequisite_id in sorted(adjacency[control_id]):
            if state[prerequisite_id] == 0:
                visit(prerequisite_id)
            elif state[prerequisite_id] == 1:
                cycle_start = stack.index(prerequisite_id)
                cycle_path = stack[cycle_start:] + [prerequisite_id]
                raise DependencyGraphValidationError(
                    "Dependency cycle detected: " + " -> ".join(cycle_path)
                )
        stack.pop()
        state[control_id] = 2

    for control_id in sorted(adjacency):
        if state[control_id] == 0:
            visit(control_id)


class ControlDependencyGraph:
    """Validated offline graph with deterministic prerequisite queries.

    Transitive queries exclude the queried control. Topological ordering
    includes transitive prerequisites by default and always places a
    prerequisite before its dependent, using control ID as the tie-breaker.
    """

    def __init__(
        self,
        catalog: ControlCatalog,
        dependency_set: ControlDependencySet,
    ) -> None:
        validate_dependency_graph(catalog, dependency_set)
        self.catalog_version = catalog.catalog_version
        self._controls = {control.id: control for control in catalog.controls}
        self._dependencies = tuple(dependency_set.dependencies)
        self._dependencies_by_control: dict[str, tuple[ControlDependency, ...]] = {
            control_id: tuple(
                sorted(
                    (
                        dependency
                        for dependency in self._dependencies
                        if dependency.control_id == control_id
                    ),
                    key=lambda dependency: (
                        dependency.depends_on_control_id,
                        dependency.dependency_type.value,
                    ),
                )
            )
            for control_id in self._controls
        }

    def get_control(self, control_id: str) -> ControlDefinition:
        try:
            return self._controls[control_id]
        except KeyError as error:
            raise UnknownControlError(f"Unknown control ID: {control_id}") from error

    def get_direct_dependencies(
        self,
        control_id: str,
        dependency_type: DependencyType | None = None,
    ) -> list[ControlDependency]:
        """Return immediate prerequisite edges, optionally filtered by type."""

        self.get_control(control_id)
        return [
            dependency
            for dependency in self._dependencies_by_control[control_id]
            if dependency_type is None
            or dependency.dependency_type is dependency_type
        ]

    def get_transitive_dependencies(
        self,
        control_id: str,
        dependency_type: DependencyType | None = None,
    ) -> list[str]:
        """Return the prerequisite closure without duplicates or the query ID."""

        self.get_control(control_id)
        discovered = self._collect_transitive_dependencies(
            {control_id}, dependency_type
        )
        discovered.discard(control_id)
        return self.topologically_order_controls(
            discovered,
            include_transitive_dependencies=False,
            dependency_type=dependency_type,
        )

    def topologically_order_controls(
        self,
        control_ids: Iterable[str],
        *,
        include_transitive_dependencies: bool = True,
        dependency_type: DependencyType | None = None,
    ) -> list[str]:
        """Order unique controls with prerequisites first and ID tie-breaking.

        By default the result includes the full transitive closure selected by
        ``dependency_type``. Pass ``include_transitive_dependencies=False`` to
        order only the requested controls while respecting edges among them.
        """

        requested = set(control_ids)
        unknown_ids = sorted(requested - self._controls.keys())
        if unknown_ids:
            raise UnknownControlError(
                "Unknown control IDs: " + ", ".join(unknown_ids)
            )

        selected = set(requested)
        if include_transitive_dependencies:
            selected.update(
                self._collect_transitive_dependencies(
                    requested, dependency_type
                )
            )

        dependents: dict[str, list[str]] = {
            control_id: [] for control_id in selected
        }
        indegree = {control_id: 0 for control_id in selected}
        for control_id in sorted(selected):
            for dependency in self.get_direct_dependencies(
                control_id, dependency_type
            ):
                prerequisite_id = dependency.depends_on_control_id
                if prerequisite_id not in selected:
                    continue
                dependents[prerequisite_id].append(control_id)
                indegree[control_id] += 1

        ready = [
            control_id
            for control_id, degree in indegree.items()
            if degree == 0
        ]
        heapq.heapify(ready)
        ordered: list[str] = []
        while ready:
            control_id = heapq.heappop(ready)
            ordered.append(control_id)
            for dependent_id in sorted(dependents[control_id]):
                indegree[dependent_id] -= 1
                if indegree[dependent_id] == 0:
                    heapq.heappush(ready, dependent_id)

        if len(ordered) != len(selected):
            raise DependencyGraphValidationError(
                "Cannot topologically order a cyclic dependency graph"
            )
        return ordered

    def _collect_transitive_dependencies(
        self,
        control_ids: set[str],
        dependency_type: DependencyType | None,
    ) -> set[str]:
        discovered: set[str] = set()
        pending = sorted(control_ids, reverse=True)
        while pending:
            control_id = pending.pop()
            for dependency in self.get_direct_dependencies(
                control_id, dependency_type
            ):
                prerequisite_id = dependency.depends_on_control_id
                if prerequisite_id in discovered:
                    continue
                discovered.add(prerequisite_id)
                pending.append(prerequisite_id)
        return discovered


def load_dependency_graph(
    catalog_path: str | Path = DEFAULT_CONTROL_CATALOG_PATH,
    dependencies_path: str | Path = DEFAULT_CONTROL_DEPENDENCIES_PATH,
) -> ControlDependencyGraph:
    """Load both static documents and return a fully validated graph."""

    return ControlDependencyGraph(
        load_control_catalog(catalog_path),
        load_control_dependencies(dependencies_path),
    )
