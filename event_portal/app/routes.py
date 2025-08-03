from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User
from flask import Blueprint

from datetime import datetime

from .models import Event, Registration

from . import login_manager

from flask import current_app as app

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='sha256'),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')

    # Get user's event registrations with event info
    registrations = Registration.query.filter_by(user_id=current_user.id).all()

    return render_template('user_dashboard.html', registered_events=registrations)



from flask import abort
from werkzeug.utils import secure_filename
import os

# Check admin role decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/events')
@login_required
@admin_required
def admin_events():
    events = Event.query.order_by(Event.date.asc()).all()
    return render_template('admin_events.html', events=events)


from datetime import datetime

@app.route('/admin/events/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_str = request.form['date']
        time_str = request.form['time']
        location = request.form['location']
        image_file = request.files['image']

        # Convert string inputs to proper Python objects
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()

        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.root_path, 'static', 'images', filename)
            image_file.save(image_path)

        new_event = Event(
            title=title,
            description=description,
            date=date,
            time=time,
            location=location,
            image=filename
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin_events'))

    return render_template('create_event.html')



@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'info')
    return redirect(url_for('admin_events'))


@app.route('/user/events')
@login_required
def user_events():
    events = Event.query.order_by(Event.date.asc()).all()
    registrations = [r.event_id for r in current_user.registrations]
    return render_template('user_events.html', events=events, registrations=registrations)


@app.route('/user/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)

    already_registered = Registration.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if already_registered:
        flash('You already registered for this event.', 'warning')
        return redirect(url_for('user_events'))

    registration = Registration(user_id=current_user.id, event_id=event_id)
    db.session.add(registration)
    db.session.commit()
    flash('Successfully registered for the event!', 'success')
    return redirect(url_for('user_events'))


@app.route('/user/my-registrations')
@login_required
def my_registrations():
    registrations = Registration.query.filter_by(user_id=current_user.id).all()
    return render_template('my_registrations.html', registrations=registrations)


@app.route('/admin/events/<int:event_id>/attendees')
@login_required
@admin_required
def view_attendees(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(event_id=event.id).all()
    return render_template('event_attendees.html', event=event, registrations=registrations)


@app.route('/admin/registration/<int:reg_id>/checkin', methods=['POST'])
@login_required
@admin_required
def checkin_attendee(reg_id):
    registration = Registration.query.get_or_404(reg_id)
    registration.checked_in = True
    db.session.commit()
    flash(f"{registration.attendee.name} checked in!", 'success')
    return redirect(url_for('view_attendees', event_id=registration.event_id))


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')
