from datetime import date, timedelta

from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import tbl_page_data
from . import  options
from .__init__ import get_p


def validate_key(key):
    """
    check if secret key valid
    raise exception otherwise
    """
    if key != settings.VALIDATION_KEY:
        raise ValueError('Unvalid validation key!')


validate = URLValidator()


def validate_url(url):
    try:
        validate(url)
    except ValidationError as e:
        raise Exception(f'Unvalid URL: {url}')


def validate_positive(n, rep):
    try:
        n = int(n)
        if n is None or type(n) is not int or n < 0:
            raise Exception(f'Unvalid Number: {rep}')
    except:
        raise Exception(f'Unvalid Number: {rep}')

    return n


p_set = False

def auto_delete():
    global p_set
    try:
        if not p_set:
            p_set = True
            set_p(tbl_page_data.filter(status_process=tbl.NONE_STATUS).count())
    except:
        pass
    try:
        before_month = date.today() - timedelta(days=30)
        tbl_page_data.objects.filter(created_at__lte=before_month).delete()
    except:
        pass


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
            auto_delete()
            #validate the secret key
            secret_key = request.GET['validation_key']
            validate_key(secret_key)

            # getting query strings
            url = request.GET['url']
            validate_url(url)

            waiting = request.GET['waiting']
            waiting = validate_positive(waiting, 'waiting')

            scroll = request.GET['scroll']
            scroll = validate_positive(scroll, 'scroll')

            # saving the task
            tbl = tbl_page_data(
                url=url,
                waiting=waiting,
                scroll=scroll,
                pending_task=get_p(),
            )
            tbl.save()

            # starting the task in a seperate Thread
            # see options.py
            options.start_task(tbl)

            # return response (task_id, url, pending_task)
            return Response({
                    'data': {
                        'task_id': tbl.task_id,
                        'url': tbl.url,
                        'pending_task': tbl.pending_task,
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
            validate_key(secret_key)
            
            task_id = request.GET['task_id']

            tbl = tbl_page_data.objects.get(task_id=task_id)

            res = {
                "Content":{
                    "created_at":tbl.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT"), # (exe: Thu, 25 Jun 2020 12:41:02 GMT)
                    "Task_id": task_id,
                    "url": tbl.url,
                    "pending_task" : tbl.pending_task, # !!! (show us the total number of pending task in queue forthis API)
                    "status_process": 'processing' if tbl.status_process==tbl_page_data.NONE_STATUS else tbl.status_process,
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