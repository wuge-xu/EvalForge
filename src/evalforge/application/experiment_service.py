from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from evalforge.application.config_snapshot import (
    build_config_snapshot,
)
from evalforge.infrastructure.persistence import (
    Dataset,
    DatasetVersion,
    Experiment,
    ExperimentCase,
    TestCase,
)


class ExperimentCreationError(Exception):
    """Base error for experiment creation failures."""


class DatasetVersionNotFoundError(ExperimentCreationError):
    """Raised when the requested dataset version is unavailable."""


class EmptyDatasetVersionError(ExperimentCreationError):
    """Raised when a dataset version contains no test cases."""


@dataclass(frozen=True, slots=True)
class CreateExperimentCommand:
    project_id: UUID
    dataset_version_id: UUID
    name: str
    config: dict[str, object]


@dataclass(frozen=True, slots=True)
class CreateExperimentResult:
    experiment_id: UUID
    config_hash: str
    case_count: int


def create_experiment(
    session: Session,
    command: CreateExperimentCommand,
) -> CreateExperimentResult:
    dataset_version = session.scalar(
        select(DatasetVersion)
        .join(
            Dataset,
            Dataset.id == DatasetVersion.dataset_id,
        )
        .where(
            DatasetVersion.id == command.dataset_version_id,
            Dataset.project_id == command.project_id,
        )
    )

    if dataset_version is None:
        raise DatasetVersionNotFoundError("dataset version does not exist in the requested project")

    test_case_ids = list(
        session.scalars(
            select(TestCase.id)
            .where(TestCase.dataset_version_id == command.dataset_version_id)
            .order_by(
                TestCase.external_id,
                TestCase.id,
            )
        )
    )

    if not test_case_ids:
        raise EmptyDatasetVersionError("dataset version contains no test cases")

    snapshot = build_config_snapshot(command.config)

    experiment = Experiment(
        project_id=command.project_id,
        dataset_version_id=command.dataset_version_id,
        name=command.name,
        status="pending",
        config_snapshot=snapshot.data,
        config_hash=snapshot.content_hash,
    )

    session.add(experiment)
    session.flush()

    experiment_cases = [
        ExperimentCase(
            experiment_id=experiment.id,
            test_case_id=test_case_id,
            status="pending",
        )
        for test_case_id in test_case_ids
    ]

    session.add_all(experiment_cases)
    session.flush()

    return CreateExperimentResult(
        experiment_id=experiment.id,
        config_hash=snapshot.content_hash,
        case_count=len(experiment_cases),
    )
