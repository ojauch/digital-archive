from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _
from django.http import HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from .models import CrawlConfiguration, Crawl
from .crawl_runner import run_crawl, get_container_log


class CrawlConfigurationListView(LoginRequiredMixin, ListView):
    model = CrawlConfiguration
    context_object_name = "crawl_configs"

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user)


class CrawlConfigurationDetailView(LoginRequiredMixin, DetailView):
    model = CrawlConfiguration
    context_object_name = "crawl_config"

    def get_queryset(self):
        return CrawlConfiguration.objects.filter(owner=self.request.user)


class CrawlConfigurationCreateView(LoginRequiredMixin, CreateView):
    model = CrawlConfiguration
    fields = ["name", "description", "url", "scope", "include", "extra_hops"]

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
    fields = ["name", "description", "url", "scope", "include", "extra_hops"]

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
