from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	password_hash = db.Column(db.String(512), nullable=False)
	role = db.Column(db.String(20), nullable=False)
	contact = db.Column(db.String(20), nullable=False)
	is_approved = db.Column(db.Boolean, nullable=False, default=True)
	is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)


class Trek(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	location = db.Column(db.String(100), nullable=False)
	difficulty = db.Column(db.String(20), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	total_slots = db.Column(db.Integer, nullable=False)
	available_slots = db.Column(db.Integer, nullable=False)
	assigned_staff_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	assigned_staff = db.relationship("User", foreign_keys=[assigned_staff_id])
	status = db.Column(db.String(20), nullable=False, default="Pending")
	start_date = db.Column(db.Date, nullable=False)
	end_date = db.Column(db.Date, nullable=False)
	description = db.Column(db.Text)


class Booking(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"), nullable=False)
	booking_date = db.Column(db.Date, nullable=False)
	status = db.Column(db.String(20), nullable=False, default="Booked")

	user = db.relationship("User")
	trek = db.relationship("Trek")
	

