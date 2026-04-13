"""Tests for QualiCharge Afirev models."""

import pytest

from qualicharge.afirev.models import (
    AfirevPrefix,
    AfirevPrefixStatusEnum,
    AfirevPrefixTypeEnum,
)
from qualicharge.schemas.core import (
    OperationalUnit,
    OperationalUnitStatusEnum,
    OperationalUnitTypeEnum,
)


@pytest.mark.parametrize(
    "p_status,ou_status",
    (
        (AfirevPrefixStatusEnum.ACTIVE, OperationalUnitStatusEnum.ACTIVE),
        (
            AfirevPrefixStatusEnum.AWAITING_PAYMENT,
            OperationalUnitStatusEnum.AWAITING_PAYMENT,
        ),
        (AfirevPrefixStatusEnum.INACTIVE, OperationalUnitStatusEnum.INACTIVE),
        (AfirevPrefixStatusEnum.SUSPENDED, OperationalUnitStatusEnum.SUSPENDED),
        (AfirevPrefixStatusEnum.UNKNOWN, None),
    ),
)
@pytest.mark.parametrize(
    "p_type,ou_type",
    (
        (AfirevPrefixTypeEnum.BOTH, OperationalUnitTypeEnum.BOTH),
        (AfirevPrefixTypeEnum.CHARGE, OperationalUnitTypeEnum.CHARGING),
        (AfirevPrefixTypeEnum.MOBILITY, OperationalUnitTypeEnum.MOBILITY),
    ),
)
def test_afirevprefix_to_operational_unit(p_status, ou_status, p_type, ou_type):
    """Test the AfirevPrefix model `to_operational_unit` method."""
    operational_unit = AfirevPrefix(
        prefixId="FRFOO",
        name="Foo",
        amenageurName="Foo inc.",
        exploitantName="Bar inc.",
        type=p_type,
        status=p_status,
    ).to_operational_unit()
    expected = OperationalUnit(
        code="FRFOO",
        name="Foo",
        type=ou_type,
        status=ou_status,
        amenageur="Foo inc.",
        exploitant="Bar inc.",
    )
    excluded_fields = {"id", "created_at", "updated_at"}
    assert operational_unit.model_dump(exclude=excluded_fields) == expected.model_dump(
        exclude=excluded_fields
    )


@pytest.mark.parametrize(
    "p_status,ou_status",
    (
        (AfirevPrefixStatusEnum.ACTIVE, OperationalUnitStatusEnum.ACTIVE),
        (
            AfirevPrefixStatusEnum.AWAITING_PAYMENT,
            OperationalUnitStatusEnum.AWAITING_PAYMENT,
        ),
        (AfirevPrefixStatusEnum.INACTIVE, OperationalUnitStatusEnum.INACTIVE),
        (AfirevPrefixStatusEnum.SUSPENDED, OperationalUnitStatusEnum.SUSPENDED),
        (AfirevPrefixStatusEnum.UNKNOWN, None),
    ),
)
@pytest.mark.parametrize(
    "p_type,ou_type",
    (
        (AfirevPrefixTypeEnum.BOTH, OperationalUnitTypeEnum.BOTH),
        (AfirevPrefixTypeEnum.CHARGE, OperationalUnitTypeEnum.CHARGING),
        (AfirevPrefixTypeEnum.MOBILITY, OperationalUnitTypeEnum.MOBILITY),
    ),
)
def test_afirevprefix_from_operational_unit(p_status, ou_status, p_type, ou_type):
    """Test the AfirevPrefix model `from_operational_unit` method."""
    prefix = AfirevPrefix.from_operational_unit(
        OperationalUnit(
            code="FRFOO",
            name="Foo",
            type=ou_type,
            status=ou_status,
            amenageur="Foo inc.",
            exploitant="Bar inc.",
        )
    )
    expected = AfirevPrefix(
        prefixId="FRFOO",
        name="Foo",
        amenageurName="Foo inc.",
        exploitantName="Bar inc.",
        type=p_type,
        status=p_status,
    )
    assert prefix == expected
