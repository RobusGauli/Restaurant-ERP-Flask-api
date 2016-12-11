class SessionManager(object):
	def __init__(self, Session):
		self.Session = Session


	def __enter__(self):
		self.session = self.Session()
		return self.session

	def __exit__(self, type, value, trace):

		self.session.close()
		return 'helo there'

from functools import wraps
from flask import request
from flask import jsonify
def keyrequire(*keys):
	def decorator(func):
		def wrapper(*args, **kwargs):
			for key in keys:
				if not key in request.json:
					return jsonify(dict(error = 'missing Keys : Please make sure keys are correct'))
			return func(*args, **kwargs)
		return wrapper
	return decorator




def envelop(data, code, pagination=None):
	'''A envelop function that decorates the json api with the dictionary with keys : code, meta, data'''

	if isinstance(pagination,str): #if pagination is str 
		response = {'meta' : dict(code=code),
					'data' : data,
					'pagination' : pagination} 
		
	else:
		response = {'meta' : dict(code=code),
					'data' : data} 
		
	return response

def error_envelop(error_code, error_type, error_message):
	response = {'meta' : dict(error_type=error_type, error_code=error_code, error_message=error_message)
	}
	return response


def update_envelop(code):
	response = {'meta' : dict(code=code, message='Updated Successfully')}
	return response

def delete_envelop(code):
	response = {'meta' : dict(code=code, message='Deleted Successfully')}
	return response