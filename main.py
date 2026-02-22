# main.py
import imaplib
import email
import time
import logging
from typing import Optional

from config import AppConfig
from cache import ProcessedCache
from parser import VKEmailParser
from clients.bitrix import BitrixClient
from clients.telegram import TelegramClient
from utils import generate_message_id, normalize_phone, strip_html, decode_mime_words

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class EmailWorker:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.cache = ProcessedCache(cfg.processed_file)
        self.parser = VKEmailParser()
        self.bitrix = BitrixClient(cfg.bitrix) if cfg.bitrix.webhook_url else None
        self.tg = TelegramClient(cfg.telegram) if cfg.telegram.bot_token else None

    def fetch_emails(self) -> list:
        try:
            mail = imaplib.IMAP4_SSL(self.cfg.email.imap_server, self.cfg.email.imap_port)
            mail.login(self.cfg.email.address, self.cfg.email.password)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")  # только новые
            if status != "OK":
                return []

            email_ids = messages[0].split()
            result = []
            for eid in email_ids[-10:]:  # последние 10
                status, data = mail.fetch(eid, "(RFC822)")
                if status == "OK" and data and data[0]:
                    raw = data[0][1] if isinstance(data[0], tuple) else data[0]
                    if raw:
                        msg = email.message_from_bytes(raw)
                        result.append(msg)
            mail.close()
            mail.logout()
            return result
        except Exception as e:
            logger.error("IMAP error: %s", e)
            return []

    def extract_body(self, msg: email.message.Message) -> Optional[str]:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                        return strip_html(html)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
        return None

    def process(self, msg: email.message.Message) -> None:
        msg_id = generate_message_id(msg)
        if self.cache.contains(msg_id):
            logger.debug("Письмо уже обработано: %s", msg_id[:8])
            return

        body = self.extract_body(msg)
        if not body:
            return

        fields = self.parser.parse(body)
        if not fields:
            logger.debug("Письмо не распознано как VK Form")
            return

        # === Bitrix ===
        deal_id = None
        if self.bitrix and fields["name"] and fields["phone"]:
            contact_id = self.bitrix.create_contact(fields["name"], fields["phone"])
            if contact_id:
                comments = "\n".join([
                    f"Соцсеть: {fields['social_link']}",
                    f"Город: {fields['city']}",
                    f"Площадь: {fields['площадь']}",
                    f"Этажи: {fields['этажи']}",
                    f"Отделка: {fields['отделка']}",
                    f"Цель: {fields['цель']}",
                ])
                title = f"Заявка из ВК"
                deal_id = self.bitrix.create_deal(contact_id, title, comments)
                if deal_id:
                    self.bitrix.update_deal_title(deal_id, f"Заявка из ВК #{deal_id}")

        # === Telegram ===
        if self.tg:
            short_id = f"VK#{deal_id}" if deal_id else f"VK#{msg_id[:5].upper()}"
            message = (
                f"<b>{short_id}</b>\n\n"
                f"👤 {fields['name']}\n"
                f"📞 {fields['phone']}\n"
                f"🏙 {fields['city']}\n"
                f"📐 {fields['площадь']}\n"
                f"🏗 {fields['этажи']}\n"
                f"🔨 {fields['отделка']}\n"
                f"🎯 {fields['цель']}"
            )
            buttons = []
            if deal_id:
                buttons.append({
                    "text": "CRM",
                    "url": f"https://karkas.bitrix24.ru/crm/deal/details/{deal_id}/"
                })
            if fields["social_link"]:
                buttons.append({"text": "VK", "url": fields["social_link"]})
            if fields["phone"].startswith("+"):
                clean = normalize_phone(fields["phone"])
                if len(clean) >= 10:
                    buttons.append({"text": "TG", "url": f"https://t.me/+{clean}"})

            self.tg.send_message(message, buttons if buttons else None)

        self.cache.add(msg_id)
        logger.info("✅ Обработано: %s", msg_id[:8])

    def run(self):
        logger.info("📧 Запуск парсера VK Email")
        while True:
            try:
                for msg in self.fetch_emails():
                    self.process(msg)
            except KeyboardInterrupt:
                logger.info("🛑 Остановлено пользователем")
                break
            except Exception as e:
                logger.error("🔥 Цикл упал: %s", e)
            time.sleep(self.cfg.poll_interval)


def main():
    cfg = AppConfig.load()
    worker = EmailWorker(cfg)
    worker.run()


if __name__ == "__main__":
    main()
