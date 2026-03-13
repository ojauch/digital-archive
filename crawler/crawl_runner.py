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

    command = [
        "crawl",
        "--url",
        config.url,
        "--generateWACZ",
        "--text",
        "--collection",
        str(crawl.pk),
        "--scopeType",
        config.scope,
    ]

    if config.extra_hops:
        command.append("--extraHops")
        command.append(str(config.extra_hops))

    os.makedirs(settings.CRAWL_DIRECTORY, exist_ok=True)

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
        crawl.wacz_archive.name = relative_wacz_path

    # clean up crawl directory
    shutil.rmtree(os.path.join(settings.CRAWL_DIRECTORY, "collections", str(crawl.pk)))

    crawl.save()


def get_container_log(container_id):
    try:
        container = client.containers.get(container_id)

        container_log = container.logs()
        container_log = container_log.decode("utf-8")
        return container_log
    except docker.errors.NotFound:
        return None
