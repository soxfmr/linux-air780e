# linux-air780e

该程序用于与 Air780E 设备进行交互，支持历史短信读取、实时短信读取以及短信发送。

# 支持功能 

- [x] 获取保存于 SIM 卡中的历史短信 
- [x] 实时短信接收 
- [X] 发送短信
- [X] Unicode 编码支持 
- [X] 自定义短信转发功能 
  - [x] Telegram

# 用户手册

## 准备工作 

安装依赖，`venv` 为可选项:
```bash
python -m venv .venv
. .venv/bin/activate

pip install -r requirements.txt
```

将 Air780E 设备接入到系统中，本示例中使用 USB 接口。首先使用 `dmesg` 观察设备挂载信息：
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

通常在接入设备后，系统会自动在 `/dev` 目录下生成 3 个设备。通过 `AT` 命令可以找出正确的设备：
```bash
$ echo 'ATI' | socat - /dev/ttyACM5

ManufactManufactATI

AirM2M_780E_V1171_LTE_AT

OK
```

关于命令的更多信息，请参考 https://docs.openluat.com/air780e/at/app/at_command 。

## 读取短信

在本示例中，设备位于 `/dev/ttyACM5`，程序在运行后会读取历史短信，并实时监听新短信：
```bash
python main.py read -p /dev/ttyACM5
```

- `-p` 或 `--port` 用于指定设备路径

将短信转发到 Telegram 频道，在转发之前需要先将 Bot 添加到指定频道中：
```bash
python main.py read -p /dev/ttyACM5\
 -z Asia/Shanghai \
 --telegram-token 'YOUR_BOT_TOKEN' \
 --telegram-chat 'YOUR_CHANNEL_ID' \
 --telegram-proxy 'socks5://192.168.1.1:1080' \
 --delete-after-read
```

- `-z` 指定短信接收时间的时区
- `--delete-after-read` 告知程序在读取短信后，将短信从 SIM 卡存储中移除

## 发送短信 

```bash
python main.py send -p /dev/ttyACM5 -n +4412345678 \
 -m "这条短信来自 🐧 Linux 系统上的 Air780E 设备，好酷哦 🤩"
 
```

短信接收号码需要加入国家区号，本例中 `+44` 为英国区号。

**在发送短信之前，需要停止其他所有监听程序实例**，否则将无法正常发送短信。

## 系统服务（Systemd Unit）

```bash
# 替换项目根路径
sed -i 's|/linux-air780e|WorkingDirectory=YOUR_PROJECT_ROOT_PATH|g' scripts/linux-air780e@.service

# 根据需求添加运行参数
# vim scripts/run.sh

cp scripts/linux-air780e@.service /etc/systemd/system/linux-air780e@.service
sudo systemctl daemon-reload

# 分别为 `/dev/ttyACM0` 和 `/dev/ttyACM5` 两个设备创建服务
sudo systemctl enable --now linux-air780e@ACM0.service
sudo systemctl enable --now linux-air780e@ACM5.service

# 显示运行日志
sudo journalctl -u linux-air780e@ACM0.service -f
```

## 特别感谢 

- [SMS-PDU Decoder](https://github.com/qotto/smspdudecoder)

