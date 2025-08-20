from typing import Optional, Dict, Any
import requests
from config import settings

class VerificationService:
    def __init__(self):
        self.api_base_url = settings.VERIFICATION_API_BASE_URL
        self.api_key = settings.VERIFICATION_API_KEY
        self.session = requests.Session()

    def _befisc_headers(self) -> Dict[str, str]:
        return {"authkey": settings.BEFISC_API_KEY, "Content-Type": "application/json"}

    def _prescreening_headers(self) -> Dict[str, str]:
        return {"x-api-key": settings.PRESCREENING_API_KEY, "Content-Type": "application/json"}

    def _crimescan_headers(self) -> Dict[str, str]:
        return {
            "Authorization": "Bearer YlPrSHw1y7WeeiEfIpcNOLLHUCYA5Nye.sBOnxbnZxnyW4O0UlF1U0xNfEHmvwFu1xjTjx7a3Mn3K1V84",
            "Content-Type": "application/json",
        }

    async def send_aadhar_otp(self, aadhar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send Aadhar OTP via Befisc"""
        try:
            payload = {"aadharNo": aadhar_data.get("aadharNo")}
            resp = self.session.post(settings.AADHAAR_SEND_OTP_URL, json=payload, headers=self._befisc_headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def verify_aadhar(self, aadhar_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "aadharNo": aadhar_data.get("aadharNo") or aadhar_data.get("aadhar_number"),
                "otp": aadhar_data.get("otp"),
                "referenceId": aadhar_data.get("referenceId"),
            }
            resp = self.session.post(settings.AADHAAR_VERIFY_URL, json=payload, headers=self._befisc_headers(), timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error verifying Aadhar: {e}")
            return None

    async def verify_pan(self, pan_number: str) -> Optional[Dict[str, Any]]:
        """Verify PAN number via Befisc"""
        try:
            resp = self.session.post(settings.PAN_VERIFY_URL, json={"pan": pan_number}, headers=self._befisc_headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error verifying PAN: {e}")
            return None

    async def uan_from_aadhar(self, aadhar_number: str) -> Optional[str]:
        """Get UAN from Aadhar number via Befisc"""
        try:
            resp = self.session.post(settings.AADHAAR_TO_UAN_URL, json={"aadharNo": aadhar_number}, headers=self._befisc_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json() or {}
            return data.get("uan")
        except Exception as e:
            print(f"Error getting UAN: {e}")
            return None

    async def get_all_employment_history(self, uan: str) -> Optional[Dict[str, Any]]:
        """
        Get employment history from UAN via Befisc v2 API.
        """
        try:
            payload = {
                "uan": uan,
                "consent": "Y",
                "consent_text": "I give my consent to employment-history(v2) api to check my employment history"
            }

            print(f"🏢 Employment history API payload: {payload}")

            resp = self.session.post(
                settings.EMPLOYMENT_HISTORY_URL,
                json=payload,
                headers=self._befisc_headers(),
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ Error getting employment history: {e}")
            return None

    async def get_court_case_history(self, candidate_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get court case history via Crimescan (Bearer auth flow with cs_id)"""
        try:
            # Build payload per Crimescan exact search API
            payload: Dict[str, Any] = {
                "name": candidate_data.get("name"),
                "father_name": candidate_data.get("father_name"),
                "address": candidate_data.get("address"),
            }
            dob_val = candidate_data.get("dob")
            if dob_val:
                if hasattr(dob_val, "strftime"):
                    payload["dob"] = dob_val.strftime("%d-%m-%Y")
                elif isinstance(dob_val, str) and dob_val.strip():
                    payload["dob"] = dob_val

            # Search
            print(f"🧑‍⚖️ Crimescan search payload: {payload}")
            search_resp = self.session.post(
                settings.COURT_EXACT_SEARCH_URL,
                json=payload,
                headers=self._crimescan_headers(),
                timeout=120,
            )
            search_resp.raise_for_status()
            result = search_resp.json() or {}
            print(f"🧑‍⚖️ Crimescan search result: {result}")

            cs_id = result.get("cs_id") or (result.get("data") or {}).get("cs_id")
            if not cs_id:
                return {"court_cases": [], "message": "No cs_id returned"}

            # Poll for history
            import time

            max_retries = 6
            retry_interval = 10  # seconds
            hist_json = {"status": 0, "message": "Process pending"}

            for attempt in range(max_retries):
                hist_resp = self.session.post(
                    settings.COURT_HISTORY_URL,
                    json={"cs_id": cs_id},
                    headers=self._crimescan_headers(),
                    timeout=120,
                )
                hist_json = hist_resp.json()
                if hist_json.get("status") == 1:
                    print(f"✅ Report ready on attempt {attempt + 1}")
                    return hist_json
                print(f"⏳ Attempt {attempt + 1}: Report not ready, retrying in {retry_interval}s...")
                time.sleep(retry_interval)

            # If still not ready
            print("⚠️ Report still processing, try again later")
            return {"court_cases": [], "message": "Report still processing, try again later."}

        except Exception as e:
            print(f"❌ Error getting court case history: {e}")
            return {"court_cases": [], "message": str(e)}

    async def aml_verification(self, aml_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform AML verification via Prescreening"""
        try:
            resp = self.session.post(f"{settings.AML_BASE_URL}aml", json=aml_data, headers=self._prescreening_headers(), timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error performing AML verification: {e}")
            return None

    async def bank_account_verification(self, bank_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Verify bank account via Befisc"""
        try:
            # Map the frontend keys to the API expected keys
            api_payload = {
                "account_number": bank_data.get("accountNo") or bank_data.get("account_number"),
                "ifsc": bank_data.get("ifsc"),
                "name": bank_data.get("name") or bank_data.get("beneficiaryName")
            }
            
            print(f"🏦 Bank verification API payload: {api_payload}")
            resp = self.session.post(settings.BANK_ACCOUNT_BASE_URL, json=api_payload, headers=self._befisc_headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error verifying bank account: {e}")
            return None

    async def get_current_address(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get current address (placeholder)"""
        try:
            resp = self.session.post(f"{settings.AML_BASE_URL}address", json={"phone": phone_number}, headers=self._prescreening_headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error getting current address: {e}")
            return None 