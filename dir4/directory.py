from abc import ABC
from abc import abstractmethod
import os.path
import sys


class Directory(ABC):
    @abstractmethod
    def config(self) -> str:
        pass

    @classmethod
    def for_user(cls) -> "Directory":
        if sys.platform == "win32":
            return Win32Directory()


class Win32Directory(Directory):
    def config(self) -> str:
        return os.path.normpath

    def _pick_get_win_folder(self, csidl_name: str) -> str:
        import ctypes

        if hasattr(ctypes, "windll"):
            csidl_const = {
                "CSIDL_APPDATA": 26,
                "CSIDL_COMMON_APPDATA": 35,
                "CSIDL_LOCAL_APPDATA": 28,
                "CSIDL_PERSONAL": 5,
                "CSIDL_MYPICTURES": 39,
                "CSIDL_MYVIDEO": 14,
                "CSIDL_MYMUSIC": 13,
                "CSIDL_DOWNLOADS": 40,
                "CSIDL_DESKTOPDIRECTORY": 16,
            }.get(csidl_name)
            if csidl_const is None:
                msg = f"Unknown CSIDL name: {csidl_name}"
                raise ValueError(msg)

            buf = ctypes.create_unicode_buffer(1024)
            windll = getattr(ctypes, "windll")  # noqa: B009 # using getattr to avoid false positive with mypy type checker
            windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

            # Downgrade to short path name if it has high-bit chars.
            if any(ord(c) > 255 for c in buf):  # noqa: PLR2004
                buf2 = ctypes.create_unicode_buffer(1024)
                if windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
                    buf = buf2

            if csidl_name == "CSIDL_DOWNLOADS":
                return os.path.join(buf.value, "Downloads")  # noqa: PTH118

            return buf.value
        try:
            import winreg  # noqa: F401
        except ImportError:
            return get_win_folder_from_env_vars
        else:
            return get_win_folder_from_registry
