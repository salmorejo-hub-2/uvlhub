import pytest
from app import db
from app.modules.conftest import login, logout
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DataSet, DSMetaData
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.hubfile.models import Hubfile

@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Sets up test data, creating users, profiles, datasets, models, and associated files.
    Cleans up the data after the test is complete.

    user_test = user with dataset and UVL file
    user_test2 = user without any dataset
    """
    with test_client.application.app_context():
        user_test = User(email='user@example.com', password='test1234')
        user_test2 = User(email='user2@example.com', password='test1234')
        
        db.session.add_all([user_test, user_test2])
        db.session.commit()

        profiles = [
            UserProfile(user_id=user_test.id, name="Name", surname="Surname"),
            UserProfile(user_id=user_test2.id, name="Name", surname="Surname")
        ]
        db.session.add_all(profiles)
        db.session.commit()

        ds_metadata1 = DSMetaData(
            title="Test Dataset",
            publication_type="NONE",
            description="This is a test dataset"
        )

        db.session.add(ds_metadata1)
        db.session.commit()

        dataset1 = DataSet(user_id=user_test.id, ds_meta_data_id=ds_metadata1.id)

        db.session.add(dataset1)
        db.session.commit()

        feature_model = FeatureModel(data_set_id=dataset1.id)
        db.session.add(feature_model)
        db.session.commit()

        fm_metadata = FMMetaData(
            uvl_filename="test_model.uvl",
            title="Test Feature Model",
            description="This is a test feature model",
            publication_type="NONE"
        )
        db.session.add(fm_metadata)
        db.session.commit()

        feature_model.fm_meta_data_id = fm_metadata.id
        db.session.commit()

        uvl_file = Hubfile(
            name="test_model.uvl",
            checksum="test_checksum",
            size=1024,
            feature_model_id=feature_model.id
        )
        db.session.add(uvl_file)
        db.session.commit()

    yield test_client

    with test_client.application.app_context():
        db.session.expunge_all()
        try:
            db.session.delete(uvl_file)
            db.session.delete(fm_metadata)
            db.session.delete(feature_model)
            db.session.delete(dataset1)
            db.session.delete(ds_metadata1)
            db.session.delete(profiles[0])
            db.session.delete(profiles[1])
            db.session.delete(user_test)
            db.session.delete(user_test2)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error during teardown: {e}")

def test_dataset_with_uvl_file_display(test_client):
    """
    Verifies that a user with an associated UVL file sees the file and the download button on the profile page.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login failed for user with UVL file."

    response = test_client.get("/profile/summary")
    assert response.status_code == 200, "Failed to access profile summary page."

    assert b"test_model.uvl" in response.data, "UVL file not displayed for user with UVL file."
    assert b"Download" in response.data, "Download button not displayed for user with UVL file."

    logout(test_client)

def test_dataset_without_dataset_file_display(test_client):
    """
    Verifies that a user without any datasets or UVL file does not see the file or the download button on the profile page and instead sees 'No datasets found'.
    """
    login_response = login(test_client, "user2@example.com", "test1234")
    assert login_response.status_code == 200, "Login failed for user without any datasets."

    response = test_client.get("/profile/summary")
    assert response.status_code == 200, "Failed to access profile summary page."

    assert b"test_model.uvl" not in response.data, "UVL file displayed incorrectly for user without any datasets."
    assert b"Download" not in response.data, "Download button displayed incorrectly for user without any datasets."
    assert b"No datasets found" in response.data, "Message 'No datasets found' not displayed for user without datasets."

    logout(test_client)

def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user2@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected 'Edit profile' content is not present on the page."

    logout(test_client)
