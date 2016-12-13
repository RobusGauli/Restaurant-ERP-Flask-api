from flask import Flask, jsonify, url_for, redirect, request
from models.model import ItemCategory, Item, Bill, ItemOrder
from models.model import init_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
#my own utils modules
from utils import SessionManager, keyrequire
from utils import envelop, error_envelop, update_envelop, delete_envelop
#for debugging
import sys

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



####api for items in the categories-------------------*******------------

@app.route('/api/v1/itemcategories/<int:cat_id>/items', methods=['POST'])
@keyrequire('name', 'unit_price')
def setCategoryItem(cat_id):
	'''This function is used to set the item on the category using the on the given cate id'''

	name = request.json['name']
	unit_price = int(request.json['unit_price'])
	with SessionManager(Session) as session:
		category = session.query(ItemCategory).filter(ItemCategory.id==cat_id).one()
		category_item = Item(name=name, unit_price=unit_price)
		category.c_items.append(category_item)
		session.commit()
	return jsonify(dict(status='created'))

@app.route('/api/v1/itemcategories/<int:cat_id>/items', methods=['GET'])
def getCategoryItems(cat_id):
	'''This function is used to get all the items in the category
		Example : /api/v1/itemcategories/12/items 
		Result : this gets the items of particualar category
	'''
	list_of_items = [] #declaring the empty list outside the context manager
	with SessionManager(Session) as session:
		try:
			category = session.query(ItemCategory).filter(ItemCategory.id == cat_id).one()
			items = category.c_items
			list_of_items = [dict(id=item.id,
								  name=item.name,
								  unit_price=item.unit_price,
								  item_photo_uri = item.item_photo_uri,
								  url_id = url_for('getItem', item_id = item.id)									)
								  for item in items]
		except:
			return jsonify(error_envelop(error_code=404, error_type='Value Error', error_message='ID is not available'))
		
	return jsonify(envelop(code=200, data=list_of_items, pagination=None))


@app.route('/api/v1/items', methods=['GET'])
def getItems():
	''' This function return all the items in the all the categories
	Example : GET /api/v1/items HTTP/1.1
	Result : {
				"id": 1,
				"item_photo_uri": "Image URI Not Available",
				"name": "coke",
				"unit_price": 45
				},............. ... 
	'''
	page = None 
	size = None
	pagination = None
	sql_items = [] #empty items 
	if 'page' and 'size' in request.args:
			page = int(request.args['page'])
			size = int(request.args['size'])

	with SessionManager(Session) as session:
		#perform the pagination if given request.args
		if isinstance(page, int) and isinstance(size, int):
			sql_items = session.query(Item).order_by(Item.id).all()[page*size : page*size + size]
			pagination = url_for('getItems') + '?page={0}&size={1}'.format(page + 1, size)
		elif not request.args: #if there is no arguments in the url
			sql_items = session.query(Item).order_by(Item.id).all()
	items = [dict(url_id = url_for('getItem',item_id=item.id),
				 id=item.id, name=item.name,
				 item_photo_uri=item.item_photo_uri,
				 description=item.description,
				 unit_price=item.unit_price)
				 for item in sql_items]
	return jsonify(envelop(data=items, code=200, pagination=pagination))

@app.route('/api/v1/items/<int:item_id>', methods=['GET'])
def getItem(item_id):
	''' This function is used to get the particular item in items..
	Example : GET /api/v1/items/1 HTTP/1.1
	Result : {
				"description": "No Description Available",
				"id": 1,
				"item_photo_uri": "Image URI Not Available",
				"name": "coke",
				"unit_price": 45
				}
	'''
	item = {}
	with SessionManager(Session) as sesion:
		#check to see if id exisst in items list
		try:
			sql_item = sesion.query(Item).filter(Item.id == item_id).one()
			item['name'] = sql_item.name
			item['id'] = sql_item.id
			item['url_id'] = url_for('getItem', item_id=item_id)
			item['item_photo_uri']  = sql_item.item_photo_uri
			item['description'] = sql_item.description
			item['unit_price'] = sql_item.unit_price
		except:
			return jsonify(error_envelop(404, 'ValueError', 'Invalid ID'))
	return jsonify(envelop(data=item, code=200))



@app.route('/api/v1/itemcategories/<int:cat_id>/items/<int:item_id>', methods=['GET'])
def getCategoryItem(cat_id, item_id):
	'''This function will return the particular item from the list of items
		Example : GET /api/v1/itemcategories/12/items/1 	HTTP/1.1
		Result : {
					"id": 5,
					"url_id" : "/api/v1/items/5"
					"item_photo_uri": "Image URI Not Available",
					"name": "Fanta",
					"unit_price": 34
					}
	'''

	return redirect(url_for('getItem', item_id=item_id))

#updating the category item
@app.route('/api/v1/itemcategories/<int:cat_id>/items/<int:item_id>', methods=['PUT'])
@keyrequire('name', 'unit_price')
def updateCategoryItem(cat_id, item_id):
	'''This function is used to update the database item.
	Example : PUT /api/v1/itemcategories/12/items/1 HTTP/1.1
	Request Body {"name" : "Changed Name", "unit_price" : 234}
	Result : {"Status" : " Successfully Updated", "code" =200}
	'''
	with SessionManager(Session) as session:
		try:
			sql_item = session.query(Item).filter(Item.id == item_id).one()
			#it will return the value if exists or throws an exception if does not find one
			sql_item.name = request.json.get('name', sql_item.name)
			sql_item.unit_price = request.json.get('unit_price', sql_item.unit_price)
			session.commit()
		except:
			return jsonify(error_envelop(404, 'ValueError', 'Id : {0} not found'.format(item_id)))
	return jsonify(dict(status='created Successfully'))




if __name__ == '__main__':
	app.run(host='localhost', port=5000, debug=True)
