import logging
import re
from io import StringIO
from typing import Optional
from smspdudecoder.fields import SMSDeliver
from smspdudecoder.elements import Number
from smspdudecoder.codecs import UCS2

logger = logging.getLogger(__name__)

def decode_pdu(pdu: str) -> Optional[dict]:
    try:
        deliver_pdu = StringIO(pdu)
        sms_data = SMSDeliver.decode(deliver_pdu)

        logger.debug(f"Decoded PDU: {sms_data}")

        number = sms_data['sender']['number']
        if sms_data['sender']['toa']['ton'] == 'international':
            number = '+' + number

        message = sms_data['user_data']['data']
        timestamp = sms_data['scts']

        return {
            'sender': number,
            'message': message,
            'timestamp': timestamp,
        }
    except Exception as e:
        print(f"PDU decode error: {str(e)}")
        return None

def encode_pdu(number: str, message: str) -> Optional[str]:
    try:
        # Normalize number
        number = re.sub(r"[^0-9+]", "", number)
        if number.startswith("+"):
            number_type = "91"
            number = number[1:]
        else:
            number_type = "81"

        number_len = len(number)

        encoded_number = Number.encode(number)
        encoded_msg = UCS2.encode(message)

        pdu = (
                "00" +  # SMSC info
                "11" +  # First octet
                "00" +  # Message reference
                f"{number_len:02X}" +  # Real length without padding
                number_type +
                encoded_number +
                "00" +  # PID
                "08" +  # DCS (UCS2)
                "AA" +  # VP placeholder
                f"{len(encoded_msg):02X}" +
                encoded_msg
        )

        logger.debug(f"Encoded PDU: {pdu}")

        return pdu
    except Exception as e:
        print(f"PDU encode error: {str(e)}")
        return None