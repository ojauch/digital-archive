from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _

from .models import CrawlConfiguration


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
