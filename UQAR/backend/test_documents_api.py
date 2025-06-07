import pytest
from fastapi.testclient import TestClient
from fastapi import Depends, HTTPException, status
from pathlib import Path
import os

# Assuming app and other necessary components are accessible from these paths
# Adjust these imports based on your actual project structure
from app.main import app  # FastAPI app instance
from app.services.document_service import DocumentService
from app.models.user import User
from app.api.auth import get_current_active_user

# Initialize TestClient
client = TestClient(app)

# Dummy user data for authenticated requests
MOCK_USER_ID = 1
MOCK_USERNAME = "teststudent"
MOCK_USER_EMAIL = "teststudent@example.com"
MOCK_USER_ROLE = "STUDENT"

# --- Mocking Dependencies ---

@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Fixture to automatically override authentication for all tests in this module."""
    original_get_user = app.dependency_overrides.get(get_current_active_user)
    
    async def mock_get_current_active_user():
        return User(
            id=MOCK_USER_ID,
            username=MOCK_USERNAME,
            email=MOCK_USER_EMAIL,
            role=MOCK_USER_ROLE,
            is_active=True,
            hashed_password="mockpassword" # Add required fields for User model
        )
    
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    yield
    # Restore original dependency if it existed, otherwise remove override
    if original_get_user:
        app.dependency_overrides[get_current_active_user] = original_get_user
    else:
        del app.dependency_overrides[get_current_active_user]


# --- Test Cases ---

def test_download_document_success(mocker, tmp_path):
    """Test successful document download."""
    dummy_doc_id = 1
    original_filename = "test_document.txt"
    dummy_content = b"This is a test document."
    
    # Create a temporary directory for the dummy file
    # tmp_path is a pytest fixture providing a Path object to a temporary directory
    file_path = tmp_path / original_filename
    with open(file_path, "wb") as f:
        f.write(dummy_content)

    # Mock DocumentService.get_document_filepath
    mocker.patch(
        "app.api.documents.DocumentService.get_document_filepath",
        return_value=(str(file_path), original_filename),
    )

    response = client.get(f"/api/documents/download/{dummy_doc_id}")

    assert response.status_code == 200
    assert response.content == dummy_content
    # FastAPI FileResponse sets content-disposition like: 'attachment; filename="test_document.txt"'
    assert f'filename="{original_filename}"' in response.headers["content-disposition"]
    
    # Clean up the dummy file (tmp_path handles directory cleanup automatically)

def test_download_document_not_found_in_db(mocker):
    """Test document not found in database (service returns None)."""
    dummy_doc_id = 2

    # Mock DocumentService.get_document_filepath to simulate document not found
    mocker.patch(
        "app.api.documents.DocumentService.get_document_filepath",
        return_value=None, # Simulate document not found
    )

    response = client.get(f"/api/documents/download/{dummy_doc_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document non trouvé ou nom de fichier manquant"}

def test_download_document_file_not_exists_on_disk(mocker, tmp_path):
    """Test document metadata exists but file is missing from disk."""
    dummy_doc_id = 3
    original_filename = "missing_document.txt"
    
    # A file path that does not actually exist (or points to a non-existent file in tmp_path)
    non_existent_file_path = tmp_path / "definitely_not_here.txt"

    # Mock DocumentService.get_document_filepath to return path to a non-existent file
    mocker.patch(
        "app.api.documents.DocumentService.get_document_filepath",
        return_value=(str(non_existent_file_path), original_filename),
    )

    response = client.get(f"/api/documents/download/{dummy_doc_id}")

    # FileResponse will return 404 if the path it's given doesn't exist
    assert response.status_code == 404
    assert response.json() == {"detail": "Fichier non trouvé sur le serveur"}


def test_download_document_unauthenticated():
    """Test document download when user is not authenticated."""
    dummy_doc_id = 4
    
    # Temporarily remove the authentication override for this specific test
    original_get_user_override = app.dependency_overrides.pop(get_current_active_user, None)

    # If your auth system correctly raises HTTPException(status.HTTP_401_UNAUTHORIZED...)
    # when get_current_active_user is called without valid credentials (which it should by default)
    response = client.get(f"/api/documents/download/{dummy_doc_id}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 
    # Or 403 depending on how your default unauthenticated access is handled by FastAPI/Starlette
    # The specific detail message might vary based on your auth setup.
    # assert response.json()["detail"] == "Not authenticated"

    # Restore the override if it was present
    if original_get_user_override:
        app.dependency_overrides[get_current_active_user] = original_get_user_override

# It's good practice to ensure the dependency override is cleaned up after the module tests run
# The fixture with `yield` should handle this for most cases.
# If specific tests need different auth states, they can manage app.dependency_overrides locally.

# To run these tests:
# Ensure pytest and pytest-mock are installed: pip install pytest pytest-mock
# Navigate to the UQAR/backend directory in your terminal
# Run: PYTHONPATH=. pytest test_documents_api.py
# (PYTHONPATH=. assumes your 'app' module is directly under UQAR/backend)
# If 'app' is inside 'UQAR/backend/app', then run from UQAR/backend: pytest test_documents_api.py
# (pytest should automatically find the 'app' module if tests are in the same root or if 'app' is installed/in PYTHONPATH)

# Note on imports:
# If test_documents_api.py is in UQAR/backend/tests/ and your app is in UQAR/backend/app/
# then imports might look like:
# from ..app.main import app
# from ..app.services.document_service import DocumentService
# from ..app.models.user import User
# from ..app.api.auth import get_current_active_user
# This example assumes test_documents_api.py is at UQAR/backend/test_documents_api.py
# and 'app' is a directory UQAR/backend/app/
# For the provided file path, the imports are written as if 'app' is a top-level module in PYTHONPATH.
# Adjust if your structure is UQAR/backend/app and UQAR/backend/tests.
# The command `PYTHONPATH=. pytest test_documents_api.py` from `UQAR/backend` would make `app` importable.
# If `test_documents_api.py` is inside `UQAR/backend/app/tests/`, then use relative imports.
# Let's assume the file is created at `UQAR/backend/test_documents_api.py` for now.

# A common structure:
# UQAR/
#   backend/
#     app/
#       __init__.py
#       main.py
#       api/
#       models/
#       services/
#     tests/  <-- test files here
#       __init__.py
#       test_documents_api.py
#     pytest.ini
#     .env
#
# If this is the case, then `from app.main import app` would be `from ..main import app` if run from `tests` dir,
# or `from app.main import app` if `PYTHONPATH` includes `UQAR/backend`.
# The current code assumes `PYTHONPATH` is set to `UQAR/backend` or `test_documents_api.py` is in `UQAR/backend`.
# For the sake of this task, I will assume the file is created at UQAR/backend/test_documents_api.py and the `app` module is in UQAR/backend/app.

# Final check on User model fields for the mock:
# The User model in `UQAR/backend/app/models/user.py` likely has more fields.
# The mock_get_current_active_user should return a User instance with all required fields.
# Typical fields: id, username, email, full_name, role, is_active, hashed_password, created_at, updated_at.
# For the mock, only essential fields for auth logic (id, role, is_active) plus any non-nullable fields are strictly needed.
# Added `hashed_password` as it's often non-nullable.
