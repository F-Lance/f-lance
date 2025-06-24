# Let's provide the backend logic for:
# 1. Displaying invitation cards from a directory
# 2. Handling card uploads from the admin panel
# 3. Enabling download of QR codes
# We'll simulate image metadata handling in a JSON file for simplicity.

import os
import json
from flask import Flask,session,flash, render_template, request, redirect, url_for, send_from_directory,send_file,abort
import qrcode
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps
from flask_mail import Mail,Message
from dotenv import load_dotenv

load_dotenv()  #Load .env variables

# Configuration
app = Flask(__name__)


@app.route('/static/<path:filename>')
def custom_static(filename):
    static_path = os.path.join(app.root_path, 'static')
    full_path = os.path.join(static_path, filename)

    if os.path.isfile(full_path):
        return send_from_directory('static', filename)

    if filename.endswith(('.jpg', '.jpeg', '.png')):
        return send_file(os.path.join('static/images', 'default.jpg'))
    elif filename.endswith('.ico'):
        return send_file(os.path.join('static/images', 'default-icon.ico'))
    else:
        return abort(404)

# Add your secret key here
app.secret_key = os.getenv('SECRET_KEY', 'defaultfallbackkey') # Replace 'supersecretkey' with a strong and secure key
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # from .env
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # from .env
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

UPLOAD_FOLDER = 'static/cards'
QR_FOLDER = 'static/qr'
CARD_DB = 'card_data.json'


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_FOLDER'] = QR_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
 
#fallback for missing favicon
@app.route('/favicon.ico')
def favicon():
    icon_path = 'static/favicon.ico'
    if os.path.exists(icon_path):
        return send_file(icon_path)
    else:
        return send_file('static/images/default-icon.ico')  # fallback


#login  secure admin

# Load card metadata
def load_cards():
    if os.path.exists(CARD_DB):
        try:
            with open(CARD_DB, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []  # Return empty if JSON is invalid
    else:
        # Create the file with an empty list if it doesn't exist
        with open(CARD_DB, 'w') as f:
            json.dump([], f)
        return []

# Save card metadata
def save_cards(cards):
    with open(CARD_DB, 'w') as f:
        json.dump(cards, f)

# Sample service dictionary
services = {
    "Design": ["Graphic Design", "UI/UX Design", "Custom Invitations"],
    "Development": ["Web Development", "App Development", "Custom CRM/ERM"],
    "Digital": ["E-commerce Setup", "Digital Marketing", "Domain & Hosting", "Support Packages"],
    "Content": ["Social Media Management", "Content Writing", "Video Editing"]
}

# Routes
@app.route('/admin', methods=['GET'])
def admin():
    if not session.get('admin'):  # Check if 'admin' is in the session
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))  # Redirect to home if not authenticated
    cards = load_cards()
    return render_template('admin.html', cards=cards)

@app.route('/', methods=['GET'])
def index():
    cards = load_cards()
    print(cards) # debugging check the console output for cards
    return render_template('index.html', services=services, cards=cards)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.form['qr_data']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}.png"
    path = os.path.join(app.config['QR_FOLDER'], filename)

    img = qrcode.make(data)
    img.save(path)
    qr_url = url_for('static', filename=f'qr/{filename}')
    
    cards = load_cards()
    flash("QR code generated successfully!", "success")
    return render_template('admin.html', cards=cards, qr_image_url=qr_url)
@app.route('/download_qr/<filename>')
def download_qr(filename):
    return send_from_directory(app.config['QR_FOLDER'], filename, as_attachment=True)

@app.route('/upload_card', methods=['POST'])
def upload_card():
    if not session.get('admin'):  # Admin-only access
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))
    
    title = request.form['title']
    file = request.files['card_image']
    filename = secure_filename(file.filename)
    
    # Validate file type
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm'}
    if '.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash("Invalid file type. Only images and videos are allowed. File format should ve jpg, .jpeg, .png, .gif, .mp4, .webm", "error")
        return redirect(url_for('admin'))

    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    cards = load_cards()

        # Get the highest existing ID and add 1
    new_id = max((card.get('id', 0) for card in cards), default=0) + 1

    cards.append({
        "id": new_id,
        "title": title,
        "image_url": url_for('static', filename=f'cards/{filename}')
    })

    save_cards(cards)
    flash("Card uploaded successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/card/<int:card_id>')
def card_detail(card_id):
    cards = load_cards()  # <-- Load from JSON
    card = next((c for c in cards if c.get('id') == card_id), None)
    if not card:
        return "Card not found", 404

    if card['image_url'].endswith(('.mp4', '.webm')):
        return f"""
            <h1>{card['title']}</h1>
            <video src='{card['image_url']}' controls style='max-width:600px;'></video>
        """
    else:
        return f"""
            <h1>{card['title']}</h1>
            <img src='{card['image_url']}' style='max-width:600px;'>
        """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Replace with your authentication logic
        if username == 'Himanshu998' and password == '12890#F':  # Example credentials
            session['admin'] = True  # Save admin status in the session
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        elif username == 'Ankit-2606' and password == '764985#F':  # Example credentials
            session['admin'] = True  # Save admin status in the session
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials.", "error")
    return render_template('login.html')  # Display the login form

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('admin', None)  # Remove admin from session
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    cards = load_cards()
    card = next((c for c in cards if c['id'] == card_id), None)
    if card:
        # 🧹 Step 1: Get the file path from the image_url
        try:
            # Replace URL path with local path
            image_path = card['image_url'].replace('/static/', 'static/')
            
            # 🧹 Step 2: Remove the file if it exists
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting file: {e}")  # Log error but continue

        # 🧹 Step 3: Remove the card entry from JSON
        cards = [c for c in cards if c['id'] != card_id]
        save_cards(cards)
        flash("Card deleted successfully!", "success")
    else:
        flash("Card not found.", "error")
    
    return redirect(url_for('admin'))
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    service = request.form.get('service')

    # Email to Admin
    subject = f"New Service Inquiry from {name}"
    body = f"""
    New inquiry received from the website:

    Name: {name}
    Email: {email}
    Phone: {phone}
    Service Requested: {service}
    """

    try:
        msg = Message(subject=subject, recipients=[os.getenv('MAIL_USERNAME')], body=body)
        mail.send(msg)

        # Auto-reply to user
        reply = Message(
            subject="Thank You for Contacting F-lance!",
            recipients=[email],
            body=f"""Hi {name},

Thank you for reaching out to F-lance! 🙏

We’ve received your request for: "{service}".
Our team will review it and get back to you shortly.

If it's urgent, feel free to WhatsApp us directly.

Best regards,  
Team F-lance  
https://instagram.com/f_lance2
"""
        )
        mail.send(reply)

        flash("Thank you! Your request was submitted successfully.", "success")
    except Exception as e:
        print(f"Email failed: {e}")
        flash("Oops! Something went wrong while sending your message.", "error")

    return redirect(url_for('index'))


# Run the app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

