"""Dashboard core helpers."""

from typing import Optional

from apps.auth.models import DashboardUser
from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.annuaire_entreprise_api.clients import AnnuaireDesEntreprises
from apps.core.models import Entity
from apps.core.validators import validate_siret


def sync_entity_from_siret(siret: str, user: Optional[DashboardUser] = None) -> Entity:
    """Retrieve, Update or create and populate entity.

    Retrieve and populate entity data based on SIRET input.
    The function uses an external API to fetch company information and address using
    the provided SIRET number.
    If the entity does not already exist in the database, it will be created.
    Optionally associates a user with the entity.

    Arguments:
        siret (str): The SIRET number used to identify and fetch the company's
        information.
        user (Optional[User]): A user instance to be associated with the created or
        updated entity. Defaults to None.

    Returns:
        Entity: The created or updated instance of the Entity model.
    """
    validate_siret(siret)
    siren: str = siret[:9]

    ade = AnnuaireDesEntreprises()

    company_info: CompanyInformationAdapter = ade.company_details(siren)
    company_address: CompanyAddressAdapter = ade.company_address(
        company_info.siret_head_office
    )

    entity, created = Entity.objects.update_or_create(
        name=company_info.name,
        siret=siret,
        legal_form=company_info.legal_form,
        naf=company_info.naf,
        address_1=company_address.address_1,
        address_2=company_address.address_2,
        address_city=company_address.city,
        address_zip_code=company_address.zip_code,
        defaults={"name": company_info.name, "siret": siret},
    )

    if user:
        entity.users.add(user)

    return entity
