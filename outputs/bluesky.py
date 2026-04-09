#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Bluesky Publisher
# Uses the official AT Protocol Python client
#

import os
from pathlib import Path

from atproto import Client, SessionEvent, models


class BlueskyPublisher:
    MAX_POST_LENGTH = 300
    DEFAULT_SESSION_PATH = ".bluesky_session"
    PROFILE_RKEY = "self"
    BOT_LABEL_VALUE = "bot"

    def __init__(self, config):
        self.config = config if isinstance(config, dict) else {}
        self.client = None
        self.username = os.environ.get("BLUESKY_USERNAME")
        self.password = os.environ.get("BLUESKY_PASSWORD")
        self.session_path = self._resolve_session_path()
        self.enabled = False
        self._init_bluesky()

    def _resolve_session_path(self):
        configured = self.config.get("bluesky", {}).get("session_path", self.DEFAULT_SESSION_PATH)
        return Path(configured)

    def _init_bluesky(self):
        has_config_block = "bluesky" in self.config
        has_credentials = bool(self.username and self.password)
        if not has_config_block and not has_credentials:
            return

        if not self.username or not self.password:
            raise ValueError(
                "Bluesky credentials are required. Set BLUESKY_USERNAME and BLUESKY_PASSWORD in the environment."
            )

        try:
            self.client = self.create_authenticated_client(
                self.username,
                self.password,
                self.session_path,
            )
            self._save_session()
            self.enabled = True
            print("Bluesky initialized")
        except Exception as e:
            raise RuntimeError(f"Bluesky initialization failed: {e}") from e

    def _save_session(self):
        if not self.client:
            return
        session_string = self.client.export_session_string()
        self.session_path.write_text(session_string, encoding="utf-8")

    def publish(self, message):
        if not self.enabled or not self.client:
            return

        post_text = self._build_post_text(message)
        try:
            self.client.send_post(post_text)
            print("Bluesky post sent successfully")
        except Exception as e:
            print(f"Bluesky send failed: {e}")
            raise

    def _build_post_text(self, message):
        title = self._clean_text(message.get("title", ""))
        tags = self._select_tags(message)
        link = message.get("link", "").strip()

        tag_line = ""
        if tags:
            tag_line = "Tags: " + ", ".join(tags)

        lines = [line for line in [title, tag_line, link] if line]
        text = "\n".join(lines)
        if len(text) <= self.MAX_POST_LENGTH:
            return text

        reserved = len(link)
        if tag_line:
            reserved += len(tag_line) + 1
        if reserved:
            reserved += 1

        max_title_length = max(40, self.MAX_POST_LENGTH - reserved)
        shortened_title = self._truncate(title, max_title_length)
        lines = [line for line in [shortened_title, tag_line, link] if line]
        return "\n".join(lines)

    def _select_tags(self, message):
        tags = message.get("tags", []) or []
        score_reasons = message.get("score_reasons", []) or []

        selected = []
        for tag in tags:
            clean_tag = self._clean_reason_label(tag)
            if clean_tag and clean_tag not in selected:
                selected.append(clean_tag)
            if len(selected) >= 2:
                return selected

        for reason in score_reasons:
            clean_reason = self._clean_reason_label(reason)
            if clean_reason and not clean_reason.startswith("-") and clean_reason not in selected:
                selected.append(clean_reason)
            if len(selected) >= 2:
                break
        return selected[:2]

    def _clean_reason_label(self, value):
        if not value:
            return ""
        return str(value).lstrip("+").strip()

    def _clean_text(self, text):
        if not text:
            return ""
        return " ".join(str(text).split())

    def _truncate(self, text, max_length):
        if len(text) <= max_length:
            return text
        return text[: max_length - 3].rstrip() + "..."

    @classmethod
    def create_authenticated_client(cls, username, password, session_path=None):
        if not username or not password:
            raise ValueError(
                "Bluesky credentials are required. Set BLUESKY_USERNAME and BLUESKY_PASSWORD in the environment."
            )

        client = Client()
        session_file = Path(session_path or cls.DEFAULT_SESSION_PATH)

        @client.on_session_change
        def _persist_session(event, session):
            if event in (SessionEvent.CREATE, SessionEvent.REFRESH, SessionEvent.IMPORT):
                session_file.write_text(client.export_session_string(), encoding="utf-8")

        if session_file.exists():
            session_string = session_file.read_text(encoding="utf-8").strip()
            if session_string:
                client.login(session_string=session_string)
            else:
                client.login(username, password)
        else:
            client.login(username, password)

        session_file.write_text(client.export_session_string(), encoding="utf-8")
        return client

    @classmethod
    def apply_bot_self_label(cls, username, password, session_path=None):
        client = cls.create_authenticated_client(username, password, session_path)
        repo = client.me.did
        existing_record = None

        try:
            existing_record = client.app.bsky.actor.profile.get(repo, cls.PROFILE_RKEY)
            profile_record = existing_record.value
        except Exception:
            profile_record = models.AppBskyActorProfile.Record()

        current_labels = []
        if profile_record.labels and getattr(profile_record.labels, "values", None):
            current_labels = [label.val for label in profile_record.labels.values]

        if cls.BOT_LABEL_VALUE not in current_labels:
            current_labels.append(cls.BOT_LABEL_VALUE)

        profile_record.labels = models.ComAtprotoLabelDefs.SelfLabels(
            values=[models.ComAtprotoLabelDefs.SelfLabel(val=value) for value in current_labels]
        )

        client.com.atproto.repo.put_record(
            models.ComAtprotoRepoPutRecord.Data(
                repo=repo,
                collection="app.bsky.actor.profile",
                rkey=cls.PROFILE_RKEY,
                record=profile_record,
                validate_=True,
            )
        )
        return current_labels

    @staticmethod
    def bot_profile_disclosure_note():
        return (
            "Recommended Bluesky profile disclosure: "
            "'Bot account posting automatically selected papers on photoactive anticancer coordination and organometallic chemistry.'"
        )
