# api_client.py
# Example API client for the converted FastAPI endpoints

import requests
from typing import Optional, Dict, Any

class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def get(self, endpoint: str, token: Optional[str] = None, params: Optional[Dict] = None):
        """GET request"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        response = self.session.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Optional[Dict] = None, token: Optional[str] = None):
        """POST request"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        response = self.session.post(url, headers=headers, json=data or {})
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Optional[Dict] = None, token: Optional[str] = None):
        """PUT request"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        response = self.session.put(url, headers=headers, json=data or {})
        response.raise_for_status()
        return response.json()
    
    def post_multipart(self, endpoint: str, files: Dict[str, Any], token: Optional[str] = None):
        """POST multipart request for file uploads"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = self.session.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()

# Initialize API client
Api = ApiClient()

# Candidate API functions (converted from the original JavaScript/TypeScript)
def get_candidate_list(token: str):
    """GET /candidate - Get list of candidates"""
    return Api.get("/candidate", token=token)

def revalidate_identity(candidate_id: str, token: str):
    """POST /candidate/{candidate_id}/reverify/identity - Revalidate identity"""
    return Api.post(f"/candidate/{candidate_id}/reverify/identity", token=token)

def revalidate_employment(candidate_id: str, token: str):
    """POST /candidate/{candidate_id}/reverify/employment - Revalidate employment"""
    return Api.post(f"/candidate/{candidate_id}/reverify/employment", token=token)

def revalidate_aml(candidate_id: str, token: str):
    """POST /candidate/{candidate_id}/reverify/aml - Revalidate AML"""
    return Api.post(f"/candidate/{candidate_id}/reverify/aml", token=token)

def revalidate_bank(candidate_id: str, token: str):
    """POST /candidate/{candidate_id}/reverify/bankAccount - Revalidate bank account"""
    return Api.post(f"/candidate/{candidate_id}/reverify/bankAccount", token=token)

def revalidate_court(candidate_id: str, token: str):
    """POST /candidate/{candidate_id}/reverify/court - Revalidate court records"""
    return Api.post(f"/candidate/{candidate_id}/reverify/court", token=token)

def create_bulk_candidate(file_path: str, token: str):
    """POST /candidate/upload - Create bulk candidates from file"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        return Api.post_multipart("/candidate/upload", files, token=token)

# Example usage:
if __name__ == "__main__":
    # Example token (you would get this from login)
    example_token = "your_jwt_token_here"
    
    try:
        # Get candidate list
        candidates = get_candidate_list(example_token)
        print("Candidates:", candidates)
        
        # Revalidate identity for candidate ID 123
        result = revalidate_identity("123", example_token)
        print("Identity revalidation result:", result)
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}") 