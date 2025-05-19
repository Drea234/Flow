# utils/emergency_handler.py
import streamlit as st
from datetime import datetime
import json
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmergencyHandler:
    """Handles red flag detection and emergency HR contacts"""
    
    RED_FLAG_KEYWORDS = {
        'harassment': ['harassed', 'harassment', 'inappropriate', 'unwanted advances', 'uncomfortable', 'bullying', 'intimidation'],
        'safety': ['unsafe', 'dangerous', 'hazard', 'injury', 'accident', 'risk', 'emergency'],
        'discrimination': ['discriminated', 'discrimination', 'bias', 'unfair treatment', 'racism', 'sexism', 'ageism'],
        'legal': ['violation', 'illegal', 'lawsuit', 'rights violated', 'retaliation', 'wrongful', 'labor law'],
        'ethics': ['unethical', 'fraud', 'corruption', 'misconduct', 'breach', 'confidential']
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.emergency_tickets_file = "data/emergency_tickets.json"
        self._ensure_tickets_file()
    
    def _ensure_tickets_file(self):
        """Ensure emergency tickets file exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.emergency_tickets_file):
            with open(self.emergency_tickets_file, 'w') as f:
                json.dump([], f)
    
    def detect_red_flags(self, message):
        """Detect red flags in employee messages"""
        red_flags = []
        found_keywords = {}
        
        message_lower = message.lower()
        
        for category, keywords in self.RED_FLAG_KEYWORDS.items():
            found = []
            for keyword in keywords:
                if keyword in message_lower:
                    found.append(keyword)
            
            if found:
                red_flags.append(category)
                found_keywords[category] = found
        
        return red_flags, found_keywords
    
    def create_emergency_ticket(self, employee_data, categories, message, urgency='HIGH'):
        """Create an emergency HR ticket"""
        ticket_id = f"HR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        ticket = {
            'id': ticket_id,
            'employee_id': employee_data.get('id', 'Unknown'),
            'employee_name': employee_data.get('name', 'Unknown'),
            'department': employee_data.get('department', 'Unknown'),
            'manager': employee_data.get('manager', 'Unknown'),
            'categories': categories,
            'message': message,
            'urgency': urgency,
            'timestamp': datetime.now().isoformat(),
            'status': 'OPEN',
            'assigned_to': None,
            'resolution_notes': None,
            'resolved_timestamp': None,
            'conversation_id': employee_data.get('conversation_id', None),
            'position': employee_data.get('position', 'Unknown'),
            'hire_date': employee_data.get('hire_date', 'Unknown')
        }
        
        # Save ticket to file
        with open(self.emergency_tickets_file, 'r') as f:
            tickets = json.load(f)
        
        tickets.append(ticket)
        
        with open(self.emergency_tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
        
        # Also save to database if you have a tickets table
        try:
            self.db_manager.save_emergency_ticket(ticket)
        except:
            pass  # Fallback to file system if DB method doesn't exist
        
        return ticket_id
    
    def get_all_emergency_tickets(self, status=None):
        """Get all emergency tickets, optionally filtered by status"""
        with open(self.emergency_tickets_file, 'r') as f:
            tickets = json.load(f)
        
        if status:
            tickets = [t for t in tickets if t.get('status') == status]
        
        return sorted(tickets, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def update_ticket_status(self, ticket_id, status, assigned_to=None, resolution_notes=None):
        """Update emergency ticket status"""
        with open(self.emergency_tickets_file, 'r') as f:
            tickets = json.load(f)
        
        for ticket in tickets:
            if ticket['id'] == ticket_id:
                ticket['status'] = status
                if assigned_to:
                    ticket['assigned_to'] = assigned_to
                if resolution_notes:
                    ticket['resolution_notes'] = resolution_notes
                if status == 'RESOLVED':
                    ticket['resolved_timestamp'] = datetime.now().isoformat()
                break
        
        with open(self.emergency_tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
    
    def get_ticket_by_id(self, ticket_id):
        """Get specific ticket by ID"""
        with open(self.emergency_tickets_file, 'r') as f:
            tickets = json.load(f)
        
        for ticket in tickets:
            if ticket['id'] == ticket_id:
                return ticket
        return None
    
    def notify_hr_team(self, ticket_id, categories):
        """Send notifications to HR team about emergency ticket"""
        # In a real system, this would send emails, SMS, or push notifications
        print(f"URGENT: Emergency ticket {ticket_id} created with categories: {', '.join(categories)}")
    
    def render_emergency_contact_form(self, employee_data, red_flags, message):
        """Render the emergency contact form in chatbot"""
        st.error("🚨 This appears to be an urgent matter that requires immediate HR attention.")
        
        st.markdown("""
        ### Contact HR Immediately
        
        Your message contains sensitive issues that should be addressed by HR as soon as possible.
        """)
        
        # Show detected categories
        st.markdown("**Detected Issues:**")
        for category in red_flags:
            st.markdown(f"- {category.title()}")
        
        # Pre-filled form
        with st.form("emergency_contact_form"):
            st.markdown("**Your Information**")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Name", value=employee_data.get('name', ''), disabled=True)
                st.text_input("Employee ID", value=employee_data.get('id', ''), disabled=True)
            with col2:
                st.text_input("Department", value=employee_data.get('department', ''), disabled=True)
                st.text_input("Manager", value=employee_data.get('manager', ''), disabled=True)
            
            st.markdown("**Issue Details**")
            
            # Fix the default values to match available options
            if red_flags == ['Manual Request']:
                default_categories = ['Other']
            else:
                # Convert red flag categories to proper capitalization to match options
                default_categories = []
                for flag in red_flags:
                    if flag.lower() == 'harassment':
                        default_categories.append('Harassment')
                    elif flag.lower() == 'safety':
                        default_categories.append('Safety')
                    elif flag.lower() == 'discrimination':
                        default_categories.append('Discrimination')
                    elif flag.lower() == 'legal':
                        default_categories.append('Legal')
                    elif flag.lower() == 'ethics':
                        default_categories.append('Ethics')
                    else:
                        default_categories.append('Other')
            
            issue_types = st.multiselect(
                "Issue Categories",
                options=['Harassment', 'Safety', 'Discrimination', 'Legal', 'Ethics', 'Other'],
                default=default_categories
            )
            
            urgency = st.select_slider(
                "Urgency Level",
                options=['Low', 'Medium', 'High', 'Critical'],
                value='High'
            )
            
            additional_details = st.text_area(
                "Additional Details",
                value=message,
                help="Provide any additional information that might help HR address your concern."
            )
            
            preferred_contact = st.radio(
                "Preferred Contact Method",
                options=['Email', 'Phone', 'In-Person Meeting'],
                horizontal=True
            )
            
            submit_button = st.form_submit_button("Submit to HR", type="primary")
            
            if submit_button:
                ticket_id = self.create_emergency_ticket(
                    employee_data=employee_data,
                    categories=issue_types,
                    message=additional_details,
                    urgency=urgency
                )
                
                self.notify_hr_team(ticket_id, issue_types)
                
                st.success(f"""
                ✅ Your concern has been submitted to HR.
                
                **Ticket ID:** {ticket_id}
                
                An HR representative will contact you via {preferred_contact.lower()} within:
                - Critical/High urgency: 1 hour
                - Medium urgency: 4 hours
                - Low urgency: 24 hours
                
                If this is a safety emergency, please also contact Security at extension 5555.
                """)
                
                return ticket_id
        
        return None
    
    def render_ticket_details(self, ticket_id):
        """Render detailed view of an emergency ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        
        if not ticket:
            st.error("Ticket not found")
            return
        
        st.header(f"Emergency Ticket: {ticket_id}")
        
        # Employee Information Section
        st.subheader("👤 Employee Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Name:** {ticket['employee_name']}")
            st.markdown(f"**Employee ID:** {ticket['employee_id']}")
            st.markdown(f"**Department:** {ticket['department']}")
        
        with col2:
            st.markdown(f"**Position:** {ticket.get('position', 'N/A')}")
            st.markdown(f"**Manager:** {ticket['manager']}")
            st.markdown(f"**Hire Date:** {ticket.get('hire_date', 'N/A')}")
        
        with col3:
            # Calculate tenure
            try:
                hire_date = datetime.strptime(ticket.get('hire_date', ''), "%Y-%m-%d")
                tenure = (datetime.now() - hire_date).days // 365
                st.markdown(f"**Tenure:** {tenure} years")
            except:
                st.markdown(f"**Tenure:** N/A")
        
        # Ticket Information Section
        st.subheader("🎫 Ticket Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Status:** {ticket['status']}")
            st.markdown(f"**Categories:** {', '.join(ticket['categories'])}")
            st.markdown(f"**Urgency:** {ticket['urgency']}")
            st.markdown(f"**Submitted:** {ticket['timestamp']}")
        
        with col2:
            st.markdown(f"**Assigned To:** {ticket.get('assigned_to', 'Unassigned')}")
            if ticket.get('resolved_timestamp'):
                st.markdown(f"**Resolved:** {ticket['resolved_timestamp']}")
            if ticket.get('resolution_notes'):
                st.markdown(f"**Resolution:** {ticket['resolution_notes']}")
        
        # Issue Details Section
        st.subheader("📝 Issue Details")
        st.markdown(f"**Full Message:**")
        st.info(ticket['message'])
        
        # Action Buttons
        st.subheader("⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📅 Schedule Meeting", key=f"schedule_{ticket_id}"):
                st.session_state.show_meeting_scheduler = True
        
        with col2:
            if st.button("📧 Send Email", key=f"email_{ticket_id}"):
                st.session_state.show_email_composer = True
        
        with col3:
            if st.button("📞 Call Employee", key=f"call_{ticket_id}"):
                st.info(f"Employee's extension: 1234")  # Would be real data in production
        
        with col4:
            if st.button("⚖️ Escalate to Legal", key=f"escalate_legal_{ticket_id}"):
                if st.checkbox("Confirm escalation to legal team?"):
                    self.update_ticket_status(ticket_id, 'ESCALATED')
                    st.success("Escalated to legal team")
        
        # Workflow Actions
        st.subheader("🔄 Workflow Actions")
        
        if ticket['status'] == 'OPEN':
            if st.button("Assign to Me", key=f"assign_detail_{ticket_id}"):
                self.update_ticket_status(ticket_id, 'IN_PROGRESS', st.session_state.get('admin_name', 'Admin'))
                st.success("Ticket assigned to you")
                time.sleep(1)
                st.rerun()
        
        if ticket['status'] in ['OPEN', 'IN_PROGRESS']:
            with st.form(key=f"resolve_form_{ticket_id}"):
                resolution_notes = st.text_area("Resolution Notes", help="Describe how the issue was resolved")
                resolve_button = st.form_submit_button("Mark as Resolved")
                
                if resolve_button and resolution_notes:
                    self.update_ticket_status(ticket_id, 'RESOLVED', resolution_notes=resolution_notes)
                    st.success("Ticket marked as resolved")
                    time.sleep(1)
                    st.rerun()
        
        # Related Information
        st.subheader("🔍 Related Information")
        tab1, tab2, tab3 = st.tabs(["Conversation History", "Similar Issues", "Policy References"])
        
        with tab1:
            # Get conversation history
            if ticket.get('conversation_id'):
                conversations = self.db_manager.get_conversation_thread(ticket['conversation_id'])
                for conv in conversations:
                    st.markdown(f"**{conv['date_time']}**")
                    st.markdown(f"Employee: {conv['question']}")
                    st.markdown(f"Assistant: {conv['answer']}")
                    st.divider()
            else:
                st.info("No conversation history available")
        
        with tab2:
            # Find similar issues
            all_tickets = self.get_all_emergency_tickets()
            similar_tickets = []
            
            for t in all_tickets:
                if t['id'] != ticket_id and any(cat in t['categories'] for cat in ticket['categories']):
                    similar_tickets.append(t)
            
            if similar_tickets:
                for similar in similar_tickets[:5]:
                    st.markdown(f"**{similar['id']}** - {similar['employee_name']} ({similar['department']})")
                    st.markdown(f"Categories: {', '.join(similar['categories'])}")
                    st.markdown(f"Status: {similar['status']}")
                    st.divider()
            else:
                st.info("No similar issues found")
        
        with tab3:
            # Show relevant policies
            category_policies = {
                'Harassment': ["Anti-Harassment Policy", "Code of Conduct", "Workplace Behavior Guidelines"],
                'Safety': ["Safety Procedures", "Emergency Response Plan", "Incident Reporting Policy"],
                'Discrimination': ["Equal Employment Opportunity Policy", "Anti-Discrimination Policy"],
                'Legal': ["Compliance Guidelines", "Legal Reporting Procedures"],
                'Ethics': ["Ethics Policy", "Confidentiality Agreement", "Conflict of Interest Policy"]
            }
            
            relevant_policies = []
            for cat in ticket['categories']:
                relevant_policies.extend(category_policies.get(cat, []))
            
            if relevant_policies:
                for policy in set(relevant_policies):
                    st.markdown(f"📄 [{policy}](https://valleywater.org/policies/{policy.lower().replace(' ', '-')})")
            else:
                st.info("No specific policies referenced")
    
    def get_emergency_analytics(self):
        """Get analytics data for emergency tickets"""
        all_tickets = self.get_all_emergency_tickets()
        
        analytics = {
            'total_tickets': len(all_tickets),
            'open_tickets': len([t for t in all_tickets if t['status'] == 'OPEN']),
            'resolved_tickets': len([t for t in all_tickets if t['status'] == 'RESOLVED']),
            'by_category': {},
            'by_department': {},
            'by_urgency': {},
            'resolution_time': [],
            'trends': []
        }
        
        # Analyze by category
        for ticket in all_tickets:
            for category in ticket['categories']:
                analytics['by_category'][category] = analytics['by_category'].get(category, 0) + 1
            
            # Analyze by department
            dept = ticket.get('department', 'Unknown')
            analytics['by_department'][dept] = analytics['by_department'].get(dept, 0) + 1
            
            # Analyze by urgency
            urgency = ticket.get('urgency', 'Unknown')
            analytics['by_urgency'][urgency] = analytics['by_urgency'].get(urgency, 0) + 1
            
            # Calculate resolution time
            if ticket['status'] == 'RESOLVED' and ticket.get('resolved_timestamp'):
                try:
                    created = datetime.fromisoformat(ticket['timestamp'])
                    resolved = datetime.fromisoformat(ticket['resolved_timestamp'])
                    resolution_hours = (resolved - created).total_seconds() / 3600
                    analytics['resolution_time'].append(resolution_hours)
                except:
                    pass
        
        # Calculate average resolution time
        if analytics['resolution_time']:
            analytics['avg_resolution_time'] = sum(analytics['resolution_time']) / len(analytics['resolution_time'])
        else:
            analytics['avg_resolution_time'] = 0
        
        return analytics