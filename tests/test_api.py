import pytest
import requests
import json
import os


@pytest.fixture
def base_url():
    """
    Reads server info from config.json and provides the base URL for tests.
    """

    with open("config.json", "r") as f:
        config = json.load(f)
    if os.path.exists("/.dockerenv"):
        host = config["server"]["host_on_docker"]
    else:
        host = config["server"]["host_off_docker"]
    port = config["server"]["port"]

    # Construct and return the URL
    return f"https://{host}:{port}"


# def test_no_http(base_url):
#     """
#     Tests that the site is unreachable on http
#     """
#
#     response = requests.get(f"{base_url[0:5]}{base_url[5:]}/")
#     assert response.status_code == 1


def test_get_index(base_url):
    """
    Tests that the GET / endpoint is reachable
    """
    response = requests.get(f"{base_url}/", verify=False)
    assert response.status_code == 200
    assert response.is_redirect


def test_get_all_notes_endpoint_no_authentication(base_url):
    """
    Tests that the GET /notes endpoint redirects users to /login if they're not authenticated
    """
    response = requests.get(f"{base_url}/notes", verify=False)
    assert response.status_code == 200


def test_create_new_note_endpoint(base_url):
    """
    Tests that a new note can be created via the POST /api/notes endpoint.
    """
    new_note_payload = {
        "title": "My Test Note",
        "body": "This is the body of the test note.",
    }
    response = requests.post(f"{base_url}/notes", verify=False)
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["title"] == new_note_payload["title"]
