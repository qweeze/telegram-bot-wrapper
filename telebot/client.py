from __future__ import print_function
from __future__ import unicode_literals

import sys
import requests
from time import sleep
from threading import Thread
import atexit
if sys.version_info < (3, 0):
    from Queue import Queue
else:
    from queue import Queue
    basestring = (str, bytes)


HOST = 'https://api.telegram.org'


class Worker(Thread):

    def __init__(self, client):
        super(Worker, self).__init__()
        self.client = client
        self.daemon = True

    def run(self):
        while True:
            command, chat_id = self.client.tasks.get()
            answer = self.client.handler(command)
            if answer:
                if not isinstance(answer, basestring):
                    raise RuntimeError(
                        'Handler should return either a string or None')
                self.client.results.put((answer, chat_id))
            self.client.tasks.task_done()


class Sender(Thread):

    def __init__(self, client):
        super(Sender, self).__init__()
        self.client = client

    def run(self):
        while True:
            result, chat_id = self.client.results.get()
            self.client.api_call(
                method='sendMessage',
                chat_id=chat_id, text=result, parse_mode='Markdown'
            )
            self.client.results.task_done()


class Client(Thread):

    def __init__(self, token, handler, n_threads=10, timeout=300,
                 trusted_users=None):
        '''
        A simple backend for Telegram messenger bot
        https://core.telegram.org/bots

        :param token: API token
        :param handler: A callable that takes a message for bot
            and possibly returns an answer
        :param n_threads: Number of threads to spawn
        :param timeout: A long polling request timeout for `getUpdates` method
        :param trusted_users: a collection of users' ids. If provided,
            only messages from these users are handled
        '''
        super(Client, self).__init__()
        self.token = token
        self.handler = handler
        self.timeout = timeout

        if trusted_users is None:
            self.validate = lambda msg: bool(msg)
        else:
            self.validate = (
                lambda msg: msg and msg['from']['id'] in trusted_users)

        self.tasks = Queue(n_threads)
        self.results = Queue()
        for _ in range(n_threads):
            Worker(self).start()
        Sender(self).start()
        atexit.register(self.results.join)

    def run(self):
        update_id = -1
        while True:
            sleep(.1)
            updates = self.api_call(
                method='getUpdates',
                offset=update_id, timeout=self.timeout
            )
            if not updates:
                continue
            update_id = updates[-1]['update_id'] + 1
            msgs = filter(
                self.validate,
                (m.get('message') or m.get('edited_message') for m in updates))
            tasks = ((m['text'], m['chat']['id']) for m in msgs)
            list(map(self.tasks.put, tasks))

    def api_call(self, method, **kwargs):
        res = requests.post(
            url='{}/bot{}/{}'.format(HOST, self.token, method),
            params=kwargs)
        if res.status_code not in (200, 400):
            raise RuntimeError(
                'Api call returned {} status code'.format(res.status_code))
        responce = res.json()
        if not responce['ok']:
            raise RuntimeError(responce.get('description', 'Unknown API error'))
        return res.json()['result']

    def send(self, chat_id, text):
        self.results.put((text, chat_id))
