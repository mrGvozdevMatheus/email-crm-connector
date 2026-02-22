# utils.py
import re
import hashlib
from email.header import decode_header
from typing import Optional


def strip_html(text: str) -> str:
    """Удаляет HTML-теги и декодирует базовые entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return re.sub(r'\s+', ' ', text).strip()


def decode_mime_words(s: str) -> str:
    """Декодирует MIME-encoded заголовки писем."""
    fragments = decode_header(s)
    parts = []
    for fragment, encoding in fragments:
        if isinstance(fragment, bytes):
            fragment = fragment.decode(encoding or 'utf-8', errors='ignore')
        parts.append(fragment)
    return ''.join(parts)


def generate_message_id(msg: dict) -> str:
    """Генерирует уникальный ID для письма."""
    raw = msg.get("Message-ID", "")
    if not raw:
        subject = decode_mime_words(msg.get("Subject", ""))
        date = msg.get("Date", "")
        raw = f"{subject}_{date}"
    return hashlib.md5(raw.encode()).hexdigest()


def normalize_phone(phone: str) -> str:
    """Оставляет только цифры и + в номере телефона."""
    return re.sub(r'[^\d+]', '', phone.strip())


def extract_url(text: str) -> Optional[str]:
    """Извлекает первую HTTP-ссылку из текста."""
    match = re.search(r'https?://[^\s<>"\']+', text)
    return match.group(0) if match else None
