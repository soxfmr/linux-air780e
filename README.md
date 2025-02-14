# linux-air780e

This program aims to minitor the SMS messages received from Air780E USB devices on Linux. The program also supports sending SMS messages.

> 简体中文请参考 [README-zh.md](README-zh.md)

# Features

- [x] Retrieving historic SMS messages stored in the SIM card
- [x] Real-time SMS messages monitoring
- [X] Sending SMS messages
- [X] Unicode is supported
- [X] Custom callbacks to forward SMS messages
  - [x] Telegram

# Usage

## Prerequisite 

Install the required dependencies, the virtualenv is optional:
```bash
python -m venv .venv
. .venv/bin/activate

pip install -r requirements.txt
```

Plug the Air780E device into a USB port, using `dmesg` to check the corresponding device path:
```bash
$ dmesg

[164931.085772] [ T185215] usb 1-2: new high-speed USB device number 15 using ehci-pci
[164931.347774] [ T185215] usb 1-2: New USB device found, idVendor=19d1, idProduct=0001, bcdDevice= 2.00
[164931.347779] [ T185215] usb 1-2: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[164931.347781] [ T185215] usb 1-2: Product: EigenComm Compo
[164931.347782] [ T185215] usb 1-2: Manufacturer: EigenComm
[164931.347783] [ T185215] usb 1-2: SerialNumber: 000000000001
[164931.355017] [ T185215] cdc_acm 1-2:1.2: ttyACM3: USB ACM device
[164931.357828] [ T185215] cdc_acm 1-2:1.4: ttyACM4: USB ACM device
[164931.360830] [ T185215] cdc_acm 1-2:1.6: ttyACM5: USB ACM device
```

Usually, there are 3 devices available under the `/dev` subsystem after the device is connected to the system. You could issue an `AT` command to figure out the right one which has the proper response:
```bash
$ echo 'ATI' | socat - /dev/ttyACM5

ManufactManufactATI

AirM2M_780E_V1171_LTE_AT

OK
```

For more information, please refer to https://docs.openluat.com/air780e/at/app/at_command.

## Read SMS messages

Read and monitor SMS messages on the device. In this example, our device is located at `/dev/ttyACM5`:
```bash
python main.py read -p /dev/ttyACM5
```

- `-p` or `--port` accepts a device path

Forward messages to a Telegram channel. This requires to add your Telegram bot to the channel:
```bash
python main.py read -p /dev/ttyACM5\
 -z Asia/Shanghai \
 --telegram-token 'YOUR_BOT_TOKEN' \
 --telegram-chat 'YOUR_CHANNEL_ID' \
 --telegram-proxy 'socks5://192.168.1.1:1080' \
 --delete-after-read
```

- `-z` specifies the timezone for all messages before forward them
- `--delete-after-read` removes the SMS messages stored in the SIM card after read

## Send SMS Messages

```bash
python main.py send -p /dev/ttyACM5 -n +4412345678 \
 -m "This message is sent from a Air780E device on 🐧 Linux"
```

- `-n` or `--number` specifies the recipient phone number
- `-m` or `--message` contains the SMS message content

The country code (`+44` for UK) of the phone number is required.

**Currently, sending SMS messages on a monitored device is not supported.** You should stop any running instance before sending a message.

## Thanks

- [SMS-PDU Decoder](https://github.com/qotto/smspdudecoder)

