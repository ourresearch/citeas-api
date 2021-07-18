import json
import os
import sys

from flask import abort, jsonify, make_response, render_template, request

from app import app
from software import Software
from step import step_configs


def json_dumper(obj):
    """
    if the obj has a to_dict() function we've implemented, uses it to get dict.
    from http://stackoverflow.com/a/28174796
    """
    try:
        return obj.to_dict()
    except AttributeError:
        return obj.__dict__


def json_resp(thing):
    json_str = json.dumps(thing, sort_keys=True, default=json_dumper, indent=4)

    if request.path.endswith(".json") and (os.getenv("FLASK_DEBUG", False) == "True"):
        print("rendering output through debug_api.html template")
        resp = make_response(render_template("debug_api.html", data=json_str))
        resp.mimetype = "text/html"
    else:
        resp = make_response(json_str, 200)
        resp.mimetype = "application/json"
    return resp


def abort_json(status_code, msg):
    body_dict = {"HTTP_status_code": status_code, "message": msg, "error": True}
    resp_string = json.dumps(body_dict, sort_keys=True, indent=4)
    resp = make_response(resp_string, status_code)
    resp.mimetype = "application/json"
    abort(resp)


@app.after_request
def after_request_stuff(resp):
    # support CORS
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers[
        "Access-Control-Allow-Methods"
    ] = "POST, GET, OPTIONS, PUT, DELETE, PATCH"
    resp.headers[
        "Access-Control-Allow-Headers"
    ] = "origin, content-type, accept, x-requested-with"

    # without this jason's heroku local buffers forever
    sys.stdout.flush()

    return resp


# ENDPOINTS
#
######################################################################################
@app.route("/", methods=["GET"])
def index_endpoint():
    return jsonify(
        {
            "version": "0.1",
            "documentation_url": "https://citeas.org/api",
            "msg": "Don't panic",
        }
    )


@app.route("/product/<path:id>", methods=["GET"])
def citeas_product_get(id):
    if id.endswith(".pdf"):
        return jsonify({"error_message": "PDF documents are not supported."})
    elif id.endswith((".doc", "docx")):
        return jsonify({"error_message": "Word documents are not supported."})
    else:
        my_software = Software(id)
        my_software.find_metadata()
        return jsonify(my_software.to_dict())


@app.route("/steps", methods=["GET"])
@app.route("/steps/", methods=["GET"])
def citeas_step_configs():
    return jsonify(step_configs())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
