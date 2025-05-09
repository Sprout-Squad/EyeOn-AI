from flask import Response
from collections import OrderedDict
import json

def success(message, code=200, filename=None, base64_str=None):
    res = OrderedDict()
    res["isSuccess"] = True
    res["httpStatus"] = code
    res["message"] = message
    res["filename"] = filename
    res["base64"] = base64_str
    return Response(json.dumps(res), status=code, mimetype='application/json')

def error(message, code=400):
    res = OrderedDict()
    res["isSuccess"] = False
    res["httpStatus"] = code
    res["message"] = message
    return Response(json.dumps(res), status=code, mimetype='application/json')
