import subprocess
from telebot import Client


def handler(command):
    output = subprocess.check_output(
        '{}; exit 0'.format(command),
        shell=True, stderr=subprocess.STDOUT)
    if output:
        return '```{}```'.format(
            output.decode('utf8', errors='replace').rstrip('\n'))


if __name__ == '__main__':
    client = Client(token='your-API-token', handler=handler)
    client.start()
