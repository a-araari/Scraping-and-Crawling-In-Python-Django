import random
import string

from django.utils import timezone as tz
from django.db import models


def get_auto_generated_task_id():
    task_id = ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(7))

    while tbl_page_data.objects.filter(task_id=task_id).exists():
        task_id = ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(7))

    return task_id


class tbl_page_data(models.Model):
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
    # HTTP status code
    status_code = models.IntegerField(null=True, blank=True)
    # null
    page_content = models.TextField(null=True, blank=True)
    # processing
    status_process = models.CharField(max_length=50, choices=STATUS_CHOICES, default=NONE_STATUS)
    # null
    error_msg = models.CharField(max_length=255, null=True, blank=True)
    # Task create time
    created_at = models.DateTimeField(default=tz.now)
    # waiting time after page load
    waiting = models.IntegerField(null=True, blank=True)
    # scroll in page 
    scroll = models.IntegerField(null=True, blank=True)
    # pending task index
    pending_task = models.IntegerField()
    
    def __str__(self):
        return f'{self.task_id}: {self.url}'