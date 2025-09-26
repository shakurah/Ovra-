# boe/opensearch_client.py
import os 
from django.conf import settings
import logging
from ovra_backend.settings import OPENSEARCH_URL, OPENSEARCH_USER, OPENSEARCH_PASS
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from opensearchpy import OpenSearch, helpers
    OPENSEARCH_AVAILABLE = True
except Exception:
    OPENSEARCH_AVAILABLE = False
    OpenSearch = None
    helpers = None

def get_opensearch_client():
    if not OPENSEARCH_AVAILABLE:
        raise RuntimeError("opensearch-py is not available")
    host = OPENSEARCH_URL
    user = OPENSEARCH_USER
    password = OPENSEARCH_PASS
    ca_cert_path = os.path.join(BASE_DIR, 'ca-certificate.crt')  # Adjust path as needed
    if not host:
        raise RuntimeError("OPENSEARCH_URL not configured in settings")
    client = OpenSearch(
        hosts=[{'host': host, 'port': 25060}],
        http_auth=(user, password) if user and password else None,
        use_ssl=True,
        verify_certs=True,
        ca_cert=ca_cert_path
    )
    return client, helpers
