from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.urls import reverse


class CrawlConfiguration(models.Model):
    SCOPE_TYPES = (
        ("page", _("Page")),
        ("page-spa", _("Page SPA")),
        ("prefix", _("Prefix")),
        ("host", _("Host")),
        ("domain", _("Domain")),
        ("any", _("Any")),
        ("custom", _("Custom")),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Owner"))
    name = models.CharField(max_length=250, verbose_name=_("Name"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    url = models.URLField(verbose_name=_("URL"))
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_TYPES,
        default="page",
        verbose_name=_("Crawl Scope"),
    )
    include = models.TextField(
        null=True, blank=True, verbose_name=_("Include Rule Regex")
    )
    extra_hops = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Number of extra hops beyond scope"),
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("crawl_configuration_detail", kwargs={"pk": self.pk})


class Crawl(models.Model):
    CRAWL_STATUS = (
        ("created", _("Created")),
        ("running", _("Running")),
        ("finished", _("Finished")),
        ("failed", _("Failed")),
        ("aborted", _("Aborted")),
    )

    config = models.ForeignKey(
        CrawlConfiguration,
        on_delete=models.CASCADE,
        verbose_name=_("Configuration"),
        related_name="crawls",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    started_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Started at")
    )
    finished_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Finished at")
    )
    status = models.CharField(
        max_length=20, choices=CRAWL_STATUS, default="created", verbose_name=_("Status")
    )
