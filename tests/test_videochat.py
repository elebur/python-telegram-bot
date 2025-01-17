#!/usr/bin/env python
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2022
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

import datetime as dtm
import pytest

from telegram import (
    VideoChatStarted,
    VideoChatEnded,
    VideoChatParticipantsInvited,
    User,
    VideoChatScheduled,
)
from telegram.utils.helpers import to_timestamp


@pytest.fixture(scope='class')
def user1():
    return User(first_name='Misses Test', id=123, is_bot=False)


@pytest.fixture(scope='class')
def user2():
    return User(first_name='Mister Test', id=124, is_bot=False)


class TestVideoChatStarted:
    def test_slot_behaviour(self, recwarn, mro_slots):
        action = VideoChatStarted()
        for attr in action.__slots__:
            assert getattr(action, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert not action.__dict__, f"got missing slot(s): {action.__dict__}"
        assert len(mro_slots(action)) == len(set(mro_slots(action))), "duplicate slot"
        action.custom = 'should give warning'
        assert len(recwarn) == 1 and 'custom' in str(recwarn[0].message), recwarn.list

    def test_de_json(self):
        video_chat_started = VideoChatStarted.de_json({}, None)
        assert isinstance(video_chat_started, VideoChatStarted)

    def test_to_dict(self):
        video_chat_started = VideoChatStarted()
        video_chat_dict = video_chat_started.to_dict()
        assert video_chat_dict == {}


class TestVideoChatEnded:
    duration = 100

    def test_slot_behaviour(self, recwarn, mro_slots):
        action = VideoChatEnded(8)
        for attr in action.__slots__:
            assert getattr(action, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert not action.__dict__, f"got missing slot(s): {action.__dict__}"
        assert len(mro_slots(action)) == len(set(mro_slots(action))), "duplicate slot"
        action.custom = 'should give warning'
        assert len(recwarn) == 1 and 'custom' in str(recwarn[0].message), recwarn.list

    def test_de_json(self):
        json_dict = {'duration': self.duration}
        video_chat_ended = VideoChatEnded.de_json(json_dict, None)

        assert video_chat_ended.duration == self.duration

    def test_to_dict(self):
        video_chat_ended = VideoChatEnded(self.duration)
        video_chat_dict = video_chat_ended.to_dict()

        assert isinstance(video_chat_dict, dict)
        assert video_chat_dict["duration"] == self.duration

    def test_equality(self):
        a = VideoChatEnded(100)
        b = VideoChatEnded(100)
        c = VideoChatEnded(50)
        d = VideoChatStarted()

        assert a == b
        assert hash(a) == hash(b)

        assert a != c
        assert hash(a) != hash(c)

        assert a != d
        assert hash(a) != hash(d)


class TestVideoChatParticipantsInvited:
    def test_slot_behaviour(self, recwarn, mro_slots):
        action = VideoChatParticipantsInvited([user1])
        for attr in action.__slots__:
            assert getattr(action, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert not action.__dict__, f"got missing slot(s): {action.__dict__}"
        assert len(mro_slots(action)) == len(set(mro_slots(action))), "duplicate slot"
        action.custom = 'should give warning'
        assert len(recwarn) == 1 and 'custom' in str(recwarn[0].message), recwarn.list

    def test_de_json(self, user1, user2, bot):
        json_data = {"users": [user1.to_dict(), user2.to_dict()]}
        video_chat_participants = VideoChatParticipantsInvited.de_json(json_data, bot)

        assert isinstance(video_chat_participants.users, list)
        assert video_chat_participants.users[0] == user1
        assert video_chat_participants.users[1] == user2
        assert video_chat_participants.users[0].id == user1.id
        assert video_chat_participants.users[1].id == user2.id

    def test_to_dict(self, user1, user2):
        video_chat_participants = VideoChatParticipantsInvited([user1, user2])
        video_chat_dict = video_chat_participants.to_dict()

        assert isinstance(video_chat_dict, dict)
        assert video_chat_dict["users"] == [user1.to_dict(), user2.to_dict()]
        assert video_chat_dict["users"][0]["id"] == user1.id
        assert video_chat_dict["users"][1]["id"] == user2.id

    def test_equality(self, user1, user2):
        a = VideoChatParticipantsInvited([user1])
        b = VideoChatParticipantsInvited([user1])
        c = VideoChatParticipantsInvited([user1, user2])
        d = VideoChatParticipantsInvited([user2])
        e = VideoChatStarted()

        assert a == b
        assert hash(a) == hash(b)

        assert a != c
        assert hash(a) != hash(c)

        assert a != d
        assert hash(a) != hash(d)

        assert a != e
        assert hash(a) != hash(e)


class TestVideoChatScheduled:
    start_date = dtm.datetime.utcnow()

    def test_slot_behaviour(self, recwarn, mro_slots):
        inst = VideoChatScheduled(self.start_date)
        for attr in inst.__slots__:
            assert getattr(inst, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert not inst.__dict__, f"got missing slot(s): {inst.__dict__}"
        assert len(mro_slots(inst)) == len(set(mro_slots(inst))), "duplicate slot"
        inst.custom, inst.start_date = 'should give warning', self.start_date
        assert len(recwarn) == 1 and 'custom' in str(recwarn[0].message), recwarn.list

    def test_expected_values(self):
        assert pytest.approx(VideoChatScheduled(start_date=self.start_date) == self.start_date)

    def test_de_json(self, bot):
        assert VideoChatScheduled.de_json({}, bot=bot) is None

        json_dict = {'start_date': to_timestamp(self.start_date)}
        video_chat_scheduled = VideoChatScheduled.de_json(json_dict, bot)

        assert pytest.approx(video_chat_scheduled.start_date == self.start_date)

    def test_to_dict(self):
        video_chat_scheduled = VideoChatScheduled(self.start_date)
        video_chat_scheduled_dict = video_chat_scheduled.to_dict()

        assert isinstance(video_chat_scheduled_dict, dict)
        assert video_chat_scheduled_dict["start_date"] == to_timestamp(self.start_date)

    def test_equality(self):
        a = VideoChatScheduled(self.start_date)
        b = VideoChatScheduled(self.start_date)
        c = VideoChatScheduled(dtm.datetime.utcnow() + dtm.timedelta(seconds=5))
        d = VideoChatStarted()

        assert a == b
        assert hash(a) == hash(b)

        assert a != c
        assert hash(a) != hash(c)

        assert a != d
        assert hash(a) != hash(d)
