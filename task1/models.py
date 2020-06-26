import random

from django.utils import timezone as tz

from django.db import models


def get_auto_generated_task_id():
    task_id = random.randint(1, 999999)
    while tbl_page_data.objects.filter(task_id=task_id).exists():
        task_id = random.randint(1, 999999)

    return task_id


class tbl_page_data(models.Model):
    PENDING_STATUS = 'pending'
    PROCESSING_STATUS = 'processing'
    SUCCESS_STATUS = 'success'
    ERROR_STATUS = 'error'

    STATUS_CHOICES = {
        (PENDING_STATUS, 'pending'),
        (PROCESSING_STATUS, 'processing'),
        (SUCCESS_STATUS, 'success'),
        (ERROR_STATUS, 'error'),
    }

    # unique id
    task_id = models.IntegerField(default=get_auto_generated_task_id, editable=False, unique=True)
    # single url
    url = models.URLField(max_length=200)
    # HTTP status code
    status_code = models.IntegerField(null=True, blank=True)
    # null
    page_content = models.TextField(null=True, blank=True)
    # processing
    status_process = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PROCESSING_STATUS)
    # null
    error_msg = models.CharField(max_length=255, null=True, blank=True)
    # Task create time
    created_at = models.DateTimeField(default=tz.now)
    # waiting time after page load
    waiting = models.IntegerField(null=True, blank=True)
    # scroll in page 
    scroll = models.IntegerField(null=True, blank=True)