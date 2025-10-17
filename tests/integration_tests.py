import json
import pytest
import requests


@pytest.fixture
def base_url():
    """
    Reads server info from config.json and provides
    the base URL for tests.
    """

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        host = config["server"]["host"]
        port = config["server"]["port"]

    # Construct and return the URL
    return f"https://{host}:{port}"


# HAPPY PATH TESTS


def get_no_verify(base_url):
    """
    Helper method to dry up https/timeout stuff
    """
    return requests.get(base_url, verify=False, timeout=4)


def test_get_all_notes_endpoint_no_authentication(base_url):
    """
    Tests that the GET /notes endpoint redirects users to /login if
    they're not authenticated
    """
    response = get_no_verify(f"{base_url}/notes")
    assert response.history  # exists
    assert response.status_code == 200
    assert response.url != base_url


# SAD PATH TESTING


def test_no_http(base_url):
    """
    Tests that the site is unreachable on http
    """

    with pytest.raises(requests.exceptions.SSLError):
        _ = requests.get(f"{base_url[0:5]}{base_url[5:]}/", timeout=4)


# def test_get_all_notes_endpoint_bad_authentication(base_url):
#     """
#     Tests that the GET /notes endpoint redirects users to /login if
#     their auth token is bad
#     """
#     # NOTE: add a garbage session token
#     response = get_no_verify(f"{base_url}/notes")
#     assert response.status_code != 200


# def test_delete_note_unauthenticated_fails(base_url):
#     """
#     Tests whether an unauthenticated user can delete a note
#     """
#
#
# def test_create_note_unauthenticated_fails(base_url):
#     """
#     Tests whether an unauthenticated user can create a note
#     """
#
#
# def test_edit_note_unauthenticated_fails(base_url):
#     """
#     Tests whether an unauthenticated user can edit a note
#     """
