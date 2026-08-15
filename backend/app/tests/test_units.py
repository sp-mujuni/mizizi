"""Unit tests for the object-code generator and media service."""

import uuid

from app.services.media_service import UploadedFile, calculate_sha256, detect_media_type
from app.models.enums import MediaType


def test_sha256_known_vector():
    assert calculate_sha256(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert calculate_sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_detect_media_type_audio():
    assert detect_media_type("audio/mpeg", "song.mp3") == MediaType.AUDIO
    assert detect_media_type("application/octet-stream", "recording.wav") == MediaType.AUDIO


def test_detect_media_type_video_and_image():
    assert detect_media_type("video/mp4", "clip.mp4") == MediaType.VIDEO
    assert detect_media_type("image/png", "photo.png") == MediaType.IMAGE


def test_detect_media_type_document_default():
    assert detect_media_type("application/pdf", "notes.pdf") == MediaType.DOCUMENT


def test_uploaded_file_size():
    f = UploadedFile(filename="a.wav", content_type="audio/wav", data=b"12345", size=5)
    assert f.size == 5