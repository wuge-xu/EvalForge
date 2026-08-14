from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, delete, func, select
from sqlalchemy.orm import Session

from evalforge.application.config_snapshot import (
    build_config_snapshot,
)
from evalforge.application.experiment_service import (
    CreateExperimentCommand,
    DatasetVersionNotFoundError,
    EmptyDatasetVersionError,
    create_experiment,
)
from evalforge.core.config import get_settings
from evalforge.infrastructure.database import create_database_engine
from evalforge.infrastructure.persistence import (
    Dataset,
    DatasetVersion,
    Experiment,
    ExperimentCase,
    Project,
)
from evalforge.infrastructure.persistence import (
    TestCase as CaseModel,
)

pytestmark = pytest.mark.skipif(
    os.getenv("EVALFORGE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are disabled",
)


@dataclass(frozen=True, slots=True)
class SeedData:
    project_id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    test_case_ids: tuple[UUID, ...]


@pytest.fixture(scope="module")
def database_engine() -> Iterator[Engine]:
    engine = create_database_engine(get_settings())

    try:
        with engine.connect() as connection:
            connection.execute(select(1))

        yield engine
    finally:
        engine.dispose()


def seed_dataset(
    engine: Engine,
    *,
    case_count: int,
) -> SeedData:
    project_id = uuid4()
    dataset_id = uuid4()
    dataset_version_id = uuid4()
    test_case_ids = tuple(uuid4() for _ in range(case_count))
    suffix = project_id.hex[:12]

    with Session(engine) as session:
        project = Project(
            id=project_id,
            name=f"Experiment Service {suffix}",
            slug=f"experiment-service-{suffix}",
        )
        dataset = Dataset(
            id=dataset_id,
            project_id=project_id,
            name="regression-dataset",
        )
        dataset_version = DatasetVersion(
            id=dataset_version_id,
            dataset_id=dataset_id,
            version_number=1,
            content_hash="a" * 64,
        )

        session.add_all(
            [
                project,
                dataset,
                dataset_version,
            ]
        )

        session.add_all(
            [
                CaseModel(
                    id=test_case_id,
                    dataset_version_id=dataset_version_id,
                    external_id=f"case-{index:03d}",
                    question=f"Question {index}",
                    reference_answer=f"Answer {index}",
                    case_metadata={
                        "index": index,
                    },
                )
                for index, test_case_id in enumerate(
                    test_case_ids,
                    start=1,
                )
            ]
        )

        session.commit()

    return SeedData(
        project_id=project_id,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        test_case_ids=test_case_ids,
    )


def create_empty_project(engine: Engine) -> UUID:
    project_id = uuid4()
    suffix = project_id.hex[:12]

    with Session(engine) as session:
        session.add(
            Project(
                id=project_id,
                name=f"Empty Project {suffix}",
                slug=f"empty-project-{suffix}",
            )
        )
        session.commit()

    return project_id


def cleanup_project(
    engine: Engine,
    project_id: UUID,
) -> None:
    with Session(engine) as session:
        session.execute(delete(Experiment).where(Experiment.project_id == project_id))
        session.execute(delete(Project).where(Project.id == project_id))
        session.commit()


def test_create_experiment_expands_dataset_test_cases(
    database_engine: Engine,
) -> None:
    seed = seed_dataset(
        database_engine,
        case_count=3,
    )
    config: dict[str, object] = {
        "model": "mock-llm",
        "retrieval": {
            "top_k": 5,
        },
    }
    expected_snapshot = build_config_snapshot(config)

    try:
        with Session(database_engine) as session:
            with session.begin():
                result = create_experiment(
                    session,
                    CreateExperimentCommand(
                        project_id=seed.project_id,
                        dataset_version_id=seed.dataset_version_id,
                        name="Baseline",
                        config=config,
                    ),
                )

            experiment = session.get(
                Experiment,
                result.experiment_id,
            )
            assert experiment is not None

            experiment_cases = list(
                session.scalars(
                    select(ExperimentCase)
                    .where(ExperimentCase.experiment_id == result.experiment_id)
                    .order_by(ExperimentCase.test_case_id)
                )
            )

            assert result.case_count == 3
            assert result.config_hash == expected_snapshot.content_hash

            assert experiment.status == "pending"
            assert experiment.config_hash == expected_snapshot.content_hash
            assert experiment.config_snapshot == expected_snapshot.data

            assert len(experiment_cases) == 3
            assert {item.test_case_id for item in experiment_cases} == set(seed.test_case_ids)
            assert {item.status for item in experiment_cases} == {"pending"}
    finally:
        cleanup_project(
            database_engine,
            seed.project_id,
        )


def test_empty_dataset_version_is_rejected(
    database_engine: Engine,
) -> None:
    seed = seed_dataset(
        database_engine,
        case_count=0,
    )

    try:
        with Session(database_engine) as session:
            with pytest.raises(EmptyDatasetVersionError):
                create_experiment(
                    session,
                    CreateExperimentCommand(
                        project_id=seed.project_id,
                        dataset_version_id=seed.dataset_version_id,
                        name="Empty Dataset",
                        config={
                            "model": "mock-llm",
                        },
                    ),
                )

            count = session.scalar(
                select(func.count())
                .select_from(Experiment)
                .where(Experiment.project_id == seed.project_id)
            )

            assert count == 0
    finally:
        cleanup_project(
            database_engine,
            seed.project_id,
        )


def test_dataset_version_from_another_project_is_rejected(
    database_engine: Engine,
) -> None:
    seed = seed_dataset(
        database_engine,
        case_count=1,
    )
    other_project_id = create_empty_project(database_engine)

    try:
        with Session(database_engine) as session:
            with pytest.raises(DatasetVersionNotFoundError):
                create_experiment(
                    session,
                    CreateExperimentCommand(
                        project_id=other_project_id,
                        dataset_version_id=seed.dataset_version_id,
                        name="Cross Project",
                        config={
                            "model": "mock-llm",
                        },
                    ),
                )

            count = session.scalar(
                select(func.count())
                .select_from(Experiment)
                .where(Experiment.project_id == other_project_id)
            )

            assert count == 0
    finally:
        cleanup_project(
            database_engine,
            other_project_id,
        )
        cleanup_project(
            database_engine,
            seed.project_id,
        )


def test_caller_can_roll_back_created_experiment(
    database_engine: Engine,
) -> None:
    seed = seed_dataset(
        database_engine,
        case_count=2,
    )
    experiment_id: UUID | None = None

    try:
        with Session(database_engine) as session:
            try:
                with session.begin():
                    result = create_experiment(
                        session,
                        CreateExperimentCommand(
                            project_id=seed.project_id,
                            dataset_version_id=seed.dataset_version_id,
                            name="Rollback Test",
                            config={
                                "model": "mock-llm",
                            },
                        ),
                    )
                    experiment_id = result.experiment_id

                    count_inside_transaction = session.scalar(
                        select(func.count())
                        .select_from(ExperimentCase)
                        .where(ExperimentCase.experiment_id == result.experiment_id)
                    )

                    assert count_inside_transaction == 2

                    raise RuntimeError("force caller transaction rollback")
            except RuntimeError as exc:
                assert str(exc) == ("force caller transaction rollback")

        assert experiment_id is not None

        with Session(database_engine) as verification_session:
            experiment_count = verification_session.scalar(
                select(func.count()).select_from(Experiment).where(Experiment.id == experiment_id)
            )
            case_count = verification_session.scalar(
                select(func.count())
                .select_from(ExperimentCase)
                .where(ExperimentCase.experiment_id == experiment_id)
            )

            assert experiment_count == 0
            assert case_count == 0
    finally:
        cleanup_project(
            database_engine,
            seed.project_id,
        )
