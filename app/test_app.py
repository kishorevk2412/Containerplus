import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_endpoint_html(client):
    """Test root endpoint returns 200 OK and HTML web page for browsers"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'ContainerPulse' in response.data

def test_home_endpoint_json(client):
    """Test root endpoint returns JSON when requested with format=json"""
    response = client.get('/?format=json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['application'] == 'ContainerPulse'
    assert 'container_hostname' in data
    assert data['status'] == 'Running'

def test_results_endpoint(client):
    """Test results endpoint returns 200 OK and official evaluation report"""
    response = client.get('/results')
    assert response.status_code == 200
    assert b'ContainerPulse' in response.data
    assert b'Project Results' in response.data
    assert b'Self-Healing' in response.data

def test_health_endpoint(client):
    """Test health endpoint returns 200 OK and healthy status"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'container_hostname' in data

def test_error_endpoint(client):
    """Test error endpoint returns HTTP 500 status"""
    response = client.get('/error')
    assert response.status_code == 500
    data = response.get_json()
    assert data['error'] == 'Internal Server Error'

def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint returns 200 and metrics text"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'containerpulse_http_requests_total' in response.data
    assert b'containerpulse_app_health_status' in response.data
