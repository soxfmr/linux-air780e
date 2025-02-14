import re
import time
import serial
import logging
from threading import Event
from typing import Optional, List
from pdu import encode_pdu, decode_pdu


class SMSModule:

    def __init__(self, port, baud=115200, pin=None, enable_sim_storage=True):
        self.serial_port = serial.Serial(port, baud, timeout=1)
        self.exit_event = Event()
        self.pin = pin
        self.logger = logging.getLogger(__name__)
        self.own_number: Optional[str] = None
        self.enable_sim_storage = enable_sim_storage

    def send_at_command(self, command, expected_response : Optional[str] = None, timeout=1):
        self.serial_port.write(f"{command}\r\n".encode())
        time.sleep(timeout)
        response = self.serial_port.read_all().decode(errors='ignore').strip()
        success = True

        if expected_response:
            success = expected_response in response
            if not success:
                self.logger.error(f"Command failed: {command}\nResponse: {response}")

        return response if success else None

    def setup(self):
        if not self._check_basic_operation():
            return False

        if self.enable_sim_storage:
            if not self._configure_sms_storage():
                return False

        self._get_own_number()

        commands = [
            ("AT+CMGF=0", "OK"),  # PDU mode
            ("AT+CNMI=2,1,0,0,0", "OK")  # SMS notification
        ]

        for cmd, expected in commands:
            if not self.send_at_command(cmd, expected):
                return False
        return True

    def _check_basic_operation(self):
        if not self.send_at_command("AT", "OK"):
            return False

        if self.pin and not self.send_at_command(f"AT+CPIN={self.pin}", "OK"):
            return False

        return True

    def _configure_sms_storage(self):
        """Configure storage to ensure messages are saved when offline"""
        storage_preference = [
            ('"SM","SM","SM"', "SIM"),  # Try SIM first
            ('"ME","ME","ME"', "Module")  # Fallback to module memory
        ]

        for param, name in storage_preference:
            response = self.send_at_command(f'AT+CPMS={param}')
            if "OK" in response:
                self.logger.debug(f"Using {name} for message storage")

                # Verify storage configuration
                response = self.send_at_command("AT+CPMS?")
                self.logger.debug(f"SMS storage configured: {response}")

                return True

        self.logger.error("Failed to configure SMS storage")
        return False

    def read_stored_messages(self, delete_after: bool = False) -> List[dict]:
        """Read all stored messages from configured storage"""
        messages = []
        response = self.send_at_command("AT+CMGL=4")  # 4 = all messages
        if not response:
            return messages

        # Parse message indexes from CMGL response
        indexes = re.findall(r'\+CMGL: (\d+),[0-9]+,.*,[0-9]+\r\n', response)
        indexes = list(set(indexes))
        for index in indexes:
            if sms := self.read_sms(index):
                messages.append(sms)
                if delete_after:
                    self.delete_sms(index)

        messages = sorted(messages, key=lambda sms: sms['timestamp'])

        return messages

    def delete_sms(self, index: str) -> bool:
        """Delete SMS from storage"""
        return self.send_at_command(f"AT+CMGD={index}", "OK") is not None

    def _get_own_number(self):
        response = self.send_at_command("AT+CNUM")
        if not response:
            return

        match = re.search(r'\+CNUM:\s*"[^"]*","(\+?\d+)",', response)
        if match:
            self.own_number = match.group(1)
            self.logger.debug(f"Module phone number: {self.own_number}")
        else:
            self.logger.warning("Failed to retrieve own phone number")

    def get_own_number(self):
        return self.own_number

    def read_sms(self, index):
        response = self.send_at_command(f"AT+CMGR={index}", "+CMGR:")
        if not response:
            return None

        self.logger.debug(f'Response from AT+CMGR: {response}')

        pdu_match = re.search(r'\+CMGR:\s+\d+,[^"]*,\d+[\r\n]*([0-9A-F]+)', response, re.M)
        if not pdu_match:
            return None

        sms = decode_pdu(pdu_match.group(1))

        if sms:
            sms['receiver'] = self.own_number

        return sms

    def send_sms(self, number, message):
        pdu = encode_pdu(number, message)
        if not pdu:
            return False

        response = self.send_at_command(f'AT+CMGS={len(pdu) // 2 - 1}', ">", 2)
        if not response:
            return False

        self.serial_port.write(f"{pdu}\x1A".encode())
        time.sleep(3)

        data  = self.serial_port.read_all().decode(errors='ignore').strip()
        self.logger.debug(f"Response from AT+CMGS: {data}")

        return "OK" in data

    def monitor_sms(self, callback) -> None:
        while not self.exit_event.is_set():
            line = self.serial_port.readline().decode(errors='ignore').strip()
            if not line:
                continue

            self.logger.debug(f"Read line from mobile terminal: {line}")

            if "+CMTI:" in line:
                index = line.split(",")[-1].strip()
                if sms := self.read_sms(index):
                    callback(sms)

    def close(self):
        self.exit_event.set()
        self.serial_port.close()
