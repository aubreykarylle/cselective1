from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_mysqldb import MySQL
from dicttoxml import dicttoxml
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import MySQLdb  # This is required for DictCursor

app = Flask(__name__)

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'studentsdb'

# JWT Configuration
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"  # Change this for production!
jwt = JWTManager(app)

# Initialize MySQL
mysql = MySQL(app)

# Home route to view all students
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    return render_template('index.html', students=students)

# Route to show the add student form
@app.route('/add_form')
def add_form():
    return render_template('add.html')

# Route to add a student to the database
@app.route('/add', methods=['POST'])
def add():
    first_name = request.form['first_name']
    middle_name = request.form['middle_name']
    last_name = request.form['last_name']
    gender = request.form['gender']
    email = request.form['email']
    phone_number = request.form['phone_number']
    town_city = request.form['town_city']
    country = request.form['country']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO students (first_name, middle_name, last_name, gender, email, phone_number, town_city, country) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                (first_name, middle_name, last_name, gender, email, phone_number, town_city, country))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('index'))

# Route to edit a student's information
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        email = request.form['email']
        phone_number = request.form['phone_number']
        town_city = request.form['town_city']
        country = request.form['country']
        cur.execute("UPDATE students SET first_name=%s, middle_name=%s, last_name=%s, gender=%s, email=%s, phone_number=%s, town_city=%s, country=%s WHERE id=%s", 
                    (first_name, middle_name, last_name, gender, email, phone_number, town_city, country, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    else:
        cur.execute("SELECT * FROM students WHERE id = %s", (id,))
        student = cur.fetchone()
        cur.close()
        return render_template('edit.html', students=student)

# Route to delete a student
@app.route('/delete/<int:id>')
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM students WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

# Route to create a student (API endpoint)
@app.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json()

    # Data validation before insertion
    if not data.get('first_name') or not data.get('last_name'):
        abort(400, description="First name and last name are required.")

    # Insert into the MySQL database
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO students (first_name, middle_name, last_name, gender, email, phone_number, town_city, country) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                (data['first_name'], data.get('middle_name'), data['last_name'], data.get('gender'), data.get('email'), data.get('phone_number'), data.get('town_city'), data.get('country')))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Student created successfully"}), 201

# Route to get all students (with support for JSON or XML response)
@app.route('/students', methods=['GET'])
def get_students():
    format = request.args.get('format', 'json')  # Default to JSON

    # Use DictCursor to get results as dictionaries
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Using DictCursor
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()

    if format == 'xml':
        return dicttoxml.dicttoxml(students, root=False), 200, {'Content-Type': 'application/xml'}
    return jsonify(students)

# Route to get a student by ID
@app.route('/students/<int:id>', methods=['GET'])
def get_student(id):
    format = request.args.get('format', 'json')  # Default to JSON

    # Use DictCursor to get results as dictionaries
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Using DictCursor
    cur.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cur.fetchone()
    cur.close()

    if student is None:
        abort(404, description="Student not found")

    if format == 'xml':
        return dicttoxml.dicttoxml([student], root=False), 200, {'Content-Type': 'application/xml'}
    return jsonify(student)

# Error handler for 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Error handler for 400 errors (bad requests)
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
