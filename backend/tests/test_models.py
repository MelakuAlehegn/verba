from app.models import Base, OAuthAccount, User, UserSession, UserSetting


def test_auth_models_register_expected_tables() -> None:
    assert {User.__tablename__, UserSetting.__tablename__, UserSession.__tablename__, OAuthAccount.__tablename__}.issubset(
        Base.metadata.tables.keys()
    )
