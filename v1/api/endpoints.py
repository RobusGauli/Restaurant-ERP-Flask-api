from flask import Flask, jsonify, url_for, redirect, request
from models.model import ItemCategory, Item, Bill, ItemOrder
from models.model import init_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
#my own utils modules
from utils import SessionManager, keyrequire
from utils import envelop, error_envelop, update_envelop, delete_envelop

URL_DB = 'postgres://postgres:robus@localhost:5432/restaurantv1'

engine = init_db(URL_DB)

app = Flask(__name__)
Session = sessionmaker(bind=engine)

@app.route('/api/v1/itemcategories', methods=['GET'])
def getItemCategories():
	'''A function to get all the names in item categories'''

	#check to see if there is any query parameter for pagination in the http url for pagination
	if request.args and ('page' and 'size' in request.args):
		page = int(request.args['page']) 
		size = int(request.args['size'])
	

	#initiate the session
	next_pagination = None
	with SessionManager(Session) as session:
		if request.args: #if there is query parameter in the url perform the pagination
			categories = session.query(ItemCategory).order_by(ItemCategory.id).all()[size*page : size*page + size]
			#set the next pagination url as a string
			next_pagination = url_for('getItemCategories')+ '?page={0}&size={1}'.format(page+1, size)
		else:
			#display all the items
			categories = session.query(ItemCategory).order_by(ItemCategory.id).all()
		#create a list of dictionary with all the necessary data in the dictionary
		alist = [dict(name=category.name, extra=category.extra, id=category.id) for category in categories]
		return jsonify(envelop(code=200, data=alist, pagination=next_pagination))


@app.route('/api/v1/itemcategories/<int:id>', methods=['GET'])
def getItemCategory(id):
	''' This function gets the single category given the id'''
	with SessionManager(Session) as session:
		try:
			category = session.query(ItemCategory).filter(ItemCategory.id == id).one()
		except:
			return jsonify(error_envelop(error_code=404, error_type='Value Error', error_message='ID is not available'))
		category_dict = dict(name=category.name, extra=category.extra, id = category.id)
		return jsonify(envelop(code=200, data=category_dict, pagination=None))

#a function to update the item category

@app.route('/api/v1/itemcategories/<int:id>', methods=['PUT'])
def updateItemCategory(id):
	'''This function is used to update the item category in the database'''
	with SessionManager(Session) as session:
		try:
			item_category = session.query(ItemCategory).filter(ItemCategory.id == id).one()
			item_category.name = request.json.get('name', item_category.name)
			item_category.extra = request.json.get('extra', item_category.extra)
			#sesion.add(item_category)
			session.commit()

		except IntegrityError:
			# if name already exsits in database  
			return jsonify(error_envelop(400, 'Integrity Error','Name already Exists'))
		except:
			return jsonify(error_envelop(404, 'ValueError', 'Id not found'))
	#now the item is succesfulluy updated
	return jsonify(update_envelop(200))

	#update the database item



@app.route('/api/v1/itemcategories', methods=['POST'])
@keyrequire('name', 'extra') #makes sure that these keys are available
def setItemCategory():
	name = request.json['name']
	extra = request.json.get('extra', 'No Information found')
	with SessionManager(Session) as session:
		cat = ItemCategory(name=name, extra=extra)
		session.add(cat)
		try:
			session.commit()
		except IntegrityError:
			return jsonify(dict(error='{0} already exists!!'.format(name)))
	return jsonify(dict(status='created successfully'))



@app.route('/api/v1/itemcategories/<int:id>', methods=['DELETE'])
def deleteItemCategory(id):
	with SessionManager(Session) as session:
		try:
			cat_item = session.query(ItemCategory).filter(ItemCategory.id == id).one()
			session.delete(cat_item)
			session.commit()
		except:
			return jsonify(error_envelop(404, 'ValueError', 'Id Not Found'))
	#if succesfully deleted
	return jsonify(delete_envelop(200))



if __name__ == '__main__':
	app.run(host='localhost', port=5000, debug=True)