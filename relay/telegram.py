import logging
import traceback
import requests
from typing import Optional, Callable


class TelegramRelay:
    def __init__(self, token: str, chat_id: str, proxy : Optional[str] = None):
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)

        self.proxies = None
        if proxy:
            self.proxies = {
                'http': proxy,
                'https': proxy,
            }

    def send_sms_to_telegram(self, sms_data: dict):
        try:
            message = self._format_message(sms_data)
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'disable_notification': False
            }

            response = requests.post(self.base_url, params=params, proxies=self.proxies)
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Telegram send failed: {str(e)}")
            self.logger.error(''.join(traceback.TracebackException.from_exception(e).format()))
            return False

    def _format_message(self, sms_data: dict):
        lines = [
            f"📨 New SMS received on: {sms_data.get('receiver', 'Unknown number')}",
            f"From: {sms_data.get('sender', 'Unknown sender')}",
            f"Time: {sms_data.get('timestamp', 'Unknown time')}",
            "\n",
            sms_data.get('message', '')
        ]
        return '\n'.join(lines)


def create_callback(token: str, chat_id: str, proxy: str) -> Callable[[dict], None]:
    def telegram_handler(sms: dict) -> None:
        telegram = TelegramRelay(token, chat_id, proxy)
        telegram.send_sms_to_telegram(sms)
    return telegram_handler
