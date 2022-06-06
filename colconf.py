#!/usr/bin/python3


import conf
import getpass
import logging.config
import os.path
import time
from netmiko import ConnectHandler, NetmikoTimeoutException, ReadTimeout, NetmikoAuthenticationException

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
print(os.path.join(BASE_DIR, 'colconf.log'))
LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'base': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'debug_to_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'base',
            'filename': os.path.join(BASE_DIR, 'colconf.log'),
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'colconf': {
            'handlers': ['debug_to_file'],
            'level': 'DEBUG',
        },
    },
}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('colconf')


def time_tracker(function):
    def intermediate(*args, **kwargs):
        start_time = time.time()
        result = function(*args, **kwargs)
        end_time = time.time()
        run_time = end_time - start_time
        print(f'Run time: {round(run_time, 1)} s')
        return result
    return intermediate


def log_handler(message, device_ip=None):
    if device_ip is not None:
        logger.error(f"{device_ip}:{message}", exc_info=False)
        print(f"{'[NOT OK]':10} {device_ip}")
    else:
        logger.error(message, exc_info=False)
        print(message)


class SingleDeviceExecuteCommand:
    def __init__(self, ssh_user, ssh_password, device_ip, command):
        self.command = command
        self.device = {
            'device_type': 'cisco_ios',
            'host': device_ip,
            'username': ssh_user,
            'password': ssh_password
        }

    def execute(self, ssh_connection):
        _initial_prompt_string = ssh_connection.find_prompt()
        _cli_output = ssh_connection.send_command(command_string=self.command, expect_string='Address')
        _cli_output += ssh_connection.send_command(command_string='\n', expect_string='Destination')
        _cli_output += ssh_connection.send_command(command_string='\n', expect_string='Destination')
        _cli_output += ssh_connection.send_command(command_string='\n', expect_string=_initial_prompt_string)

    def ssh_operation(self):
        with ConnectHandler(**self.device) as ssh_connection:
            try:
                self.execute(ssh_connection)
                print(f"{'[OK]':10} {self.device['host']}")
            except ReadTimeout:
                log_handler(message="can't execute command", device_ip=self.device['host'])

    def run(self):
        try:
            self.ssh_operation()
        except NetmikoTimeoutException:
            log_handler(message="can't connect to appliance", device_ip=self.device['host'])


class TreatAllDevices:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.server_username = ''
        self.server_password = ''
        self.command = ''
        self.devices = []
        self.devices_file = os.path.join(BASE_DIR, 'devices.txt')

    def get_credentials(self):
        self.username = input('SSH username: ')
        self.password = getpass.getpass(prompt='SSH password: ')
        self.server_username = input('WIA-MES-TEAM username: ')
        self.server_password = getpass.getpass(prompt='WIA-MES-TEAM password: ')

    def compile_command(self):
        self.command = f'copy startup ' \
                       f'scp://{self.server_username}:{self.server_password}@' \
                       f'{conf.SERVER_IP}/{conf.FOLDER_PATH}'

    def load_devices(self):
        with open(file=self.devices_file, mode='r', encoding='utf8') as _file_content:
            for line in _file_content:
                line = line.splitlines()[0]
                if line:
                    self.devices.append(line)

    @time_tracker
    def configure_devices(self):
        for device_ip in self.devices:
            SingleDeviceExecuteCommand(ssh_user=self.username,
                                       ssh_password=self.password,
                                       device_ip=device_ip,
                                       command=self.command).run()

    def run(self):
        self.get_credentials()
        self.compile_command()
        try:
            self.load_devices()
        except Exception as exc:
            log_handler(message=exc)
        else:
            try:
                self.configure_devices()
            except NetmikoAuthenticationException:
                log_handler(message="wrong ssh password")


if __name__ == '__main__':
    TreatAllDevices().run()
