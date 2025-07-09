import os
import json
from flask import Flask, session, flash, render_template, request, redirect, url_for, send_from_directory, send_file, abort
import qrcode
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'defaultfallbackkey')

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

# Directories
UPLOAD_FOLDER = 'static/cards'
QR_FOLDER = 'static/qr'
CARD_DB = 'card_data.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_FOLDER'] = QR_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Serve static files
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

@app.route('/favicon.ico')
def favicon():
    icon_path = 'static/favicon.ico'
    if os.path.exists(icon_path):
        return send_file(icon_path)
    return send_file('static/images/default-icon.ico')

# Load and save card data
def load_cards():
    if os.path.exists(CARD_DB):
        try:
            with open(CARD_DB, 'r') as f:
                cards = json.load(f)
                return [c for c in cards if c.get('title') and c.get('image_url')]
        except json.JSONDecodeError:
            return []
    else:
        with open(CARD_DB, 'w') as f:
            json.dump([], f)
        return []

def save_cards(cards):
    with open(CARD_DB, 'w') as f:
        json.dump(cards, f, indent=2)

# Sample services
services = {
    "Design": ["Graphic Design", "UI/UX Design", "Custom Invitations"],
    "Development": ["Web Development", "App Development", "Custom CRM/ERM"],
    "Digital": ["E-commerce Setup", "Digital Marketing", "Domain & Hosting", "Support Packages"],
    "Content": ["Social Media Management", "Content Writing", "Video Editing"]
}

# Routes
@app.route('/')
def index():
    cards = load_cards()
    return render_template('index.html', services=services, cards=cards)

@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))
    cards = load_cards()
    return render_template('admin.html', cards=cards)

@app.route('/upload_card', methods=['POST'])
def upload_card():
    if not session.get('admin'):
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))

    title = request.form['title']
    category = request.form.get('category', 'General')
    file = request.files['card_image']

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{secure_filename(file.filename)}"

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm'}
    if '.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash("Invalid file type.", "error")
        return redirect(url_for('admin'))

    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    cards = load_cards()
    new_id = max((card.get('id', 0) for card in cards), default=0) + 1
    cards.append({
        "id": new_id,
        "title": title,
        "category": category,
        "image_url": url_for('static', filename=f'cards/{filename}')
    })
    save_cards(cards)
    flash("Card uploaded successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    cards = load_cards()
    card = next((c for c in cards if c['id'] == card_id), None)
    if card:
        try:
            image_path = card['image_url'].replace('/static/', 'static/')
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        cards = [c for c in cards if c['id'] != card_id]
        save_cards(cards)
        flash("Card deleted successfully!", "success")
    else:
        flash("Card not found.", "error")
    return redirect(url_for('admin'))

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

@app.route('/clear_qr')
def clear_qr_folder():
    if not session.get('admin'):
        return "Unauthorized", 403
    for file in os.listdir(QR_FOLDER):
        file_path = os.path.join(QR_FOLDER, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    flash("QR folder cleaned up.", "success")
    return redirect(url_for('admin'))

@app.route('/card/<int:card_id>')
def card_detail(card_id):
    cards = load_cards()
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
        if username == 'Himanshu998' and password == '12890#F':
            session['admin'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        elif username == 'Ankit-2606' and password == '764985#F':
            session['admin'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    service = request.form.get('service')

    subject = f"New Service Inquiry from {name}"
    body = f"""
    Name: {name}
    Email: {email}
    Phone: {phone}
    Service Requested: {service}
    """

    try:
        msg = Message(subject=subject, recipients=[os.getenv('MAIL_USERNAME')], body=body)
        mail.send(msg)

        reply = Message(
            subject="Thank You for Contacting F-lance!",
            recipients=[email],
            body=f"""Hi {name},

Thank you for reaching out to F-lance! 🙏

We’ve received your request for: \"{service}\".
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

