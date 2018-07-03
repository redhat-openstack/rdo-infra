#!/bin/env python

import argparse
import thread
import json
import irc.bot
import logging
import sys

from flask import Flask, request
from get_alerts import get_alerts

app = Flask(__name__)

class GrafanaIRCAlertBot(irc.bot.SingleServerIRCBot):
    def __init__(self, grafana_host, grafana_key):
        irc.bot.SingleServerIRCBot.__init__(
                self,
                [('irc.freenode.net', 6667)],
                'ruck-rover-alert', 'Openstack triplo ci alert bot')
        self.channel = '#tripleo-ci'
        self.grafana_host = grafana_host
        self.grafana_key = grafana_key

    def on_welcome(self, connection, event):
        connection.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(
                self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def send_message(self, message):
        self.connection.privmsg(self.channel, message)

    def send_alert(self, alert):
        if alert['state'] != 'ok':
            self.send_message("{title}: {message}".format(**alert))

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        splitted_cmd = cmd.split()
        action = splitted_cmd[0]
        if action == "alerts":
            alerts = get_alerts(
                    self.grafana_host, self.grafana_key)
            for alert in alerts:
            # Filter alerts if we have filters on the action
                if len(splitted_cmd) > 1:
                    filters = splitted_cmd[1:]
                    if not any(filter in alert['name'] for filter in filters):
                        continue

                self.send_alert(
                    {'title': alert['name'],
                     'message': alert['Message'],
                     'state' : 'alerting'})
        else:
            self.send_message("Not understood: " + cmd)

@app.route('/',methods=['POST'])
def alert():
   irc_alert.send_alert(json.loads(request.data))
   return "OK"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Export grafana as json files")

    parser.add_argument('--grafana-host', required=True)
    parser.add_argument('--grafana-key', required=True)

    args = parser.parse_args()


    irc_alert = GrafanaIRCAlertBot(args.grafana_host, args.grafana_key)
    thread.start_new_thread(app.run, ())
    irc_alert.start()
