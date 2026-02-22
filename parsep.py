# parser.py
import re
from typing import Optional, Dict
from utils import strip_html


class VKEmailParser:
    """Парсит письма от VK Forms в структурированный словарь."""

    REQUIRED_FIELDS = ("Имя:", "Телефон:")

    def parse(self, raw_body: str) -> Optional[Dict[str, str]]:
        body = strip_html(raw_body)

        if not all(field in body for field in self.REQUIRED_FIELDS):
            return None

        data = {
            "name": "",
            "phone": "",
            "city": "",
            "social_link": "",
            "площадь": "",
            "этажи": "",
            "отделка": "",
            "цель": "",
        }

        data["name"] = self._extract_name(body)
        data["phone"] = self._extract_phone(body)
        data["social_link"] = self._extract_social_link(body)
        data["city"] = self._extract_city(body)
        data.update(self._extract_questions(body))

        return data if any(data.values()) else None

    def _extract_name(self, body: str) -> str:
        if "Телефон:" not in body:
            match = re.search(r'Имя:\s*(\S+)', body)
            return match.group(1) if match else ""
        name_part = body.split("Телефон:", 1)[0]
        if "Имя:" not in name_part:
            return ""
        return name_part.split("Имя:", 1)[1].strip()

    def _extract_phone(self, body: str) -> str:
        if "Телефон:" not in body:
            match = re.search(r'(\+?\d[\d\s\-\(\)]+)', body)
            return re.sub(r'[^\d+]', '', match.group(1)) if match else ""
        rest = body.split("Телефон:", 1)[1]
        if "Ссылка на профиль" in rest:
            phone_part = rest.split("Ссылка на профиль", 1)[0]
        else:
            phone_part = rest
        match = re.search(r'(\+?\d[\d\s\-\(\)]+)', phone_part)
        return re.sub(r'[^\d+]', '', match.group(1)) if match else ""

    def _extract_social_link(self, body: str) -> str:
        if "Ссылка на профиль в социальной сети:" not in body:
            return ""
        link_part = body.split("Ссылка на профиль в социальной сети:", 1)[1]
        if "Город:" in link_part:
            link_part = link_part.split("Город:", 1)[0]
        from utils import extract_url
        return extract_url(link_part.strip()) or ""

    def _extract_city(self, body: str) -> str:
        if "Город:" not in body or "Вопрос:" not in body:
            return ""
        city_part = body.split("Город:", 1)[1]
        return city_part.split("Вопрос:", 1)[0].strip()

    def _extract_questions(self, body: str) -> Dict[str, str]:
        result = {}
        pattern = r'Вопрос:\s*(.+?)\s*Ответ:\s*([^\n\r<]*?)(?=\s*(?:Вопрос:|Переход с рекламного объявления:|$))'
        matches = re.findall(pattern, body, re.IGNORECASE | re.DOTALL)

        mapping = {
            "площадь": "площадь",
            "этаж": "этажи",
            "отделка": "отделка",
            "утепление": "отделка",
            "расчет цены": "цель",
            "отправить расчет": "цель",
        }

        for question, answer in matches:
            q_lower = question.strip().lower()
            for key, field in mapping.items():
                if key in q_lower and field not in result:
                    result[field] = answer.strip()
                    break
        return result
