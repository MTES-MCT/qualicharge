"""App HTTP client pytest fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from qualicharge.api.v1 import app
from qualicharge.api.v1.routers.dynamic import get_pdc_id
from qualicharge.auth.factories import GroupFactory, IDTokenFactory, UserFactory
from qualicharge.auth.oidc import get_token, get_user_from_db
from qualicharge.auth.schemas import UserGroup


@pytest.fixture
def client():
    """A test client configured for the /api/v1 application."""
    yield TestClient(app)


@pytest.fixture
def client_auth(
    request, db_session: Session, id_token_factory: IDTokenFactory = IDTokenFactory
):
    """An authenticated test client configured for the /api/v1 application.

    Parameter:

        `request.param` is supposed to be a (`persist`, `fields`) tuple representing
        the user that will perform the request, with:

            * `persist` (`bool`): wether to persist or not the user
            * `fields` (`dict`): input field values for the user to create

    Note that by default, we will persist a superuser in database.
    """
    GroupFactory.__session__ = db_session
    UserFactory.__session__ = db_session

    persist = True
    fields = {
        "email": "john@doe.com",
        "is_superuser": True,
        "is_active": True,
        "is_staff": True,
    }
    if hasattr(request, "param"):
        (persist, extras) = request.param
        fields.update(extras)
    user = UserFactory.build(**fields)
    if persist:
        group = GroupFactory.create_sync(name="administrators")
        user = UserFactory.create_sync(**user.model_dump())
        db_session.add(UserGroup(user_id=user.id, group_id=group.id))

    app.dependency_overrides[get_token] = lambda: id_token_factory.build(
        email=user.email, scope=" ".join(user.scopes)
    )
    yield TestClient(app)
    app.dependency_overrides = {}


@pytest.fixture(autouse=True)
def clear_lru_cache():
    """Taken from codeinthehole.

    https://til.codeinthehole.com/posts/how-to-inspect-and-clear-pythons-functoolslrucache/
    """
    # Execute the test...
    yield

    # Clear the LRU cache.
    get_user_from_db.cache_clear()
    get_pdc_id.cache_clear()
