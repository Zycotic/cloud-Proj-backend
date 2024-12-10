import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'  # SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Room model (to store room details)
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)

# Define the Reservation model (to store reservations)
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    check_in = db.Column(db.String(50), nullable=False)
    check_out = db.Column(db.String(50), nullable=False)
    room = db.relationship('Room', backref=db.backref('reservations', lazy=True))

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    room_list = []
    for room in rooms:
        room_data = {
            'id': room.id,
            'type': room.type,
            'price': room.price,
            'availability': room.availability
        }
        room_list.append(room_data)
    return jsonify(room_list)

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.query.get_or_404(room_id)
    room_data = {
        'id': room.id,
        'type': room.type,
        'price': room.price,
        'availability': room.availability
    }
    return jsonify(room_data)

@app.route('/rooms', methods=['POST'])
def add_room():
    data = request.get_json()
    new_room = Room(
        type=data['type'],
        price=data['price'],
        availability=data['availability']
    )
    db.session.add(new_room)
    db.session.commit()
    return jsonify({"message": "Room added successfully!"}), 201

@app.route('/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    reservation_list = []
    for reservation in reservations:
        reservation_data = {
            'id': reservation.id,
            'room_id': reservation.room_id,
            'customer_name': reservation.customer_name,
            'check_in': reservation.check_in,
            'check_out': reservation.check_out
        }
        reservation_list.append(reservation_data)
    return jsonify(reservation_list)

@app.route('/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)  # Fetch reservation by ID
    reservation_data = {
        'id': reservation.id,
        'room_id': reservation.room_id,
        'customer_name': reservation.customer_name,
        'check_in': reservation.check_in,
        'check_out': reservation.check_out
    }
    return jsonify(reservation_data)

@app.route('/reservations', methods=['POST'])
def make_reservation():
    data = request.get_json()
    
    # Check if the room exists
    room = Room.query.get(data['room_id'])
    if not room:
        return jsonify({"message": "Room not found!"}), 404
    
    # Check if the room is already reserved during the requested dates
    existing_reservation = Reservation.query.filter(
        Reservation.room_id == data['room_id'],
        # Check for overlapping reservation dates
        (Reservation.check_in <= data['check_out']) & 
        (Reservation.check_out >= data['check_in'])
    ).first()

    if existing_reservation:
        return jsonify({"message": "Room already reserved during these dates!"}), 400
    
    # If the room is available, create the reservation
    new_reservation = Reservation(
        room_id=data['room_id'],
        customer_name=data['customer_name'],
        check_in=data['check_in'],
        check_out=data['check_out']
    )
    
    # Mark room as unavailable after reservation
    room.availability = False

    db.session.add(new_reservation)
    db.session.commit()

    return jsonify({"message": "Reservation made successfully!"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
