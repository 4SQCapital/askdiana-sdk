from __future__ import annotations

import json

from askdiana import ChatService

from .blocks import build_blocks
from .pack import Pack
from .pipeline import AnswerPipeline


class ErpChatService(ChatService):
    def __init__(self, client, pack: Pack, pipeline: AnswerPipeline):
        super().__init__(client)
        self._pack = pack
        self._pipeline = pipeline

    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        answer = self._pipeline.answer(install_id, message)
        return json.dumps({"type": "rich_response", "blocks": build_blocks(self._pack, answer)})
