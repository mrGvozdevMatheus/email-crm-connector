# clients/bitrix.py
import requests
import logging
from typing import Optional
from config import BitrixConfig

logger = logging.getLogger(__name__)


class BitrixClient:
    """Клиент для работы с Bitrix24 REST API."""

    def __init__(self, config: BitrixConfig):
        self.base_url = config.webhook_url.rstrip("/") + "/"
        self.manager_id = config.default_manager_id
        self.category_id = config.default_category_id

    def _post(self, method: str, payload: dict) -> Optional[dict]:
        url = f"{self.base_url}{method}"
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            return result if isinstance(result, dict) else None
        except requests.RequestException as e:
            logger.warning("Bitrix API error [%s]: %s", method, str(e)[:100])
            return None

    def create_contact(self, name: str, phone: str) -> Optional[int]:
        payload = {
            "fields": {
                "NAME": name,
                "PHONE": [{"VALUE": phone, "TYPE_ID": "WORK"}],
                "SOURCE_ID": "REPEAT_SALE",
            }
        }
        resp = self._post("crm.contact.add", payload)
        if resp and "result" in resp:
            logger.info("Контакт создан: ID=%s", resp["result"])
            return resp["result"]
        return None

    def create_deal(self, contact_id: int, title: str, comments: str) -> Optional[int]:
        payload = {
            "fields": {
                "TITLE": title,
                "CONTACT_ID": contact_id,
                "SOURCE_ID": "REPEAT_SALE",
                "CATEGORY_ID": self.category_id,
                "ASSIGNED_BY_ID": self.manager_id,
                "COMMENTS": comments,
            }
        }
        resp = self._post("crm.deal.add", payload)
        if resp and "result" in resp:
            logger.info("Сделка создана: ID=%s", resp["result"])
            return resp["result"]
        return None

    def update_deal_title(self, deal_id: int, new_title: str) -> bool:
        payload = {"fields": {"TITLE": new_title}}
        resp = self._post(f"crm.deal.update?id={deal_id}", payload)
        return bool(resp and "result" in resp)
