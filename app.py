from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Trek, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask import flash

#CONFIGURING + INITIALISING:

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "temporary-secret-key"

db.init_app(app)

with app.app_context():
	db.create_all()


# HOME PLACEHOLDER

@app.route('/')
def home():
	user_id = session.get("user_id")
	role = session.get("role")
	
	if user_id:
		current_user = db.session.get(User, user_id)
	else:
		current_user = None

	return render_template("index.html", title = "Trekking Management App", current_user=current_user, role=role)


# REGITRSATION PAGE



@app.route('/register', methods = ['GET', 'POST'])
def register():

	if request.method == 'POST':
		name = request.form["name"]
		email = request.form["email"]
		password = request.form["password"]
		contact = request.form["contact"]
		role = request.form["role"]

		#CHECKInG fOR EXISTING USER
		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
			return "Email already registered"
		

		new_user = User(
			name=name,
			email=email,
			password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
			contact=contact,
			role=role,
			is_approved=False if role == "staff" else True
		)
		
		db.session.add(new_user)
		db.session.commit()

		flash("Registration successful. Please log in")
		return redirect(url_for("login"))
	
	return render_template("register.html")


# LOGIN PAGE


@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == "POST":
		email = request.form["email"]
		password = request.form["password"]

		user = User.query.filter_by(email=email).first()

		if user and check_password_hash(user.password_hash, password):

			if user.is_blacklisted:
				return "Your account has been blacklisted."

			
			session["user_id"] = user.id
			session["role"] = user.role

			if user.role == 'admin':
				flash("Logged in successfully!")
				return redirect(url_for('admin_dashboard'))

			elif user.role == 'staff':
				flash("Logged in successfully!")
				return redirect(url_for('staff_dashboard'))

			else:
				flash("Logged in successfully!")
				return redirect(url_for('user_dashboard'))

		flash("Invalid email or password")
		return redirect(url_for('login'))

	
	return render_template("login.html")


#LOGOUT

@app.route('/logout')
def logout():
	session.clear()
	flash("Logged out successfully")
	return redirect(url_for("home"))



#USER EDIT PROFILE
@app.route('/profile', methods=['GET','POST'])
def edit_profile():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user:
		return redirect(url_for('home'))

	if request.method == "POST":

		existing = User.query.filter(
					User.email == request.form['email'],
					User.id != current_user.id
				).first()
		
		if existing:
			flash("Email already exists.")
			return redirect(url_for("edit_profile"))

		current_user.name = request.form['name']
		current_user.email = request.form['email']
		current_user.contact = request.form['contact']

		db.session.commit()

		flash("Profile updated successfully!")

		if current_user.role == 'admin':
			return redirect(url_for('admin_settings'))
		elif current_user.role == 'staff':
			return redirect(url_for('staff_dashboard'))
		else:
			return redirect(url_for('user_dashboard'))

		

	return render_template(
		'edit_profile.html',
		current_user=current_user,
		title="Edit Profile"
	)


###ADMIN###3

#ADMIN DASHBOARD

@app.route('/admin/dashboard')
def admin_dashboard():
	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)
	
	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	total_treks = Trek.query.count()
	total_users = User.query.filter_by(role='user').count()
	total_staff = User.query.filter_by(role='staff').count()
	total_bookings = Booking.query.count()

	return render_template(
		'admin_dashboard.html',
		title='Admin Dashboard',
		current_user=current_user,
		total_treks=total_treks,
		total_staff=total_staff,
		total_users=total_users,
		total_bookings=total_bookings
		)


#ADMIN VIEW ALL BOOKINGS

@app.route('/admin/bookings')
def admin_bookings():
	user_id = session.get('user_id')
	
	if not user_id:
		return redirect(url_for('login'))
	
	current_user = db.session.get(User, user_id)
		
	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	bookings = Booking.query.order_by(
		Booking.booking_date.desc()
	).all()

	return render_template(
		'admin_bookings.html',
		bookings=bookings
	)



#ADMIN ADD TRWK

@app.route('/admin/add-trek', methods = ['GET','POST'])
def add_trek():
	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	staff_members = User.query.filter_by(role='staff', is_approved=True).all()



	if request.method == "POST":
		name = request.form['name']
		location = request.form['location']
		difficulty = request.form['difficulty']
		location = request.form["location"]
		assigned_staff_id = int(request.form['assigned_staff_id'])
		total_slots = request.form["total_slots"]
		start_date = datetime.strptime(request.form['start_date'], "%Y-%m-%d").date()
		end_date = datetime.strptime(request.form['end_date'], "%Y-%m-%d").date()
		
		if end_date < start_date:
			return "End date cannot be before start date"

		duration = (end_date - start_date).days + 1

		description = request.form["description"]
		

		new_trek = Trek(name=name, location=location, difficulty=difficulty, duration=int(duration), total_slots=int(total_slots), available_slots=int(total_slots), assigned_staff_id=assigned_staff_id, start_date=start_date, end_date=end_date, description=description)
		
		db.session.add(new_trek)
		db.session.commit()

		flash("Trek added successfully!")
		return redirect(url_for('admin_dashboard'))

	return render_template('add_treks.html', title='Add Trek', current_user=current_user, staff_members=staff_members)



#ADMIN APPROVE STAFF MANAGE PAGE

@app.route('/admin/staff')
def manage_staff():
	user_id = session.get('user_id')
	
	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	search = request.args.get('search', '')
	
	query = User.query.filter_by(role='staff')
	
	if search:
		if search.isdigit():
			query = query.filter(User.id == int(search))
		else:
			query = query.filter(User.name.ilike(f'%{search}%'))
	
	staff_members = query.all()

	
	return render_template('manage_staff.html', title='Manage Staff', current_user=current_user, staff_members=staff_members)


# ADMIN REPORTS PAGE
@app.route('/admin/report')
def admin_report():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))


	# Overview statistics

	total_treks = Trek.query.count()
	total_users = User.query.filter_by(role='user').count()
	total_staff = User.query.filter_by(role='staff').count()
	total_bookings = Booking.query.count()


	# Booking status counts

	booked_count = Booking.query.filter_by(status='Booked').count()
	cancelled_count = Booking.query.filter_by(status='Cancelled').count()
	completed_count = Booking.query.filter_by(status='Completed').count()


	# Trek booking report

	treks = Trek.query.all()

	trek_reports = []

	for trek in treks:

		booking_count = Booking.query.filter_by(
			trek_id=trek.id
		).count()

		trek_reports.append({
			'trek': trek,
			'booking_count': booking_count
		})


	# Staff assignment report

	staff_reports = []

	for trek in treks:

		participant_count = Booking.query.filter_by(
			trek_id=trek.id,
			status='Booked'
		).count()

		staff_reports.append({
			'trek': trek,
			'participant_count': participant_count
		})


	return render_template(
		'admin_report.html',
		current_user=current_user,
		title="Reports",
		total_treks=total_treks,
		total_users=total_users,
		total_staff=total_staff,
		total_bookings=total_bookings,
		booked_count=booked_count,
		cancelled_count=cancelled_count,
		completed_count=completed_count,
		trek_reports=trek_reports,
		staff_reports=staff_reports
	)

#ADMINN SETTIGNS PAGE

@app.route('/admin/settings')
def admin_settings():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	return render_template(
		'admin_settings.html',
		current_user=current_user,
		title="Settings"
	)

#ADMIN STAFF APPROVAL PAGE

@app.route('/admin/staff/<int:staff_id>/approve', methods = ['POST'])
def approve_staff(staff_id):
	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User,user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	staff = db.session.get(User, staff_id)

	if not staff or staff.role != 'staff':
		return 'Staff member not found', 404

	staff.is_approved = True
	db.session.commit()

	flash("Staff approved!")
	return redirect(url_for('manage_staff'))



#CHANGHE PASSWORD ADMIN

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user:
		return redirect(url_for('home'))


	if request.method == 'POST':

		current_password = request.form.get('current_password')
		new_password = request.form.get('new_password')
		confirm_password = request.form.get('confirm_password')


		if not check_password_hash(current_user.password_hash, current_password):
			flash('Current password is incorrect.')
			return redirect(url_for('change_password'))


		if new_password != confirm_password:
			flash('New passwords do not match.')
			return redirect(url_for('change_password'))


		if not new_password:
			flash('New password cannot be empty.')
			return redirect(url_for('change_password'))


		current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

		db.session.commit()

		flash('Password changed successfully.')
		return redirect(url_for('admin_settings'))


	return render_template(
		'change_password.html',
		current_user=current_user,
		title='Change Password'
	)

#ADMIN STAFF BLACKLIST PAGE

@app.route('/admin/staff/<int:staff_id>/blacklist', methods=['POST'])
def blacklist_staff(staff_id):

	if session.get('role') != 'admin':
		return redirect(url_for('home'))

	staff = db.session.get(User, staff_id)

	if not staff or staff.role != 'staff':
		return "Staff not found", 404

	staff.is_blacklisted = True
	db.session.commit()

	flash("Staff Blacklisted")
	return redirect(url_for('manage_staff'))



#ADMIN STAFF UNBLACKLIST PAGE

@app.route('/admin/staff/<int:staff_id>/unblacklist', methods=['POST'])
def unblacklist_staff(staff_id):

	if session.get('role') != 'admin':
		return redirect(url_for('home'))

	staff = db.session.get(User, staff_id)

	if not staff or staff.role != 'staff':
		return "Staff not found", 404

	staff.is_blacklisted = False
	db.session.commit()

	flash("Staff Unblacklisted")
	return redirect(url_for('manage_staff'))

#MANAGE TREKS PAGE

@app.route('/admin/treks')
def manage_treks():
	
	if 'user_id' not in session:
		return redirect(url_for('login'))

	if session.get('role') != 'admin':
		return 'Access Denied', 403

	search = request.args.get("search")
	if search:
		if search.isdigit():

			treks = Trek.query.filter(
				Trek.id == int(search)
			).all()

		else:
			treks = Trek.query.filter(
				Trek.name.ilike(f'%{search}%')
			).all()

	else:
		treks = Trek.query.all()

	return render_template('manage_treks.html', title='Manage Treks', treks=treks)



#EDIT TRKS PAGE

@app.route('/admin/treks/<int:trek_id>/edit', methods = ['GET','POST'])
def edit_trek(trek_id):
	if 'user_id' not in session:
		return redirect(url_for('login'))

	if session.get('role') != 'admin':
		return 'Access denied', 403
	
	trek = Trek.query.get_or_404(trek_id)
	staff_members = User.query.filter_by(role='staff', is_approved=True).all()
	
	if request.method == 'POST':
		trek.name = request.form['name']
		trek.location = request.form['location']
		trek.difficulty = request.form['difficulty']

		new_total_slots = int(request.form['total_slots'])
		
		booked_slots = Booking.query.filter_by(
			trek_id=trek.id,
			status="Booked"
		).count()

		if new_total_slots<booked_slots:
			return "Total slots cannot be less than the number of existing bookings", 400

		trek.total_slots = new_total_slots
		trek.available_slots = new_total_slots-booked_slots

		trek.assigned_staff_id = int(request.form['assigned_staff_id'])

		trek.description = request.form['description']
		start_date = datetime.strptime(request.form['start_date'],"%Y-%m-%d").date()
		end_date = datetime.strptime(request.form['end_date'],"%Y-%m-%d").date()
		
		if end_date < start_date:
			return "End date cannot be beofre start date", 400

		trek.start_date = start_date
		trek.end_date = end_date
		trek.duration = (end_date - start_date).days + 1

		db.session.commit()
		flash("Trek updated!")
		return redirect(url_for('manage_treks'))

	flash("Trek updated!")
	return render_template('edit_trek.html', trek=trek, staff_members=staff_members)




# DELETE TREKS PAGE

@app.route('/admin/treks/<int:trek_id>/delete', methods = ['POST'])
def delete_trek(trek_id):
	
	if 'user_id' not in session:
		return redirect(url_for('login'))

	if session.get('role') != 'admin':
		return "Access denied", 403

	trek = Trek.query.get_or_404(trek_id)

	db.session.delete(trek)
	db.session.commit()

	flash("Trek deleted")
	return redirect(url_for('manage_treks'))



#ADMIN MANAGE USERS
@app.route('/admin/users')
def manage_users():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'admin':
		return redirect(url_for('home'))

	search = request.args.get('search', '')

	query = User.query.filter_by(role='user')

	if search:
		if search.isdigit():
			query = query.filter(User.id == int(search))
		else:
			query = query.filter(User.name.ilike(f'%{search}%'))

	users = query.all()

	return render_template(
		'manage_users.html',
		users=users,
		search=search,
		current_user=current_user,
		title="Manage Users"
	)


#ADMIN USERS BLACKLIST PAGE

@app.route('/admin/users/<int:user_id>/blacklist', methods=['POST'])
def blacklist_user(user_id):

	if session.get('role') != 'admin':
		return redirect(url_for('home'))

	user = db.session.get(User, user_id)

	if not user or user.role != 'user':
		return "User not found", 404

	user.is_blacklisted = True
	db.session.commit()

	flash("User Blacklisted")
	return redirect(url_for('manage_users'))



#ADMIN USERS UNBLACKLIST PAGE

@app.route('/admin/users/<int:user_id>/unblacklist', methods=['POST'])
def unblacklist_user(user_id):

	if session.get('role') != 'admin':
		return redirect(url_for('home'))

	user = db.session.get(User, user_id)

	if not user or user.role != 'user':
		return "User not found", 404

	user.is_blacklisted = False
	db.session.commit()

	flash("User Unblacklisted")
	return redirect(url_for('manage_users'))

###STAFF####

#STAFF DASHBOARD

@app.route('/staff/dashboard')
def staff_dashboard():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	if not current_user.is_approved:
		return "Waiting for admin approval"

	search = request.args.get('search', '')

	query = Trek.query.filter_by(
		assigned_staff_id=current_user.id
	)

	if search:
		query = query.filter(Trek.name.ilike(f'%{search}%'))

	assigned_treks = query.all()

	participant_counts = {}

	for trek in assigned_treks:
		participant_counts[trek.id] = Booking.query.filter_by(
			trek_id=trek.id,
			status="Booked"
		).count()

	total_treks = Trek.query.filter_by(
		assigned_staff_id=current_user.id
	).count()

	upcoming_treks = Trek.query.filter(
		Trek.assigned_staff_id == current_user.id,
		Trek.status.in_(["Pending", "Open"])
	).count()

	total_participants = Booking.query.join(Trek).filter(
		Trek.assigned_staff_id == current_user.id,
		Booking.status == "Booked"
	).count()

	completed_treks = Trek.query.filter_by(
		assigned_staff_id=current_user.id,
		status="Completed"
	).count()

	return render_template(
		'staff_dashboard.html',
		title='Staff Dashboard',
		current_user=current_user,
		treks=assigned_treks,
		participant_counts=participant_counts,
		search=search,
		total_treks=total_treks,
		upcoming_treks=upcoming_treks,
		total_participants=total_participants,
		completed_treks=completed_treks
	)

#STAFF MY TREKS PAGE
# STAFF MY TREKS PAGE

@app.route('/staff/my-treks')
def staff_my_treks():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	if not current_user.is_approved:
		return "Waiting for admin approval"

	treks = Trek.query.filter_by(
		assigned_staff_id=current_user.id
	).all()

	participant_counts = {}

	for trek in treks:
		participant_counts[trek.id] = Booking.query.filter_by(
			trek_id=trek.id,
			status="Booked"
		).count()

	return render_template(
		'staff_my_treks.html',
		current_user=current_user,
		treks=treks,
		participant_counts=participant_counts,
		title="My Treks"
	)


# STAFF VIEW TREK

@app.route('/staff/trek/<int:trek_id>/view')
def view_staff_trek(trek_id):

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	if not current_user.is_approved:
		return "Waiting for admin approval"

	trek = Trek.query.get_or_404(trek_id)

	if trek.assigned_staff_id != current_user.id:
		return "Access denied", 403

	bookings = Booking.query.filter_by(
		trek_id=trek.id,
		status="Booked"
	).all()

	return render_template(
		'view_staff_trek.html',
		current_user=current_user,
		trek=trek,
		bookings=bookings,
		title="View Trek"
	)

#STAFF UPDATE TREK

@app.route('/staff/treks/<int:trek_id>/update', methods=['GET','POST'])
def update_trek(trek_id):

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	if not current_user.is_approved:
		return "Waiting for admin approval"

	trek = Trek.query.get_or_404(trek_id)

	if trek.assigned_staff_id != current_user.id:
		return "Access denied", 403

	if request.method == "POST":
		trek.available_slots = int(request.form['available_slots'])
		trek.status = request.form['status']

		if trek.status == "Completed":
			bookings = Booking.query.filter_by(
				trek_id=trek.id,
				status="Booked"
			).all()

			for booking in bookings:
				booking.status = "Completed"

				
		db.session.commit()
		flash("Trek updated!")

		return redirect(url_for('staff_dashboard'))

	
	return render_template(
		'update_trek.html',
		trek=trek,
		current_user=current_user,
		title='Update Trek'
	)

#STAFF TREK PARTICIPANTS PAGE

@app.route('/staff/trek/<int:trek_id>/participants')
def trek_participants(trek_id):
	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	trek = Trek.query.get_or_404(trek_id)

	if trek.assigned_staff_id != current_user.id:
		return "Access denied", 403

	bookings = Booking.query.filter_by(
		trek_id = trek.id,
		status = "Booked"
	).all()

	return render_template(
		'participants.html',
		trek=trek,
		bookings=bookings
	)


#STAFF ALL PARTICIPANTS PAGE

@app.route('/staff/participants')
def staff_participants():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'staff':
		return redirect(url_for('home'))

	treks = Trek.query.filter_by(
		assigned_staff_id=current_user.id
	).all()

	trek_ids = [trek.id for trek in treks]

	bookings = Booking.query.filter(
		Booking.trek_id.in_(trek_ids),
		Booking.status == "Booked"
	).all() if trek_ids else []

	return render_template(
		'staff_participants.html',
		current_user=current_user,
		treks=treks,
		bookings=bookings,
		title="Participants"
	)

#####USER######
#USER DASHBOARD

@app.route('/user/dashboard')
def user_dashboard():

	user_id = session.get("user_id")

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	current_bookings = Booking.query.filter_by(
		user_id=current_user.id,
		status="Booked"
	).all()

	total_bookings = Booking.query.filter_by(
		user_id=current_user.id
	).count()

	completed_bookings = Booking.query.filter_by(
		user_id=current_user.id,
		status="Completed"
	).count()

	available_treks = Trek.query.filter_by(
		status="Open"
	).count()

	return render_template(
		'user_dashboard.html',
		title="User Dashboard",
		current_user=current_user,
		bookings=current_bookings,
		total_bookings=total_bookings,
		completed_bookings=completed_bookings,
		available_treks=available_treks
	)


#USER BOOK TREK
@app.route('/book/<int:trek_id>', methods = ["POST"])
def book_trek(trek_id):

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	trek = Trek.query.get_or_404(trek_id)

	existing_booking = Booking.query.filter_by(
		user_id=current_user.id,
		trek_id=trek.id,
		status="Booked"
	).first()

	if existing_booking:
		return "You have already booked htis trek"

	if trek.available_slots <= 0:
		return "No slots available"

	booking = Booking(
		user_id=current_user.id,
		trek_id=trek.id,
		booking_date=date.today()
	)

	db.session.add(booking)

	trek.available_slots -= 1

	db.session.commit()

	flash("Trek booked successfully!")
	return redirect(url_for('user_dashboard'))


#USER BROWSE TREKS

@app.route('/user/treks')
def browse_treks():

	user_id = session.get("user_id")

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	search = request.args.get('search', '')
	difficulty = request.args.get('difficulty', '')
	location = request.args.get('location', '')

	query = Trek.query.filter_by(status="Open")

	if search:
		query = query.filter(Trek.name.ilike(f'%{search}%'))

	if difficulty:
		query = query.filter(Trek.difficulty == difficulty)

	if location:
		query = query.filter(Trek.location.ilike(f"%{location}%"))

	treks = query.all()

	current_bookings = Booking.query.filter_by(
		user_id=current_user.id,
		status="Booked"
	).all()

	booked_trek_ids = [
		booking.trek_id
		for booking in current_bookings
	]

	locations = db.session.query(Trek.location).distinct().all()
	locations = [loc[0] for loc in locations]

	return render_template(
		'browse_treks.html',
		title="Browse Treks",
		current_user=current_user,
		treks=treks,
		booked_trek_ids=booked_trek_ids,
		search=search,
		difficulty=difficulty,
		location=location,
		locations=locations
	)





#USER VIEW TREK

@app.route('/user/trek/<int:trek_id>')
def view_trek(trek_id):

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	trek = Trek.query.get_or_404(trek_id)

	booking = Booking.query.filter_by(
		user_id=current_user.id,
		trek_id=trek.id
	).first()

	booking_status = None

	if booking:
		booking_status = booking.status

	return render_template(
		'view_trek.html',
		current_user=current_user,
		trek=trek,
		booking_status=booking_status,
		title=trek.name
	)



#USER MY BOOKINGS

@app.route('/user/bookings')
def my_bookings():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	bookings = Booking.query.filter_by(
		user_id=current_user.id,
		status="Booked"
	).all()

	return render_template(
		'my_bookings.html',
		current_user=current_user,
		bookings=bookings,
		title="My Bookings"
	)

#USER BOOKING HISTORY

@app.route('/user/history')
def booking_history():

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	current_user = db.session.get(User, user_id)

	if not current_user or current_user.role != 'user':
		return redirect(url_for('home'))

	history = Booking.query.filter(
		Booking.user_id == current_user.id,
		Booking.status.in_(["Completed", "Cancelled"])
	).all()

	return render_template(
		'booking_history.html',
		current_user=current_user,
		history=history,
		title="Booking History"
	)

#CANCEL BOOKING
@app.route('/cancel/<int:booking_id>', methods=["POST"])
def cancel_booking(booking_id):

	user_id = session.get('user_id')

	if not user_id:
		return redirect(url_for('login'))

	booking = Booking.query.get_or_404(booking_id)

	if booking.user_id != user_id:
		return "Access denied", 403

	trek = db.session.get(Trek, booking.trek_id)

	booking.status = "Cancelled"
	trek.available_slots += 1

	db.session.commit()

	flash("Trek cancelled successfully!")
	return redirect(url_for('user_dashboard'))


# JUST FOR DEBUG

if __name__ == "__main__":
	app.run(debug=True)
