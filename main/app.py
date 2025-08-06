from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from config import DB_CONFIG, SSL_COMMERZ_CONFIG
import uuid
import requests
import json
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '12345'

# Database connection
def get_db_connection():
   return mysql.connector.connect(**DB_CONFIG)

# Home/Welcome page
@app.route('/')
def welcome():
   return render_template('welcome.html')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
   if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']
       conn = get_db_connection()
       cursor = conn.cursor(dictionary=True)
       cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s', (username, password))
       admin = cursor.fetchone()
       cursor.close()
       conn.close()
       if admin:
           session['admin_id'] = admin['id']
           session['admin_username'] = admin['username']
           return redirect(url_for('admin_panel'))
       else:
           flash('Invalid credentials')
   return render_template('admin_login.html')

# User Login
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
   if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']
       conn = get_db_connection()
       cursor = conn.cursor(dictionary=True)
       cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
       user = cursor.fetchone()
       cursor.close()
       conn.close()
       if user:
           session['user_id'] = user['id']
           session['user_username'] = user['username']
           return redirect(url_for('user_panel'))
       else:
           flash('Invalid credentials')
   return render_template('user_login.html')

# User Register
@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
   if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']
       email = request.form['email']
       conn = get_db_connection()
       cursor = conn.cursor()
       try:
           cursor.execute('INSERT INTO users (username, password, email, balance) VALUES (%s, %s, %s, %s)', 
                          (username, password, email, 0.0))
           conn.commit()
           flash('Registration successful! Please login.')
           return redirect(url_for('user_login'))
       except mysql.connector.Error as err:
           flash('Username or email already exists')
       finally:
           cursor.close()
           conn.close()
   return render_template('user_register.html')

# Admin Panel
@app.route('/admin_panel')
def admin_panel():
   if 'admin_id' not in session:
       return redirect(url_for('admin_login'))
   conn = get_db_connection()
   cursor = conn.cursor(dictionary=True)

   
   
   # Fetch admins
   cursor.execute('SELECT * FROM admins')
   admins = cursor.fetchall()
   
   # Fetch users
   cursor.execute('SELECT * FROM users')
   users = cursor.fetchall()

   
   # Fetch trains
   cursor.execute('SELECT * FROM trains')
   trains = cursor.fetchall()
   
   # Fetch feedback
   cursor.execute('SELECT * FROM feedback')
   feedback = cursor.fetchall()

   cursor.execute("SELECT balance FROM system_wallet WHERE id = 1")
   balance_result = cursor.fetchone()

    
   cursor.close()
   conn.close()
   return render_template('admin_panel.html', admins=admins, users=users, trains=trains, feedback=feedback, system_wallet=balance_result)

# Add Admin
@app.route('/add_admin', methods=['POST'])
def add_admin():
   if 'admin_id' not in session:
       return redirect(url_for('admin_login'))
   username = request.form['username']
   password = request.form['password']
   conn = get_db_connection()
   cursor = conn.cursor()
   try:
       cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', (username, password))
       conn.commit()
       flash('Admin added successfully')
   except mysql.connector.Error:
       flash('Username already exists')
   finally:
       cursor.close()
       conn.close()
   return redirect(url_for('admin_panel'))


# Remove Admin
@app.route('/remove_admin/<int:admin_id>')
def remove_admin(admin_id):
   if 'admin_id' not in session:
       return redirect(url_for('admin_login'))
   conn = get_db_connection()
   cursor = conn.cursor()
   cursor.execute('DELETE FROM admins WHERE id = %s', (admin_id,))
   conn.commit()
   cursor.close()
   conn.close()
   flash('Admin removed successfully')
   return redirect(url_for('admin_panel'))

# Add Train
@app.route('/add_train', methods=['POST'])
def add_train():
   if 'admin_id' not in session:
       return redirect(url_for('admin_login'))
   train_number = request.form['train_number']
   train_name = request.form['train_name']
   source = request.form['source']
   destination = request.form['destination']
   departure_time = request.form['departure_time']
   fare = request.form['fare']
   conn = get_db_connection()
   cursor = conn.cursor()
   try:
       cursor.execute('INSERT INTO trains (train_number, train_name, source, destination, departure_time, fare) VALUES (%s, %s, %s, %s, %s, %s)', 
                      (train_number, train_name, source, destination, departure_time, fare))
       conn.commit()
       flash('Train added successfully')
   except mysql.connector.Error:
       flash('Train number already exists')
   finally:
       cursor.close()
       conn.close()
   return redirect(url_for('admin_panel'))

# Remove Train
@app.route('/remove_train/<int:train_id>')
def remove_train(train_id):
   if 'admin_id' not in session:
       return redirect(url_for('admin_login'))
   conn = get_db_connection()
   cursor = conn.cursor()
   cursor.execute('DELETE FROM trains WHERE id = %s', (train_id,))
   conn.commit()
   cursor.close()
   conn.close()
   flash('Train removed successfully')
   return redirect(url_for('admin_panel'))




# User Panel
@app.route('/user_panel')
def user_panel():
   if 'user_id' not in session:
       return redirect(url_for('user_login'))
   conn = get_db_connection()
   cursor = conn.cursor(dictionary=True)
   cursor.execute('SELECT balance FROM users WHERE id = %s', (session['user_id'],))
   user = cursor.fetchone()
   cursor.close()
   conn.close()
   return render_template('user_panel.html', balance=user['balance'])

# Buy Ticket
@app.route('/buy_ticket', methods=['GET', 'POST'])
def buy_ticket():
   if 'user_id' not in session:
       return redirect(url_for('user_login'))
   conn = get_db_connection()
   cursor = conn.cursor(dictionary=True)
   cursor.execute('SELECT * FROM trains')
   trains = cursor.fetchall()
   if request.method == 'POST':
       train_id = request.form['train_id']
       cursor.execute('SELECT * FROM trains WHERE id = %s', (train_id,))
       train = cursor.fetchone()
       session['payment_data'] = {
           'type': 'ticket',
           'train_id': train_id,
           'amount': train['fare'],
           'ticket_number': str(uuid.uuid4())
       }
       return redirect(url_for('initiate_payment'))
   cursor.close()
   conn.close()
   return render_template('buy_ticket.html', trains=trains)

# Recharge Rapid Pass
@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
   if 'user_id' not in session:
       return redirect(url_for('user_login'))
   if request.method == 'POST':
       amount = float(request.form['amount'])
       session['payment_data'] = {
           'type': 'recharge',
           'amount': amount
       }
       return redirect(url_for('initiate_payment'))
   return render_template('recharge.html')

# View Available Trains
@app.route('/view_trains')
def view_trains():
   if 'user_id' not in session:
       return redirect(url_for('user_login'))
   conn = get_db_connection()
   cursor = conn.cursor(dictionary=True)
   cursor.execute('SELECT * FROM trains')
   trains = cursor.fetchall()
   cursor.close()
   conn.close()
   return render_template('view_trains.html', trains=trains)

# Initiate SSLCommerz Payment (Demo)
@app.route('/initiate_payment')
def initiate_payment():
   if 'user_id' not in session or 'payment_data' not in session:
       return redirect(url_for('user_login'))
   payment_data = session['payment_data']
   transaction_id = str(uuid.uuid4())
   
   payload = {
       'store_id': SSL_COMMERZ_CONFIG['store_id'],
       'store_passwd': SSL_COMMERZ_CONFIG['store_password'],
       'total_amount': payment_data['amount'],
       'currency': 'BDT',
       'tran_id': transaction_id,
       'success_url': url_for('payment_success', _external=True),
       'fail_url': url_for('payment_fail', _external=True),
       'cancel_url': url_for('payment_cancel', _external=True),
       'emi_option': 0,
       'cus_name': session['user_username'],
       'cus_email': 'customer@example.com',
       'cus_add1': 'Dhaka',
       'cus_city': 'Dhaka',
       'cus_country': 'Bangladesh',
       'cus_phone': '01711111111',
       'shipping_method': 'NO',
       'product_name': 'Metro Ticket' if payment_data['type'] == 'ticket' else 'Rapid Pass Recharge',
       'product_category': 'Service',
       'product_profile': 'general'
   }
   
   response = requests.post(SSL_COMMERZ_CONFIG['api_url'], data=payload)
   if response.status_code == 200:
       data = response.json()
       if data['status'] == 'SUCCESS':
           session['transaction_id'] = transaction_id
           return redirect(data['GatewayPageURL'])
       else:
           flash('Payment initiation failed')
           return redirect(url_for('user_panel'))
   else:
       flash('Error connecting to payment gateway')
       return redirect(url_for('user_panel'))

# Payment Success
@app.route('/payment_success', methods=['GET', 'POST'])
def payment_success():
    if 'user_id' not in session or 'payment_data' not in session or 'transaction_id' not in session:
        return redirect(url_for('user_login'))

    payment_data = session['payment_data']
    payment_amount = payment_data.get('amount')

    if not payment_amount:
        flash("Payment amount missing.")
        return redirect(url_for('ticket_confirmation'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction()

        cursor.execute("UPDATE system_wallet SET balance = balance + %s WHERE id = 1", (payment_amount,))
        if cursor.rowcount == 0:
            raise Exception("Failed to update system balance")

        
        conn.commit()

        ##flash("Ticket purchased and system balance updated successfully!")

    except Exception as e:
        conn.rollback()
        flash("Payment failed due to internal error: " + str(e))
        return redirect(url_for('ticket_confirmation'))

    # Continue post-payment tasks
    if payment_data['type'] == 'ticket':
        train_id= payment_data['train_id']
        ticket_number = payment_data['ticket_number']
        cursor.execute('INSERT INTO tickets (user_id, train_id, ticket_number, purchase_date, amount) VALUES (%s, %s, %s, %s,%s)',
                       (session['user_id'], train_id, ticket_number, datetime.now(),payment_amount))
        conn.commit()

          
        os.makedirs('Metro_Rail_System/static/tickets', exist_ok=True)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(ticket_number)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_path = f'Metro_Rail_System/static/tickets/{ticket_number}.png'
        qr_img.save(qr_path)

        width, height = 3.5 * inch, 2 * inch
        pdf_path = f'Metro_Rail_System/static/tickets/{ticket_number}.pdf'
        c = canvas.Canvas(pdf_path, pagesize=(width, height))

        c.setFillColor(HexColor("#E0F7FA"))
        c.rect(0, 0, width, height, fill=1)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HexColor("#004D40"))
        c.drawString(10, height - 20, "Bangladesh Metro Rail")

        logo_path = os.path.join(os.path.dirname(__file__), 'Metro_Rail_System/static/images/metro_logo.png')
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 10, height - 45, width=40, height=20)
        else:
            c.drawString(10, height - 45, '[Metro Logo Missing]')

        c.setFont("Helvetica", 7)
        c.drawString(60, height - 30, f"Passenger: {session['user_username']}")
        c.drawString(60, height - 42, f"Ticket: {ticket_number}")

        train_cursor = conn.cursor(dictionary=True)
        train_cursor.execute('SELECT * FROM trains WHERE id = %s', (train_id,))
        train = train_cursor.fetchone()
        train_cursor.close()

        c.drawString(10, height - 60, f"Train: {train['train_name']} ({train['train_number']})")
        c.drawString(10, height - 72, f"From: {train['source']} To: {train['destination']}")
        c.drawString(10, height - 84, f"Time: {train['departure_time']}")
        c.drawString(10, height - 96, f"Fare: BDT {train['fare']}")

        c.drawString(10, 10, 'Scan QR at gate')
        c.drawImage(qr_path, width - 60, 5, width=50, height=50)

        c.save()

        session['ticket_pdf_path'] = pdf_path

    elif payment_data['type'] == 'recharge':
        cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s',
                       (payment_data['amount'], session['user_id']))
        conn.commit()
        flash('Rapid Pass recharged successfully')

    # Clean up
    cursor.close()
    conn.close()
    session.pop('payment_data', None)
    session.pop('transaction_id', None)

    return redirect(url_for('ticket_confirmation') if payment_data['type'] == 'ticket' else 'user_panel')

# Payment Fail
@app.route('/payment_fail')
def payment_fail():
   session.pop('payment_data', None)
   session.pop('transaction_id', None)
   flash('Payment failed')
   return redirect(url_for('user_panel'))

# Payment Cancel
@app.route('/payment_cancel')
def payment_cancel():
   session.pop('payment_data', None)
   session.pop('transaction_id', None)
   flash('Payment cancelled')
   return redirect(url_for('user_panel'))

# Logout
@app.route('/logout')
def logout():
   session.clear()
   return redirect(url_for('welcome'))

# Download Ticket
@app.route('/download_ticket')
def download_ticket():
    pdf_path = session.pop('ticket_pdf_path', None)
    if not pdf_path or not os.path.exists(pdf_path):
        flash('Ticket not found')
        return redirect(url_for('user_panel'))
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

# Ticket Confirmation
@app.route('/ticket_confirmation')
def ticket_confirmation():
    if 'ticket_pdf_path' not in session:
        return redirect(url_for('user_panel'))
    return render_template('ticket_confirmation.html')

if __name__ == '__main__':
   app.run(debug=True)