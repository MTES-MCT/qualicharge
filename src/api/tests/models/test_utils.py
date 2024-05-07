"""QualiCharge models utilities tests."""

from qualicharge.factories.static import StatiqueFactory
from qualicharge.schemas import Amenageur


def test_statique_model_get_fields_for_schema():
    """Test the Statique model get_fields_for_schema method."""
    statique = StatiqueFactory.build()

    assert statique.get_fields_for_schema(Amenageur) == {
        "nom_amenageur": statique.nom_amenageur,
        "siren_amenageur": statique.siren_amenageur,
        "contact_amenageur": statique.contact_amenageur,
    }

    amenageur = Amenageur(**statique.get_fields_for_schema(Amenageur))
    assert amenageur.nom_amenageur == statique.nom_amenageur
    assert amenageur.siren_amenageur == statique.siren_amenageur
    assert amenageur.contact_amenageur == statique.contact_amenageur
