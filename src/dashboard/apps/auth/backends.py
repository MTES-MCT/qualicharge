"""Dashboard auth middleware."""

import requests
from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as MozillaOIDCAuthenticationBackend,
)
from mozilla_django_oidc.auth import default_username_algo


class OIDCAuthenticationBackend(MozillaOIDCAuthenticationBackend):
    """Override mozilla_django_oidc's authentication."""

    # Bluntly stolen from betagouv/gestion-des-subventions-locales.
    # Thanks to Agnès Haasser for the tip.
    # https://github.com/betagouv/gestion-des-subventions-locales/blob/develop/gsl_oidc/backends.py

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details dictionary.

        Overridden original method to allow ProConnect tokens to be decoded:
        JSON decoding of JWT content is problematic with ProConnect,
        which returns it in JWT format (content-type: application/jwt)
        """
        user_response = requests.get(
            self.OIDC_OP_USER_ENDPOINT,
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )

        user_response.raise_for_status()
        try:
            # default case: JWT token is `application/json`
            return user_response.json()
        except requests.exceptions.JSONDecodeError:
            # if except, it is assumed to be a JWT token in `application/jwt` format
            # as happens for ProConnect.
            return self.verify_token(user_response.text)

    def get_data_for_user_create_and_update(self, claims):
        """Return data for user creation and update."""
        return {
            "email": claims.get("email"),
            "first_name": claims.get("given_name", ""),
            "last_name": claims.get("usual_name", ""),
            "siret": claims.get("siret", ""),
        }

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified username."""
        username = self.get_username(claims)
        return self.UserModel.objects.filter(username=username)

    def create_user(self, claims):
        """Return object for a newly created user account."""
        username = self.get_username(claims)
        return self.UserModel.objects.create_user(
            username, **self.get_data_for_user_create_and_update(claims)
        )

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user."""
        for key, value in self.get_data_for_user_create_and_update(claims).items():
            if value:
                user.__setattr__(key, value)
        user.save()
        return user

    def get_username(self, claims):
        """Generate username based on claims."""
        return default_username_algo(claims.get("sub"))
