# config.py
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailConfig:
    address: str
    password: str
    imap_server: str
    imap_port: int

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            address=os.getenv("EMAIL", ""),
            password=os.getenv("EMAIL_PASSWORD", ""),
            imap_server=os.getenv("IMAP_SERVER", "imap.yandex.ru"),
            imap_port=int(os.getenv("IMAP_PORT", "993")),
        )

    def validate(self) -> None:
        if not self.address or not self.password:
            raise ValueError("EMAIL and EMAIL_PASSWORD must be set")


@dataclass
class BitrixConfig:
    webhook_url: str
    default_manager_id: int
    default_category_id: int

    @classmethod
    def from_env(cls) -> "BitrixConfig":
        url = os.getenv("BITRIX_WEBHOOK", "").rstrip("/")
        if url and not url.endswith("/"):
            url += "/"
        return cls(
            webhook_url=url,
            default_manager_id=int(os.getenv("BITRIX_MANAGER_ID", "159")),
            default_category_id=int(os.getenv("BITRIX_CATEGORY_ID", "0")),
        )

    def validate(self) -> None:
        if not self.webhook_url:
            raise ValueError("BITRIX_WEBHOOK must be set")


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("CHAT_ID", ""),
        )

    def validate(self) -> None:
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and CHAT_ID must be set")


@dataclass
class AppConfig:
    email: EmailConfig
    bitrix: BitrixConfig
    telegram: TelegramConfig
    processed_file: str = "processed_emails.txt"
    poll_interval: int = 60

    @classmethod
    def load(cls) -> "AppConfig":
        from dotenv import load_dotenv
        load_dotenv()

        email_cfg = EmailConfig.from_env()
        bitrix_cfg = BitrixConfig.from_env()
        tg_cfg = TelegramConfig.from_env()

        email_cfg.validate()
        bitrix_cfg.validate()
        tg_cfg.validate()

        return cls(
            email=email_cfg,
            bitrix=bitrix_cfg,
            telegram=tg_cfg,
        )
