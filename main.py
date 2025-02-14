import pytz
import argparse
import logging
from sms import SMSModule
from relay.telegram import create_callback as create_telegram_callback

def init_logger(args):
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,  # Set the log level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the log message format
    )

def handle_read(args):
    logger = logging.getLogger(__name__)

    def print_sms(sms):
        logger.info(f"===============================")
        logger.info(f"Device: {args.port}")
        logger.info(f"From: {sms['sender']}")
        logger.info(f"To: {sms['receiver']}")
        logger.info(f"Date: {sms['timestamp']}")
        logger.info(f"{sms['message']}")
        logger.info(f"===============================")

    def create_callback_chain(timezone, callbacks):
        def callback_chain(sms):
            # Convert the timestamp from UTC to local time
            local_timezone = pytz.timezone(timezone)
            timestamp = sms['timestamp']
            sms['timestamp'] = timestamp.astimezone(local_timezone)

            for func in callbacks:
                func(sms)

        return callback_chain

    modem = SMSModule(args.port, args.baud, args.pin)
    if not modem.setup():
        print("Failed to initialize modem")
        return

    logger.info(f"Connected to {args.port}")
    logger.info(f"Active phone number: {modem.get_own_number()}")

    callbacks = [print_sms]
    if args.telegram_token and args.telegram_chat:
        telegram_callback = create_telegram_callback(args.telegram_token, args.telegram_chat, args.telegram_proxy)
        callbacks.append(telegram_callback)
        logger.info('Telegram callback is enabled')

    callback_chain = create_callback_chain(args.timezone, callbacks)

    # Read and process stored messages
    if args.read_stored:
        logger.info("Reading stored messages...")
        stored = modem.read_stored_messages(delete_after=args.delete_after_read)
        for sms in stored:
            callback_chain(sms)
        logger.info(f"Processed {len(stored)} stored messages")

    try:
        print("Waiting for SMS... (Ctrl+C to stop)")
        modem.monitor_sms(callback_chain)
    except KeyboardInterrupt:
        modem.close()

def handle_send(args):
    logger = logging.getLogger(__name__)

    modem = SMSModule(args.port, args.baud, args.pin)
    if not modem.setup():
        logger.error("Failed to initialize modem")
        return

    logger.info(f"Connected to {args.port}")
    logger.info(f"Active phone number: {modem.get_own_number()}")

    if modem.send_sms(args.number, args.message):
        logger.info("Message sent successfully")
    else:
        logger.error("Failed to send message")
    modem.close()

def main():
    parser = argparse.ArgumentParser(description="SMS Tool for Air780E")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Enable verbose logging, this flags must precede any subcommand")
    subparsers = parser.add_subparsers()

    # Read command
    read_parser = subparsers.add_parser('read', help='Monitor incoming SMS')
    read_parser.add_argument('-p', '--port', required=True, help='Serial port')
    read_parser.add_argument('-b', '--baud', type=int, default=115200, help='Baud rate')
    read_parser.add_argument('--pin', help='SIM PIN')
    read_parser.add_argument('--read-stored', action='store_true', default=True,
                           help='Read existing messages on startup')
    read_parser.add_argument('--delete-after-read', action='store_true', default=False,
                           help='Delete messages after reading')
    read_parser.add_argument('-z', '--timezone', default='UTC')
    read_parser.add_argument('--telegram-token', help='Telegram Bot Token')
    read_parser.add_argument('--telegram-chat', help='Telegram Chat ID')
    read_parser.add_argument('--telegram-proxy', help='Proxy server to communicate with the Telegram server')
    read_parser.set_defaults(func=handle_read)

    # Send command
    send_parser = subparsers.add_parser('send', help='Send SMS')
    send_parser.add_argument('-p', '--port', required=True, help='Serial port')
    send_parser.add_argument('-b', '--baud', type=int, default=115200, help='Baud rate')
    send_parser.add_argument('--pin', help='SIM PIN')
    send_parser.add_argument('-n', '--number', required=True, help='Recipient number')
    send_parser.add_argument('-m', '--message', required=True, help='Message content')
    send_parser.set_defaults(func=handle_send)

    args = parser.parse_args()

    init_logger(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
