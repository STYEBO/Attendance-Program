import sqlite3
from datetime import datetime
import hashlib
import getpass

class AttendanceDB:
    def __init__(self, db_name='attendance_system.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        # Employees table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode_id TEXT UNIQUE NOT NULL,
                department TEXT,
                position TEXT,
                hire_date TEXT,
                status TEXT DEFAULT 'Active'
            )
        ''')
        
        # Shifts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Employee shifts assignment
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_shifts (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                shift_id INTEGER NOT NULL,
                effective_date TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
                FOREIGN KEY (shift_id) REFERENCES shifts (shift_id)
            )
        ''')
        
        # Attendance records
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT,
                time_out TEXT,
                status TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        # Admin users
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TEXT
            )
        ''')
        
        self.conn.commit()
        
    # Employee operations
    def add_employee(self, name, barcode_id, department, position, hire_date):
        try:
            self.cursor.execute('''
                INSERT INTO employees (name, barcode_id, department, position, hire_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, barcode_id, department, position, hire_date))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def get_employee_by_barcode(self, barcode_id):
        self.cursor.execute('SELECT * FROM employees WHERE barcode_id = ?', (barcode_id,))
        return self.cursor.fetchone()
        
    def get_all_employees(self):
        self.cursor.execute('SELECT * FROM employees ORDER BY name')
        return self.cursor.fetchall()
        
    def update_employee(self, employee_id, name, department, position, status):
        self.cursor.execute('''
            UPDATE employees 
            SET name = ?, department = ?, position = ?, status = ?
            WHERE employee_id = ?
        ''', (name, department, position, status, employee_id))
        self.conn.commit()
        
    def delete_employee(self, employee_id):
        self.cursor.execute('DELETE FROM employees WHERE employee_id = ?', (employee_id,))
        self.conn.commit()
        
    # Shift operations
    def add_shift(self, name, start_time, end_time, description=None):
        self.cursor.execute('''
            INSERT INTO shifts (name, start_time, end_time, description)
            VALUES (?, ?, ?, ?)
        ''', (name, start_time, end_time, description))
        self.conn.commit()
        return self.cursor.lastrowid
        
    def get_all_shifts(self):
        self.cursor.execute('SELECT * FROM shifts ORDER BY start_time')
        return self.cursor.fetchall()
        
    def assign_shift_to_employee(self, employee_id, shift_id, effective_date):
        self.cursor.execute('''
            INSERT INTO employee_shifts (employee_id, shift_id, effective_date)
            VALUES (?, ?, ?)
        ''', (employee_id, shift_id, effective_date))
        self.conn.commit()
        
    def get_employee_shift(self, employee_id, date):
        self.cursor.execute('''
            SELECT s.* FROM shifts s
            JOIN employee_shifts es ON s.shift_id = es.shift_id
            WHERE es.employee_id = ? AND es.effective_date <= ?
            ORDER BY es.effective_date DESC
            LIMIT 1
        ''', (employee_id, date))
        return self.cursor.fetchone()
        
    # Attendance operations
    def record_attendance(self, employee_id, date, time_in=None, time_out=None, status=None):
        # Check if record exists for this employee and date
        self.cursor.execute('''
            SELECT * FROM attendance 
            WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        existing = self.cursor.fetchone()
        
        if existing:
            # Update existing record
            if time_out:
                self.cursor.execute('''
                    UPDATE attendance 
                    SET time_out = ?, status = ?
                    WHERE record_id = ?
                ''', (time_out, status, existing[0]))
            elif time_in:
                self.cursor.execute('''
                    UPDATE attendance 
                    SET time_in = ?, status = ?
                    WHERE record_id = ?
                ''', (time_in, status, existing[0]))
            self.conn.commit()
            return False  # Record updated
        else:
            # Create new record
            self.cursor.execute('''
                INSERT INTO attendance (employee_id, date, time_in, time_out, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, date, time_in, time_out, status))
            self.conn.commit()
            return True  # New record created
            
    def get_attendance_records(self, start_date, end_date, employee_id=None):
        query = '''
            SELECT a.*, e.name 
            FROM attendance a
            JOIN employees e ON a.employee_id = e.employee_id
            WHERE a.date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        
        if employee_id:
            query += ' AND a.employee_id = ?'
            params.append(employee_id)
            
        query += ' ORDER BY a.date, e.name'
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
        
    # Admin operations
    def add_admin_user(self, username, password, full_name, role):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute('''
                INSERT INTO admin_users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, full_name, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def verify_admin(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('''
            SELECT * FROM admin_users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        return self.cursor.fetchone()
        
    def update_admin_last_login(self, username):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            UPDATE admin_users 
            SET last_login = ?
            WHERE username = ?
        ''', (now, username))
        self.conn.commit()
        
    def get_all_admins(self):
        self.cursor.execute('SELECT user_id, username, full_name, role FROM admin_users')
        return self.cursor.fetchall()
        
    def change_admin_password(self, username, new_password):
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.cursor.execute('''
            UPDATE admin_users 
            SET password_hash = ?
            WHERE username = ?
        ''', (password_hash, username))
        self.conn.commit()
        return self.cursor.rowcount > 0
        
    def delete_admin(self, user_id):
        self.cursor.execute('DELETE FROM admin_users WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
        
    def close(self):
        self.conn.close()
        
    def __del__(self):
        self.close()

def initialize_database():
    db = AttendanceDB()
    
    # Check if any admin exists, if not create a default one
    db.cursor.execute('SELECT COUNT(*) FROM admin_users')
    if db.cursor.fetchone()[0] == 0:
        print("No admin users found. Creating default admin account (username: admin, password: admin)")
        db.add_admin_user('admin', 'admin', 'System Administrator', 'Super Admin')
    
    db.close()

if __name__ == '__main__':
    initialize_database()
