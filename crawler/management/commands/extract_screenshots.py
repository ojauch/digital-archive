from django.core.management.base import BaseCommand

from crawler.crawl_runner import extract_crawl_screenshot
from crawler.models import Crawl


class Command(BaseCommand):
    def handle(self, *args, **options):
        crawls = Crawl.objects.filter(
            wacz_archive__isnull=False, screenshot__isnull=True
        )

        for crawl in crawls:
            extract_crawl_screenshot(crawl)
