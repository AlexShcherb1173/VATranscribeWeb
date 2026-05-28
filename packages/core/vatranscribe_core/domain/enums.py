from __future__ import annotations

from enum import Enum


class JobType(str, Enum):
    DOWNLOAD = "download"
    TRANSCRIBE = "transcribe"
    COMBINED = "combined"
    EXPORT = "export"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class SourceType(str, Enum):
    URL = "url"
    UPLOAD = "upload"
    LOCAL_FILE = "local_file"


class MediaKind(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


class OutputFormat(str, Enum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


class TranscriptionEngine(str, Enum):
    FASTER_WHISPER = "faster_whisper"
    OPENAI_WHISPER = "openai_whisper"


class WhisperModelName(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
