## Telegram bot wrapper
A simple backend for [Telegram messenger bots](https://core.telegram.org/bots).

Here's a minimal example of how to turn a bot into a remote shell client.

```python
import subprocess
from telebot import Client

def handler(message):
    command = '{}; exit 0'.format(message)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    if output:
        answer = output.decode('utf8', errors='replace').rstrip('\n')
        return '```{}```'.format(answer)

client = Client(token='your-API-token', handler=handler)
client.start()
```
<p align="center">
  <img src="https://github.com/qweeze/telegram-bot-wrapper/raw/master/examples/screenshot.png?raw=true" width=50% alt="screenshot"/>
</p>