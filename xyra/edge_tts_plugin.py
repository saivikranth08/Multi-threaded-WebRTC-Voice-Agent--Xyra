import uuid
import edge_tts
import logging
from typing import Optional

from livekit import rtc
from livekit.agents.tts import TTS, ChunkedStream, TTSCapabilities
from livekit.agents.tts.tts import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS, AudioEmitter

logger = logging.getLogger("edge_tts_plugin")

class EdgeChunkedStream(ChunkedStream):
    def __init__(
        self,
        tts: TTS,
        input_text: str,
        conn_options: APIConnectOptions,
        voice: str
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self.voice = voice

    async def _run(self, output_emitter: AudioEmitter) -> None:
        communicate = edge_tts.Communicate(self.input_text, self.voice)
        
        output_emitter.initialize(
            request_id=str(uuid.uuid4()),
            sample_rate=self._tts.sample_rate,
            num_channels=1,
            mime_type="audio/mp3",
            stream=False,
        )
        
        has_data = False
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                has_data = True
                output_emitter.push(chunk["data"])
        
        if not has_data:
            logger.warning(f"No audio data returned from Edge TTS for text: {self.input_text}")


class EdgeTTS(TTS):
    def __init__(
        self,
        voice: str = "en-IN-NeerjaNeural",
        sample_rate: int = 24000,
    ) -> None:
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self.voice = voice
        self._label = f"edge_tts.EdgeTTS"

    @property
    def model(self) -> str:
        return "edge-tts"

    @property
    def provider(self) -> str:
        return "microsoft-edge"

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> ChunkedStream:
        return EdgeChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            voice=self.voice
        )
