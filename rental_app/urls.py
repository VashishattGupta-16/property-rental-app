from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page


manifest_view = cache_page(60 * 60)(
    TemplateView.as_view(template_name="manifest.json", content_type="application/json")
)
service_worker_view = cache_page(60)(
    TemplateView.as_view(template_name="sw.js", content_type="application/javascript")
)

urlpatterns = [
    # PWA
    path(
        "manifest.json",
        manifest_view,
        name="manifest",
    ),
    path(
        "sw.js",
        service_worker_view,
        name="service_worker",
    ),

    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("tweet.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
