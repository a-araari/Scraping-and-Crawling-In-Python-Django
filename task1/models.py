from django.utils import timezone as tz

from django.db import models


class tbl_page_data(models.Model):
    # unique id
    task_id = models.IntegerField()
    # single url
    url = models.URLField(max_length=200)
    # HTTP status code
    status_code = models.IntegerField(null=True, blank=True)
    # null
    page_content = models.TextField(null=True, blank=True)
    # processing
    status_process = models.IntegerField(null=True, blank=True)
    # null
    error_msg = models.CharField(max_length=255, null=True, blank=True)
    # Task create time
    created_at = models.DateTimeField(default=tz.now)
    # waiting time after page load
    waiting = models.IntegerField(null=True, blank=True)
    # scroll in page 
    scroll = models.IntegerField(null=True, blank=True)