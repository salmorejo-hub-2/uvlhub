import os
from unittest.mock import patch
from flask import url_for
import pytest
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import (
    DataSet, DSMetaData, DatasetStatus, PublicationType
)
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.dataset.routes import dataset_service
from app.modules.dataset.services import DataSetService, DSMetaDataService
from app.modules.conftest import login, logout
from app import create_app


@pytest.fixture(scope="function")
def test_client():

    test_app = create_app("testing")

    test_app.config['SERVER_NAME'] = 'localhost'
    test_app.config['APPLICATION_ROOT'] = '/'
    test_app.config['PREFERRED_URL_SCHEME'] = 'http'

    with test_app.app_context():

        db.drop_all()
        db.create_all()
        user_test = User(email='user_dataset@example.com', password='test1234')
        db.session.add(user_test)
        db.session.commit()

        ds_meta_data = DSMetaData(
            title="UnitTest Dataset",
            description="Dataset creado para pruebas unitarias.",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            publication_doi="10.1234/dataset.unittest",
            dataset_doi=None,
            tags="unit,test",
            dataset_status=DatasetStatus.UNSTAGED
        )
        db.session.add(ds_meta_data)
        db.session.commit()

        dataset_test = DataSet(user_id=user_test.id, ds_meta_data_id=ds_meta_data.id)
        db.session.add(dataset_test)
        db.session.commit()

        fm_meta_data = FMMetaData(
            uvl_filename="example.uvl",
            title="Test Feature Model",
            description="Feature model for UVL preview test.",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            publication_doi="10.1234/featuremodel.unittest"
        )
        db.session.add(fm_meta_data)
        db.session.commit()

        feature_model = FeatureModel(data_set_id=dataset_test.id, fm_meta_data_id=fm_meta_data.id)
        db.session.add(feature_model)
        db.session.commit()

        uploads_path = os.path.join('uploads', f'user_{user_test.id}', f'dataset_{dataset_test.id}')
        os.makedirs(uploads_path, exist_ok=True)
        file_path = os.path.join(uploads_path, "example.uvl")
        with open(file_path, "w") as f:
            f.write("// Example UVL file content for preview test\n")

        with test_app.test_client() as testing_client:
            yield testing_client

        db.session.remove()
        db.drop_all()


@pytest.fixture
def datasetservice():
    return DataSetService()


@pytest.fixture(scope="function")
def mock_dataset_service():
    with patch('app.modules.dataset.services.DataSetService') as mock:
        yield mock


def test_dataset_creation(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email='user_dataset@example.com').first()
        dataset = DataSet.query.first()

        assert user is not None, "Usuario de prueba no encontrado."
        assert dataset is not None, "Dataset no creado."
        assert dataset.ds_meta_data is not None, "DSMetaData no asociada al dataset."
        assert dataset.ds_meta_data.title == "UnitTest Dataset"
        assert dataset.ds_meta_data.dataset_status == DatasetStatus.UNSTAGED
        assert dataset.ds_meta_data.dataset_doi is None


def test_uvl_preview(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email='user_dataset@example.com').first()
        assert user is not None, "Usuario de prueba no encontrado."
        response = login(test_client, user.email, 'test1234')
        assert response.status_code == 200, "Error al iniciar sesión."
        feature_model = FeatureModel.query.first()
        assert feature_model is not None, "Modelo de características no encontrado."
        uploads_path = os.path.join('uploads', f'user_{user.id}', f'dataset_{feature_model.data_set_id}')
        file_path = os.path.join(uploads_path, "example.uvl")
        assert os.path.exists(file_path), f"Archivo UVL no encontrado: {file_path}"
        with open(file_path, "r") as f:
            content = f.read()
        assert "// Example UVL file content for preview test" in content, "Contenido del archivo UVL no coincide."
        response = logout(test_client)
        assert response.status_code == 200, "Error al cerrar sesión."


def test_dataset_to_dict(test_client):

    with test_client.application.app_context():

        with test_client.application.test_request_context('/'):
            dataset = DataSet.query.first()
            dataset_dict = dataset.to_dict()

            assert isinstance(dataset_dict, dict), "El método to_dict debe devolver un diccionario."
            assert 'title' in dataset_dict, "El diccionario debe incluir 'title'."
            assert 'id' in dataset_dict, "El diccionario debe incluir 'id'."
            assert 'authors' in dataset_dict, "El diccionario debe incluir 'authors'."
            assert dataset_dict['title'] == dataset.ds_meta_data.title


def test_dsmetadata_service(test_client):

    with test_client.application.app_context():
        dsmetadata_service = DSMetaDataService()
        dataset = DataSet.query.first()
        meta_id = dataset.ds_meta_data.id

        new_doi = "10.9999/updated.doi"
        dsmetadata_service.update(meta_id, dataset_doi=new_doi)
        db.session.refresh(dataset.ds_meta_data)

        assert dataset.ds_meta_data.dataset_doi == new_doi, "El DOI de DSMetaData no se actualizó correctamente."


def test_stage_dataset_positive(test_client, datasetservice):

    with test_client.application.app_context():
        dataset = DataSet.query.first()
        dataset_id = dataset.id

        datasetservice.set_dataset_to_staged(dataset_id)
        db.session.refresh(dataset)

        assert dataset.ds_meta_data.dataset_status == DatasetStatus.STAGED, \
            "El dataset no se pudo pasar a estado STAGED."


def test_stage_dataset_negative(test_client, datasetservice):

    with test_client.application.app_context():
        with pytest.raises(ValueError) as excinfo:
            dataset = DataSet.query.first()
            dataset_id = dataset.id

            datasetservice.set_dataset_to_staged(dataset_id)
            db.session.refresh(dataset)

            # Comprobamos que no se puede volver a sincronizar el mismo dataset

            datasetservice.set_dataset_to_staged(dataset_id)
            db.session.refresh(dataset)
        assert str(excinfo.value) == "Dataset is not in 'UNSTAGED' status", \
            "No debería volver a sincronizar un dataset ya en STAGED"


def test_unstage_dataset_positive(test_client, datasetservice):

    with test_client.application.app_context():
        dataset = DataSet.query.first()
        dataset_id = dataset.id

        # Poniendo el dataset de prueba en estado STAGED
        datasetservice.set_dataset_to_staged(dataset_id)
        db.session.refresh(dataset)
        assert dataset.ds_meta_data.dataset_status == DatasetStatus.STAGED, \
            "El dataset no se pudo pasar a estado STAGED."

        datasetservice.set_dataset_to_unstaged(dataset_id)
        db.session.refresh(dataset)

        assert dataset.ds_meta_data.dataset_status == DatasetStatus.UNSTAGED, \
            "El dataset no se pudo pasar a estado UNSTAGED."


def test_unstage_dataset_negative(test_client, datasetservice):

    with test_client.application.app_context():
        with pytest.raises(ValueError) as excinfo:
            dataset = DataSet.query.first()
            dataset_id = dataset.id

            # Comprobamos que no se puede volver a sincronizar el mismo dataset

            datasetservice.set_dataset_to_unstaged(dataset_id)
            db.session.refresh(dataset)
        assert str(excinfo.value) == "Dataset is not in 'STAGED' status", \
            "No debería volver a dessincronizar un dataset ya en UNSTAGED"


def test_publish_all_datasets_positive(test_client, datasetservice):

    with test_client.application.app_context():
        dataset = DataSet.query.first()
        dataset_id = dataset.id

        # Poniendo el dataset de prueba en estado STAGED
        datasetservice.set_dataset_to_staged(dataset_id)
        db.session.refresh(dataset)
        assert dataset.ds_meta_data.dataset_status == DatasetStatus.STAGED, \
            "El dataset no se pudo pasar a estado STAGED."

        datasetservice.publish_datasets(User.query.first().id)
        db.session.refresh(dataset)

        assert dataset.ds_meta_data.dataset_status == DatasetStatus.PUBLISHED, \
            "El dataset no se pudo pasar a estado PUBLISHED."


def test_download_all(test_client, mock_dataset_service):
    with test_client.application.app_context():
        mock_service = mock_dataset_service.return_value
        mock_service.zip_datasets.return_value = None

        with patch('app.modules.dataset.routes.send_file') as mock_send_file:
            mock_send_file.return_value = "Zip sent"

            response = test_client.get(url_for('dataset.download_all_datasets'))
            assert response.status_code == 200, response.status_code
            assert response.data == b"Zip sent", response.data


def test_download_all_datasets_empty_directory(test_client, mock_dataset_service):
    mock_service_instance = mock_dataset_service.return_value
    mock_service_instance.zip_datasets.return_value = None

    with patch('os.listdir', return_value=[]):
        response = test_client.get(url_for('dataset.download_all_datasets'))

        assert response.status_code == 200
        assert b'\x00' in response.data
        assert len(response.data) == 22  # Header length


def test_download_all_datasets_error(test_client):
    with patch.object(dataset_service, 'zip_datasets', side_effect=Exception("Error al crear el ZIP")):
        response = test_client.get(url_for('dataset.download_all_datasets'))
        assert response.status_code == 500
        assert response.json['error'] == "Error al crear el ZIP"


@patch('os.remove')
def test_download_all_datasets_cleanup(mock_remove, test_client):
    response = test_client.get(url_for('dataset.download_all_datasets'))
    assert response.status_code == 200
    mock_remove.assert_called_once()
