from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from evalforge.infrastructure.persistence import (
    Experiment,
    ExperimentCase,
    GateResult,
    MetricResult,
)


def _check_constraint_sql(model: type[object]) -> set[str]:
    table = model.__table__  # type: ignore[attr-defined]

    return {
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_experiment_status_constraint_is_registered() -> None:
    constraints = _check_constraint_sql(Experiment)

    assert "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')" in constraints


def test_experiment_case_constraints_are_registered() -> None:
    constraints = _check_constraint_sql(ExperimentCase)

    assert "status IN ('pending', 'running', 'completed', 'failed', 'skipped')" in constraints
    assert "latency_ms IS NULL OR latency_ms >= 0" in constraints


def test_experiment_case_is_unique_per_test_case() -> None:
    constraints = [
        constraint
        for constraint in ExperimentCase.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("experiment_id", "test_case_id")
        for constraint in constraints
    )


def test_metric_scope_constraint_is_registered() -> None:
    constraints = _check_constraint_sql(MetricResult)

    assert (
        "("
        "scope = 'experiment' AND experiment_case_id IS NULL"
        ") OR ("
        "scope = 'case' AND experiment_case_id IS NOT NULL"
        ")" in constraints
    )


def test_metric_partial_unique_indexes_are_registered() -> None:
    indexes = {
        index.name: index for index in MetricResult.__table__.indexes if isinstance(index, Index)
    }

    experiment_index = indexes["uq_metric_results_experiment_metric"]
    case_index = indexes["uq_metric_results_case_metric"]

    assert experiment_index.unique is True
    assert tuple(column.name for column in experiment_index.columns) == (
        "experiment_id",
        "metric_name",
        "evaluator_name",
    )

    assert (
        str(experiment_index.dialect_options["postgresql"]["where"]) == "experiment_case_id IS NULL"
    )

    assert case_index.unique is True
    assert tuple(column.name for column in case_index.columns) == (
        "experiment_case_id",
        "metric_name",
        "evaluator_name",
    )

    assert (
        str(case_index.dialect_options["postgresql"]["where"]) == "experiment_case_id IS NOT NULL"
    )


def test_gate_result_constraints_are_registered() -> None:
    constraints = _check_constraint_sql(GateResult)

    assert "operator IN ('gte', 'lte', 'gt', 'lt', 'eq')" in constraints

    unique_constraints = [
        constraint
        for constraint in GateResult.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("experiment_id", "gate_name")
        for constraint in unique_constraints
    )


def test_experiment_foreign_key_delete_policies() -> None:
    foreign_keys = {
        foreign_key.parent.name: foreign_key for foreign_key in Experiment.__table__.foreign_keys
    }

    assert foreign_keys["project_id"].ondelete == "RESTRICT"
    assert foreign_keys["dataset_version_id"].ondelete == "RESTRICT"


def test_experiment_case_foreign_key_delete_policies() -> None:
    foreign_keys = {
        foreign_key.parent.name: foreign_key
        for foreign_key in ExperimentCase.__table__.foreign_keys
    }

    assert foreign_keys["experiment_id"].ondelete == "CASCADE"
    assert foreign_keys["test_case_id"].ondelete == "RESTRICT"


def test_metric_and_gate_results_follow_experiment_lifecycle() -> None:
    metric_foreign_keys = {
        foreign_key.parent.name: foreign_key for foreign_key in MetricResult.__table__.foreign_keys
    }
    gate_foreign_keys = {
        foreign_key.parent.name: foreign_key for foreign_key in GateResult.__table__.foreign_keys
    }

    assert metric_foreign_keys["experiment_id"].ondelete == "CASCADE"
    assert metric_foreign_keys["experiment_case_id"].ondelete == "CASCADE"
    assert gate_foreign_keys["experiment_id"].ondelete == "CASCADE"
