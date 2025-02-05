from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

EMPLOYEE_FILE = 'employees.xlsx'  # Path to the employee records Excel file

# Initialize the database
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        employee_name TEXT,
        date TEXT,
        time_in TEXT,
        time_out TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Home route to show dashboard
@app.route('/')
def index():
    # Load the employee records from the Excel file
    employee_df = pd.read_excel(EMPLOYEE_FILE)
    total_employees = len(employee_df)  # Total number of employees

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT * FROM attendance")
    records = c.fetchall()

    # Calculate the attendance percentage for each employee
    attendance_percentages = {}
    c.execute("SELECT DISTINCT employee_id FROM attendance")
    employees = c.fetchall()

    for employee in employees:
        employee_id = employee[0]
        c.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = ?", (employee_id,))
        total_days = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = ? AND time_out IS NOT NULL", (employee_id,))
        present_days = c.fetchone()[0]

        if total_days > 0:
            percentage = (present_days / total_days) * 100
        else:
            percentage = 0

        # Store the attendance percentage
        attendance_percentages[employee_id] = percentage

    # Calculate total attendance percentage for today
    today = datetime.today().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(DISTINCT employee_id) FROM attendance WHERE date = ? AND time_out IS NOT NULL", (today,))
    present_employees = c.fetchone()[0]

    if total_employees > 0:
        total_percentage = (present_employees / total_employees) * 100
    else:
        total_percentage = 0

    conn.close()
    return render_template('index.html', records=records, attendance_percentages=attendance_percentages, total_percentage=total_percentage)

# Route to mark attendance (Time In)
@app.route('/mark_in', methods=['POST'])
def mark_in():
    employee_id = request.form['employee_id']
    employee_name = request.form['employee_name']
    date_today = datetime.today().strftime('%Y-%m-%d')
    time_in = datetime.now().strftime('%H:%M:%S')

    # Load the employee records from the Excel file
    employee_df = pd.read_excel(EMPLOYEE_FILE)

    # Check if the employee ID exists
    if employee_id not in employee_df['Employee ID'].values:
        flash('Error: Employee ID does not exist.')
        return redirect(url_for('index'))

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("INSERT INTO attendance (employee_id, employee_name, date, time_in, time_out) VALUES (?, ?, ?, ?, ?)", 
              (employee_id, employee_name, date_today, time_in, None))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# Route to mark time-out
@app.route('/mark_out/<int:record_id>')
def mark_out(record_id):
    time_out = datetime.now().strftime('%H:%M:%S')

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("UPDATE attendance SET time_out = ? WHERE id = ?", (time_out, record_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# Logout route to mark logout
@app.route('/logout/<int:record_id>')
def logout(record_id):
    # Mark the record as logged out by updating 'time_out'
    time_out = datetime.now().strftime('%H:%M:%S')

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("UPDATE attendance SET time_out = ? WHERE id = ?", (time_out, record_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 3000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)