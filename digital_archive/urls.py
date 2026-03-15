"""
URL configuration for digital_archive project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include

from crawler.views import (
    CrawlConfigurationListView,
    CrawlConfigurationDetailView,
    CrawlConfigurationCreateView,
    CrawlConfigurationUpdateView,
    CrawlConfigurationDeleteView,
    start_crawl_view,
    CrawlListView,
    CrawlDetailView,
    BrowserProfileListView,
    BrowserProfileUpdateView,
    BrowserProfileDeleteView,
    browser_profile_create_view,
    get_wacz,
    get_crawl_screenshot,
)

urlpatterns = [
    path(
        "crawler/configs/",
        CrawlConfigurationListView.as_view(),
        name="crawl_configuration_list",
    ),
    path(
        "crawler/configs/<int:pk>",
        CrawlConfigurationDetailView.as_view(),
        name="crawl_configuration_detail",
    ),
    path(
        "crawler/configs/<int:pk>/edit",
        CrawlConfigurationUpdateView.as_view(),
        name="crawl_configuration_update",
    ),
    path(
        "crawler/configs/<int:pk>/delete",
        CrawlConfigurationDeleteView.as_view(),
        name="crawl_configuration_delete",
    ),
    path(
        "crawler/configs/<int:pk>/run",
        start_crawl_view,
        name="crawl_configuration_start_crawl",
    ),
    path(
        "crawler/configs/create",
        CrawlConfigurationCreateView.as_view(),
        name="crawl_configuration_create",
    ),
    path(
        "",
        CrawlListView.as_view(),
        name="crawl_list",
    ),
    path(
        "crawls/<int:pk>",
        CrawlDetailView.as_view(),
        name="crawl_detail",
    ),
    path(
        "crawls/<int:crawl_pk>/wacz",
        get_wacz,
        name="wacz",
    ),
    path(
        "crawls/<int:crawl_pk>/screenshot",
        get_crawl_screenshot,
        name="crawl_screenshot",
    ),
    path("browsers/", BrowserProfileListView.as_view(), name="browser_profile_list"),
    path(
        "browsers/create",
        browser_profile_create_view,
        name="browser_profile_create",
    ),
    path(
        "browsers/<int:pk>/edit",
        BrowserProfileUpdateView.as_view(),
        name="browser_profile_update",
    ),
    path(
        "browsers/<int:pk>/delete",
        BrowserProfileDeleteView.as_view(),
        name="browser_profile_delete",
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]
