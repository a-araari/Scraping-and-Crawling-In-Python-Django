import random
import string

from django.utils import timezone as tz
from django.db import models


def get_auto_generated_task_id():
    task_id = ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(7))
    
    while tbl_crawl_task.objects.filter(task_id=task_id).exists():
        task_id = ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(7))

    return task_id


class tbl_crawl_task(models.Model):
    NONE_STATUS = 'none'
    PROCESSING_STATUS = 'processing'
    SUCCESS_STATUS = 'success'
    ERROR_STATUS = 'error'

    STATUS_CHOICES = {
        (NONE_STATUS, 'none'),
        (PROCESSING_STATUS, 'processing'),
        (SUCCESS_STATUS, 'success'),
        (ERROR_STATUS, 'error'),
    }

    # unique id
    task_id = models.CharField(max_length=7, default=get_auto_generated_task_id, editable=False, unique=True)
    # single url
    url = models.URLField(max_length=200)
    # processing
    status_process = models.CharField(max_length=50, choices=STATUS_CHOICES, default=NONE_STATUS)
    # null
    error_msg = models.CharField(max_length=255, null=True, blank=True)
    # Task create time
    created_at = models.DateTimeField(default=tz.now)
    # url-crawl-limitation
    limit = models.IntegerField(null=True, blank=True)
    # waiting time after page load
    waiting = models.IntegerField(null=True, blank=True)
    # scroll in page 
    scroll = models.IntegerField(null=True, blank=True)
    # pending task index
    pending_task = models.IntegerField()

    def __str__(self):
        return f'{self.task_id}: {self.url}'


class tbl_crawl_task_data(models.Model):
    EXTERNAL_LINK_TYPE = 'external'
    INTERNAL_LINK_TYPE = 'internal'
    LINK_TYPE_CHOICES = {
        (EXTERNAL_LINK_TYPE, 'external'),
        (INTERNAL_LINK_TYPE, 'internal'),
    }

    # unique id
    task_id = models.ForeignKey(
        tbl_crawl_task,
        to_field='task_id',
        on_delete=models.CASCADE,
    )
    # single url
    url = models.URLField(max_length=200)
    # Link type
    link_type = models.CharField(max_length=10, choices=LINK_TYPE_CHOICES)
    # status code
    status_code = models.IntegerField()
    # depth level
    depth_level = models.IntegerField()

    def __str__(self):
        return f'{self.task_id}: {self.url} : depth={self.depth_level}'

class Logger(models.Model):
    text = models.TextField()