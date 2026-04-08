#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Email Publisher (Future)
# Uses smtplib for newsletters
#

import smtplib
from email.mime.text import MIMEText


class EmailPublisher:
    def __init__(self, config):
        self.config = config
        # Future: init SMTP

    def publish(self, message):
        # Placeholder for future implementation
        print("Email not implemented yet")