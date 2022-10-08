from django.http import HttpResponse
from django.http.response import JsonResponse
from .sqlite import query_token
import logging
from . import settings
import json
import os
from uuid import uuid4
from django import forms
from .systen_unit import download_unit
from .systen_unit import isURL
from .systen_unit import get_unique_str
import re
from .core_algorithm import core_algorithm
import threading

logger = logging.getLogger('log')


def identity_authentication(func):
    '''
    common_token:ebc74c68-c620-4457-841b-da52ee2fa78a
    :param func:
    :return:
    '''

    def wrapper(req):
        try:
            token_arr = query_token()
            request_headers = req.headers
            logger.info("token:" + str(token_arr))
            if 'Authorization' in request_headers and request_headers['Authorization'] in token_arr:
                return func(req)
            else:
                return JsonResponse({
                    "success": False,
                    "msg": "tocken Verification failed"
                })
        except Exception as exp:
            return JsonResponse({
                "success": False,
                "msg": "tocken Verification failed"
            })

    return wrapper


@identity_authentication
def HeartBeat(req):
    return JsonResponse({
        "success": True,
        "msg": "heartbeat success..."
    })


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


def handle_uploaded_file(f, file_name):
    file_path = os.path.join(settings.UPLOAD_URL)
    logger.info(file_path + " - upload success")
    with open(os.path.join(file_path, file_name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


@identity_authentication
def FileUp(request):
    if request.method == 'POST':
        myFile = request.FILES.get("file", None)
        if myFile:
            file_name = str(uuid4()) + ".csv"
            handle_uploaded_file(myFile, file_name)
            return HttpResponse(json.dumps({
                "code": 200,
                "msg": "upload success",
                "body": {
                    "file_url": "static/upload/" + file_name,
                    "ret": "6000"
                }
            }))
        else:
            return HttpResponse(json.dumps({
                "code": 201,
                "msg": "file upload fail,please do upload again,make sure use http-post",
                "body": {
                    "file_url": "",
                    "ret": "6001"
                }
            }))

    else:
        pass
    return HttpResponse(json.dumps({
        "code": 201,
        "msg": "file upload fail,please do upload again,make sure use http-post",
        "body": {
            "file_url": "",
            "ret": "6002"
        }
    }))


@identity_authentication
def FileDown(req):
    '''文件下载'''
    if req.method == "POST":
        req_para = json.loads(req.body)
        if "work_id" not in req_para:
            return JsonResponse({
                "success": False,
                "msg": "miss para work_id"
            })
        work_id = str(req_para["work_id"])
        file_path = os.path.join(settings.DWON_RESU_URL)
        if work_id + ".csv" in os.listdir(file_path):
            with open(os.path.join(file_path, work_id + ".csv")) as file:
                resp = HttpResponse(file)
                resp['Content-Type'] = 'application/octet-stream'
                resp['Content-Disposition'] = 'attachment;filename="' + work_id + '.csv"'
                return resp
        else:
            return HttpResponse(json.dumps({
                "code": 201,
                "msg": "request err,please use post request",
                "body": {
                    "ret": "6001"
                }
            }))
    else:
        return HttpResponse(json.dumps({
            "code": 201,
            "msg": "request err,please use post request",
            "body": {
                "ret": "6002"
            }
        }))


@identity_authentication
def get_process(req):
    if req.method == "POST":
        req_para = json.loads(req.body)
        if "work_id" not in req_para:
            return JsonResponse({
                "success": False,
                "msg": "miss para work_id"
            })

        work_id = str(req_para["work_id"])
        resu_file_url = os.path.join(settings.DWON_RESU_URL, work_id + ".csv")
        process_file_url = os.path.join(settings.PROCESS_URL, "process_" + work_id)
        if os.path.exists(resu_file_url):
            return HttpResponse(json.dumps({
                "code": 200,
                "msg": "task complete",
                "body": {
                    "ret": "5000",
                    "process": "100%"
                }
            }))
        else:
            if os.path.exists(process_file_url):
                with open(process_file_url, 'r') as process:
                    lines = process.readlines()
                if len(lines) >= 2:
                    current_process = str(lines[-1]).split("：")[-1].strip()
                    if current_process == "100%":
                        current_process = "98.7%"
                    return HttpResponse(json.dumps({
                        "code": 200,
                        "msg": "task in progress",
                        "body": {
                            "ret": "5000",
                            "process": current_process
                        }
                    }))
                else:
                    return HttpResponse(json.dumps({
                        "code": 200,
                        "msg": "task in progress",
                        "body": {
                            "ret": "5000",
                            "process": "0%"
                        }

                    }))

            else:
                return HttpResponse(json.dumps({
                    "code": 201,
                    "msg": "work err,please upload file again to start task",
                    "body": {
                        "ret": "5001",
                        "process": "0%"
                    }
                }))
    else:
        return HttpResponse(json.dumps({
            "code": 201,
            "msg": "wrong request type",
            "body": {
                "ret": "5002",
                "process": "0%"
            }
        }))


@identity_authentication
def do_algorithm(req):
    work_id = get_unique_str()
    if req.method == "POST" and req.body != None:
        try:
            down_un = download_unit()
            req_para = json.loads(req.body)
            # 文件路径
            if "file_url" not in req_para:
                return JsonResponse({
                    "success": False,
                    "msg": "miss para file_url"
                })
            file_url = str(req_para["file_url"])
            upload_url = str(req_para["file_url"])
            if isURL(file_url):
                # 参数校验

                save_url = os.path.join(settings.MEDIA_ROOT, work_id + "." + str(file_url).split(".")[-1])
                ca = core_algorithm('core_para')

                down_thread = threading.Thread(target=down_un.download_file, args=(file_url, save_url, work_id))
                core_thread = threading.Thread(target=ca.file_deal, args=(save_url, work_id))
                down_thread.start()
                down_thread.join()
                if down_un.get_result():
                    logger.info("[" + work_id + "]:请求成功，任务开始启动")
                    core_thread.start()
                    return HttpResponse(json.dumps({
                        "code": 200,
                        "msg": "Check successed.",
                        "body": {
                            "ret": "4000",
                            "pre_time": str(
                                down_un.get_len() / 4000 + down_un.get_len() / 300000 + down_un.get_len() / 25000),
                            "work_id": work_id,
                            "download_url": upload_url.split("upload")[0] + "download/" + work_id + ".csv",

                        }
                    }))
                else:
                    logger.error("[" + work_id + "]:没有告警文件下载url，或者告警文件url不合法，下载地址为" + str(file_url))
                    return HttpResponse(json.dumps({
                        "code": 201,
                        "msg": "warn file download address error",
                        "body": {
                            "ret": "4003"
                        }
                    }))
            else:
                logger.error("[" + work_id + "]:告警文件下载失败，或者告警文件不符合要求，下载地址为" + str(file_url))
                return HttpResponse(json.dumps({
                    "code": 201,
                    "msg": "warn data download failed",
                    "body": {
                        "ret": "4001"
                    }
                }))
        except Exception as e:
            logger.error("[" + work_id + "]:" + str(e) + " line_no " + str(e.__traceback__.tb_lineno))
            return HttpResponse(json.dumps({
                "code": 500,
                "msg": "unknown exception",
                "body": {
                    "ret": "4002"
                }
            }))
    else:
        return HttpResponse(json.dumps({
            "code": 201,
            "msg": "wrong request type",
            "body": {
                "ret": "4004"
            }
        }))
