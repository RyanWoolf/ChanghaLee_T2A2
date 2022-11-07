from flask import Blueprint, request, url_for, redirect
from config import db, bcrypt
from models.customer import Customer
from models.booking import Booking
from schemas.customer_schema import CustomerSchema
from schemas.booking_schema import BookingSchema
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from controllers.auth_controller import auth_login, auth_register, authorization, authorization_admin
from datetime import date, timedelta

from flask_jwt_extended import jwt_required


bookings_bp = Blueprint('bookings', __name__, url_prefix='/bookings')


def not_found():
    return {'error': f'Bookings not found.'}, 404


#Getting all bookings from the db
@bookings_bp.route('/')
@jwt_required()
def all_bookings():
    authorization()
    stmt = db.select(Booking).order_by(Booking.id)
    bookings = db.session.scalars(stmt)
    return BookingSchema(many=True).dump(bookings), 201
    
    
#Get specific booking with id
@bookings_bp.route('/<int:id>/')
@jwt_required()
def get_one_booking(id):
    authorization()
    stmt = db.select(Booking).filter_by(id=id)
    booking = db.session.scalar(stmt)
    if booking:
        return BookingSchema().dump(booking)
    else:
        return not_found()
    

#Get bookings of today
@bookings_bp.route('/today/')
@jwt_required()
def get_today_bookings():
    authorization()
    stmt = db.select(Booking).filter_by(date=date.today())
    booking = db.session.scalars(stmt)
    result = BookingSchema(many=True).dump(booking)
    if len(result) == 0:
        return not_found()
    else:
        return result
    
#Get bookings of tomorrow
@bookings_bp.route('/tomorrow/')
@jwt_required()
def get_tomorrow_bookings():
    authorization()
    stmt = db.select(Booking).filter_by(date=date.today()+timedelta(days=1))
    booking = db.session.scalars(stmt)
    result = BookingSchema(many=True).dump(booking)
    if len(result) == 0:
        return not_found()
    else:
        return result


#Get specific customer with full name. first name/last name
@bookings_bp.route('/<string:f_name>/<string:l_name>')
@jwt_required()
def search_booking_fullname(f_name, l_name):
    authorization()
    stmt = db.select(Customer).filter_by(
        first_name=f_name.capitalize(), 
        last_name=l_name.capitalize())
    customer = db.session.scalars(stmt) # there could be lots of customers with exactly same name
    result = CustomerSchema(many=True).dump(customer)
    if len(result) == 0:
        return {'error': f'Booking under {f_name} {l_name} not found'}, 404
    else:
        return result


#New customer join through here
@bookings_bp.route('/join', methods=['POST'])
def join():
    data = CustomerSchema().load(request.json)
    customer = Customer(
        email = data.get('email'),
        password = bcrypt.generate_password_hash(data['password']).decode('utf-8'),
        first_name = data['first_name'].capitalize(),
        last_name = data.get('last_name').capitalize(),
        phone = data['phone'],
        token = create_access_token(identity=str(customer.id), expires_delta=timedelta(days=1))
    )
    db.session.add(customer)
    db.session.commit()
    return CustomerSchema(exclude='password').dump(customer), 201


# Create a new booking
@bookings_bp.route('/', methods=['POST'])
@jwt_required()
def create_booking():
    data_booking = BookingSchema().load(request.json)
    booking = Booking(
        date = data_booking['date'], # check again
        time = data_booking['time'], # check again
        pax = data_booking['pax'],
        table = data_booking['table'], # check again
        comment = data_booking.get('comment'),
        customer_id = get_jwt_identity()
    )
    db.session.add(booking)
    stmt = db.select(Customer).filter_by(id=get_jwt_identity())
    customer = db.session.scalar(stmt)
    customer.visited += 1
    db.session.commit()
    return BookingSchema().dump(booking), 201
    


#Delete customer from the DB. For safety reasons, only accessible through id and admin
@bookings_bp.route('/<int:id>/', methods = ['DELETE'])
@jwt_required()
def delete_one_customer(id):
    authorization_admin()
    stmt = db.select(Customer).filter_by(id=id)
    customer = db.session.scalar(stmt)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        return {'msg': f'Customer id:{id} {customer.first_name} {customer.last_name} deleted successfully'}
    else:
        return not_found(id)


#Modify customer. Only accessible through id
@bookings_bp.route('/<int:id>/', methods = ['PUT', 'PATCH'])
@jwt_required()
def update_one_customer(id):
    authorization_admin()
    stmt = db.select(Customer).filter_by(id=id)
    customer = db.session.scalar(stmt)
    if customer:
        customer.first_name = request.json.get('first_name') or customer.first_name
        customer.last_name = request.json.get('last_name') or customer.last_name
        customer.phone = request.json.get('phone') or customer.phone
        customer.email = request.json.get('email') or customer.email
        customer.visited = request.json.get('visited') or customer.visited
        db.session.commit()
        return CustomerSchema().dump(customer)
    else:
        return not_found(id)