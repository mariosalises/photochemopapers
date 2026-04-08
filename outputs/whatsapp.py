#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# WhatsApp Publisher
# Uses Twilio WhatsApp API (free tier available)
# Setup: Get Twilio account, verify number, enable WhatsApp sandbox
#

from twilio.rest import Client


class WhatsAppPublisher:
    def __init__(self, config):
        self.config = config
        self.client = None
        if 'whatsapp' in config:
            self._init_twilio()

    def _init_twilio(self):
        cred = self.config['whatsapp']
        self.client = Client(cred['account_sid'], cred['auth_token'])
        self.from_number = f"whatsapp:{cred['from_number']}"
        self.to_group = cred.get('to_group', [])  # List of numbers or group ID
        print("WhatsApp (Twilio) initialized")

    def publish(self, message):
        if not self.client:
            return
        body = f"📄 {message['title']}\n"
        if message.get('source'):
            body += f"Source: {message['source']}\n"
        if message.get('summary'):
            body += f"Summary: {message['summary'][:150]}...\n"
        if message.get('tags'):
            body += f"Tags: {', '.join(message['tags'])}\n"
        body += f"Link: {message['link']}"
        for to in self.to_group:
            try:
                self.client.messages.create(
                    body=body,
                    from_=self.from_number,
                    to=f"whatsapp:{to}"
                )
                print(f"WhatsApp sent to {to}")
            except Exception as e:
                print(f"WhatsApp error: {e}")