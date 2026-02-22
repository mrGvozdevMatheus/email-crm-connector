# clients/telegram.py
import requests
import logging
from typing import List, Dict, Optional
from config import TelegramConfig

logger = logging.getLogger(__name__)


class TelegramClient:
    """Клиент для отправки сообщений в Telegram."""

    API_URL = "https://api.telegram.org/bot"

    def __init__(self, config: TelegramConfig):
        self.token = config.bot_token
        self.chat_id = config.chat_id
        self._session = requests.Session()

    def send_message(
        self,
        text: str,
        buttons: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        url = f"{self.API_URL}{self.token}/sendMessage"
        payload: Dict[str, object] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": [buttons]}

        try:
            resp = self._session.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            logger.info("Telegram сообщение отправлено")
            return True
        except requests.RequestException as e:
            logger.error("Telegram error: %s", str(e)[:200])
            return False
