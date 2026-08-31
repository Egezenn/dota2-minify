from typing import Sequence

from ui.alerts import alert
from ui.pickers import pick_file, pick_files, pick_folder, pick_save_file


class DialogService:
    @staticmethod
    def pick_file(title: str = "Select File", file_types: Sequence[str] = ()) -> str | None:
        return pick_file(title, file_types)

    @staticmethod
    def pick_files(title: str = "Select Files", file_types: Sequence[str] = ()) -> list[str]:
        return pick_files(title, file_types)

    @staticmethod
    def pick_folder(title: str = "Select Folder") -> str | None:
        return pick_folder(title)

    @staticmethod
    def pick_save_file(title: str = "Save File", default_filename: str = "") -> str | None:
        return pick_save_file(title, default_filename)

    @staticmethod
    def alert(msg: str, *args, msg_type: str = "info") -> None:
        alert(msg, *args, msg_type=msg_type)
