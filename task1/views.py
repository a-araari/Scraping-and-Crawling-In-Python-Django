from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import tbl_page_data
from . import  options


def check_key_validation(key):
    """
    check if secret key valid
    raise exception otherwise
    """
    if key != settings.VALIDATION_KEY:
        raise ValueError('Unvalid validation key!')


class PageDataSetView(APIView):
    """
    Set API View for creating scrape tasks
    """
    def get(self, request, format=None):
        """
        Create a task in tbl_page_data using the args in request.GET
        required query strings: (url, waiting, scroll, validation_key)
        """
        try:
            #validate the secret key
            secret_key = request.GET['validation_key']
            check_key_validation(secret_key)

            # getting query strings
            url = request.GET['url']
            waiting = request.GET['waiting']
            scroll = request.GET['scroll']

            # saving the task
            tbl = tbl_page_data(url=url, waiting=waiting, scroll=scroll)
            tbl.save()

            # starting the task in a seperate Thread
            # see options.py
            options.start_task(tbl)

            # return response (task_id, url, pending_task)
            return Response({
                    'data': {
                        'task_id': tbl.task_id,
                        'url': tbl.url,
                        'pending_task': tbl_page_data.objects.filter(status_process=tbl_page_data.PENDING_STATUS).count(),
                    }
                })
        except Exception as e:
            return Response({
                    'data': {
                        'error': repr(e),
                    }
                })


class PageDataGetView(APIView):

    # api_main_url/page_data/get/?task_id={task_id}&validation_key={our-secret-key}
    def get(self, request, format=None):
        """
        Create a row in tbl_page_data using the values in request.GET
        """
        try:
            secret_key = request.GET['validation_key']
            check_key_validation(secret_key)
            
            task_id = request.GET['task_id']

            tbl = tbl_page_data.objects.get(task_id=task_id)

            res = {
                "Content":{
                    "created_at":tbl.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT"), # (exe: Thu, 25 Jun 2020 12:41:02 GMT)
                    "Task_id": task_id,
                    "url": tbl.url,
                    "pending_task" : tbl_page_data.objects.filter(status_process=tbl_page_data.PENDING_STATUS).count(),# (show us the total number of pending task in queue forthis API)
                    "status_process": tbl.status_process,
                    "page_status": tbl.status_code # {page HTTP status  status},(exe: 200,404,500,505 or null onstatus_process=processing)
                }
            }
            if (tbl.status_process == 'error'):
                res["Content"]["error_msg"] = tbl.error_msg # {only when status_process = error} (exe: 404 Page not found or any othererror)

            #{page_100% loaded content or null onstatus_process=error,processing}",
            res["Content"]["page_content"] =  tbl.page_content if (tbl.status_process == 'success') else None

            # delete this instance if status_process in ('success', 'error')
            if tbl.status_process in (tbl_page_data.SUCCESS_STATUS, tbl_page_data.ERROR_STATUS):
                options.delete_tbl(tbl)

            return Response(res)

        except Exception as e:
            return Response({
                    'data': {
                        'error': repr(e),
                    }
                })