import os, tempfile
from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=64, ttl=60))
def create_temp_cert_file():
    
    CLIENT_CERT_STRING = os.getenv('CLIENT_CERT_STRING')
    if not CLIENT_CERT_STRING:
        raise ValueError("No CLIENT_CERT_STRING")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False) as f_cert, \
        tempfile.NamedTemporaryFile(delete=False) as f_key:
        f_cert.write(CLIENT_CERT_STRING.encode("utf-8"))
        f_cert.seek(0)
        
        cert_path = f_cert.name
        return cert_path