"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

from drf_yasg import openapi
from drf_yasg.views import get_schema_view as swagger_get_schema_view


schema_view = swagger_get_schema_view(
    openapi.Info(
        title="TrixWallet Api",
        default_version="4.10.6",
        description="Api documentation of TrixWallet",
        contact=openapi.Contact(email='ivantomdio@gmail.com'),
        license=openapi.License(name='BSD Licence')
    ),
    public=True
)

admin.site.site_header = 'TrixWallet Admin'
admin.site.site_title = "TrixWallet Admin"
# admin.site.site_url = "https:trix-car-backend.vercel.app"
admin.site.index_title = "TrixWallet Administration"
admin.empty_value_display = "**Empty**"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('accounts.urls'),name="accounts"),
    path('api/v3/',
        include([
            path('auth/',include(('accounts.api.urls','accounts'),namespace='accounts')),
            path('momo/',include(('core.api.urls','core'),namespace='momo')),
            path('notifications/',include(('notifications.api.urls','notifications'),namespace='notifications')),

            #docs urls
            path('docs/',include([
                path('',include_docs_urls(title='TrixWallet API',description="TrixWallet Api documentation")),
                re_path(r'swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
                re_path(r'swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                re_path(r'redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
            ]))
        ]
    )),
    path('api-auth/', include('rest_framework.urls'),name="api-auth"),
]