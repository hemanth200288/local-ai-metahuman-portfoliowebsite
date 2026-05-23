###############################################################################
#  Output — LiveKit 输出
###############################################################################

import asyncio
import cv2
import numpy as np
from threading import Thread
from typing import TYPE_CHECKING, Optional
from streamout.base_output import BaseOutput
from registry import register
from utils.logger import logger

try:
    from livekit import api, rtc
except ImportError:
    logger.error("LiveKit SDK not found. Please install with: pip install livekit")

if TYPE_CHECKING:
    from avatars.base_avatar import BaseAvatar

@register("streamout", "livekit")
class LiveKitOutput(BaseOutput):
    """LiveKit 输出模式 — 将音视频推送到 LiveKit Room"""

    def __init__(self, opt=None, parent: Optional['BaseAvatar'] = None, **kwargs):
        super().__init__(opt, parent)
        self.url = getattr(opt, 'livekit_url', '')
        self.api_key = getattr(opt, 'livekit_api_key', '')
        self.api_secret = getattr(opt, 'livekit_api_secret', '')
        self.room_name = getattr(opt, 'livekit_room', 'livetalking_room')
        self.participant_name = f"avatar_{parent.sessionid if parent else '0'}"
        
        self.room = None
        self.video_source = None
        self.audio_source = None
        self.video_track = None
        self.audio_track = None
        self._loop = asyncio.get_event_loop()
        self.video_width = 512
        self.video_height = 512

    def start(self) -> None:
        """启动 LiveKit 并在后台连接"""
        logger.info(f"Starting LiveKit output for room: {self.room_name}")
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            Thread(target=self._loop.run_forever, daemon=True).start()
        
        asyncio.run_coroutine_threadsafe(self._connect(), self._loop)

    async def _connect(self):
        logger.info(f"Connecting to LiveKit URL: {self.url}")
        try:
            from livekit import api, rtc
            self.room = rtc.Room()
            
            token = api.AccessToken(self.api_key, self.api_secret) \
                .with_identity(self.participant_name) \
                .with_name("Digital Human") \
                .with_grants(api.VideoGrants(room_join=True, room=self.room_name)) \
                .to_jwt()

            await self.room.connect(self.url, token)
            logger.info(f"Successfully connected to LiveKit room: {self.room_name}")

            self.video_source = rtc.VideoSource(self.video_width, self.video_height)
            self.video_track = rtc.LocalVideoTrack.create_video_track("avatar_video", self.video_source)
            
            self.audio_source = rtc.AudioSource(16000, 1)
            self.audio_track = rtc.LocalAudioTrack.create_audio_track("avatar_audio", self.audio_source)

            await self.room.local_participant.publish_track(self.video_track)
            await self.room.local_participant.publish_track(self.audio_track)
            logger.info("Published LiveKit tracks successfully")

        except Exception as e:
            logger.error(f"LiveKit connection error: {e}", exc_info=True)

    def push_video_frame(self, frame) -> None:
        """
        Push a video frame (numpy BGR/RGB)
        """
        if not self.video_source:
            return
            
        try:
            from livekit import rtc
            h, w, _ = frame.shape
            if h != self.video_height or w != self.video_width:
                logger.info(f"Updating LiveKit video resolution to {w}x{h}")
                self.video_width = w
                self.video_height = h
            
            rgba_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            video_frame = rtc.VideoFrame(w, h, rtc.VideoBufferType.RGBA, rgba_frame.tobytes())
            res = self.video_source.capture_frame(video_frame)
            if asyncio.iscoroutine(res):
                asyncio.run_coroutine_threadsafe(res, self._loop)
        except Exception as e:
            logger.error(f"Error pushing LiveKit video frame: {e}")

    def push_audio_frame(self, frame: np.ndarray, eventpoint=None) -> None:
        """
        Push an audio frame (numpy int16 pcm)
        """
        if not self.audio_source:
            return
            
        try:
            from livekit import rtc
            audio_frame = rtc.AudioFrame(frame.tobytes(), 16000, 1, len(frame))
            res = self.audio_source.capture_frame(audio_frame)
            if asyncio.iscoroutine(res):
                asyncio.run_coroutine_threadsafe(res, self._loop)
        except Exception as e:
            logger.error(f"Error pushing LiveKit audio frame: {e}")

    def stop(self) -> None:
        if self.room:
            asyncio.run_coroutine_threadsafe(self.room.disconnect(), self._loop)
            logger.info("Disconnected from LiveKit")
