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

    TEXT_EXTRACTION_OPTIONS = (
        (None, _("-")),
        ("to-pages", _("to pages")),
        ("to-warc", _("to WARC")),
        ("final-to-warc", _("final to WARC")),
    )

    SCREENSHOT_OPTIONS = (
        (None, _("-")),
        ("view", _("View")),
        ("fullPage", _("Full Page")),
        ("thumbnail", _("Thumbnail")),
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
    text_extract = models.CharField(
        null=True,
        blank=True,
        max_length=20,
        choices=TEXT_EXTRACTION_OPTIONS,
        verbose_name=_("Text Extraction"),
    )
    screenshots = models.CharField(
        null=True,
        blank=True,
        max_length=20,
        choices=SCREENSHOT_OPTIONS,
        verbose_name=_("Screenshots"),
    )
    block_ads = models.BooleanField(default=False, verbose_name=_("Block Ads"))
    workers = models.IntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name=_("Workers")
    )
    page_limit = models.IntegerField(default=0, verbose_name=_("Page Limit"))
    page_load_timeout = models.IntegerField(
        default=90, verbose_name=_("Page Load Timeout")
    )
    allow_hash_urls = models.BooleanField(
        default=False, verbose_name=_("Allow Hash URLs")
    )
    behavior_timeout = models.IntegerField(
        default=90, verbose_name=_("Behavior Timeout")
    )
    size_limit = models.IntegerField(default=0, verbose_name=_("Size Limit"))
    time_limit = models.IntegerField(default=0, verbose_name=_("Time Limit"))
    lang = models.CharField(
        max_length=10, null=True, blank=True, verbose_name=_("Language Code")
    )
    max_page_retries = models.IntegerField(
        default=2, verbose_name=_("Max Page Retries")
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
    container_id = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Docker Container ID")
    )
    wacz_archive = models.FileField(
        upload_to="waczs/", null=True, blank=True, verbose_name=_("WACZ Archive")
    )
    wacz_file_size = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("WACZ File Size"),
    )

    class Meta:
        ordering = ["-created_at"]
