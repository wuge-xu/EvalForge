from evalforge.infrastructure.persistence.base import (
    NAMING_CONVENTION,
    Base,
)


def test_base_uses_stable_constraint_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"
    assert NAMING_CONVENTION["fk"].startswith("fk_")
