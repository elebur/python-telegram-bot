#!/usr/bin/env python
#
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
import os
import inspect

import certifi
import pytest
from bs4 import BeautifulSoup
from telegram.vendor.ptb_urllib3 import urllib3

import telegram
from tests.conftest import env_var_2_bool

IGNORED_OBJECTS = ('ResponseParameters', 'CallbackGame')
IGNORED_PARAMETERS = {
    'self',
    'args',
    '_kwargs',
    'read_latency',
    'network_delay',
    'timeout',
    'bot',
    'api_kwargs',
}


def find_next_sibling_until(tag, name, until):
    for sibling in tag.next_siblings:
        if sibling is until:
            return
        if sibling.name == name:
            return sibling


def parse_table(h4):
    table = find_next_sibling_until(h4, 'table', h4.find_next_sibling('h4'))
    if not table:
        return []
    t = []
    for tr in table.find_all('tr')[1:]:
        t.append([td.text for td in tr.find_all('td')])
    return t


def check_method(h4):
    name = h4.text
    method = getattr(telegram.Bot, name)
    table = parse_table(h4)

    # Check arguments based on source
    sig = inspect.signature(method, follow_wrapped=True)

    checked = []
    for parameter in table:
        param = sig.parameters.get(parameter[0])
        assert param is not None, f"Parameter {parameter[0]} not found in {method.__name__}"
        # TODO: Check type via docstring
        # TODO: Check if optional or required
        checked.append(parameter[0])

    ignored = IGNORED_PARAMETERS.copy()
    if name == 'getUpdates':
        ignored -= {'timeout'}  # Has it's own timeout parameter that we do wanna check for
    elif name in (
        f'send{media_type}'
        for media_type in [
            'Animation',
            'Audio',
            'Document',
            'Photo',
            'Video',
            'VideoNote',
            'Voice',
        ]
    ):
        ignored |= {'filename'}  # Convenience parameter
    elif name == 'setGameScore':
        ignored |= {'edit_message'}  # TODO: Now deprecated, so no longer in telegrams docs
    elif name == 'sendContact':
        ignored |= {'contact'}  # Added for ease of use
    elif name in ['sendLocation', 'editMessageLiveLocation']:
        ignored |= {'location'}  # Added for ease of use
    elif name == 'sendVenue':
        ignored |= {'venue'}  # Added for ease of use
    elif name == 'answerInlineQuery':
        ignored |= {'current_offset'}  # Added for ease of use
    elif name == 'promoteChatMember':
        ignored |= {'can_manage_voice_chats'}  # for backwards compatibility

    assert (sig.parameters.keys() ^ checked) - ignored == set()


def check_object(h4):
    name = h4.text
    obj = getattr(telegram, name)
    table = parse_table(h4)

    # Check arguments based on source
    sig = inspect.signature(obj, follow_wrapped=True)

    checked = []
    for parameter in table:
        field = parameter[0]
        if field == 'from':
            field = 'from_user'
        elif (
            name.startswith('InlineQueryResult')
            or name.startswith('InputMedia')
            or name.startswith('BotCommandScope')
            or name.startswith('MenuButton')
        ) and field == 'type':
            continue
        elif (name.startswith('ChatMember')) and field == 'status':
            continue
        elif (
            name.startswith('PassportElementError') and field == 'source'
        ) or field == 'remove_keyboard':
            continue

        param = sig.parameters.get(field)
        assert param is not None, f"Attribute {field} not found in {obj.__name__}"
        # TODO: Check type via docstring
        # TODO: Check if optional or required
        checked.append(field)

    ignored = IGNORED_PARAMETERS.copy()
    if name == 'InputFile':
        return
    if name == 'InlineQueryResult':
        ignored |= {'id', 'type'}  # attributes common to all subclasses
    if name == 'ChatMember':
        ignored |= {
            'user',
            'status',
            'can_manage_video_chats',
        }  # attributes common to all subclasses
    if name == 'ChatMember':
        ignored |= {
            'can_add_web_page_previews',  # for backwards compatibility
            'can_be_edited',
            'can_change_info',
            'can_delete_messages',
            'can_edit_messages',
            'can_invite_users',
            'can_manage_chat',
            'can_manage_voice_chats',
            'can_pin_messages',
            'can_post_messages',
            'can_promote_members',
            'can_restrict_members',
            'can_send_media_messages',
            'can_send_messages',
            'can_send_other_messages',
            'can_send_polls',
            'custom_title',
            'is_anonymous',
            'is_member',
            'until_date',
        }
    if name == 'BotCommandScope':
        ignored |= {'type'}  # attributes common to all subclasses
    if name == 'MenuButton':
        ignored |= {'type'}  # attributes common to all subclasses
    elif name == 'User':
        ignored |= {'type'}  # TODO: Deprecation
    elif name in ('PassportFile', 'EncryptedPassportElement'):
        ignored |= {'credentials'}
    elif name == 'PassportElementError':
        ignored |= {'message', 'type', 'source'}
    elif name.startswith('InputMedia'):
        ignored |= {'filename'}  # Convenience parameter
    elif name == 'ChatMemberAdministrator':
        ignored |= {'can_manage_voice_chats'}  # for backwards compatibility
    elif name == 'Message':
        # for backwards compatibility
        ignored |= {
            'voice_chat_ended',
            'voice_chat_participants_invited',
            'voice_chat_scheduled',
            'voice_chat_started',
        }

    assert (sig.parameters.keys() ^ checked) - ignored == set()


argvalues = []
names = []
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
request = http.request('GET', 'https://core.telegram.org/bots/api')
soup = BeautifulSoup(request.data.decode('utf-8'), 'html.parser')

for thing in soup.select('h4 > a.anchor'):
    # Methods and types don't have spaces in them, luckily all other sections of the docs do
    # TODO: don't depend on that
    if '-' not in thing['name']:
        h4 = thing.parent

        # Is it a method
        if h4.text[0].lower() == h4.text[0]:
            argvalues.append((check_method, h4))
            names.append(h4.text)
        elif h4.text not in IGNORED_OBJECTS:  # Or a type/object
            argvalues.append((check_object, h4))
            names.append(h4.text)


@pytest.mark.parametrize(('method', 'data'), argvalues=argvalues, ids=names)
@pytest.mark.skipif(
    not env_var_2_bool(os.getenv('TEST_OFFICIAL')), reason='test_official is not enabled'
)
def test_official(method, data):
    method(data)
