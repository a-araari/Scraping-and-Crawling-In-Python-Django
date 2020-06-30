from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import tbl_crawl_task, tbl_crawl_task_data
from . import options


def check_key_validation(key):
    """
    check secret key validation in the database
    raise exception if key is unvalid
    """
    if key != settings.VALIDATION_KEY:
        raise ValueError('Unvalid validation key!')


class CrawlSetView(APIView):
    # Args: ?url & limit & waiting & scroll & validation_key
    def get(self, request, format=None):
        """
        Create a row in tbl_crawl_task using the values in request.GET
        """
        try:
            secret_key = request.GET['validation_key']
            check_key_validation(secret_key)

            url = request.GET['url']
            waiting = request.GET['waiting']
            scroll = request.GET['scroll']
            limit = request.GET.get('limit', None)

            tbl = tbl_crawl_task(url=url, limit=limit, waiting=waiting, scroll=scroll)
            tbl.save()

            # starting the crawl task in a seperate Thread
            options.start_crawl_task(tbl)

            return Response({
                    'data': {
                        'task_id': tbl.task_id,
                        'url': tbl.url,
                        'pending_task': tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count(),
                    }
                })
        except Exception as e:
            return Response({
                    'data': {
                        'error': repr(e),
                    }
                })


class CrawlGetView(APIView):
    # Args: ?task_id & validation_key
    def get(self, request, format=None):
        """
        Create a row in tbl_crawl_task using the values in request.GET
        """

        try:
            secret_key = request.GET['validation_key']
            check_key_validation(secret_key)

            task_id = request.GET['task_id']

            tbl = tbl_crawl_task.objects.get(task_id=task_id)


            resp = {
                "Content": {
                    "created_at": tbl.created_at.strftime("%a, %d %b %Y %H:%M:%S GMT"), # (exe: Thu, 25 Jun 2020 12:41:02 GMT)
                    "Task_id": tbl.task_id,
                    "url": tbl.url,
                    "pending_task": tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count(),
                    "status_process": tbl.status_process,
                }
            }
            if tbl.status_process == tbl_crawl_task.ERROR_STATUS:
                resp['Content']['error_msg'] = tbl.error_msg # only when status_process = error, (exe: 404 Page not found or any othererror)

            if tbl.status_process == tbl_crawl_task.SUCCESS_STATUS:
                url_list = list()
                tbl_data_set = tbl.tbl_crawl_task_data_set
                for tbl_data in tbl_data_set.all():
                    url_list.append({
                            "url": tbl_data.url,
                            "depth_level": tbl_data.depth_level,
                            "link_type": tbl_data.link_type, # (External url not need to crawled)
                            "page_status": tbl_data.status_code, # {page HTTP status},(exe: 200,404,500,505)
                        })
                
                resp['Content']['url_list'] = url_list
            else:
                resp['Content']['url_list'] = None

            # delete this instance if status_process in ('success', 'error')
            if tbl.status_process in (tbl_crawl_task.SUCCESS_STATUS, tbl_crawl_task.ERROR_STATUS):
                options.delete_tbl(tbl)


            return Response(resp)
        except Exception as e:
            return Response({
                    'data': {
                        'error': repr(e),
                    }
                })
