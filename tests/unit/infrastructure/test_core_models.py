from sqlalchemy import CheckConstraint, UniqueConstraint, inspect

from evalforge.infrastructure.persistence import (
    Base,
    Dataset,
    DatasetVersion,
    Project,
)
from evalforge.infrastructure.persistence import TestCase as CaseModel


def test_core_tables_are_registered() -> None:
    assert {
        "projects",
        "datasets",
        "dataset_versions",
        "test_cases",
    }.issubset(Base.metadata.tables)


def test_project_slug_is_unique() -> None:
    constraints = [
        constraint
        for constraint in Project.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("slug",)
        for constraint in constraints
    )


def test_dataset_name_is_unique_within_project() -> None:
    constraints = [
        constraint
        for constraint in Dataset.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("project_id", "name")
        for constraint in constraints
    )


def test_dataset_version_has_version_constraints() -> None:
    constraints = DatasetVersion.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("dataset_id", "version_number")
        for constraint in constraints
    )

    assert any(
        isinstance(constraint, CheckConstraint) and str(constraint.sqltext) == "version_number > 0"
        for constraint in constraints
    )


def test_test_case_external_id_is_unique_per_version() -> None:
    constraints = [
        constraint
        for constraint in CaseModel.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("dataset_version_id", "external_id")
        for constraint in constraints
    )


def test_core_relationships_are_registered() -> None:
    project_relationships = inspect(Project).relationships
    dataset_relationships = inspect(Dataset).relationships
    version_relationships = inspect(DatasetVersion).relationships
    case_relationships = inspect(CaseModel).relationships

    assert "datasets" in project_relationships
    assert "project" in dataset_relationships
    assert "versions" in dataset_relationships
    assert "dataset" in version_relationships
    assert "test_cases" in version_relationships
    assert "dataset_version" in case_relationships


def test_test_case_metadata_uses_database_metadata_column() -> None:
    assert CaseModel.case_metadata.property.columns[0].name == "metadata"
