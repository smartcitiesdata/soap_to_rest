from quart import Quart, Response, jsonify, request
from schema import Schema, And, Use, Optional, SchemaError
from soap_to_rest.wsdl_service import invoke_action, WsdlError
from soap_to_rest.suds_converter import to_serializable

WSDL_PARAMS_SCHEMA = Schema(
  {
    'url': str,
    'action': str,
    Optional('params'): Use(dict, error="'params' must be an object"),
    Optional('auth'): Schema({
      'username': str,
      'password': str
    })
  },
  name="WSDL Parameters"
)

import logging
logging.basicConfig(level=logging.WARNING)

app = Quart(__name__)


@app.route('/api/v1/wsdl', methods=['POST'])
async def wsdl():
  try:
    (url, action, params, auth) = await _validate_wsdl_params(request)
    result = invoke_action(url, action, params, auth)
    serializable_result = to_serializable(result)

    return jsonify(serializable_result)
  except SchemaError as se:
    return _schema_error(se)
  except WsdlError as we:
    return _wsdl_error(we)


async def _validate_wsdl_params(wsdl_request):
  request_body = await wsdl_request.json

  WSDL_PARAMS_SCHEMA.validate(request_body)

  url = request_body.get('url')
  action = request_body.get('action')
  params = request_body.get('params')
  auth = request_body.get('auth')

  return (url, action, params, auth)


def _schema_error(error):
  message = error.code
  logging.error(f"Failed to validate WSDL request parameters: {message}")
  return Response(message, status=400, mimetype="text/plain")


def _wsdl_error(error):
  message = f"Failed to invoke WSDL: {error.wrapped}"
  logging.error(message)
  return Response(message, status=400, mimetype="text/plain")


if __name__ == '__main__':
  app.run()