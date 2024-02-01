import abc
import os
from pathlib import Path
import typing

from google.cloud import storage
from google.oauth2 import service_account

class Workspace(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path

    @classmethod
    @abc.abstractmethod
    def read(self, task_id: str, path: str) -> bytes:
        pass

    @classmethod
    @abc.abstractmethod
    def write(self, task_id: str, path: str, data: bytes) -> None:
        pass

    @classmethod
    @abc.abstractmethod
    def delete(
        self, task_id: str, path: str, directory: bool = False, recursive: bool = False
    ) -> None:
        pass

    @classmethod
    @abc.abstractmethod
    def exists(self, task_id: str, path: str) -> bool:
        pass

    @classmethod
    @abc.abstractmethod
    def list(self, task_id: str, path: str) -> typing.List[str]:
        pass


class LocalWorkspace(Workspace):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()

    def _resolve_path(self, task_id: str, _path: Path) -> Path:
        path = _path.as_posix()
        path = path if not path.startswith("/") else path[1:]
        abs_path = (self.base_path / task_id / path).resolve()
        if not str(abs_path).startswith(str(self.base_path)):
            print("Error")
            raise ValueError(f"Directory traversal is not allowed! - {abs_path}")
        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        return abs_path

    def read(self, task_id: str, path: Path) -> bytes:
        with open(self._resolve_path(task_id, path), "rb") as f:
            return f.read()

    def write(self, task_id: str, path: Path, data: bytes) -> None:
        file_path = self._resolve_path(task_id, path)
        with open(file_path, "wb") as f:
            f.write(data)

    def delete(
        self, task_id: str, path: str, directory: bool = False, recursive: bool = False
    ) -> None:
        fullPath = self.base_path / task_id / path
        resolved_path = self._resolve_path(task_id, fullPath)
        if directory:
            if recursive:
                os.rmdir(resolved_path)
            else:
                os.removedirs(resolved_path)
        else:
            os.remove(resolved_path)

    def exists(self, task_id: str, _path: str) -> bool:
        path = self.base_path / task_id / _path
        return self._resolve_path(task_id, path).exists()

    def list(self, task_id: str, _path: str) -> typing.List[str]:
        path = self.base_path / task_id / _path
        base = self._resolve_path(task_id, path)
        if not base.exists() or not base.is_dir():
            return []
        return [str(p.relative_to(self.base_path / task_id)) for p in base.iterdir()]


class GCSWorkspace(Workspace):
    def __init__(self, bucket_name: str, base_path: str = ""):
        self.bucket_name = bucket_name
        if base_path:
            self.base_path = Path(base_path)
        else:
            raise Exception("Not basepath set")
        cred_filepath = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_filepath is None:
            raise Exception("Not GOOGLE_APPLICATION_CREDENTIALS set")
        project = os.getenv("GCE_PROJECT")
        if project is None:
            raise Exception("Not GCE_PROJECT set")

        credentials = service_account.Credentials.from_service_account_file(Path(cred_filepath).resolve())    
        self.storage_client = storage.Client(credentials=credentials, project=project)
        self.bucket = self.storage_client.get_bucket(self.bucket_name)

    def _resolve_path(self, task_id: str, path: str) -> Path:
        path = str(path)
        path = path if not path.startswith("/") else path[1:]
        abs_path = (self.base_path / task_id / path).resolve()
        gcs_path = os.path.relpath(abs_path, os.getcwd())
        if not gcs_path.startswith(str(self.base_path)):
            print("Error")
            raise ValueError(f"Directory traversal is not allowed! - {gcs_path}")
        return Path(gcs_path)

    def read(self, task_id: str, path: str) -> bytes:
        blob = self.bucket.blob(self._resolve_path(task_id, path))
        if not blob.exists():
            raise FileNotFoundError()
        return blob.download_as_bytes()

    def write(self, task_id: str, path: str, data: bytes) -> None:
        blob = self.bucket.blob(self._resolve_path(task_id, path).as_posix())
        blob.upload_from_string(data)

    def delete(self, task_id: str, path: str, directory=False, recursive=False):
        if directory and not recursive:
            raise ValueError("recursive must be True when deleting a directory")
        blob = self.bucket.blob(self._resolve_path(task_id, path).as_posix())
        if not blob.exists():
            return
        if directory:
            for b in list(self.bucket.list_blobs(prefix=blob.name)):
                b.delete()
        else:
            blob.delete()

    def exists(self, task_id: str, path: str) -> bool:
        blob = self.bucket.blob(self._resolve_path(task_id, path).as_posix())
        return blob.exists()

    def list(self, task_id: str, path: str) -> typing.List[str]:
        prefix = os.path.join(task_id, self.base_path, path).replace("\\", "/") + "/"
        blobs = list(self.bucket.list_blobs(prefix=prefix))
        return [str(Path(b.name).relative_to(prefix[:-1])) for b in blobs]
