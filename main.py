import socket
from aenum import Enum
import argparse

# Default values from https://www.globalcache.com/files/releases/flex-16/API-Flex_TCP_1.6.pdf
HOST = "192.168.1.70"
PORT = 4999  # Port to listen on (non-privileged ports are > 1023)

# Value to submit to device to accept command
CR = b'\r'
# Value to receive as response to the above request
CR_RESP = b'\r\n#'

# Commands for amplifier
POWER_CMD = 'PR'
VOLUME_CMD = 'VO'
CHANNEL_CMD = 'CH'

MAX_VOLUME = 38
MAX_CHANNEL_ZONE = 6


class ControlConfig:
    def __init__(self, commands, host: str, port: int):
        self.commands = commands
        self.host = host
        self.port = port


# Defined based on:
# https://www.parts-express.com/pedocs/tech-docs/300-585--dayton-audio-dax66-rs232-commands.txt
class Amplifier(Enum):
    _init_ = 'value string'

    PRIMARY = 10, 'primary'
    SECONDARY = 20, 'secondary'
    TERTIARY = 30, 'tertiary'

    def __str__(self):
        return self.string

    @classmethod
    def _missing_value_(cls, value):
        for member in cls:
            if member.string == value:
                return member


class PowerCommand(Enum):
    _init_ = 'value string'
    OFF = 0, 'off'
    ON = 1, 'on'

    def __str__(self):
        return self.string

    @classmethod
    def _missing_value_(cls, value):
        for member in cls:
            if member.string == value:
                return member


def issue_command(commands, host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        for command in commands:
            s.sendall(command)
            response = s.recv(1024)
            # print(f'response: {data!r}')
            if response == command:
                s.sendall(CR)
                response = s.recv(1024)
                # print(f'response: {data!r}')
                if response == CR_RESP:
                    print('command successful!')
                else:
                    print('command failed')
            else:
                print('command failed')


def parse_args(arguments):
    host = HOST
    if arguments.Host:
        print("Host is: %s" % arguments.Host)
        host = arguments.Host

    port = PORT
    if arguments.Port:
        if arguments.Port.isnumeric():
            print("Port is: %s" % arguments.Port)
            port = int(arguments.Port)
        else:
            print('Port %s is invalid' % arguments.Port)
            exit(1)

    amp_ch = 0
    if arguments.Amplifier:
        enum_amp = Amplifier(arguments.Amplifier)
        amp_ch = enum_amp.value
    else:
        print('Amplifier %s is invalid' % arguments.Amplifier)
        exit(1)

    if arguments.Zone:
        if arguments.Zone.isnumeric():
            zone_int = int(arguments.Zone)
            if 0 < zone_int < 6:
                amp_ch += zone_int
            else:
                print('Zone %s is invalid' % arguments.Zone)
                exit(1)
        else:
            print('Zone %s is invalid' % arguments.Zone)
            exit(1)

    power_cmd = None
    if arguments.Power:
        enum_power = PowerCommand(arguments.Power)
        power_int = enum_power.value
        power_cmd = f"{power_int:02d}"

    volume_cmd = None
    if arguments.Volume:
        if arguments.Volume.isnumeric():
            vol_int = int(arguments.Volume)
            if 0 <= vol_int <= 100:
                volume_calc = int((vol_int * MAX_VOLUME) / 100)
                volume_cmd = f"{volume_calc:02d}"
            else:
                print('Invalid volume %s' % arguments.Volume)
                exit(1)
        else:
            print('Invalid volume %s' % arguments.Volume)
            exit(1)

    channel_cmd = None
    if arguments.Channel:
        if arguments.Channel.isnumeric():
            ch_int = int(arguments.Channel)
            if 0 < ch_int < 6:
                channel_cmd = f"{ch_int:02d}"
            else:
                print('Zone %s is invalid' % arguments.Zone)
                exit(1)
        else:
            print('Zone %s is invalid' % arguments.Zone)
            exit(1)

    command_pre = '<'
    amp_ch = f"{amp_ch:02d}"
    command_pre += amp_ch

    cmds = []
    if power_cmd:
        cmd = command_pre
        cmd += POWER_CMD
        cmd += power_cmd
        cmds.append(bytes(cmd, encoding="utf-8"))
    if channel_cmd:
        cmd = command_pre
        cmd += CHANNEL_CMD
        cmd += channel_cmd
        cmds.append(bytes(cmd, encoding="utf-8"))
    if volume_cmd:
        cmd = command_pre
        cmd += VOLUME_CMD
        cmd += volume_cmd
        cmds.append(bytes(cmd, encoding="utf-8"))
    return ControlConfig(cmds, host, port)


if __name__ == '__main__':
    # Initialize parser
    parser = argparse.ArgumentParser()

    # Adding optional argument
    parser.add_argument('-b', '--Host', help='iTach Flex (or other serial communication device) IP address -> '
                                             'default=192.168.1.70')
    parser.add_argument('-p', '--Port', help='TCP port for serial data -> default=4999')
    parser.add_argument('-a', '--Amplifier', help='Amplifier to control. Options: primary, secondary, tertiary')
    parser.add_argument('-z', '--Zone', help='Zone to control. Options: 1-6')
    parser.add_argument('-d', '--Power', help='Power on/off. Options: on, off')
    parser.add_argument('-v', '--Volume', help='Set volume level. Options: 0-100')
    parser.add_argument('-c', '--Channel', help='Set channel. Options: 1-6')

    # Read arguments from command line
    args = parser.parse_args()

    # Validate and get commands/configs
    configs = parse_args(args)

    issue_command(configs.commands, host=configs.host, port=configs.port)