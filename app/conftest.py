from app import create_app
import pytest

# configure a flask testing app

@pytest.fixture()
def app():
    # create an app for testing
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    # other setup can go here
    yield app
    # clean up / reset resources here

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
