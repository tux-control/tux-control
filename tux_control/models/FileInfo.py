import datetime
import stat
import magic
from pathlib import Path
from flask_jwt_extended import current_user
from tux_control.tools.IDictify import IDictify


class FileInfo(IDictify):
    is_writable = False
    is_readable = False
    updated = None
    created = None
    size = 0

    def __init__(self, path: Path, resolve_parents: bool = True):
        self.path = path

        self.name = self.path.name
        self.suffix = self.path.suffix.strip('.')
        self.parts = self.path.parts
        self.is_dir = self.path.is_dir()
        self.is_file = self.path.is_file()
        self.stem = self.path.stem
        self.absolute = str(path.absolute())

        if path.is_file():
            mime = magic.Magic(mime=True)
            self.mime_type = mime.from_file(self.absolute)
        else:
            self.mime_type = None

        self.owner = path.owner() if self.is_file or self.is_dir else None

        self.parent = FileInfo(self.path.parent, False) if resolve_parents else None
        self.parents = [FileInfo(p, False) for p in self.path.parents] if resolve_parents else None

        stat_info = path.stat() if self.is_file or self.is_dir else None

        if stat_info:
            self.size = stat_info.st_size

            self.updated = datetime.datetime.fromtimestamp(stat_info.st_mtime)
            self.created = datetime.datetime.fromtimestamp(stat_info.st_ctime)

            self.is_writable = (bool(stat_info.st_mode & stat.S_IWUSR) and self.owner == current_user.system_user) or bool(stat_info.st_mode & stat.S_IWOTH)
            self.is_readable = (bool(stat_info.st_mode & stat.S_IRUSR) and self.owner == current_user.system_user) or bool(stat_info.st_mode & stat.S_IROTH)

    @staticmethod
    def from_string(path: str, resolve_parents: bool = True) -> 'FileInfo':
        return FileInfo(Path(path), resolve_parents)

    def is_allowed_file(self) -> bool:
        if self.name.startswith('.'):
            return False

        if not self.path.is_file() and not self.path.is_dir():
            return False

        if not self.is_writable:
            return False

        return True

    def to_dict(self):
        return {
            'parts': self.parts,
            'parent': self.parent,
            'parents': self.parents,
            'name': self.name,
            'absolute': self.absolute,
            'suffix': self.suffix,
            'stem': self.stem,
            'is_dir': self.is_dir,
            'is_file': self.is_file,
            'is_writable': self.is_writable,
            'is_readable': self.is_readable,
            'mime_type': self.mime_type,
            'owner': self.owner,
            'size': self.size,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None,
        }