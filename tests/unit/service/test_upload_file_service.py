import io
import pytest

from src.services.upload_file import UploadFileService
from fastapi import UploadFile


class DummyUploader:
    def __init__(self, version=123):
        self.calls = []
        self.version = version

    def upload(self, fileobj, public_id: str, overwrite: bool):
        # Ensure we can read content
        assert hasattr(fileobj, "read")
        data = fileobj.read()
        assert isinstance(data, (bytes, bytearray))
        self.calls.append({"public_id": public_id, "overwrite": overwrite})
        return {"version": self.version}


class DummyCloudinaryImage:
    def __init__(self, public_id: str):
        self.public_id = public_id

    def build_url(self, width: int, height: int, crop: str, version: int):
        return f"https://res.cloudinary.com/demo/image/upload/v{version}/{self.public_id}.png?w={width}&h={height}&c={crop}"


@pytest.mark.anyio
async def test_upload_file_builds_expected_url(monkeypatch):
    # Patch cloudinary module parts used inside service
    import src.services.upload_file as mod

    dummy_uploader = DummyUploader(version=456)
    monkeypatch.setattr(mod.cloudinary, "uploader", dummy_uploader)
    monkeypatch.setattr(mod.cloudinary, "CloudinaryImage", DummyCloudinaryImage)

    # Initialize service (it will call cloudinary.config)
    svc = UploadFileService(cloud_name="demo", api_key="key", api_secret="secret")

    # Prepare UploadFile with some bytes
    content = b"fake-image-bytes"
    file = UploadFile(filename="avatar.png", file=io.BytesIO(content))

    url = svc.upload_file(file, username="alice")

    assert (
        dummy_uploader.calls and dummy_uploader.calls[0]["public_id"] == "RestApp/alice"
    )
    assert url.startswith(
        "https://res.cloudinary.com/demo/image/upload/v456/RestApp/alice.png"
    )
    assert "w=250" in url and "h=250" in url and "c=fill" in url
