from django.core.management.base import BaseCommand

from crawler.crawl_runner import finish_crawl
from crawler.models import Crawl


class Command(BaseCommand):
    def handle(self, *args, **options):
        for crawl in Crawl.objects.filter(status="running"):
            finish_crawl(crawl)
