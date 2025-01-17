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
from pathlib import Path
from time import sleep

import pytest
from flaky import flaky

from telegram import Sticker, PhotoSize, TelegramError, StickerSet, Audio, MaskPosition, Bot, File
from telegram.error import BadRequest
from tests.conftest import check_shortcut_call, check_shortcut_signature, check_defaults_handling


@pytest.fixture(scope='function')
def sticker_file():
    f = open('tests/data/telegram.webp', 'rb')
    yield f
    f.close()


@pytest.fixture(scope='class')
def sticker(bot, chat_id):
    with open('tests/data/telegram.webp', 'rb') as f:
        return bot.send_sticker(chat_id, sticker=f, timeout=50).sticker


@pytest.fixture(scope='function')
def animated_sticker_file():
    f = open('tests/data/telegram_animated_sticker.tgs', 'rb')
    yield f
    f.close()


@pytest.fixture(scope='class')
def animated_sticker(bot, chat_id):
    with open('tests/data/telegram_animated_sticker.tgs', 'rb') as f:
        return bot.send_sticker(chat_id, sticker=f, timeout=50).sticker


@pytest.fixture(scope='function')
def video_sticker_file():
    with open('tests/data/telegram_video_sticker.webm', 'rb') as f:
        yield f


@pytest.fixture(scope='class')
def video_sticker(bot, chat_id):
    with open('tests/data/telegram_video_sticker.webm', 'rb') as f:
        return bot.send_sticker(chat_id, sticker=f, timeout=50).sticker


class TestSticker:
    # sticker_file_url = 'https://python-telegram-bot.org/static/testfiles/telegram.webp'
    # Serving sticker from gh since our server sends wrong content_type
    sticker_file_url = (
        'https://github.com/python-telegram-bot/python-telegram-bot/blob/master'
        '/tests/data/telegram.webp?raw=true'
    )

    emoji = '💪'
    width = 510
    height = 512
    is_animated = False
    is_video = False
    file_size = 39518
    thumb_width = 319
    thumb_height = 320
    thumb_file_size = 21472

    sticker_file_id = '5a3128a4d2a04750b5b58397f3b5e812'
    sticker_file_unique_id = 'adc3145fd2e84d95b64d68eaa22aa33e'

    premium_animation = File("this_is_an_id", "this_is_an_unique_id")

    def test_slot_behaviour(self, sticker, mro_slots, recwarn):
        for attr in sticker.__slots__:
            assert getattr(sticker, attr, 'err') != 'err', f"got extra slot '{attr}'"
        assert not sticker.__dict__, f"got missing slot(s): {sticker.__dict__}"
        assert len(mro_slots(sticker)) == len(set(mro_slots(sticker))), "duplicate slot"
        sticker.custom, sticker.emoji = 'should give warning', self.emoji
        assert len(recwarn) == 1 and 'custom' in str(recwarn[0].message), recwarn.list

    def test_creation(self, sticker):
        # Make sure file has been uploaded.
        assert isinstance(sticker, Sticker)
        assert isinstance(sticker.file_id, str)
        assert isinstance(sticker.file_unique_id, str)
        assert sticker.file_id != ''
        assert sticker.file_unique_id != ''
        assert isinstance(sticker.thumb, PhotoSize)
        assert isinstance(sticker.thumb.file_id, str)
        assert isinstance(sticker.thumb.file_unique_id, str)
        assert sticker.thumb.file_id != ''
        assert sticker.thumb.file_unique_id != ''

    def test_expected_values(self, sticker):
        assert sticker.width == self.width
        assert sticker.height == self.height
        assert sticker.is_animated == self.is_animated
        assert sticker.is_video == self.is_video
        assert sticker.file_size == self.file_size
        assert sticker.thumb.width == self.thumb_width
        assert sticker.thumb.height == self.thumb_height
        assert sticker.thumb.file_size == self.thumb_file_size
        # we need to be a premium TG user to send a premium sticker, so the below is not tested
        # assert sticker.premium_animation == self.premium_animation

    @flaky(3, 1)
    def test_send_all_args(self, bot, chat_id, sticker_file, sticker):
        message = bot.send_sticker(
            chat_id, sticker=sticker_file, disable_notification=False, protect_content=True
        )

        assert isinstance(message.sticker, Sticker)
        assert isinstance(message.sticker.file_id, str)
        assert isinstance(message.sticker.file_unique_id, str)
        assert message.sticker.file_id != ''
        assert message.sticker.file_unique_id != ''
        assert message.sticker.width == sticker.width
        assert message.sticker.height == sticker.height
        assert message.sticker.is_animated == sticker.is_animated
        assert message.sticker.is_video == sticker.is_video
        assert message.sticker.file_size == sticker.file_size
        # we need to be a premium TG user to send a premium sticker, so the below is not tested
        # assert message.sticker.premium_animation == sticker.premium_animation

        assert isinstance(message.sticker.thumb, PhotoSize)
        assert isinstance(message.sticker.thumb.file_id, str)
        assert isinstance(message.sticker.thumb.file_unique_id, str)
        assert message.sticker.thumb.file_id != ''
        assert message.sticker.thumb.file_unique_id != ''
        assert message.sticker.thumb.width == sticker.thumb.width
        assert message.sticker.thumb.height == sticker.thumb.height
        assert message.sticker.thumb.file_size == sticker.thumb.file_size
        assert message.has_protected_content

    @flaky(3, 1)
    def test_get_and_download(self, bot, sticker):
        new_file = bot.get_file(sticker.file_id)

        assert new_file.file_size == sticker.file_size
        assert new_file.file_id == sticker.file_id
        assert new_file.file_unique_id == sticker.file_unique_id
        assert new_file.file_path.startswith('https://')

        new_file.download('telegram.webp')

        assert os.path.isfile('telegram.webp')

    @flaky(3, 1)
    def test_resend(self, bot, chat_id, sticker):
        message = bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)

        assert message.sticker == sticker

    @flaky(3, 1)
    def test_send_on_server_emoji(self, bot, chat_id):
        server_file_id = 'CAADAQADHAADyIsGAAFZfq1bphjqlgI'
        message = bot.send_sticker(chat_id=chat_id, sticker=server_file_id)
        sticker = message.sticker
        assert sticker.emoji == self.emoji

    @flaky(3, 1)
    def test_send_from_url(self, bot, chat_id):
        message = bot.send_sticker(chat_id=chat_id, sticker=self.sticker_file_url)
        sticker = message.sticker

        assert isinstance(message.sticker, Sticker)
        assert isinstance(message.sticker.file_id, str)
        assert isinstance(message.sticker.file_unique_id, str)
        assert message.sticker.file_id != ''
        assert message.sticker.file_unique_id != ''
        assert message.sticker.width == sticker.width
        assert message.sticker.height == sticker.height
        assert message.sticker.is_animated == sticker.is_animated
        assert message.sticker.is_video == sticker.is_video
        assert message.sticker.file_size == sticker.file_size

        assert isinstance(message.sticker.thumb, PhotoSize)
        assert isinstance(message.sticker.thumb.file_id, str)
        assert isinstance(message.sticker.thumb.file_unique_id, str)
        assert message.sticker.thumb.file_id != ''
        assert message.sticker.thumb.file_unique_id != ''
        assert message.sticker.thumb.width == sticker.thumb.width
        assert message.sticker.thumb.height == sticker.thumb.height
        assert message.sticker.thumb.file_size == sticker.thumb.file_size

    def test_de_json(self, bot, sticker):
        json_dict = {
            'file_id': self.sticker_file_id,
            'file_unique_id': self.sticker_file_unique_id,
            'width': self.width,
            'height': self.height,
            'is_animated': self.is_animated,
            'is_video': self.is_video,
            'thumb': sticker.thumb.to_dict(),
            'emoji': self.emoji,
            'file_size': self.file_size,
            'premium_animation': self.premium_animation.to_dict(),
        }
        json_sticker = Sticker.de_json(json_dict, bot)

        assert json_sticker.file_id == self.sticker_file_id
        assert json_sticker.file_unique_id == self.sticker_file_unique_id
        assert json_sticker.width == self.width
        assert json_sticker.height == self.height
        assert json_sticker.is_animated == self.is_animated
        assert json_sticker.is_video == self.is_video
        assert json_sticker.emoji == self.emoji
        assert json_sticker.file_size == self.file_size
        assert json_sticker.thumb == sticker.thumb
        assert json_sticker.premium_animation == self.premium_animation

    def test_send_with_sticker(self, monkeypatch, bot, chat_id, sticker):
        def test(url, data, **kwargs):
            return data['sticker'] == sticker.file_id

        monkeypatch.setattr(bot.request, 'post', test)
        message = bot.send_sticker(sticker=sticker, chat_id=chat_id)
        assert message

    def test_send_sticker_local_files(self, monkeypatch, bot, chat_id):
        # For just test that the correct paths are passed as we have no local bot API set up
        test_flag = False
        expected = (Path.cwd() / 'tests/data/telegram.jpg/').as_uri()
        file = 'tests/data/telegram.jpg'

        def make_assertion(_, data, *args, **kwargs):
            nonlocal test_flag
            test_flag = data.get('sticker') == expected

        monkeypatch.setattr(bot, '_post', make_assertion)
        bot.send_sticker(chat_id, file)
        assert test_flag
        monkeypatch.delattr(bot, '_post')

    @flaky(3, 1)
    @pytest.mark.parametrize(
        'default_bot,custom',
        [
            ({'allow_sending_without_reply': True}, None),
            ({'allow_sending_without_reply': False}, None),
            ({'allow_sending_without_reply': False}, True),
        ],
        indirect=['default_bot'],
    )
    def test_send_sticker_default_allow_sending_without_reply(
        self, default_bot, chat_id, sticker, custom
    ):
        reply_to_message = default_bot.send_message(chat_id, 'test')
        reply_to_message.delete()
        if custom is not None:
            message = default_bot.send_sticker(
                chat_id,
                sticker,
                allow_sending_without_reply=custom,
                reply_to_message_id=reply_to_message.message_id,
            )
            assert message.reply_to_message is None
        elif default_bot.defaults.allow_sending_without_reply:
            message = default_bot.send_sticker(
                chat_id, sticker, reply_to_message_id=reply_to_message.message_id
            )
            assert message.reply_to_message is None
        else:
            with pytest.raises(BadRequest, match='message not found'):
                default_bot.send_sticker(
                    chat_id, sticker, reply_to_message_id=reply_to_message.message_id
                )

    def test_to_dict(self, sticker):
        sticker_dict = sticker.to_dict()

        assert isinstance(sticker_dict, dict)
        assert sticker_dict['file_id'] == sticker.file_id
        assert sticker_dict['file_unique_id'] == sticker.file_unique_id
        assert sticker_dict['width'] == sticker.width
        assert sticker_dict['height'] == sticker.height
        assert sticker_dict['is_animated'] == sticker.is_animated
        assert sticker_dict['is_video'] == sticker.is_video
        assert sticker_dict['file_size'] == sticker.file_size
        assert sticker_dict['thumb'] == sticker.thumb.to_dict()

    @flaky(3, 1)
    def test_error_send_empty_file(self, bot, chat_id):
        with pytest.raises(TelegramError):
            bot.send_sticker(chat_id, open(os.devnull, 'rb'))

    @flaky(3, 1)
    def test_error_send_empty_file_id(self, bot, chat_id):
        with pytest.raises(TelegramError):
            bot.send_sticker(chat_id, '')

    def test_error_without_required_args(self, bot, chat_id):
        with pytest.raises(TypeError):
            bot.send_sticker(chat_id)

    @flaky(3, 1)
    def test_premium_animation(self, bot):
        # testing animation sucks a bit since we can't create a premium sticker. What we can do is
        # get a sticker set which includes a premium sticker and check that specific one.
        premium_sticker_set = bot.get_sticker_set("Flame")
        # the first one to appear here is a sticker with unique file id of AQADOBwAAifPOElr
        # this could change in the future ofc.
        premium_sticker = premium_sticker_set.stickers[20]
        assert premium_sticker.premium_animation.file_unique_id == "AQADOBwAAifPOElr"
        assert isinstance(premium_sticker.premium_animation.file_id, str)
        assert premium_sticker.premium_animation.file_id != ""
        premium_sticker_dict = {
            "file_unique_id": "AQADOBwAAifPOElr",
            "file_id": premium_sticker.premium_animation.file_id,
            "file_size": premium_sticker.premium_animation.file_size,
        }
        assert premium_sticker.premium_animation.to_dict() == premium_sticker_dict

    def test_equality(self, sticker):
        a = Sticker(
            sticker.file_id,
            sticker.file_unique_id,
            self.width,
            self.height,
            self.is_animated,
            self.is_video,
        )
        b = Sticker(
            '', sticker.file_unique_id, self.width, self.height, self.is_animated, self.is_video
        )
        c = Sticker(sticker.file_id, sticker.file_unique_id, 0, 0, False, True)
        d = Sticker('', '', self.width, self.height, self.is_animated, self.is_video)
        e = PhotoSize(
            sticker.file_id, sticker.file_unique_id, self.width, self.height, self.is_animated
        )

        assert a == b
        assert hash(a) == hash(b)
        assert a is not b

        assert a == c
        assert hash(a) == hash(c)

        assert a != d
        assert hash(a) != hash(d)

        assert a != e
        assert hash(a) != hash(e)


@pytest.fixture(scope='function')
def sticker_set(bot):
    ss = bot.get_sticker_set(f'test_by_{bot.username}')
    if len(ss.stickers) > 100:
        try:
            for i in range(1, 50):
                bot.delete_sticker_from_set(ss.stickers[-i].file_id)
        except BadRequest as e:
            if e.message == 'Stickerset_not_modified':
                return ss
            raise Exception('stickerset is growing too large.')
    return ss


@pytest.fixture(scope='function')
def animated_sticker_set(bot):
    ss = bot.get_sticker_set(f'animated_test_by_{bot.username}')
    if len(ss.stickers) > 100:
        try:
            for i in range(1, 50):
                bot.delete_sticker_from_set(ss.stickers[-i].file_id)
        except BadRequest as e:
            if e.message == 'Stickerset_not_modified':
                return ss
            raise Exception('stickerset is growing too large.')
    return ss


@pytest.fixture(scope='function')
def video_sticker_set(bot):
    ss = bot.get_sticker_set(f'video_test_by_{bot.username}')
    if len(ss.stickers) > 100:
        try:
            for i in range(1, 50):
                bot.delete_sticker_from_set(ss.stickers[-i].file_id)
        except BadRequest as e:
            if e.message == 'Stickerset_not_modified':
                return ss
            raise Exception('stickerset is growing too large.')
    return ss


@pytest.fixture(scope='function')
def sticker_set_thumb_file():
    f = open('tests/data/sticker_set_thumb.png', 'rb')
    yield f
    f.close()


class TestStickerSet:
    title = 'Test stickers'
    is_animated = True
    is_video = True
    contains_masks = False
    stickers = [Sticker('file_id', 'file_un_id', 512, 512, True, True)]
    name = 'NOTAREALNAME'

    def test_de_json(self, bot, sticker):
        name = f'test_by_{bot.username}'
        json_dict = {
            'name': name,
            'title': self.title,
            'is_animated': self.is_animated,
            'is_video': self.is_video,
            'contains_masks': self.contains_masks,
            'stickers': [x.to_dict() for x in self.stickers],
            'thumb': sticker.thumb.to_dict(),
        }
        sticker_set = StickerSet.de_json(json_dict, bot)

        assert sticker_set.name == name
        assert sticker_set.title == self.title
        assert sticker_set.is_animated == self.is_animated
        assert sticker_set.is_video == self.is_video
        assert sticker_set.contains_masks == self.contains_masks
        assert sticker_set.stickers == self.stickers
        assert sticker_set.thumb == sticker.thumb

    def test_create_sticker_set(
        self, bot, chat_id, sticker_file, animated_sticker_file, video_sticker_file
    ):
        """Creates the sticker set (if needed) which is required for tests. Make sure that this
        test comes before the tests that actually use the sticker sets!
        """
        test_by = f"test_by_{bot.username}"
        for sticker_set in [test_by, f'animated_{test_by}', f'video_{test_by}']:
            try:
                bot.get_sticker_set(sticker_set)
            except BadRequest as e:
                if not e.message == "Stickerset_invalid":
                    raise e

                if sticker_set.startswith(test_by):
                    s = bot.create_new_sticker_set(
                        chat_id,
                        name=sticker_set,
                        title="Sticker Test",
                        png_sticker=sticker_file,
                        emojis='😄',
                    )
                    assert s
                elif sticker_set.startswith("animated"):
                    a = bot.create_new_sticker_set(
                        chat_id,
                        name=sticker_set,
                        title="Animated Test",
                        tgs_sticker=animated_sticker_file,
                        emojis='😄',
                    )
                    assert a
                elif sticker_set.startswith("video"):
                    v = bot.create_new_sticker_set(
                        chat_id,
                        name=sticker_set,
                        title="Video Test",
                        webm_sticker=video_sticker_file,
                        emojis='🤔',
                    )
                    assert v

    @flaky(3, 1)
    def test_bot_methods_1_png(self, bot, chat_id, sticker_file):
        with open('tests/data/telegram_sticker.png', 'rb') as f:
            # chat_id was hardcoded as 95205500 but it stopped working for some reason
            file = bot.upload_sticker_file(chat_id, f)
        assert file
        assert bot.add_sticker_to_set(
            chat_id, f'test_by_{bot.username}', png_sticker=file.file_id, emojis='😄'
        )
        # Also test with file input and mask
        assert bot.add_sticker_to_set(
            chat_id,
            f'test_by_{bot.username}',
            png_sticker=sticker_file,
            emojis='😄',
            mask_position=MaskPosition(MaskPosition.EYES, -1, 1, 2),
        )

    @flaky(3, 1)
    def test_bot_methods_1_tgs(self, bot, chat_id):
        assert bot.add_sticker_to_set(
            chat_id,
            f'animated_test_by_{bot.username}',
            tgs_sticker=open('tests/data/telegram_animated_sticker.tgs', 'rb'),
            emojis='😄',
        )

    @flaky(3, 1)
    def test_bot_methods_1_webm(self, bot, chat_id):
        with open('tests/data/telegram_video_sticker.webm', 'rb') as f:
            assert bot.add_sticker_to_set(
                chat_id, f'video_test_by_{bot.username}', webm_sticker=f, emojis='🤔'
            )

    def test_sticker_set_to_dict(self, sticker_set):
        sticker_set_dict = sticker_set.to_dict()

        assert isinstance(sticker_set_dict, dict)
        assert sticker_set_dict['name'] == sticker_set.name
        assert sticker_set_dict['title'] == sticker_set.title
        assert sticker_set_dict['is_animated'] == sticker_set.is_animated
        assert sticker_set_dict['is_video'] == sticker_set.is_video
        assert sticker_set_dict['contains_masks'] == sticker_set.contains_masks
        assert sticker_set_dict['stickers'][0] == sticker_set.stickers[0].to_dict()

    @flaky(3, 1)
    def test_bot_methods_2_png(self, bot, sticker_set):
        file_id = sticker_set.stickers[0].file_id
        assert bot.set_sticker_position_in_set(file_id, 1)

    @flaky(3, 1)
    def test_bot_methods_2_tgs(self, bot, animated_sticker_set):
        file_id = animated_sticker_set.stickers[0].file_id
        assert bot.set_sticker_position_in_set(file_id, 1)

    @flaky(3, 1)
    def test_bot_methods_2_webm(self, bot, video_sticker_set):
        file_id = video_sticker_set.stickers[0].file_id
        assert bot.set_sticker_position_in_set(file_id, 1)

    @flaky(10, 1)
    def test_bot_methods_3_png(self, bot, chat_id, sticker_set_thumb_file):
        sleep(1)
        assert bot.set_sticker_set_thumb(
            f'test_by_{bot.username}', chat_id, sticker_set_thumb_file
        )

    @flaky(10, 1)
    def test_bot_methods_3_tgs(self, bot, chat_id, animated_sticker_file, animated_sticker_set):
        sleep(1)
        animated_test = f'animated_test_by_{bot.username}'
        assert bot.set_sticker_set_thumb(animated_test, chat_id, animated_sticker_file)
        file_id = animated_sticker_set.stickers[-1].file_id
        # also test with file input and mask
        assert bot.set_sticker_set_thumb(animated_test, chat_id, file_id)

    # TODO: Try the below by creating a custom .webm and not by downloading another pack's thumb
    @pytest.mark.skip(
        "Skipped for now since Telegram throws a 'File is too big' error "
        "regardless of the .webm file size."
    )
    def test_bot_methods_3_webm(self, bot, chat_id, video_sticker_file, video_sticker_set):
        pass

    @flaky(10, 1)
    def test_bot_methods_4_png(self, bot, sticker_set):
        sleep(1)
        file_id = sticker_set.stickers[-1].file_id
        assert bot.delete_sticker_from_set(file_id)

    @flaky(10, 1)
    def test_bot_methods_4_tgs(self, bot, animated_sticker_set):
        sleep(1)
        file_id = animated_sticker_set.stickers[-1].file_id
        assert bot.delete_sticker_from_set(file_id)

    @flaky(10, 1)
    def test_bot_methods_4_webm(self, bot, video_sticker_set):
        sleep(1)
        file_id = video_sticker_set.stickers[-1].file_id
        assert bot.delete_sticker_from_set(file_id)

    def test_upload_sticker_file_local_files(self, monkeypatch, bot, chat_id):
        # For just test that the correct paths are passed as we have no local bot API set up
        test_flag = False
        expected = (Path.cwd() / 'tests/data/telegram.jpg/').as_uri()
        file = 'tests/data/telegram.jpg'

        def make_assertion(_, data, *args, **kwargs):
            nonlocal test_flag
            test_flag = data.get('png_sticker') == expected

        monkeypatch.setattr(bot, '_post', make_assertion)
        bot.upload_sticker_file(chat_id, file)
        assert test_flag
        monkeypatch.delattr(bot, '_post')

    def test_create_new_sticker_set_local_files(self, monkeypatch, bot, chat_id):
        # For just test that the correct paths are passed as we have no local bot API set up
        test_flag = False
        expected = (Path.cwd() / 'tests/data/telegram.jpg/').as_uri()
        file = 'tests/data/telegram.jpg'

        def make_assertion(_, data, *args, **kwargs):
            nonlocal test_flag
            test_flag = (
                data.get('png_sticker') == expected
                and data.get('tgs_sticker') == expected
                and data.get('webm_sticker') == expected
            )

        monkeypatch.setattr(bot, '_post', make_assertion)
        bot.create_new_sticker_set(
            chat_id,
            'name',
            'title',
            'emoji',
            png_sticker=file,
            tgs_sticker=file,
            webm_sticker=file,
        )
        assert test_flag
        monkeypatch.delattr(bot, '_post')

    def test_add_sticker_to_set_local_files(self, monkeypatch, bot, chat_id):
        # For just test that the correct paths are passed as we have no local bot API set up
        test_flag = False
        expected = (Path.cwd() / 'tests/data/telegram.jpg/').as_uri()
        file = 'tests/data/telegram.jpg'

        def make_assertion(_, data, *args, **kwargs):
            nonlocal test_flag
            test_flag = data.get('png_sticker') == expected and data.get('tgs_sticker') == expected

        monkeypatch.setattr(bot, '_post', make_assertion)
        bot.add_sticker_to_set(chat_id, 'name', 'emoji', png_sticker=file, tgs_sticker=file)
        assert test_flag
        monkeypatch.delattr(bot, '_post')

    def test_set_sticker_set_thumb_local_files(self, monkeypatch, bot, chat_id):
        # For just test that the correct paths are passed as we have no local bot API set up
        test_flag = False
        expected = (Path.cwd() / 'tests/data/telegram.jpg/').as_uri()
        file = 'tests/data/telegram.jpg'

        def make_assertion(_, data, *args, **kwargs):
            nonlocal test_flag
            test_flag = data.get('thumb') == expected

        monkeypatch.setattr(bot, '_post', make_assertion)
        bot.set_sticker_set_thumb('name', chat_id, thumb=file)
        assert test_flag
        monkeypatch.delattr(bot, '_post')

    def test_get_file_instance_method(self, monkeypatch, sticker):
        def make_assertion(*_, **kwargs):
            return kwargs['file_id'] == sticker.file_id

        assert check_shortcut_signature(Sticker.get_file, Bot.get_file, ['file_id'], [])
        assert check_shortcut_call(sticker.get_file, sticker.bot, 'get_file')
        assert check_defaults_handling(sticker.get_file, sticker.bot)

        monkeypatch.setattr(sticker.bot, 'get_file', make_assertion)
        assert sticker.get_file()

    def test_equality(self):
        a = StickerSet(
            self.name,
            self.title,
            self.is_animated,
            self.contains_masks,
            self.stickers,
            self.is_video,
        )
        b = StickerSet(
            self.name,
            self.title,
            self.is_animated,
            self.contains_masks,
            self.stickers,
            self.is_video,
        )
        c = StickerSet(self.name, None, None, None, None, None)
        d = StickerSet(
            'blah', self.title, self.is_animated, self.contains_masks, self.stickers, self.is_video
        )
        e = Audio(self.name, '', 0, None, None)

        assert a == b
        assert hash(a) == hash(b)
        assert a is not b

        assert a == c
        assert hash(a) == hash(c)

        assert a != d
        assert hash(a) != hash(d)

        assert a != e
        assert hash(a) != hash(e)


@pytest.fixture(scope='class')
def mask_position():
    return MaskPosition(
        TestMaskPosition.point,
        TestMaskPosition.x_shift,
        TestMaskPosition.y_shift,
        TestMaskPosition.scale,
    )


class TestMaskPosition:
    point = MaskPosition.EYES
    x_shift = -1
    y_shift = 1
    scale = 2

    def test_mask_position_de_json(self, bot):
        json_dict = {
            'point': self.point,
            'x_shift': self.x_shift,
            'y_shift': self.y_shift,
            'scale': self.scale,
        }
        mask_position = MaskPosition.de_json(json_dict, bot)

        assert mask_position.point == self.point
        assert mask_position.x_shift == self.x_shift
        assert mask_position.y_shift == self.y_shift
        assert mask_position.scale == self.scale

    def test_mask_position_to_dict(self, mask_position):
        mask_position_dict = mask_position.to_dict()

        assert isinstance(mask_position_dict, dict)
        assert mask_position_dict['point'] == mask_position.point
        assert mask_position_dict['x_shift'] == mask_position.x_shift
        assert mask_position_dict['y_shift'] == mask_position.y_shift
        assert mask_position_dict['scale'] == mask_position.scale

    def test_equality(self):
        a = MaskPosition(self.point, self.x_shift, self.y_shift, self.scale)
        b = MaskPosition(self.point, self.x_shift, self.y_shift, self.scale)
        c = MaskPosition(MaskPosition.FOREHEAD, self.x_shift, self.y_shift, self.scale)
        d = MaskPosition(self.point, 0, 0, self.scale)
        e = Audio('', '', 0, None, None)

        assert a == b
        assert hash(a) == hash(b)
        assert a is not b

        assert a != c
        assert hash(a) != hash(c)

        assert a != d
        assert hash(a) != hash(d)

        assert a != e
        assert hash(a) != hash(e)
