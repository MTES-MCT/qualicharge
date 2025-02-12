"""Dashboard core annuaire entreprise API."""
import requests


class AnnuaireEntrepriseAPI:
    """Annuaire entreprise API client."""

    def __init__(self):
        """Initialize the API client."""
        self.api_url = "https://staging.entreprise.api.gouv.fr/v3/"
        # todo : add token in settings
        self.token = ""

    def _make_request(self, endpoint, params=None):
        """Make a request to the API."""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.api_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def get_entreprise_info(self, siren, attributes=None):
        """Get the enterprise information from the API."""
        # todo config context - recipient must be a SIREN
        context = "?context=test+API&object=test+API&recipient=10000001700010"
        # endpoint = f"insee/sirene/etablissements/{siren}"
        endpoint = "insee/sirene/unites_legales/552049447"

        params = {"attributes": attributes} if attributes else None
        return self._make_request(endpoint, params)


# TEST ...
api = AnnuaireEntrepriseAPI()
siren = "55204944776279"
entreprise_info = api.get_entreprise_info(siren, None)

# print(entreprise_info['data']['siret']) #siret
# print(entreprise_info['data']['enseigne']) # trade name
# print(entreprise_info['data']['activite_principale']["code"]) #naf
# print(entreprise_info['data']['unite_legale']["siren"]) #naf
# print(entreprise_info['data']['unite_legale']["personne_morale_attributs"]["raison_sociale"]) #name
# print(entreprise_info['data']['unite_legale']["forme_juridique"]["libelle"]) #name
# print(entreprise_info['data']['adresse']) #name

print(entreprise_info)
