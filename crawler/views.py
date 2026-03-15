import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseForbidden,
    HttpResponseNotFound,
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from werkzeug.http import parse_range_header

from .forms import BrowserProfileCreateForm
from .models import CrawlConfiguration, Crawl, BrowserProfile
from .crawl_runner import run_crawl, get_container_log


class CrawlConfigurationListView(LoginRequiredMixin, ListView):
    model = CrawlConfiguration
    context_object_name = "crawl_configs"

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user).annotate(
            size=Sum("crawls__wacz_file_size")
        )


class CrawlConfigurationDetailView(LoginRequiredMixin, DetailView):
    model = CrawlConfiguration
    context_object_name = "crawl_config"

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user).annotate(
            size=Sum("crawls__wacz_file_size")
        )


crawl_configuration_fields = [
    "name",
    "description",
    "url",
    "scope",
    "include",
    "extra_hops",
    "text_extract",
    "screenshots",
    "block_ads",
    "workers",
    "page_limit",
    "page_load_timeout",
    "allow_hash_urls",
    "behavior_timeout",
    "size_limit",
    "time_limit",
    "lang",
    "max_page_retries",
    "browser_profile",
]


class CrawlConfigurationCreateView(LoginRequiredMixin, CreateView):
    model = CrawlConfiguration
    fields = crawl_configuration_fields

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = _("Create Crawl Configuration")
        context["cancel_url"] = reverse("crawl_configuration_list")
        return context


class CrawlConfigurationUpdateView(LoginRequiredMixin, UpdateView):
    model = CrawlConfiguration
    fields = crawl_configuration_fields

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = _("Update Crawl Configuration")
        context["cancel_url"] = reverse(
            "crawl_configuration_detail", kwargs={"pk": self.object.pk}
        )
        return context


class CrawlConfigurationDeleteView(LoginRequiredMixin, DeleteView):
    model = CrawlConfiguration
    success_url = reverse_lazy("crawl_configuration_list")
    context_object_name = "crawl_config"

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user)


class CrawlListView(LoginRequiredMixin, ListView):
    model = Crawl
    context_object_name = "crawls"

    def get_queryset(self):
        return Crawl.objects.filter(config__owner=self.request.user)


class CrawlDetailView(LoginRequiredMixin, DetailView):
    model = Crawl

    def get_queryset(self):
        return Crawl.objects.filter(config__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["debug"] = settings.DEBUG

        if self.object.container_id:
            context["log"] = get_container_log(self.object.container_id)

        return context


@login_required
def start_crawl_view(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    config = get_object_or_404(CrawlConfiguration, pk=pk)
    if config.owner != request.user:
        return HttpResponseForbidden(
            _("Only the owner of a crawl configuration is allowed to start a crawl.")
        )

    crawl = Crawl.objects.create(config=config)
    run_crawl.enqueue(crawl.id)
    return redirect(reverse("crawl_configuration_detail", kwargs={"pk": pk}))


class BrowserProfileListView(LoginRequiredMixin, ListView):
    model = BrowserProfile
    context_object_name = "browser_profiles"


@login_required
def browser_profile_create_view(request):
    if request.method == "POST":
        form = BrowserProfileCreateForm(request.POST, request.FILES)

        if form.is_valid():
            form.instance.owner = request.user
            profile = form.save()

            profile_dir = os.path.join(settings.CRAWL_DIRECTORY, "profiles")
            os.makedirs(profile_dir, exist_ok=True)

            profile_path = os.path.join(profile_dir, f"{profile.id}.tar.gz")
            with open(profile_path, "wb") as f:
                for chunk in form.cleaned_data["profile_file"].chunks():
                    f.write(chunk)

            return redirect(reverse("browser_profile_list"))
    else:
        form = BrowserProfileCreateForm()

    heading = _("Create Browser Profile")
    multipart = True
    return render(
        request,
        "crawler/browserprofile_form.html",
        {"form": form, "heading": heading, "multipart": multipart},
    )


class BrowserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = BrowserProfile
    fields = ["name", "description"]
    success_url = reverse_lazy("browser_profile_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = _("Update Browser Profile")
        context["multipart"] = False
        return context


class BrowserProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = BrowserProfile
    success_url = reverse_lazy("browser_profile_list")
    context_object_name = "browser_profile"


@login_required
def get_wacz(request, crawl_pk):
    crawl = get_object_or_404(Crawl, pk=crawl_pk)

    if crawl.config.owner != request.user:
        return HttpResponseForbidden(
            _("Only the owner of a crawl configuration is allowed to view it's crawls.")
        )

    if not crawl.wacz_archive:
        return HttpResponseNotFound(_("Crawl does not have a WACZ archive."))

    range_header = request.headers.get("Range")
    if range_header:
        parsed_ranges = parse_range_header(range_header)
        if not parsed_ranges:
            return HttpResponse(_("Invalid range header"), status=416)

        ranges = parsed_ranges.ranges

        # only support single ranges for now
        # TODO: implement multi range support
        if len(ranges) > 1:
            return HttpResponseBadRequest(
                _("Server does only support single range requests.")
            )

        first_range = ranges[0]

        wacz_file = crawl.wacz_archive

        if (first_range[0] is not None and abs(first_range[0]) > wacz_file.size) or (
            first_range[1] is not None and first_range[1] > wacz_file.size
        ):
            return HttpResponse(_("Range is out of bounds"), status=416)

        if first_range[0] is not None and first_range[0] > 0:
            wacz_file.seek(first_range[0])
        # if first value is negative it has to be interpreted as suffix length
        elif first_range[0] is not None and first_range[0] < 0:
            offset = first_range[0] + wacz_file.size
            wacz_file.seek(offset)

        if first_range[1] is not None:
            data = wacz_file.read(first_range[1] - first_range[0])
        else:
            data = wacz_file.read()

        response = HttpResponse(data, status=206)

        if first_range[0] is not None and first_range[0] < 0:
            content_range_header = f"bytes {first_range[0]}/{wacz_file.size}"
        elif first_range[1] is None:
            content_range_header = f"bytes {first_range[0]}-/{wacz_file.size}"
        elif first_range[0] is None:
            content_range_header = f"bytes -{first_range[1]}/{wacz_file.size}"
        else:
            content_range_header = (
                f"bytes {first_range[0]}-{first_range[1]}/{wacz_file.size}"
            )

        response.headers["Content-Range"] = content_range_header
        filename = os.path.split(wacz_file.name)[1]
        response.headers["Content-Type"] = "application/zip"
        response.headers["Content-Disposition"] = f"inline; filename={filename}"
    else:
        response = FileResponse(crawl.wacz_archive, content_type="application/zip")

    response.headers["Accept-Ranges"] = "bytes"
    return response


@login_required
def get_crawl_screenshot(request, crawl_pk):
    crawl = get_object_or_404(Crawl, pk=crawl_pk)
    if crawl.config.owner != request.user:
        return HttpResponseForbidden(
            _("Only the owner of a crawl configuration is allowed to view it's crawls.")
        )

    if not crawl.screenshot:
        return HttpResponseNotFound(_("Crawl does not have a screenshot."))

    return FileResponse(crawl.screenshot, content_type="image/jpeg")
