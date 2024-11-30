from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import secrets
import pgeocode



app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Folder where uploaded images will be saved
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

volunteers = []
events = [
]



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/eventlist')
def eventlist():
    filtered_events = []
    
    if 'zip' in session:
        user_zip = session['zip']
        dist = pgeocode.GeoDistance('us')

        for event in events:
            event_zip = event.get('zip', None)
            if event_zip:
                distance = dist.query_postal_code(user_zip, event_zip)
                if distance is not None and distance <= 0.01:  # (100 m)
                    filtered_events.append(event)
        
    else:
        filtered_events = events
    
    return render_template('eventlist.html', events=filtered_events)

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        zipcode = request.form['zip']
        role = request.form['role']

        volunteers.append({"name": name, "email": email, "password": password, "zip": zipcode, "role": role})
        return redirect(url_for('index'))
    return render_template('sign_up.html')



@app.route('/events/<int:event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    event = next((e for e in events if e['id'] == event_id), None)
    if request.method == 'POST':
        name = request.form['name']
        event['volunteers'].append(name)
        return redirect(url_for('event_details', event_id=event_id))
    return render_template('events.html', event=event)



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        for i in volunteers:
            if i["email"] == email and i["password"] == password:
                session['logged_in'] = True
                session['role'] = i['role']
                session['name'] = i['name']
                session['email'] = i['email']
                session['zip'] = i['zip']
                return redirect(url_for('index'))
        
        error = "Invalid email or password, please try again."
    
    return render_template('login.html', error = error)



@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    if 'logged_in' in session:
        if request.method == 'POST':
            event_name = request.form['name']
            event_date = request.form['date']
            event_address = request.form['address']
            event_description = request.form['description']
            event_zipcode = request.form['zip']
            event_wage = request.form['wage']
            
            image = request.files['image']
            if image:
                image_filename = secrets.token_hex(8) + os.path.splitext(image.filename)[1]
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image.save(image_path)
            else:
                image_filename = "" 

            event_id = len(events) + 1  #so i already found it alr im getting to work!
            events.append({"id": event_id, "name": event_name, "date": event_date, "description": event_description,"address": event_address, "zip": event_zipcode, "wage": event_wage,"image": image_filename})
            return redirect(url_for('index'))
        return render_template('create_event.html')
    else:
        return redirect(url_for('login'))


@app.route('/hours')
def hours():
    hours = 0
    if 'logged_in' in session:
        email = session.get('email')
        for i in volunteers:
            if i['email'] == email:
                hours = i['hours']
    return render_template('hours.html', hours = hours)

@app.route('/update-hours', methods = ['GET', 'POST'])
def update_hours():
    text = None
    if 'logged_in' in session:
        if request.method == 'POST':
            email = request.form['email']
            additional_hours = int(request.form['hours'])
            volunteer = next((v for v in volunteers if v['email'] == email), None)
            if volunteer:
                volunteer['hours'] = int(volunteer['hours']) +additional_hours
                text = f"Updated hours for {volunteer['name']}."

        return render_template('update_hours.html', text=text) 

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True)
