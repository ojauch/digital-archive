import docker
import docker.errors
import os
import shutil
import time

from django.conf import settings
from django.tasks import task
from django.utils import timezone

from .models import Crawl

client = docker.from_env()


@task
def run_crawl(crawl_id):
    crawl = Crawl.objects.get(pk=crawl_id)
    config = crawl.config

    # pull latest crawler image if not already present
    image_name = "webrecorder/browsertrix-crawler"
    client.images.pull(image_name)

    os.makedirs(settings.CRAWL_DIRECTORY, exist_ok=True)

    command = get_crawler_command(crawl)
    container = client.containers.create(
        image_name,
        command,
        volumes={settings.CRAWL_DIRECTORY: {"bind": "/crawls", "mode": "rw"}},
        detach=True,
    )
    crawl.container_id = container.id
    crawl.status = "running"
    crawl.started_at = timezone.now()
    crawl.save()

    container.start()

    while container.status != "exited":
        time.sleep(5)
        container.reload()

    crawl.status = "finished"
    crawl.finished_at = timezone.now()

    wacz_path = os.path.join(
        settings.CRAWL_DIRECTORY, "collections", str(crawl.pk), f"{crawl.pk}.wacz"
    )

    if os.path.exists(wacz_path):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, "waczs"), exist_ok=True)
        relative_wacz_path = os.path.join("waczs", f"{crawl.pk}.wacz")
        new_wacz_path = os.path.join(settings.MEDIA_ROOT, relative_wacz_path)
        os.rename(wacz_path, new_wacz_path)
        wacz_file_size = os.path.getsize(new_wacz_path)
        crawl.wacz_archive.name = relative_wacz_path
        crawl.wacz_file_size = wacz_file_size

    # clean up crawl directory
    shutil.rmtree(os.path.join(settings.CRAWL_DIRECTORY, "collections", str(crawl.pk)))

    crawl.save()


def get_crawler_command(crawl):
    config = crawl.config
    command = [
        "crawl",
        "--url",
        config.url,
        "--generateWACZ",
        "--collection",
        str(crawl.pk),
        "--scopeType",
        config.scope,
        "--workers",
        str(config.workers),
        "--pageLimit",
        str(config.page_limit),
        "--pageLoadTimeout",
        str(config.page_load_timeout),
        "--behaviorTimeout",
        str(config.behavior_timeout),
        "--sizeLimit",
        str(config.size_limit),
        "--timeLimit",
        str(config.time_limit),
        "--maxPageRetries",
        str(config.max_page_retries),
        "--title",
        config.name,
        "--description",
        config.description,
    ]

    if config.extra_hops:
        command.append("--extraHops")
        command.append(str(config.extra_hops))

    if config.text_extract:
        command.append("--text")
        command.append(config.text_extract)

    if config.screenshots:
        command.append("--screenshot")
        command.append(config.screenshots)

    if config.block_ads:
        command.append("--blockAds")

    if config.allow_hash_urls:
        command.append("--allowHashUrls")

    if config.lang:
        command.append("--lang")
        command.append(config.lang)

    if config.browser_profile:
        command.append("--profile")
        command.append(config.browser_profile.get_docker_profile_path())

    return command


def get_container_log(container_id):
    try:
        container = client.containers.get(container_id)

        container_log = container.logs()
        container_log = container_log.decode("utf-8")
        return container_log
    except docker.errors.NotFound:
        return None
