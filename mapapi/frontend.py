from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin

_INDEX_PATH = Path(settings.MAP_FRONTEND_DIST_DIR) / "index.html"


@xframe_options_sameorigin
def serve_map_frontend(request, *args, **kwargs):
    if not _INDEX_PATH.exists():
        return HttpResponse(
            "Map frontend build not found. Run `npm run build` in map_frontend/ first.",
            status=501,
        )
    return HttpResponse(_INDEX_PATH.read_text(encoding="utf-8"))
