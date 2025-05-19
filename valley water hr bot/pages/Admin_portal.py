api# pages/admin_portal.py
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import json
from utils.user_auth import admin_required, logout_user
from utils.db_manager import DBManager
from utils.report_generator import ReportGenerator
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.smart_topic_analyzer import SmartTopicAnalyzer
from utils.ai_dashboard import AIDashboard
from utils.emergency_handler import EmergencyHandler

# Initialize components
db_manager = DBManager()
report_generator = ReportGenerator(db_manager)
sentiment_analyzer = SentimentAnalyzer()
topic_analyzer = SmartTopicAnalyzer()
emergency_handler = EmergencyHandler(db_manager)
ai_dashboard = AIDashboard(db_manager, topic_analyzer, sentiment_analyzer)

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 2rem !important;
        margin-bottom: 1rem;
        color: #1c8ccc;
    }
    
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .card {
        border-radius: 8px;
        background-color: #f8f9fa;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background-color: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1c8ccc;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #505050;
    }
    
    .emergency-alert {
        background-color: #ffe6e6;
        border-left: 4px solid #ff4444;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    
    .emergency-ticket {
        background-color: #fff5f5;
        border: 1px solid #ff4444;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .footer {
        text-align: center;
        padding: 1rem;
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 2rem;
    }
    
    .filter-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #1c8ccc;
        font-size: 14px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        border-bottom: 2px solid #1c8ccc;
    }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    /* More specific selectors for Streamlit elements */
    h1, h2, h3 {
        color: #1c8ccc !important;
    }
    
    .stMetric .metric-value {
        color: #1c8ccc !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #1c8ccc !important;
    }
    
    /* Target specific Streamlit components */
    .stButton>button {
        border-color: #1c8ccc !important;
    }
    
    .stButton>button:hover {
        background-color: #1c8ccc !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)
# Date range selector
def date_range_selector():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            min_value=start_date,
            max_value=datetime.now()
        )
    return start_date, end_date

@admin_required
def main():
    # Check if database has department column and update if needed
    if "db_checked" not in st.session_state:
        check_and_update_database()
        st.session_state.db_checked = True
    
    # Get admin data from session
    admin_data = st.session_state.employee_data
    st.session_state.admin_name = admin_data['name']  # Store admin name for use in emergency handler
    
    # Header with logout button
    col1, col2, col3 = st.columns([4, 4, 2])
    with col1:
        st.markdown("<h1 class='main-title'>HR Admin Portal</h1>", unsafe_allow_html=True)
    with col3:
        st.button("Logout", key="logout_btn", on_click=logout_user)
        if st.button("Return to Portal", key="portal_btn"):
            st.switch_page("pages/employee_portal.py")
    
    # Admin info
    st.markdown(f"**Logged in as:** {admin_data['name']} ({admin_data['position']})")
    
    # Show emergency alert banner if there are open tickets
    open_tickets = emergency_handler.get_all_emergency_tickets(status='OPEN')
    if open_tickets:
        st.error(f"⚠️ {len(open_tickets)} EMERGENCY TICKETS REQUIRING IMMEDIATE ATTENTION")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", 
        "Conversation History", 
        "Employee Reports", 
        "AI Analytics", 
        "System Management"
    ])
    
    # Tab 1: Dashboard
    with tab1:
        # Get statistics
        stats = db_manager.get_conversation_stats()
        
        st.subheader("Overview")
        
        # Metrics in cards
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats.get('total_conversations', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Total Messages</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats.get('conversation_threads', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Conversation Threads</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats.get('unique_employees', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Unique Employees</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col4:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats.get('conversations_last_7_days', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Last 7 Days</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col5:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            avg_length = int(stats.get('avg_answer_length', 0))
            st.markdown(f"<div class='metric-value'>{avg_length}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Avg Answer Length</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col6:
            # Emergency tickets metric
            ticket_count = len(open_tickets)
            ticket_color = "#F44336" if ticket_count > 0 else "#4CAF50"
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value' style='color: {ticket_color};'>{ticket_count}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Emergency Tickets</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Show emergency tickets if any
        if open_tickets:
            st.markdown("---")
            st.subheader("🚨 Emergency Tickets")
            
            for ticket in open_tickets[:3]:  # Show up to 3 most recent
                with st.expander(f"URGENT: {ticket['employee_name']} - {', '.join(ticket['categories'])}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Ticket ID:** {ticket['id']}")
                        st.markdown(f"**Department:** {ticket['department']}")
                        st.markdown(f"**Submitted:** {ticket['timestamp']}")
                        st.markdown(f"**Message:** {ticket['message'][:200]}...")
                    
                    with col2:
                        if st.button("View Details", key=f"dashboard_view_{ticket['id']}"):
                            st.session_state.selected_ticket = ticket['id']
                            st.session_state.active_tab = "AI Analytics"
                            st.session_state.show_ticket_details = True
                            st.rerun()
                        
                        if st.button("Assign to Me", key=f"dashboard_assign_{ticket['id']}"):
                            emergency_handler.update_ticket_status(
                                ticket['id'], 
                                'IN_PROGRESS', 
                                admin_data['name']
                            )
                            st.success("Assigned to you")
                            time.sleep(1)
                            st.rerun()
            
            if len(open_tickets) > 3:
                st.info(f"View all {len(open_tickets)} emergency tickets in the AI Analytics tab → Risk Radar section")
        
        # Conversation trends chart
        st.subheader("Conversation Trends")
        trends_fig = report_generator.plot_conversation_trends(days=30)
        if trends_fig:
            st.plotly_chart(trends_fig, use_container_width=True)
        else:
            st.info("No conversation data available for trend analysis.")
        
        # Two charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Topic Distribution")
            topics_fig = report_generator.plot_topic_distribution()
            if topics_fig:
                st.plotly_chart(topics_fig, use_container_width=True)
            else:
                st.info("No topic data available.")
        
        with col2:
            st.subheader("Employee Activity")
            employee_fig = report_generator.plot_employee_activity()
            if employee_fig:
                st.plotly_chart(employee_fig, use_container_width=True)
            else:
                st.info("No employee activity data available.")
        
        # Export report button
        st.subheader("Export Dashboard Report")
        if st.button("Generate Admin Report", key="gen_admin_report"):
            with st.spinner("Generating report..."):
                # Generate admin report
                report = report_generator.generate_admin_report(days=30)
                
                # Add emergency ticket info to report
                report['emergency_tickets'] = {
                    'open_count': len(open_tickets),
                    'tickets': open_tickets
                }
                
                json_path = report_generator.save_report_to_json(report)
                
                # Provide download link
                with open(json_path, "rb") as file:
                    st.download_button(
                        label="Download Report (JSON)",
                        data=file,
                        file_name=os.path.basename(json_path),
                        mime="application/json"
                    )
    
    # Tab 2: Conversation History
    with tab2:
        st.subheader("Conversation History")
        
        # View mode selector
        view_mode = st.radio("View mode", ["Conversation Threads", "Individual Messages"], horizontal=True)
        
        # Filters
        st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            # Date range filter
            date_filter = st.checkbox("Filter by date", value=False)
            if date_filter:
                start_date, end_date = date_range_selector()
        
        with col2:
            # Topic filter
            topics = ["All Topics", "Emergency"] + [topic["name"] for topic in db_manager.get_top_topics(limit=20)]
            selected_topic = st.selectbox("Topic", topics)
        
        with col3:
            # Search filter
            search_term = st.text_input("Search", placeholder="Search conversations...")
        
        with col4:
            # Emergency filter
            show_emergencies = st.checkbox("Show Emergency Only", value=False)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if view_mode == "Conversation Threads":
            # Check if get_conversation_threads method exists
            if hasattr(db_manager, 'get_conversation_threads'):
                # Get conversation threads data
                conversation_threads = db_manager.get_conversation_threads(limit=1000)
                
                if not conversation_threads:
                    st.info("No conversation data available.")
                else:
                    # Apply filters to threads
                    filtered_threads = conversation_threads
                    
                    # Date filter
                    if date_filter:
                        filtered_threads = [
                            t for t in filtered_threads 
                            if start_date <= datetime.strptime(t['start_time'].split()[0], "%Y-%m-%d").date() <= end_date
                        ]
                    
                    # Topic filter
                    if selected_topic != "All Topics":
                        filtered_threads = [
                            t for t in filtered_threads 
                            if t.get('topic') == selected_topic or (selected_topic == "Emergency" and "Emergency" in t.get('topic', ''))
                        ]
                    
                    # Search filter
                    if search_term:
                        search_term = search_term.lower()
                        matching_threads = []
                        for thread in filtered_threads:
                            # Get all messages in this thread
                            thread_messages = db_manager.get_conversation_thread(thread['conversation_id'])
                            # Check if search term appears in any message in the thread
                            if any(
                                search_term in msg['question'].lower() or 
                                search_term in msg['answer'].lower() or 
                                search_term in msg.get('summary', '').lower() or
                                search_term in msg['employee_name'].lower()
                                for msg in thread_messages
                            ):
                                matching_threads.append(thread)
                        filtered_threads = matching_threads
                    
                    # Emergency filter
                    if show_emergencies:
                        filtered_threads = [
                            t for t in filtered_threads 
                            if "Emergency" in t.get('topic', '')
                        ]
                    
                    # Display filtered conversations
                    st.write(f"Showing {len(filtered_threads)} of {len(conversation_threads)} conversation threads")
                    
                    # Convert to DataFrame for display
                    if filtered_threads:
                        df = pd.DataFrame([
                            {
                                "Thread ID": t['conversation_id'],
                                "Employee ID": t['employee_id'],
                                "Employee": t['employee_name'],
                                "Start Date": t['start_time'],
                                "End Date": t.get('end_time', t['start_time']),
                                "Messages": t['message_count'],
                                "Topic": t.get('topic', 'Uncategorized'),
                                "Department": t.get('department', 'Unknown'),
                                "Emergency": "🚨" if "Emergency" in t.get('topic', '') else ""
                            }
                            for t in filtered_threads
                        ])
                        
                        # Display table
                        st.dataframe(
                            df,
                            column_config={
                                "Thread ID": st.column_config.TextColumn("Thread ID", width="medium"),
                                "Employee ID": st.column_config.TextColumn("Employee ID", width="medium"),
                                "Employee": st.column_config.TextColumn("Employee", width="medium"),
                                "Start Date": st.column_config.DatetimeColumn("Start Date", width="medium", format="MMM DD, YYYY, h:mm a"),
                                "End Date": st.column_config.DatetimeColumn("End Date", width="medium", format="MMM DD, YYYY, h:mm a"),
                                "Messages": st.column_config.NumberColumn("Messages", width="small"),
                                "Topic": st.column_config.TextColumn("Topic", width="medium"),
                                "Department": st.column_config.TextColumn("Department", width="medium"),
                                "Emergency": st.column_config.TextColumn("", width="small")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Detailed view for selected conversation thread
                        selected_thread_id = st.selectbox("Select conversation thread for detailed view:", ["None"] + [t['conversation_id'] for t in filtered_threads])
                        
                        if selected_thread_id != "None":
                            # Find selected thread
                            selected_thread = next((t for t in filtered_threads if t['conversation_id'] == selected_thread_id), None)
                            
                            if selected_thread:
                                st.subheader(f"Conversation with {selected_thread['employee_name']} (ID: {selected_thread['employee_id']})")
                                
                                # Show emergency alert if applicable
                                if "Emergency" in selected_thread.get('topic', ''):
                                    st.markdown("""
                                    <div class="emergency-alert">
                                        🚨 <strong>This conversation contains emergency/sensitive content</strong>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                                col1.markdown(f"**Start:** {selected_thread['start_time']}")
                                col2.markdown(f"**End:** {selected_thread.get('end_time', selected_thread['start_time'])}")
                                col3.markdown(f"**Messages:** {selected_thread['message_count']}")
                                col4.markdown(f"**Department:** {selected_thread.get('department', 'Unknown')}")
                                
                                # Get all messages in this thread
                                thread_messages = db_manager.get_conversation_thread(selected_thread_id)
                                
                                # Display the conversation
                                st.markdown("### Conversation:")
                                
                                for i, msg in enumerate(thread_messages):
                                    # User message
                                    st.markdown(f"**{msg['employee_name']}:** {msg['question']}")
                                    
                                    # Assistant message (with styling)
                                    st.markdown(f"**HR Assistant:** {msg['answer']}")
                                    
                                    # Add divider if not the last message
                                    if i < len(thread_messages) - 1:
                                        st.divider()
                                
                                # Action buttons
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    if st.button("Contact Employee", key=f"contact_{selected_thread_id}"):
                                        st.session_state.contact_employee = selected_thread['employee_id']
                                
                                with col2:
                                    if st.button("Create Follow-up Task", key=f"followup_{selected_thread_id}"):
                                        st.session_state.create_followup = True
                                        st.session_state.followup_employee = selected_thread['employee_id']
                                
                                with col3:
                                    if hasattr(db_manager, 'delete_conversation_thread') and st.button("Delete Thread", key=f"delete_thread_{selected_thread_id}"):
                                        if st.checkbox("I understand this action cannot be undone", key=f"confirm_delete_thread_{selected_thread_id}"):
                                            if db_manager.delete_conversation_thread(selected_thread_id):
                                                st.success(f"Conversation thread deleted successfully.")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to delete conversation thread.")
                    else:
                        st.info("No conversation threads match the current filters.")
            else:
                st.warning("Conversation thread functionality not yet available. Please update your database manager.")
                st.info("To enable this feature, add support for conversation threads in your database manager.")
        
        else:
            # Individual messages view
            conversations = db_manager.get_all_conversations(limit=1000)
            
            if not conversations:
                st.info("No conversation data available.")
            else:
                # Apply filters
                filtered_conversations = conversations
                
                # Date filter
                if date_filter:
                    filtered_conversations = [
                        c for c in filtered_conversations 
                        if start_date <= datetime.strptime(c['date_time'].split()[0], "%Y-%m-%d").date() <= end_date
                    ]
                
                # Topic filter
                if selected_topic != "All Topics":
                    filtered_conversations = [
                        c for c in filtered_conversations 
                        if c.get('topic') == selected_topic or (selected_topic == "Emergency" and "Emergency" in c.get('topic', ''))
                    ]
                
                # Search filter
                if search_term:
                    search_term = search_term.lower()
                    filtered_conversations = [
                        c for c in filtered_conversations 
                        if (search_term in c['question'].lower() or 
                            search_term in c['answer'].lower() or 
                            search_term in c.get('summary', '').lower() or
                            search_term in c['employee_name'].lower())
                    ]
                
                # Emergency filter
                if show_emergencies:
                    filtered_conversations = [
                        c for c in filtered_conversations 
                        if "Emergency" in c.get('topic', '')
                    ]
                
                # Display filtered conversations
                st.write(f"Showing {len(filtered_conversations)} of {len(conversations)} messages")
                
                # Convert to DataFrame for display
                if filtered_conversations:
                    df = pd.DataFrame([
                        {
                            "ID": c['id'],
                            "Thread ID": c.get('conversation_id', 'N/A'),
                            "Employee ID": c['employee_id'],
                            "Employee": c['employee_name'],
                            "Date": c['date_time'],
                            "Topic": c.get('topic', 'Uncategorized'),
                            "Department": c.get('department', 'Unknown'),
                            "Question": c['question'],
                            "Summary": c.get('summary', 'No summary available'),
                            "Emergency": "🚨" if "Emergency" in c.get('topic', '') else ""
                        }
                        for c in filtered_conversations
                    ])
                    
                    # Display table
                    st.dataframe(
                        df,
                        column_config={
                            "ID": st.column_config.NumberColumn("ID", width="small"),
                            "Thread ID": st.column_config.TextColumn("Thread ID", width="medium"),
                            "Employee ID": st.column_config.TextColumn("Employee ID", width="medium"),
                            "Employee": st.column_config.TextColumn("Employee", width="medium"),
                            "Date": st.column_config.DatetimeColumn("Date", width="medium", format="MMM DD, YYYY, h:mm a"),
                            "Topic": st.column_config.TextColumn("Topic", width="medium"),
                            "Department": st.column_config.TextColumn("Department", width="medium"),
                            "Question": st.column_config.TextColumn("Question", width="large"),
                            "Summary": st.column_config.TextColumn("Summary", width="large"),
                            "Emergency": st.column_config.TextColumn("", width="small")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Detailed view for selected conversation
                    selected_id = st.selectbox("Select message for detailed view:", ["None"] + [str(c['id']) for c in filtered_conversations])
                    
                    if selected_id != "None":
                        selected_id = int(selected_id)
                        # Find selected conversation
                        selected_convo = next((c for c in filtered_conversations if c['id'] == selected_id), None)
                        
                        if selected_convo:
                            st.subheader(f"Message #{selected_id} - {selected_convo['employee_name']} (ID: {selected_convo['employee_id']})")
                            
                            # Show emergency alert if applicable
                            if "Emergency" in selected_convo.get('topic', ''):
                                st.markdown("""
                                <div class="emergency-alert">
                                    🚨 <strong>This message contains emergency/sensitive content</strong>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                            col1.markdown(f"**Date:** {selected_convo['date_time']}")
                            col2.markdown(f"**Topic:** {selected_convo.get('topic', 'Uncategorized')}")
                            col3.markdown(f"**Thread ID:** {selected_convo.get('conversation_id', 'N/A')}")
                            col4.markdown(f"**Department:** {selected_convo.get('department', 'Unknown')}")
                            
                            # Allow topic editing
                            new_topic = st.text_input("Edit topic:", value=selected_convo.get('topic', ''), key=f"topic_edit_{selected_id}")
                            if new_topic != selected_convo.get('topic', '') and st.button("Update Topic", key=f"update_topic_{selected_id}"):
                                if db_manager.update_conversation_topic(selected_id, new_topic):
                                    st.success("Topic updated successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Failed to update topic.")
                            
                            # Display Q&A
                            st.markdown("**Question:**")
                            st.markdown(f"<div class='card'>{selected_convo['question']}</div>", unsafe_allow_html=True)
                            
                            st.markdown("**Answer:**")
                            st.markdown(f"<div class='card'>{selected_convo['answer']}</div>", unsafe_allow_html=True)
                            
                            if selected_convo.get('summary'):
                                st.markdown("**Summary:**")
                                st.markdown(f"<div class='card'>{selected_convo['summary']}</div>", unsafe_allow_html=True)
                else:
                    st.info("No messages match the current filters.")
        
        # Export filtered data
        st.subheader("Export Data")
        
        if view_mode == "Conversation Threads" and 'filtered_threads' in locals() and filtered_threads:
            if st.button("Export Filtered Threads to CSV", key="export_threads"):
                # Create a temporary file for the filtered data
                temp_file = os.path.join("data", "reports", f"filtered_threads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                
                # Convert to DataFrame and save
                df = pd.DataFrame(filtered_threads)
                df.to_csv(temp_file, index=False)
                
                # Provide download button
                with open(temp_file, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(temp_file),
                        mime="text/csv"
                    )
        elif view_mode == "Individual Messages" and 'filtered_conversations' in locals() and filtered_conversations:
            if st.button("Export Filtered Messages to CSV", key="export_filtered"):
                # Create a temporary file for the filtered data
                temp_file = os.path.join("data", "reports", f"filtered_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                
                # Convert to DataFrame and save
                df = pd.DataFrame(filtered_conversations)
                df.to_csv(temp_file, index=False)
                
                # Provide download button
                with open(temp_file, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(temp_file),
                        mime="text/csv"
                    )
    
    # Tab 3: Employee Reports
    with tab3:
        st.subheader("Employee Reports")
        
        # Get unique employees from conversations
        employee_conversations = db_manager.get_conversation_counts_by_employee(limit=1000)
        
        if not employee_conversations:
            st.info("No employee conversation data available.")
        else:
            # Show employees with emergency tickets
            emergency_employees = set()
            for ticket in open_tickets:
                emergency_employees.add(ticket['employee_id'])
            
            if emergency_employees:
                st.markdown("### ⚠️ Employees with Open Emergency Tickets")
                emergency_df = pd.DataFrame([
                    e for e in employee_conversations 
                    if e['employee_id'] in emergency_employees
                ])
                
                if not emergency_df.empty:
                    st.dataframe(emergency_df)
                
                st.markdown("---")
            
            # Get employee activity with thread counts if available
            if hasattr(db_manager, 'get_thread_counts_by_employee'):
                employee_data = db_manager.get_thread_counts_by_employee(limit=1000)
                
                # Display employee stats table
                df = pd.DataFrame([
                    {
                        "Employee ID": e['employee_id'],
                        "Employee Name": e['employee_name'],
                        "Conversation Threads": e.get('thread_count', 1),
                        "Total Messages": e['message_count'],
                        "Emergency": "🚨" if e['employee_id'] in emergency_employees else ""
                    }
                    for e in employee_data
                ])
                
                st.dataframe(
                    df,
                    column_config={
                        "Employee ID": st.column_config.TextColumn("Employee ID", width="medium"),
                        "Employee Name": st.column_config.TextColumn("Employee Name", width="medium"),
                        "Conversation Threads": st.column_config.NumberColumn("Conversation Threads", width="medium"),
                        "Total Messages": st.column_config.NumberColumn("Total Messages", width="medium"),
                        "Emergency": st.column_config.TextColumn("", width="small")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            # Create dropdown of employees
            employee_options = [f"{e['employee_name']} ({e['employee_id']})" for e in employee_conversations]
            employee_options.insert(0, "Select an employee")
            
            selected_employee_option = st.selectbox("Select employee for detailed report:", employee_options)
            
            if selected_employee_option != "Select an employee":
                # Extract employee ID from selection
                employee_id = selected_employee_option.split("(")[1].split(")")[0]
                
                # Check if employee has emergency tickets
                employee_tickets = [t for t in open_tickets if t['employee_id'] == employee_id]
                
                if employee_tickets:
                    st.error(f"⚠️ This employee has {len(employee_tickets)} open emergency tickets")
                    
                    for ticket in employee_tickets:
                        with st.expander(f"Emergency Ticket: {ticket['id']}", expanded=True):
                            st.markdown(f"**Categories:** {', '.join(ticket['categories'])}")
                            st.markdown(f"**Submitted:** {ticket['timestamp']}")
                            st.markdown(f"**Message:** {ticket['message']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Resolve Ticket", key=f"resolve_emp_{ticket['id']}"):
                                    with st.form(key=f"resolve_form_emp_{ticket['id']}"):
                                        resolution = st.text_area("Resolution Notes")
                                        if st.form_submit_button("Submit"):
                                            emergency_handler.update_ticket_status(
                                                ticket['id'], 
                                                'RESOLVED', 
                                                resolution_notes=resolution
                                            )
                                            st.success("Ticket resolved")
                                            time.sleep(1)
                                            st.rerun()
                            
                            with col2:
                                if st.button("Contact Employee", key=f"contact_emp_{ticket['id']}"):
                                    st.session_state.contact_employee = employee_id
                
                # Generate and display employee report
                report_generator.render_streamlit_employee_report(employee_id)
    
    # Tab 4: AI Analytics
    with tab4:
        # Check if we should show ticket details
        if st.session_state.get('show_ticket_details', False):
            ticket_id = st.session_state.get('selected_ticket')
            if ticket_id:
                emergency_handler.render_ticket_details(ticket_id)
                if st.button("← Back to AI Analytics"):
                    st.session_state.show_ticket_details = False
                    st.rerun()
        else:
            ai_dashboard.render_dashboard()
    
    # Tab 5: System Management
    with tab5:
        st.subheader("System Management")
        
        # System info card
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Database Path:** {db_manager.db_path}")
            if os.path.exists(db_manager.db_path):
                st.write(f"**Database Size:** {os.path.getsize(db_manager.db_path) / (1024*1024):.2f} MB")
            else:
                st.write("**Database Status:** Not created yet")
            st.write(f"**Admin Account:** {admin_data['name']}")
        
        with col2:
            st.write(f"**Session Start Time:** {st.session_state.get('login_time', 'Unknown')}")
            st.write(f"**Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Emergency system status
            emergency_tickets_file = os.path.join("data", "emergency_tickets.json")
            if os.path.exists(emergency_tickets_file):
                st.write(f"**Emergency System:** Operational")
                total_tickets = len(emergency_handler.get_all_emergency_tickets())
                st.write(f"**Total Emergency Tickets:** {total_tickets}")
            else:
                st.write(f"**Emergency System:** Not initialized")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Database management
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Database Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Full Database", key="export_full_db"):
                if not os.path.exists(db_manager.db_path):
                    st.warning("Database file does not exist yet. No conversations have been recorded.")
                else:
                    with st.spinner("Exporting database..."):
                        export_path = db_manager.export_conversations_to_csv(
                            os.path.join("data", "reports", f"full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                        )
                        
                        with open(export_path, "rb") as file:
                            st.download_button(
                                label="Download Full Export",
                                data=file,
                                file_name=os.path.basename(export_path),
                                mime="text/csv"
                            )
        
        with col2:
            # Database backup option
            if st.button("Backup Database", key="backup_db"):
                if not os.path.exists(db_manager.db_path):
                    st.warning("Database file does not exist yet. No conversations have been recorded.")
                else:
                    backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    
                    # Create backup
                    import shutil
                    try:
                        shutil.copy2(db_manager.db_path, backup_path)
                        st.success(f"Database backed up to {backup_path}")
                    except Exception as e:
                        st.error(f"Backup failed: {e}")
        
        # Emergency system management
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Emergency System Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Emergency Tickets", key="export_emergency"):
                tickets = emergency_handler.get_all_emergency_tickets()
                if tickets:
                    df = pd.DataFrame(tickets)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Emergency Tickets CSV",
                        data=csv,
                        file_name=f"emergency_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No emergency tickets to export")
        
        with col2:
            if st.button("Clear Resolved Tickets", key="clear_resolved"):
                resolved_tickets = emergency_handler.get_all_emergency_tickets(status='RESOLVED')
                if resolved_tickets:
                    # Archive resolved tickets
                    archive_path = f"data/archived_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(archive_path, 'w') as f:
                        json.dump(resolved_tickets, f, indent=2)
                    
                    # Update tickets file to remove resolved
                    all_tickets = emergency_handler.get_all_emergency_tickets()
                    active_tickets = [t for t in all_tickets if t['status'] != 'RESOLVED']
                    
                    with open(os.path.join("data", "emergency_tickets.json"), 'w') as f:
                        json.dump(active_tickets, f, indent=2)
                    
                    st.success(f"Archived {len(resolved_tickets)} resolved tickets to {archive_path}")
                else:
                    st.info("No resolved tickets to clear")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Check if database schema needs to be updated
        if st.button("Update Database Schema", key="update_schema"):
            try:
                # Connect to the database
                import sqlite3
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                # Check if department column exists
                cursor.execute("PRAGMA table_info(conversations)")
                columns = [column[1] for column in cursor.fetchall()]
                
                updates_made = False
                
                if "conversation_id" not in columns:
                    cursor.execute("ALTER TABLE conversations ADD COLUMN conversation_id TEXT")
                    updates_made = True
                    st.info("Added conversation_id column")
                
                if "department" not in columns:
                    cursor.execute("ALTER TABLE conversations ADD COLUMN department TEXT")
                    updates_made = True
                    st.info("Added department column")
                
                if updates_made:
                    # Update existing records
                    cursor.execute("""
                    UPDATE conversations 
                    SET conversation_id = employee_id || '_' || substr(date_time, 1, 10)
                    WHERE conversation_id IS NULL
                    """)
                    
                    # Update departments from employee database
                    try:
                        with open("data/employee_database.json", "r") as f:
                            employee_data = json.load(f)
                        
                        cursor.execute("SELECT id, employee_id FROM conversations")
                        conversations = cursor.fetchall()
                        
                        for conv_id, emp_id in conversations:
                            department = employee_data.get(emp_id, {}).get("department", "Unknown")
                            cursor.execute(
                                "UPDATE conversations SET department = ? WHERE id = ?", 
                                (department, conv_id)
                            )
                    except Exception as e:
                        st.warning(f"Could not update department information: {e}")
                    
                    conn.commit()
                    st.success("Database schema updated successfully!")
                else:
                    st.info("Database schema is up to date.")
                
                conn.close()
            except Exception as e:
                st.error(f"Error updating database schema: {e}")
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("⚠️ Danger Zone", help="These actions cannot be undone")
        
        # Delete conversation
        delete_id = st.number_input("Enter conversation ID to delete:", min_value=1, step=1)
        if st.button("Delete Conversation", key="delete_convo"):
            # Confirm deletion
            if st.checkbox("I understand this action cannot be undone", key="confirm_delete"):
                # Try to delete
                if db_manager.delete_conversation(delete_id):
                    st.success(f"Conversation #{delete_id} deleted successfully.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to delete conversation #{delete_id}. It may not exist.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>© 2025 Valley Water HR Assistant | Developed by Team Sapphire</div>", unsafe_allow_html=True)

def check_and_update_database():
    """Check if database has department column and update if needed"""
    try:
        import sqlite3
        if not os.path.exists(db_manager.db_path):
            # Create new database if it doesn't exist
            return
        
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # Check if department column exists
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "department" not in columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN department TEXT")
            
            # Update existing records with department information
            try:
                with open("data/employee_database.json", "r") as f:
                    employee_data = json.load(f)
                
                cursor.execute("SELECT id, employee_id FROM conversations")
                conversations = cursor.fetchall()
                
                for conv_id, emp_id in conversations:
                    department = employee_data.get(emp_id, {}).get("department", "Unknown")
                    cursor.execute(
                        "UPDATE conversations SET department = ? WHERE id = ?", 
                        (department, conv_id)
                    )
                
                conn.commit()
            except Exception as e:
                print(f"Warning: Could not update department information: {e}")
        
        conn.close()
    except Exception as e:
        print(f"Error checking/updating database: {e}")

if __name__ == "__main__":
    main()