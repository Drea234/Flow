import json
import random
import datetime
import os
import pandas as pd
import hashlib

# Configuration
NUM_EMPLOYEES = 15
OUTPUT_FILE_JSON = "data/employee_database.json"
OUTPUT_FILE_CSV = "data/employee_database.csv"
CREDENTIALS_FILE = "data/login_credentials.json"

# Required employees
required_employees = [
    "Jonathan Le",
    "Vincent Shih",
    "Sergio Guido",
    "Que Anh Tran",
    "Ngoc Tien Cao"
]

# Additional sample names
additional_names = [
    "Mary Johnson", "John Williams", "Patricia Jones", "Robert Brown", 
    "Jennifer Davis", "Michael Miller", "Linda Wilson", "David Moore", 
    "Barbara Taylor"
]

# Valley Water specific departments and positions
departments = [
    "Engineering", "Water Supply", "Communications", "Human Resources", 
    "Information Technology", "Legal", "Finance", "Environmental Services",
    "Watershed Operations", "Dam Safety", "Community Projects", "Administration"
]

positions = {
    "Engineering": ["Water Resources Engineer", "Civil Engineer", "Senior Engineer", "Engineering Manager", "Engineering Technician", "Project Manager"],
    "Water Supply": ["Water Supply Specialist", "Operations Manager", "System Operator", "Field Technician", "Water Quality Specialist"],
    "Communications": ["Communications Specialist", "Outreach Coordinator", "Media Relations Manager", "Public Affairs Representative"],
    "Human Resources": ["HR Specialist", "HR Manager", "Benefits Coordinator", "Talent Acquisition Specialist", "Employee Relations Manager"],
    "Information Technology": ["IT Specialist", "System Administrator", "Network Engineer", "IT Manager", "Database Administrator", "Security Specialist"],
    "Legal": ["Legal Counsel", "Paralegal", "Compliance Officer", "Contract Specialist", "Legal Assistant"],
    "Finance": ["Financial Analyst", "Accountant", "Budget Manager", "Payroll Specialist", "Procurement Officer"],
    "Environmental Services": ["Environmental Scientist", "Conservation Specialist", "Biologist", "Resource Planner"],
    "Watershed Operations": ["Watershed Manager", "Field Supervisor", "Maintenance Worker", "Flood Control Specialist"],
    "Dam Safety": ["Dam Safety Engineer", "Safety Inspector", "Risk Assessment Specialist", "Structural Engineer"],
    "Community Projects": ["Project Coordinator", "Community Liaison", "Grant Manager", "Planning Specialist"],
    "Administration": ["Administrative Assistant", "Office Manager", "Executive Assistant", "Records Specialist", "Board Liaison"]
}

managers = {dept: [] for dept in departments}  # Will be populated with employees who can be managers

# Valley Water specific benefits
health_plans = ["Blue Shield PPO", "Blue Shield HMO", "Kaiser HMO"]
dental_plans = ["Delta Dental"]
vision_plans = ["VSP"]  # Only for Blue Shield members
retirement_contribution_rates = [3, 4, 5, 6, 7, 8, 9, 10]

def generate_employee_id():
    """Generate a unique employee ID in the format EMP12345"""
    return f"EMP{random.randint(10000, 99999)}"

def generate_hire_date():
    """Generate a random hire date within the last 15 years"""
    days_ago = random.randint(0, 365 * 15)  # Up to 15 years ago
    hire_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    return hire_date.strftime("%Y-%m-%d")

def generate_next_review_date(hire_date):
    """Generate next review date in 2026"""
    hire_date_obj = datetime.datetime.strptime(hire_date, "%Y-%m-%d")
    # Reviews happen on the anniversary of hire date, set for 2026
    next_review_date = datetime.datetime(2026, hire_date_obj.month, hire_date_obj.day)
    return next_review_date.strftime("%Y-%m-%d")

def generate_pto_balance():
    """Generate a random PTO balance between 0 and 25 days"""
    return round(random.uniform(0, 25), 1)

def generate_benefits():
    """Generate a list of enrolled benefits with Valley Water specific plans"""
    benefits = []
    
    # Health plan - everyone has one
    health_plan = random.choice(health_plans)
    benefits.append(health_plan)
    
    # Dental plan - everyone gets Delta Dental
    benefits.append("Delta Dental")
    
    # Vision plan - only for Blue Shield members
    if "Blue Shield" in health_plan:
        benefits.append("VSP")
    # Kaiser includes vision in their plan
    
    # 401(k) - 90% chance
    if random.random() < 0.9:
        contribution_rate = random.choice(retirement_contribution_rates)
        benefits.append(f"401(k) - {contribution_rate}%")
    
    return benefits

def generate_employees():
    """Generate a list of synthetic employees"""
    employees = {}
    employee_ids = set()
    
    # First, add the required employees
    for i, name in enumerate(required_employees):
        employee_id = generate_employee_id()
        employee_ids.add(employee_id)
        
        department = departments[i % len(departments)]  # Distribute across departments
        position = random.choice(positions[department])
        hire_date = generate_hire_date()
        
        employee = {
            "name": name,
            "position": position,
            "department": department,
            "manager": None,
            "hire_date": hire_date,
            "pto_balance": generate_pto_balance(),
            "next_review_date": generate_next_review_date(hire_date),
            "enrolled_benefits": generate_benefits()
        }
        
        employees[employee_id] = employee
        
        if "Manager" in position or "Director" in position or "Lead" in position or "Supervisor" in position:
            managers[department].append(employee_id)
    
    # Add remaining employees to reach total of 15
    remaining_count = NUM_EMPLOYEES - len(required_employees) - 1  # -1 for test user
    for i in range(remaining_count):
        while True:
            employee_id = generate_employee_id()
            if employee_id not in employee_ids:
                employee_ids.add(employee_id)
                break
                
        department = random.choice(departments)
        position = random.choice(positions[department])
        hire_date = generate_hire_date()
        name = additional_names[i % len(additional_names)]
        
        employee = {
            "name": name,
            "position": position,
            "department": department,
            "manager": None,
            "hire_date": hire_date,
            "pto_balance": generate_pto_balance(),
            "next_review_date": generate_next_review_date(hire_date),
            "enrolled_benefits": generate_benefits()
        }
        
        employees[employee_id] = employee
        
        if "Manager" in position or "Director" in position or "Lead" in position or "Supervisor" in position:
            managers[department].append(employee_id)
    
    # Second pass - assign managers
    for employee_id, employee in employees.items():
        dept = employee["department"]
        potential_managers = [m for m in managers[dept] if m != employee_id]
        
        if potential_managers:
            employee["manager"] = employees[random.choice(potential_managers)]["name"]
    
    # Add test user
    employees["test"] = {
        "name": "Test User",
        "position": "System Administrator",
        "department": "Information Technology",
        "manager": None,
        "hire_date": "2020-01-01",
        "pto_balance": 15.0,
        "next_review_date": "2026-01-01",
        "enrolled_benefits": ["Blue Shield PPO", "Delta Dental", "VSP", "401(k) - 10%"]
    }
    
    return employees

def create_login_credentials(employees):
    """Create login credentials for all employees"""
    credentials = {}
    
    for emp_id, employee in employees.items():
        # Create a simple password
        if emp_id == "test":
            password = "test"  # Special case for test user
        else:
            password = emp_id[-5:]  # Last 5 characters of employee ID
        
        # Check if this is an administrative position
        is_admin = (
            "Manager" in employee["position"] or 
            "Director" in employee["position"] or 
            "Administrator" in employee["position"] or 
            employee["department"] == "Human Resources" or
            emp_id == "test"  # Test user is always admin
        )
        
        # Hash the password
        hashed_pw = hashlib.md5(password.encode()).hexdigest()
        
        credentials[emp_id] = {
            "password_hash": hashed_pw,
            "is_admin": is_admin
        }
    
    return credentials

def save_employees(employees, credentials):
    """Save the employee database as JSON and CSV"""
    # Create the data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save employees as JSON
    with open(OUTPUT_FILE_JSON, 'w') as f:
        json.dump(employees, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame([
        {
            "employee_id": emp_id,
            "name": emp["name"],
            "position": emp["position"],
            "department": emp["department"],
            "manager": emp["manager"] if emp["manager"] else "",
            "hire_date": emp["hire_date"],
            "pto_balance": emp["pto_balance"],
            "next_review_date": emp["next_review_date"],
            "enrolled_benefits": ", ".join(emp["enrolled_benefits"])
        }
        for emp_id, emp in employees.items()
    ])
    
    df.to_csv(OUTPUT_FILE_CSV, index=False)
    
    # Save credentials
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f, indent=2)
    
    return OUTPUT_FILE_JSON, OUTPUT_FILE_CSV, CREDENTIALS_FILE

def main():
    print(f"Generating synthetic employee database with {NUM_EMPLOYEES} employees...")
    employees = generate_employees()
    credentials = create_login_credentials(employees)
    json_file, csv_file, cred_file = save_employees(employees, credentials)
    
    print(f"Employee database saved to {json_file} and {csv_file}")
    print(f"Login credentials saved to {cred_file}")
    
    # Print sample of the data
    print("\nRequired employees have been added:")
    for emp_id, emp in employees.items():
        if emp["name"] in required_employees:
            print(f"ID: {emp_id}, Name: {emp['name']}, Department: {emp['department']}")
            print(f"  Position: {emp['position']}")
            print(f"  Benefits: {', '.join(emp['enrolled_benefits'])}")
            print(f"  Next Review: {emp['next_review_date']}")
            print(f"  Password: {emp_id[-5:]}")
            print()
    
    # Print test user info
    print("\nTest user credentials:")
    print(f"ID: test, Password: test, Admin: {credentials['test']['is_admin']}")

if __name__ == "__main__":
    main()