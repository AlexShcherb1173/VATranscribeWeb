from __future__ import annotations


class VATranscribeError(Exception):
    pass


class DownloadError(VATranscribeError):
    pass


class TranscriptionError(VATranscribeError):
    pass


class ExportError(VATranscribeError):
    pass
