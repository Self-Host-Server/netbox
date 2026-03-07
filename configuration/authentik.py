from os import environ

# Pull in OIDC settings from environment
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = environ.get("SOCIAL_AUTH_OIDC_OIDC_ENDPOINT")
SOCIAL_AUTH_OIDC_KEY = environ.get("SOCIAL_AUTH_OIDC_KEY")
SOCIAL_AUTH_OIDC_SECRET = environ.get("SOCIAL_AUTH_OIDC_SECRET")

_scope = environ.get("SOCIAL_AUTH_OIDC_SCOPE", "openid profile email roles")
SOCIAL_AUTH_OIDC_SCOPE = _scope.split(" ")

LOGOUT_REDIRECT_URL = environ.get("LOGOUT_REDIRECT_URL")

# Enable group/role sync pipeline (see custom_pipeline.py)
SOCIAL_AUTH_PIPELINE = (
    # Default pipelines
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "netbox.custom_pipeline.check_allowed_groups",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    # Custom pipelines (groups + roles from token)
    "netbox.custom_pipeline.add_groups",
    "netbox.custom_pipeline.remove_groups",
    "netbox.custom_pipeline.set_roles",
)
