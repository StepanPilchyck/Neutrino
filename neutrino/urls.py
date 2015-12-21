from django.conf.urls import include, url, patterns
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import ugettext_lazy as _

import neutrino.settings as settings
from django.contrib import admin

from django.shortcuts import render_to_response
from django.template import RequestContext


def handler404(request):
    response = render_to_response('system/404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('system/500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response

urlpatterns = i18n_patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^catalogue/', include('catalogue.urls')),
    url(r'', include('static_page.urls')),
)

urlpatterns += patterns(
    url(r'^localization_api/', include('localization.urls')),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = _('Neutrino Admin Panel')
