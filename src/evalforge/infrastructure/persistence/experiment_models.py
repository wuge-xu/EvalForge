from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evalforge.infrastructure.persistence.base import Base
from evalforge.infrastructure.persistence.models import (
    DatasetVersion,
    Project,
    TestCase,
)


class Experiment(Base):
    __tablename__ = "experiments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="status_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "dataset_versions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    config_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    config_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped[Project] = relationship()
    dataset_version: Mapped[DatasetVersion] = relationship()

    cases: Mapped[list[ExperimentCase]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    metrics: Mapped[list[MetricResult]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    gate_results: Mapped[list[GateResult]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ExperimentCase(Base):
    __tablename__ = "experiment_cases"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "test_case_id",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name="status_valid",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="latency_non_negative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "experiments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    test_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "test_cases.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    output_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    output_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    experiment: Mapped[Experiment] = relationship(
        back_populates="cases",
    )
    test_case: Mapped[TestCase] = relationship()

    metrics: Mapped[list[MetricResult]] = relationship(
        back_populates="experiment_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MetricResult(Base):
    __tablename__ = "metric_results"
    __table_args__ = (
        CheckConstraint(
            "("
            "scope = 'experiment' AND experiment_case_id IS NULL"
            ") OR ("
            "scope = 'case' AND experiment_case_id IS NOT NULL"
            ")",
            name="scope_matches_case",
        ),
        Index(
            "uq_metric_results_experiment_metric",
            "experiment_id",
            "metric_name",
            "evaluator_name",
            unique=True,
            postgresql_where=text("experiment_case_id IS NULL"),
        ),
        Index(
            "uq_metric_results_case_metric",
            "experiment_case_id",
            "metric_name",
            "evaluator_name",
            unique=True,
            postgresql_where=text("experiment_case_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "experiments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    experiment_case_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "experiment_cases.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )
    scope: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    metric_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    evaluator_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    details: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    experiment: Mapped[Experiment] = relationship(
        back_populates="metrics",
    )
    experiment_case: Mapped[ExperimentCase | None] = relationship(
        back_populates="metrics",
    )


class GateResult(Base):
    __tablename__ = "gate_results"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "gate_name",
        ),
        CheckConstraint(
            "operator IN ('gte', 'lte', 'gt', 'lt', 'eq')",
            name="operator_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "experiments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    gate_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    metric_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    operator: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    observed_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    details: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    experiment: Mapped[Experiment] = relationship(
        back_populates="gate_results",
    )
