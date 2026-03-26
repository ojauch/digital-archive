import logging

import docker
import docker.errors
import os
import shutil
import time

from zipfile import ZipFile

from django.conf import settings
from django.tasks import task
from django.utils import timezone
from warcio import ArchiveIterator

from .models import Crawl

client = docker.from_env()

logger = logging.getLogger(__name__)


@task
def run_crawl(crawl_id):
    crawl = Crawl.objects.get(pk=crawl_id)

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

    finish_crawl(crawl)


def finish_crawl(crawl):
    container = client.containers.get(crawl.container_id)

    if container.status != "exited":
        logger.info(
            f"Stop finishing crawl because container status is {container.status}"
        )
        return

    crawl.status = "finished"
    crawl.finished_at = timezone.now()
    crawl.save()

    wacz_path = os.path.join(
        settings.CRAWL_DIRECTORY, "collections", str(crawl.pk), f"{crawl.pk}.wacz"
    )

    if not os.path.exists(wacz_path):
        logger.info(f"Stop finishing crawl because wacz does not exist")
        return

    os.makedirs(os.path.join(settings.MEDIA_ROOT, "waczs"), exist_ok=True)
    relative_wacz_path = os.path.join("waczs", f"{crawl.pk}.wacz")
    new_wacz_path = os.path.join(settings.MEDIA_ROOT, relative_wacz_path)
    shutil.move(wacz_path, new_wacz_path)
    wacz_file_size = os.path.getsize(new_wacz_path)
    crawl.wacz_archive.name = relative_wacz_path
    crawl.wacz_file_size = wacz_file_size

    # clean up crawl directory
    shutil.rmtree(os.path.join(settings.CRAWL_DIRECTORY, "collections", str(crawl.pk)))

    crawl.save()
    extract_crawl_screenshot(crawl)


def extract_crawl_screenshot(crawl):
    if not crawl.wacz_archive:
        return

    wacz_path = os.path.join(settings.MEDIA_ROOT, crawl.wacz_archive.name)
    screenshot_data = get_wacz_screenshot(wacz_path)

    if not screenshot_data:
        return

    screenshot_dir = os.path.join(settings.MEDIA_ROOT, "wacz-screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    with open(os.path.join(screenshot_dir, f"{crawl.pk}.jpg"), "wb") as f:
        f.write(screenshot_data)

    relative_screenshot_path = os.path.join("wacz-screenshots", f"{crawl.pk}.jpg")
    crawl.screenshot.name = relative_screenshot_path
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


def get_wacz_screenshot(wacz_path):
    wacz = ZipFile(wacz_path)
    screenshot_archives = [
        path for path in wacz.namelist() if path.startswith("archive/screenshots-")
    ]

    if len(screenshot_archives) == 0:
        return None

    screenshot_archive = wacz.open(screenshot_archives[0])
    screenshot_data = None
    for record in ArchiveIterator(screenshot_archive):
        if record.rec_type == "resource" and record.content_type == "image/jpeg":
            screenshot_data = record.content_stream().read()
            break

    screenshot_archive.close()
    wacz.close()
    return screenshot_data
