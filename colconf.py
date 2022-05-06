#! /usr/bin/python3


import getpass
import logging.config
import time
from netmiko import ConnectHandler, NetmikoTimeoutException, ReadTimeout
from pathlib import Path

log_config = {
    'version': 1,
    'formatters': {
        'full': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'main_full_to_file': {
            'class': 'logging.FileHandler',
            'formatter': 'full',
            'filename': 'colconf.log',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['main_full_to_file'],
            'level': 'DEBUG',
        },
    },
}

logging.config.dictConfig(log_config)
logger = logging.getLogger('main')


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
        logger.exception(f"{device_ip}:{message}", exc_info=False)
        print(f"[NOT OK] {device_ip:>20}")
    else:
        logger.exception(message, exc_info=False)
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
                print(f"[OK] {self.device['host']:>20}")
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
        self.program_hosting_folder = Path(__file__).parent.resolve()

    def get_credentials(self):
        self.username = input('SSH username: ')
        self.password = getpass.getpass(prompt='SSH password: ')
        self.server_username = input('WIA-MES-TEAM username: ')
        self.server_password = getpass.getpass(prompt='WIA-MES-TEAM password: ')

    def compile_command(self):
        self.command = f'copy startup ' \
                       f'scp://{self.server_username}:{self.server_password}@10.115.21.55/configs/switches/'

    def load_devices(self):
        _devices_full_path = self.program_hosting_folder / 'devices.txt'
        with open(file=_devices_full_path, mode='r', encoding='utf8') as file_content:
            for line in file_content:
                line = line.splitlines()[0]
                if line:
                    self.devices.append(line)

    @time_tracker
    def configure_devices(self):
        for device_ip in self.devices:
            command_runner = SingleDeviceExecuteCommand(ssh_user=self.username,
                                                        ssh_password=self.password,
                                                        device_ip=device_ip,
                                                        command=self.command)
            command_runner.run()

    def run(self):
        self.get_credentials()
        self.compile_command()
        try:
            self.load_devices()
        except Exception:
            log_handler(message="Can't open devices file")
        else:
            self.configure_devices()


if __name__ == '__main__':
    controller = TreatAllDevices()
    controller.run()
