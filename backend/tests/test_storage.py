from unittest.mock import MagicMock

from app.storage.s3 import S3StorageClient


def test_put_object_targets_bucket_and_key() -> None:
    client = MagicMock()
    storage = S3StorageClient(client, "documents")

    storage.put_object("users/u1/documents/d1/taxes.pdf", b"bytes", "application/pdf")

    client.put_object.assert_called_once_with(
        Bucket="documents",
        Key="users/u1/documents/d1/taxes.pdf",
        Body=b"bytes",
        ContentType="application/pdf",
    )


def test_get_object_reads_streaming_body() -> None:
    client = MagicMock()
    body = MagicMock()
    body.read.return_value = b"file-contents"
    client.get_object.return_value = {"Body": body}
    storage = S3StorageClient(client, "documents")

    assert storage.get_object("k") == b"file-contents"
    client.get_object.assert_called_once_with(Bucket="documents", Key="k")


def test_delete_object_targets_bucket_and_key() -> None:
    client = MagicMock()
    storage = S3StorageClient(client, "documents")

    storage.delete_object("k")

    client.delete_object.assert_called_once_with(Bucket="documents", Key="k")


def test_generate_presigned_url_delegates_to_client() -> None:
    client = MagicMock()
    client.generate_presigned_url.return_value = "http://signed.example/x"
    storage = S3StorageClient(client, "documents")

    url = storage.generate_presigned_url("k", expires_in=60)

    assert url == "http://signed.example/x"
    client.generate_presigned_url.assert_called_once_with(
        "get_object", Params={"Bucket": "documents", "Key": "k"}, ExpiresIn=60
    )


def test_ensure_bucket_creates_when_missing() -> None:
    from botocore.exceptions import ClientError

    client = MagicMock()
    client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
    storage = S3StorageClient(client, "documents")

    storage.ensure_bucket()

    client.create_bucket.assert_called_once_with(Bucket="documents")
