import os

import httpx
from pydantic import BaseModel


class SMSResponse(BaseModel):
	success: bool
	message: str
	balance: str | None = None
	delivery_code: str | None = None


class SMSService:
	def __init__(
		self,
		api_key: str | None = None,
		base_url: str = 'https://www.expresssms.co.ke/api/sms/send',
		timeout: float = 10.0,
	) -> None:
		self.api_key = api_key or os.getenv('BULKSMS_API_KEY', '')
		self.base_url = base_url
		self.timeout = timeout

	def send_sms(self, phone: str, message: str) -> SMSResponse:
		payload = {
			'api_key': self.api_key,
			'message': message,
			'phone': phone,
		}

		response = httpx.post(self.base_url, json=payload, timeout=self.timeout)
		response.raise_for_status()
		data = response.json()
		return SMSResponse.model_validate(data)
