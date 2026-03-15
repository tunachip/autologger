from __future__ import annotations

from .finder_popup import FinderPopupMixin
from .queue_picker_popup import QueuePickerPopupMixin
from .search_core import SearchCoreMixin
from .video_picker_popup import VideoPickerPopupMixin


class SearchPopupMixin(
    QueuePickerPopupMixin,
    VideoPickerPopupMixin,
    FinderPopupMixin,
    SearchCoreMixin,
):
    pass
