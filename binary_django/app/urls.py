from django.urls import path, re_path
from app import views

urlpatterns = [
    # Matches any html file - to be used for gentella
    # Avoid using your .html in your resources.
    # Or create a separate django app.

    path("urls.html", views.urls_info, name = "urls_info"),
    path("data_stats.html",views.binary_urls, name = "binary_urls"),
    path("binaries.html", views.binaries, name = "tables"),
    path("relations.json", views.json_test, name = "qq_json"),
    re_path(r'^.*\.html', views.gentella_html, name='gentella'),

    # The home page
    path('', views.binary_urls, name='index'),
]
