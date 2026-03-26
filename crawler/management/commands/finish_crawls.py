import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from crawler.crawl_runner import finish_crawl
from crawler.models import Crawl

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        crawls = Crawl.objects.filter(
            Q(status="running")
            | (
                Q(status="finished")
                & (Q(wacz_archive__isnull=True) | Q(wacz_archive=""))
            )
        )
        print(f"Found {crawls.count()} crawls")
        for crawl in crawls:
            finish_crawl(crawl)
