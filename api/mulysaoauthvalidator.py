from oauth2_provider.oauth2_validators import OAuth2Validator


class MulysaOAuth2Validator(OAuth2Validator):
    """
    For providing more data to keycloack
    """

    # keep pre 2.0 behaviour for now
    # see https://django-oauth-toolkit.readthedocs.io/en/latest/changelog.html#id7
    oidc_claim_scope = None

    def get_additional_claims(self, request):
        """
        give email, firstname and lastname in oid claims data
        """
        return {
            "sub": request.user.email,
            "email": request.user.email,
            "firstName": request.user.first_name,
            "lastName": request.user.last_name,
        }
