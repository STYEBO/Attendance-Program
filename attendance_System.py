import sqlite3
from datetime import datetime, timedelta
import sys
import os
from attendance import AttendanceDB, initialize_database
import getpass
import time

class AttendanceSystem:
    def __init__(self):
        self.db = AttendanceDB()
        self.current_user = None
        self.login_attempts = 0
        self.max_attempts = 3

    def clear_screen(self):
        # Clear screen command based on OS
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_header(self, title):
        self.clear_screen()
        print("=" * 50)
        print(f"=== {title.center(44)} ===")
        print("=" * 50)
        if self.current_user:
            print(f"Logged in as: {self.current_user[3]} ({self.current_user[4]})")
        print()
        
    def display_menu(self):
        while True:
            self.display_header("Attendance Management System")
            print("1. Attendance Operations (with barcode scanner)")
            print("2. Employee Management")
            print("3. Shift Management")
            print("4. Admin Security")
            print("5. Reports")
            print("6. Exit\n")
            
            choice = input("Enter your choice (1-6): ")
            
            if choice == '1':
                self.attendance_operations()
            elif choice == '2':
                self.employee_management()
            elif choice == '3':
                self.shift_management()
            elif choice == '4':
                self.admin_security()
            elif choice == '5':
                self.reports()
            elif choice == '6':
                print("Exiting system...")
                self.db.close()
                sys.exit()
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def login(self):
        while self.login_attempts < self.max_attempts:
            self.display_header("Admin Login")
            
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            
            admin = self.db.verify_admin(username, password)
            if admin:
                self.current_user = admin
                self.db.update_admin_last_login(username)
                self.login_attempts = 0
                print(f"\nWelcome, {admin[3]} ({admin[4]})!")
                time.sleep(1)
                return True
            else:
                self.login_attempts += 1
                remaining_attempts = self.max_attempts - self.login_attempts
                if remaining_attempts > 0:
                    print(f"\nInvalid username or password. {remaining_attempts} attempts remaining.")
                    time.sleep(1.5)
                else:
                    print("\nMaximum login attempts reached. System will exit.")
                    time.sleep(2)
                    sys.exit()
        
        return False
            
    def attendance_operations(self):
        while True:
            self.display_header("Attendance Operations")
            print("1. Record Time In/Out (Barcode Scanner)")
            print("2. Manual Attendance Entry")
            print("3. View Today's Attendance")
            print("4. Back to Main Menu\n")
            
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                self.barcode_attendance()
            elif choice == '2':
                self.manual_attendance()
            elif choice == '3':
                self.view_todays_attendance()
            elif choice == '4':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def barcode_attendance(self):
        while True:
            self.display_header("Barcode Attendance Scanner")
            print("Scan employee barcode or enter '0' to cancel")
            
            barcode = input("\nScan barcode: ").strip()
            if barcode == '0':
                return
                
            employee = self.db.get_employee_by_barcode(barcode)
            if not employee:
                print("Employee not found. Please try again.")
                time.sleep(1.5)
                continue
                
            now = datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M:%S')
            
            # Check if employee has already checked in today
            self.db.cursor.execute('''
                SELECT * FROM attendance 
                WHERE employee_id = ? AND date = ?
            ''', (employee[0], current_date))
            record = self.db.cursor.fetchone()
            
            if record and record[3] and record[4]:  # Already has time_in and time_out
                print(f"\n{employee[1]} has already completed attendance for today.")
            elif record and record[3]:  # Has time_in but no time_out
                self.db.record_attendance(employee[0], current_date, time_out=current_time, status="Present")
                print(f"\nTime Out recorded for {employee[1]} at {current_time}")
            else:  # No record yet
                self.db.record_attendance(employee[0], current_date, time_in=current_time, status="Present")
                print(f"\nTime In recorded for {employee[1]} at {current_time}")
            
            time.sleep(2)
                
    def manual_attendance(self):
        self.display_header("Manual Attendance Entry")
        
        # List employees
        employees = self.db.get_all_employees()
        if not employees:
            print("No employees found.")
            time.sleep(1.5)
            return
            
        print("\nEmployee List:")
        for idx, emp in enumerate(employees, 1):
            print(f"{idx}. {emp[1]} (ID: {emp[0]}, Barcode: {emp[2]})")
            
        try:
            emp_choice = int(input("\nSelect employee (number) or 0 to cancel: "))
            if emp_choice == 0:
                return
            employee = employees[emp_choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        date = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip()
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        print("\n1. Record Time In")
        print("2. Record Time Out")
        print("3. Record Both")
        print("4. Cancel")
        
        try:
            choice = int(input("\nSelect operation: "))
            if choice == 4:
                return
                
            time_in = None
            time_out = None
            status = "Present"
            
            if choice in [1, 3]:
                time_in = input("Enter Time In (HH:MM:SS or leave blank for now): ").strip()
                if not time_in:
                    time_in = datetime.now().strftime('%H:%M:%S')
                    
            if choice in [2, 3]:
                time_out = input("Enter Time Out (HH:MM:SS or leave blank for now): ").strip()
                if not time_out:
                    time_out = datetime.now().strftime('%H:%M:%S')
                    
            if choice == 1:
                self.db.record_attendance(employee[0], date, time_in=time_in, status=status)
                print(f"\nRecorded Time In for {employee[1]} on {date} at {time_in}")
            elif choice == 2:
                self.db.record_attendance(employee[0], date, time_out=time_out, status=status)
                print(f"\nRecorded Time Out for {employee[1]} on {date} at {time_out}")
            elif choice == 3:
                self.db.record_attendance(employee[0], date, time_in=time_in, time_out=time_out, status=status)
                print(f"\nRecorded attendance for {employee[1]} on {date}: In {time_in}, Out {time_out}")
                
        except ValueError:
            print("\nInvalid input.")
        
        time.sleep(2)
            
    def view_todays_attendance(self):
        today = datetime.now().strftime('%Y-%m-%d')
        records = self.db.get_attendance_records(today, today)
        
        self.display_header(f"Today's Attendance ({today})")
        
        if not records:
            print("\nNo attendance records for today.")
            time.sleep(1.5)
            return
            
        print("\n{:<5} {:<20} {:<10} {:<10} {:<10}".format(
            "ID", "Name", "Time In", "Time Out", "Status"))
        print("-" * 60)
        
        for record in records:
            print("{:<5} {:<20} {:<10} {:<10} {:<10}".format(
                record[1], record[6], 
                record[3] if record[3] else "-", 
                record[4] if record[4] else "-", 
                record[5] if record[5] else "-"))
        
        input("\nPress Enter to continue...")
                
    def employee_management(self):
        while True:
            self.display_header("Employee Management")
            print("1. Add New Employee")
            print("2. View All Employees")
            print("3. Update Employee")
            print("4. Delete Employee")
            print("5. Back to Main Menu\n")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == '1':
                self.add_employee()
            elif choice == '2':
                self.view_employees()
            elif choice == '3':
                self.update_employee()
            elif choice == '4':
                self.delete_employee()
            elif choice == '5':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def add_employee(self):
        self.display_header("Add New Employee")
        
        name = input("\nEmployee Name: ").strip()
        barcode_id = input("Barcode ID: ").strip()
        department = input("Department: ").strip()
        position = input("Position: ").strip()
        hire_date = input("Hire Date (YYYY-MM-DD): ").strip()
        
        if not all([name, barcode_id, department, position, hire_date]):
            print("\nAll fields are required.")
            time.sleep(1.5)
            return
            
        if self.db.add_employee(name, barcode_id, department, position, hire_date):
            print(f"\nEmployee {name} added successfully.")
        else:
            print("\nError adding employee. Barcode ID may already exist.")
        
        time.sleep(1.5)
            
    def view_employees(self):
        employees = self.db.get_all_employees()
        
        self.display_header("Employee List")
        
        if not employees:
            print("\nNo employees found.")
            time.sleep(1.5)
            return
            
        print("\n{:<5} {:<20} {:<15} {:<15} {:<10} {:<10}".format(
            "ID", "Name", "Department", "Position", "Barcode", "Status"))
        print("-" * 80)
        
        for emp in employees:
            print("{:<5} {:<20} {:<15} {:<15} {:<10} {:<10}".format(
                emp[0], emp[1], emp[3], emp[4], emp[2], emp[6]))
        
        input("\nPress Enter to continue...")
                
    def update_employee(self):
        employees = self.db.get_all_employees()
        if not employees:
            print("No employees found.")
            time.sleep(1.5)
            return
            
        self.display_header("Update Employee")
        print("\nSelect employee to update:")
        for idx, emp in enumerate(employees, 1):
            print(f"{idx}. {emp[1]} (ID: {emp[0]})")
            
        try:
            choice = int(input("\nSelect employee (number) or 0 to cancel: "))
            if choice == 0:
                return
            employee = employees[choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        print(f"\nUpdating {employee[1]}:")
        name = input(f"Name ({employee[1]}): ").strip() or employee[1]
        department = input(f"Department ({employee[3]}): ").strip() or employee[3]
        position = input(f"Position ({employee[4]}): ").strip() or employee[4]
        status = input(f"Status (Active/Inactive) ({employee[6]}): ").strip() or employee[6]
        
        self.db.update_employee(employee[0], name, department, position, status)
        print("\nEmployee updated successfully.")
        time.sleep(1.5)
        
    def delete_employee(self):
        employees = self.db.get_all_employees()
        if not employees:
            print("No employees found.")
            time.sleep(1.5)
            return
            
        self.display_header("Delete Employee")
        print("\nSelect employee to delete:")
        for idx, emp in enumerate(employees, 1):
            print(f"{idx}. {emp[1]} (ID: {emp[0]})")
            
        try:
            choice = int(input("\nSelect employee (number) or 0 to cancel: "))
            if choice == 0:
                return
            employee = employees[choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        confirm = input(f"\nAre you sure you want to delete {employee[1]}? (y/n): ").lower()
        if confirm == 'y':
            self.db.delete_employee(employee[0])
            print("\nEmployee deleted successfully.")
        
        time.sleep(1.5)
            
    def shift_management(self):
        while True:
            self.display_header("Shift Management")
            print("1. Add New Shift")
            print("2. View All Shifts")
            print("3. Assign Shift to Employee")
            print("4. Back to Main Menu\n")
            
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                self.add_shift()
            elif choice == '2':
                self.view_shifts()
            elif choice == '3':
                self.assign_shift()
            elif choice == '4':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def add_shift(self):
        self.display_header("Add New Shift")
        
        name = input("\nShift Name: ").strip()
        start_time = input("Start Time (HH:MM:SS): ").strip()
        end_time = input("End Time (HH:MM:SS): ").strip()
        description = input("Description (optional): ").strip()
        
        if not all([name, start_time, end_time]):
            print("\nName, start time and end time are required.")
            time.sleep(1.5)
            return
            
        shift_id = self.db.add_shift(name, start_time, end_time, description)
        print(f"\nShift '{name}' added successfully with ID {shift_id}.")
        time.sleep(1.5)
        
    def view_shifts(self):
        shifts = self.db.get_all_shifts()
        
        self.display_header("Shift List")
        
        if not shifts:
            print("\nNo shifts found.")
            time.sleep(1.5)
            return
            
        print("\n{:<5} {:<15} {:<10} {:<10} {:<20}".format(
            "ID", "Name", "Start", "End", "Description"))
        print("-" * 70)
        
        for shift in shifts:
            print("{:<5} {:<15} {:<10} {:<10} {:<20}".format(
                shift[0], shift[1], shift[2], shift[3], 
                shift[4] if shift[4] else "-"))
        
        input("\nPress Enter to continue...")
                
    def assign_shift(self):
        self.display_header("Assign Shift to Employee")
        
        # Get all employees
        employees = self.db.get_all_employees()
        if not employees:
            print("No employees found.")
            time.sleep(1.5)
            return
            
        # Get all shifts
        shifts = self.db.get_all_shifts()
        if not shifts:
            print("No shifts found. Please create shifts first.")
            time.sleep(1.5)
            return
            
        # Display employees
        print("\nSelect employee:")
        for idx, emp in enumerate(employees, 1):
            print(f"{idx}. {emp[1]} (ID: {emp[0]})")
            
        try:
            emp_choice = int(input("\nSelect employee (number) or 0 to cancel: "))
            if emp_choice == 0:
                return
            employee = employees[emp_choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        # Display shifts
        print("\nSelect shift:")
        for idx, shift in enumerate(shifts, 1):
            print(f"{idx}. {shift[1]} ({shift[2]} - {shift[3]})")
            
        try:
            shift_choice = int(input("\nSelect shift (number): "))
            shift = shifts[shift_choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        effective_date = input("\nEffective Date (YYYY-MM-DD) or leave blank for today: ").strip()
        if not effective_date:
            effective_date = datetime.now().strftime('%Y-%m-%d')
            
        self.db.assign_shift_to_employee(employee[0], shift[0], effective_date)
        print(f"\nShift '{shift[1]}' assigned to {employee[1]} effective {effective_date}.")
        time.sleep(1.5)
        
    def admin_security(self):
        while True:
            self.display_header("Admin Security")
            print("1. Add New Admin")
            print("2. View All Admins")
            print("3. Change Password")
            print("4. Delete Admin")
            print("5. Back to Main Menu\n")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == '1':
                self.add_admin()
            elif choice == '2':
                self.view_admins()
            elif choice == '3':
                self.change_password()
            elif choice == '4':
                self.delete_admin()
            elif choice == '5':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def add_admin(self):
        if self.current_user[4] != "Super Admin":
            print("\nOnly Super Admins can add new admin users.")
            time.sleep(1.5)
            return
            
        self.display_header("Add New Admin")
        
        username = input("\nUsername: ").strip()
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")
        full_name = input("Full Name: ").strip()
        role = input("Role (Admin/Super Admin): ").strip().capitalize()
        
        if not all([username, password, full_name, role]):
            print("\nAll fields are required.")
            time.sleep(1.5)
            return
            
        if password != confirm_password:
            print("\nPasswords do not match.")
            time.sleep(1.5)
            return
            
        if role not in ["Admin", "Super Admin"]:
            print("\nRole must be either 'Admin' or 'Super Admin'.")
            time.sleep(1.5)
            return
            
        if self.db.add_admin_user(username, password, full_name, role):
            print(f"\nAdmin user '{username}' added successfully.")
        else:
            print("\nError adding admin. Username may already exist.")
        
        time.sleep(1.5)
            
    def view_admins(self):
        admins = self.db.get_all_admins()
        
        self.display_header("Admin Users")
        
        if not admins:
            print("\nNo admin users found.")
            time.sleep(1.5)
            return
            
        print("\n{:<5} {:<15} {:<20} {:<15}".format(
            "ID", "Username", "Full Name", "Role"))
        print("-" * 60)
        
        for admin in admins:
            print("{:<5} {:<15} {:<20} {:<15}".format(
                admin[0], admin[1], admin[2], admin[3]))
        
        input("\nPress Enter to continue...")
                
    def change_password(self):
        self.display_header("Change Password")
        
        current_password = getpass.getpass("\nCurrent Password: ")
        if not self.db.verify_admin(self.current_user[1], current_password):
            print("\nIncorrect current password.")
            time.sleep(1.5)
            return
            
        new_password = getpass.getpass("New Password: ")
        confirm_password = getpass.getpass("Confirm New Password: ")
        
        if new_password != confirm_password:
            print("\nPasswords do not match.")
            time.sleep(1.5)
            return
            
        if self.db.change_admin_password(self.current_user[1], new_password):
            print("\nPassword changed successfully.")
        else:
            print("\nError changing password.")
        
        time.sleep(1.5)
            
    def delete_admin(self):
        if self.current_user[4] != "Super Admin":
            print("\nOnly Super Admins can delete admin users.")
            time.sleep(1.5)
            return
            
        admins = self.db.get_all_admins()
        if len(admins) <= 1:
            print("\nCannot delete the only admin user.")
            time.sleep(1.5)
            return
            
        self.display_header("Delete Admin")
        print("\nSelect admin to delete (you cannot delete yourself):")
        for admin in admins:
            if admin[0] != self.current_user[0]:  # Can't delete yourself
                print(f"{admin[0]}. {admin[1]} ({admin[3]})")
                
        try:
            admin_id = int(input("\nEnter admin ID to delete or 0 to cancel: "))
            if admin_id == 0:
                return
                
            if admin_id == self.current_user[0]:
                print("\nYou cannot delete yourself.")
                time.sleep(1.5)
                return
                
            confirm = input("\nAre you sure you want to delete this admin? (y/n): ").lower()
            if confirm == 'y':
                if self.db.delete_admin(admin_id):
                    print("\nAdmin deleted successfully.")
                else:
                    print("\nError deleting admin.")
        except ValueError:
            print("\nInvalid input.")
        
        time.sleep(1.5)
            
    def reports(self):
        while True:
            self.display_header("Reports")
            print("1. Daily Attendance Report")
            print("2. Date Range Attendance Report")
            print("3. Employee Attendance Summary")
            print("4. Back to Main Menu\n")
            
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                self.daily_report()
            elif choice == '2':
                self.date_range_report()
            elif choice == '3':
                self.employee_summary()
            elif choice == '4':
                return
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)
                
    def daily_report(self):
        date = input("\nEnter date (YYYY-MM-DD) or leave blank for today: ").strip()
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        records = self.db.get_attendance_records(date, date)
        
        self.display_header(f"Attendance Report for {date}")
        
        if not records:
            print("\nNo attendance records for this date.")
            time.sleep(1.5)
            return
            
        present = 0
        absent = 0
        late = 0
        
        print("\n{:<5} {:<20} {:<10} {:<10} {:<10}".format(
            "ID", "Name", "Time In", "Time Out", "Status"))
        print("-" * 60)
        
        for record in records:
            print("{:<5} {:<20} {:<10} {:<10} {:<10}".format(
                record[1], record[6], 
                record[3] if record[3] else "-", 
                record[4] if record[4] else "-", 
                record[5] if record[5] else "-"))
                
            if record[5] == "Present":
                present += 1
            elif record[5] == "Absent":
                absent += 1
            elif record[5] == "Late":
                late += 1
                
        total_employees = len(self.db.get_all_employees())
        print("\nSummary:")
        print(f"Present: {present}")
        print(f"Absent: {absent}")
        print(f"Late: {late}")
        print(f"Not Recorded: {total_employees - (present + absent + late)}")
        
        input("\nPress Enter to continue...")
        
    def date_range_report(self):
        start_date = input("\nEnter start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
        
        records = self.db.get_attendance_records(start_date, end_date)
        
        self.display_header(f"Attendance Report from {start_date} to {end_date}")
        
        if not records:
            print("\nNo attendance records for this date range.")
            time.sleep(1.5)
            return
            
        # Group by employee
        employee_data = {}
        for record in records:
            if record[1] not in employee_data:
                employee_data[record[1]] = {
                    'name': record[6],
                    'records': []
                }
            employee_data[record[1]]['records'].append(record)
            
        # Display summary for each employee
        print("\n{:<5} {:<20} {:<10} {:<10} {:<10}".format(
            "ID", "Name", "Present", "Absent", "Late"))
        print("-" * 60)
        
        for emp_id, data in employee_data.items():
            present = sum(1 for r in data['records'] if r[5] == "Present")
            absent = sum(1 for r in data['records'] if r[5] == "Absent")
            late = sum(1 for r in data['records'] if r[5] == "Late")
            
            print("{:<5} {:<20} {:<10} {:<10} {:<10}".format(
                emp_id, data['name'], present, absent, late))
        
        input("\nPress Enter to continue...")
                
    def employee_summary(self):
        employees = self.db.get_all_employees()
        if not employees:
            print("No employees found.")
            time.sleep(1.5)
            return
            
        self.display_header("Employee Attendance Summary")
        print("\nSelect employee:")
        for idx, emp in enumerate(employees, 1):
            print(f"{idx}. {emp[1]} (ID: {emp[0]})")
            
        try:
            emp_choice = int(input("\nSelect employee (number) or 0 to cancel: "))
            if emp_choice == 0:
                return
            employee = employees[emp_choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            time.sleep(1.5)
            return
            
        start_date = input("\nEnter start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
        
        records = self.db.get_attendance_records(start_date, end_date, employee[0])
        
        self.display_header(f"Attendance Summary for {employee[1]}\nFrom {start_date} to {end_date}")
        
        if not records:
            print("\nNo attendance records for this employee in the selected date range.")
            time.sleep(1.5)
            return
            
        present = 0
        absent = 0
        late = 0
        
        print("\n{:<12} {:<10} {:<10} {:<10}".format(
            "Date", "Time In", "Time Out", "Status"))
        print("-" * 50)
        
        for record in records:
            print("{:<12} {:<10} {:<10} {:<10}".format(
                record[2], 
                record[3] if record[3] else "-", 
                record[4] if record[4] else "-", 
                record[5] if record[5] else "-"))
                
            if record[5] == "Present":
                present += 1
            elif record[5] == "Absent":
                absent += 1
            elif record[5] == "Late":
                late += 1
                
        total_days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                     datetime.strptime(start_date, '%Y-%m-%d')).days + 1
                     
        print("\nSummary:")
        print(f"Total Days: {total_days}")
        print(f"Present: {present} ({present/total_days*100:.1f}%)")
        print(f"Absent: {absent} ({absent/total_days*100:.1f}%)")
        print(f"Late: {late} ({late/total_days*100:.1f}%)")
        print(f"Not Recorded: {total_days - (present + absent + late)}")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    system = AttendanceSystem()
    
    # First initialize the database to ensure admin account exists
    initialize_database()
    
    # Login loop
    while True:
        if system.login():
            system.display_menu()
        else:
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                print("Goodbye!")
                break
