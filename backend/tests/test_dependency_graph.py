import ast
from pathlib import Path

from pydantic import ValidationError
import pytest

import core.dependency_graph as dependency_graph_module
from core.dependency_graph import (
    DependencyGraphValidationError,
    UnknownControlError,
    load_control_catalog,
    load_control_dependencies,
    load_dependency_graph,
    validate_dependency_graph,
)
from core.models import (
    ControlCatalog,
    ControlDefinition,
    ControlDependency,
    ControlDependencySet,
    DependencyType,
    TrustPacket,
)


CATALOG_VERSION = "1.0.0"


def make_control(
    control_id: str,
    *,
    catalog_version: str = CATALOG_VERSION,
) -> ControlDefinition:
    return ControlDefinition(
        id=control_id,
        name=control_id.replace("_", " ").title(),
        domain="test_domain",
        description=f"Synthetic definition for {control_id}.",
        catalog_version=catalog_version,
    )


def make_catalog(
    *control_ids: str,
    catalog_version: str = CATALOG_VERSION,
) -> ControlCatalog:
    return ControlCatalog(
        catalog_version=catalog_version,
        controls=[
            make_control(
                control_id,
                catalog_version=catalog_version,
            )
            for control_id in control_ids
        ],
    )


def make_dependency(
    control_id: str,
    depends_on_control_id: str,
    dependency_type: DependencyType = DependencyType.REQUIRED,
) -> ControlDependency:
    return ControlDependency(
        control_id=control_id,
        depends_on_control_id=depends_on_control_id,
        dependency_type=dependency_type,
        reason=f"{control_id} uses {depends_on_control_id} in this synthetic graph.",
    )


def make_dependency_set(
    *dependencies: ControlDependency,
    catalog_version: str = CATALOG_VERSION,
) -> ControlDependencySet:
    return ControlDependencySet(
        catalog_version=catalog_version,
        dependencies=list(dependencies),
    )


def test_production_catalog_and_dependencies_load_successfully():
    catalog = load_control_catalog()
    dependency_set = load_control_dependencies()
    graph = load_dependency_graph()

    assert catalog.catalog_version == CATALOG_VERSION
    assert dependency_set.catalog_version == CATALOG_VERSION
    assert graph.catalog_version == CATALOG_VERSION
    assert len(catalog.controls) == 21
    assert len(dependency_set.dependencies) == 18


def test_production_catalog_has_unique_ids_and_representative_controls():
    catalog = load_control_catalog()
    control_ids = [control.id for control in catalog.controls]

    assert len(control_ids) == len(set(control_ids))
    assert {
        "identity_management",
        "tenant_data_scoping",
        "centralized_audit_logging",
        "incident_response_readiness",
        "prompt_injection_testing",
        "soc2_status",
    } <= set(control_ids)


def test_all_production_dependencies_reference_catalog_controls():
    catalog = load_control_catalog()
    dependency_set = load_control_dependencies()
    control_ids = {control.id for control in catalog.controls}

    validate_dependency_graph(catalog, dependency_set)
    assert all(
        dependency.control_id in control_ids
        and dependency.depends_on_control_id in control_ids
        for dependency in dependency_set.dependencies
    )


def test_production_dependency_type_counts_are_stable():
    dependencies = load_control_dependencies().dependencies

    assert sum(
        dependency.dependency_type is DependencyType.REQUIRED
        for dependency in dependencies
    ) == 12
    assert sum(
        dependency.dependency_type is DependencyType.SUPPORTING
        for dependency in dependencies
    ) == 6


def test_unknown_source_control_is_rejected():
    catalog = make_catalog("control_a", "control_b")
    dependency_set = make_dependency_set(
        make_dependency("unknown_control", "control_a")
    )

    with pytest.raises(
        DependencyGraphValidationError, match="Unknown control_id.*unknown_control"
    ):
        validate_dependency_graph(catalog, dependency_set)


def test_unknown_dependency_control_is_rejected():
    catalog = make_catalog("control_a", "control_b")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "unknown_control")
    )

    with pytest.raises(
        DependencyGraphValidationError,
        match="Unknown depends_on_control_id.*unknown_control",
    ):
        validate_dependency_graph(catalog, dependency_set)


def test_self_dependency_is_rejected():
    catalog = make_catalog("control_a")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "control_a")
    )

    with pytest.raises(DependencyGraphValidationError, match="Self-dependency"):
        validate_dependency_graph(catalog, dependency_set)


def test_duplicate_edge_is_rejected():
    catalog = make_catalog("control_a", "control_b")
    edge = make_dependency("control_a", "control_b")
    dependency_set = make_dependency_set(edge, edge)

    with pytest.raises(DependencyGraphValidationError, match="Duplicate dependency"):
        validate_dependency_graph(catalog, dependency_set)


def test_ambiguous_dependency_types_are_rejected():
    catalog = make_catalog("control_a", "control_b")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "control_b", DependencyType.REQUIRED),
        make_dependency("control_a", "control_b", DependencyType.SUPPORTING),
    )

    with pytest.raises(
        DependencyGraphValidationError, match="Ambiguous dependency types"
    ):
        validate_dependency_graph(catalog, dependency_set)


def test_duplicate_control_id_is_rejected():
    with pytest.raises(ValidationError, match="Duplicate control IDs: control_a"):
        ControlCatalog(
            catalog_version=CATALOG_VERSION,
            controls=[make_control("control_a"), make_control("control_a")],
        )


def test_direct_cycle_is_rejected_with_diagnostic_path():
    catalog = make_catalog("control_a", "control_b")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "control_b"),
        make_dependency("control_b", "control_a"),
    )

    with pytest.raises(
        DependencyGraphValidationError,
        match=r"control_a -> control_b -> control_a",
    ):
        validate_dependency_graph(catalog, dependency_set)


def test_indirect_cycle_is_rejected_with_diagnostic_path():
    catalog = make_catalog("control_a", "control_b", "control_c")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "control_b"),
        make_dependency("control_b", "control_c"),
        make_dependency("control_c", "control_a"),
    )

    with pytest.raises(
        DependencyGraphValidationError,
        match=r"control_a -> control_b -> control_c -> control_a",
    ):
        validate_dependency_graph(catalog, dependency_set)


def test_mismatched_catalog_versions_are_rejected():
    catalog = make_catalog("control_a", "control_b")
    dependency_set = make_dependency_set(
        make_dependency("control_a", "control_b"),
        catalog_version="2.0.0",
    )

    with pytest.raises(DependencyGraphValidationError, match="version mismatch"):
        validate_dependency_graph(catalog, dependency_set)


def test_control_definition_version_must_match_catalog_version():
    with pytest.raises(ValidationError, match="versions do not match"):
        ControlCatalog(
            catalog_version=CATALOG_VERSION,
            controls=[make_control("control_a", catalog_version="2.0.0")],
        )


def test_invalid_control_id_format_is_rejected_without_normalization():
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        make_control("Invalid-Control")


def test_get_control_returns_definition_and_rejects_unknown_id():
    graph = load_dependency_graph()

    assert graph.get_control("identity_management").name == "Identity Management"
    with pytest.raises(UnknownControlError, match="unknown_control"):
        graph.get_control("unknown_control")


def test_direct_dependencies_are_sorted_and_can_be_filtered_by_type():
    graph = load_dependency_graph()

    all_dependencies = graph.get_direct_dependencies(
        "privileged_action_logging"
    )
    required = graph.get_direct_dependencies(
        "privileged_action_logging", DependencyType.REQUIRED
    )
    supporting = graph.get_direct_dependencies(
        "privileged_action_logging", DependencyType.SUPPORTING
    )

    assert [
        dependency.depends_on_control_id for dependency in all_dependencies
    ] == ["centralized_audit_logging", "privileged_access_management"]
    assert [dependency.depends_on_control_id for dependency in required] == [
        "centralized_audit_logging"
    ]
    assert [dependency.depends_on_control_id for dependency in supporting] == [
        "privileged_access_management"
    ]


def test_transitive_dependencies_exclude_query_and_have_no_duplicates():
    graph = load_dependency_graph()

    dependencies = graph.get_transitive_dependencies(
        "incident_response_readiness"
    )

    assert dependencies == [
        "centralized_audit_logging",
        "incident_alerting",
        "incident_response_policy",
        "incident_response_testing",
    ]
    assert "incident_response_readiness" not in dependencies
    assert len(dependencies) == len(set(dependencies))


def test_required_transitive_dependencies_exclude_supporting_only_paths():
    graph = load_dependency_graph()

    assert graph.get_transitive_dependencies(
        "privileged_action_logging", DependencyType.REQUIRED
    ) == ["centralized_audit_logging"]


def test_independent_control_has_no_dependencies():
    graph = load_dependency_graph()

    assert graph.get_direct_dependencies("soc2_status") == []
    assert graph.get_transitive_dependencies("soc2_status") == []


def test_unknown_control_query_is_rejected():
    graph = load_dependency_graph()

    with pytest.raises(UnknownControlError, match="unknown_control"):
        graph.get_transitive_dependencies("unknown_control")
    with pytest.raises(UnknownControlError, match="unknown_control"):
        graph.topologically_order_controls(["unknown_control"])


def test_topological_order_includes_prerequisites_before_dependents():
    graph = load_dependency_graph()

    ordered = graph.topologically_order_controls(
        ["privileged_action_logging"]
    )

    assert ordered == [
        "centralized_audit_logging",
        "identity_management",
        "role_based_access",
        "privileged_access_management",
        "privileged_action_logging",
    ]
    assert ordered.index("identity_management") < ordered.index(
        "role_based_access"
    )
    assert ordered.index("privileged_access_management") < ordered.index(
        "privileged_action_logging"
    )


def test_topological_order_is_deterministic_and_deduplicates_input():
    graph = load_dependency_graph()
    first = graph.topologically_order_controls(
        ["audit_readiness", "incident_response_readiness"]
    )
    second = graph.topologically_order_controls(
        [
            "incident_response_readiness",
            "audit_readiness",
            "audit_readiness",
        ]
    )

    assert first == second
    assert first == graph.topologically_order_controls(
        ["audit_readiness", "incident_response_readiness"]
    )
    assert len(first) == len(set(first))


def test_topological_order_can_be_limited_to_requested_controls():
    graph = load_dependency_graph()

    assert graph.topologically_order_controls(
        ["role_based_access", "privileged_access_management"],
        include_transitive_dependencies=False,
    ) == ["role_based_access", "privileged_access_management"]


def test_graph_module_has_no_policy_workflow_infrastructure_or_ai_imports():
    source_path = Path(dependency_graph_module.__file__)
    syntax_tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    prohibited_prefixes = (
        "core.policy",
        "core.fact_graph",
        "core.trust_packet",
        "fastapi",
        "langchain",
        "langgraph",
        "openai",
        "supabase",
    )
    assert not any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in imported_modules
        for prefix in prohibited_prefixes
    )


def test_graph_foundation_does_not_add_readiness_or_claim_output():
    dependencies = load_control_dependencies().dependencies

    assert "control_assessments" not in TrustPacket.model_fields
    assert all(
        set(dependency.model_dump())
        == {
            "control_id",
            "depends_on_control_id",
            "dependency_type",
            "reason",
        }
        for dependency in dependencies
    )
