# utils/ai_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import json
import time
import os
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from utils.emergency_handler import EmergencyHandler
from utils.ai_insights import AIPoweredInsights

class AIDashboard:
    """Smart Insights Hub with AI-powered analytics - Detailed Mode Only"""
    
    def __init__(self, db_manager, topic_analyzer, sentiment_analyzer):
        self.db_manager = db_manager
        self.topic_analyzer = topic_analyzer
        self.sentiment_analyzer = sentiment_analyzer
        self.emergency_handler = EmergencyHandler(db_manager)
        self.ai_insights = AIPoweredInsights(db_manager, topic_analyzer)
        # Connect emergency handler to AI insights
        self.ai_insights.set_emergency_handler(self.emergency_handler)
    
    def render_dashboard(self):
        """Render the Smart Insights Hub with tabs"""
        st.header("Smart Insights Hub")
        
        # Create tab containers
        tab1, tab2 = st.tabs(["Smart Insights", "Deep Sentiment Analysis"])
        
        # Render Smart Insights in tab1 (Detailed view only)
        with tab1:
            self.render_smart_insights_detailed()
        
        # Render Deep Sentiment Analysis in tab2
        with tab2:
            self.render_sentiment_analysis()
    
    def render_smart_insights_detailed(self):
        """Render the detailed smart insights view"""
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            timeframe_options = ["Last 7 Days", "Last 30 Days", "All Time", "Custom Range"]
            timeframe = st.selectbox("Time Period", timeframe_options, key="smart_timeframe")
            
            # Custom date range
            if timeframe == "Custom Range":
                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                with date_col2:
                    end_date = st.date_input("End Date", datetime.now())
            else:
                start_date = end_date = None
                
        with col2:
            # Get unique departments from conversations
            departments = ["All Departments"]
            try:
                all_convos = self.db_manager.get_all_conversations(limit=1000)
                dept_set = set([conv.get("department", "Unknown") for conv in all_convos if conv.get("department")])
                departments.extend(sorted(list(dept_set)))
            except:
                departments.extend(["Engineering", "HR", "Finance", "Marketing"])
            department = st.selectbox("Department", departments, key="smart_department")
        
        # Get data based on filters
        if timeframe == "Custom Range":
            conversations = self.get_filtered_conversations_custom(start_date, end_date, department)
        else:
            days = 7 if timeframe == "Last 7 Days" else 30 if timeframe == "Last 30 Days" else 3650
            conversations = self.get_filtered_conversations(days, department)
        
        if not conversations:
            st.info("No data available for the selected filters. Try adjusting your selection or adding some conversations first.")
            return
        
        # Analyze data
        topic_analysis = self.analyze_topics_safely(conversations)
        sentiment_data = self.calculate_overall_sentiment(conversations)
        risk_analysis = self.analyze_emerging_risks(conversations, topic_analysis)
        
        # Overview Dashboard
        self.render_overview_dashboard(sentiment_data, conversations)
        
        # Main insights sections
        st.markdown("---")
        
        # Create columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            # What People Are Talking About - detailed view
            self.render_trending_conversations(topic_analysis, conversations)
        
        with col2:
            # Risk Radar - detailed view
            self.render_risk_radar(risk_analysis)
        
        # AI Insights button
        st.markdown("---")
        
        # Get current conversations for analysis
        self.ai_insights.render_insights_button(conversations, timeframe)
    
    def get_filtered_conversations_custom(self, start_date, end_date, department):
        """Get filtered conversations based on custom date range"""
        try:
            all_conversations = self.db_manager.get_all_conversations(limit=10000)
            
            filtered = []
            for conv in all_conversations:
                try:
                    date_str = conv.get('date_time', '')
                    if date_str:
                        conv_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
                        
                        if start_date <= conv_date <= end_date:
                            if department == "All Departments" or conv.get('department', '') == department:
                                filtered.append(conv)
                except Exception:
                    continue
            
            return filtered
        except Exception as e:
            st.error(f"Error getting conversations: {str(e)}")
            return []
    
    def render_overview_dashboard(self, sentiment_data, conversations):
        """Render the overview dashboard section"""
        st.subheader("Overview Dashboard")
        
        # Get emergency ticket count
        emergency_tickets = self.emergency_handler.get_all_emergency_tickets(status='OPEN')
        
        # Key metrics in cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            percentage = sentiment_data.get('percentage', 50)
            if percentage >= 70:
                sentiment_emoji = "😊"
                sentiment_color = "#4CAF50"
            elif percentage >= 40:
                sentiment_emoji = "😐"
                sentiment_color = "#FFC107"
            else:
                sentiment_emoji = "😟"
                sentiment_color = "#F44336"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: {sentiment_color}20; border-radius: 10px;'>
                <div style='font-size: 32px;'>{sentiment_emoji}</div>
                <div style='font-size: 20px; font-weight: bold;'>{percentage}%</div>
                <div style='font-size: 12px;'>Overall Sentiment</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_convos = len(conversations)
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: #E3F2FD; border-radius: 10px;'>
                <div style='font-size: 32px;'>💬</div>
                <div style='font-size: 20px; font-weight: bold;'>{total_convos}</div>
                <div style='font-size: 12px;'>Total Conversations</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            unique_employees = len(set(c.get('employee_id') for c in conversations))
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: #F3E5F5; border-radius: 10px;'>
                <div style='font-size: 32px;'>👥</div>
                <div style='font-size: 20px; font-weight: bold;'>{unique_employees}</div>
                <div style='font-size: 12px;'>Active Employees</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            trend = sentiment_data.get('trend', 'stable')
            trend_emoji = "↗️" if trend == 'improving' else "↘️" if trend == 'declining' else "→"
            trend_color = "#4CAF50" if trend == 'improving' else "#F44336" if trend == 'declining' else "#FFC107"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: {trend_color}20; border-radius: 10px;'>
                <div style='font-size: 32px;'>{trend_emoji}</div>
                <div style='font-size: 20px; font-weight: bold;'>{trend.title()}</div>
                <div style='font-size: 12px;'>Sentiment Trend</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            # Emergency Tickets metric
            ticket_color = "#F44336" if emergency_tickets else "#4CAF50"
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: {ticket_color}20; border-radius: 10px;'>
                <div style='font-size: 32px;'>🚨</div>
                <div style='font-size: 20px; font-weight: bold;'>{len(emergency_tickets)}</div>
                <div style='font-size: 12px;'>Emergency Tickets</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_trending_conversations(self, topic_analysis, conversations):
        """Render what people are talking about section with enhanced individual employee tracking"""
        st.subheader("💬 What People Are Talking About")
        
        # Create tabs for different views
        topic_tab1, topic_tab2, topic_tab3 = st.tabs(["Company-Wide", "By Department", "Individual Attention"])
        
        with topic_tab1:
            company_issues = [t for t in topic_analysis if t.get('category') == 'company_wide']
            if company_issues:
                for i, topic in enumerate(company_issues[:5], 1):
                    sentiment_emoji = self.get_sentiment_emoji(topic.get('avg_sentiment', 0))
                    trend_indicator = self.get_topic_trend(topic, conversations)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{i}. {topic.get('topic', 'Unknown')}** {sentiment_emoji}")
                    with col2:
                        st.markdown(f"{topic.get('unique_askers', 0)} employees")
                    with col3:
                        st.markdown(trend_indicator)
            else:
                st.info("No company-wide topics detected")
        
        with topic_tab2:
            dept_issues = [t for t in topic_analysis if t.get('category') == 'department_level']
            if dept_issues:
                # Group by department
                dept_grouped = {}
                for topic in dept_issues:
                    for dept in topic.get('departments', ['Unknown']):
                        if dept not in dept_grouped:
                            dept_grouped[dept] = []
                        dept_grouped[dept].append(topic)
                
                for dept, topics in dept_grouped.items():
                    st.markdown(f"**{dept} Department**")
                    # Get actual employee count for this department
                    dept_employees = set(c.get('employee_id') for c in conversations if c.get('department') == dept)
                    dept_employee_count = len(dept_employees)
                    
                    for topic in topics[:3]:
                        sentiment_emoji = self.get_sentiment_emoji(topic.get('avg_sentiment', 0))
                        # Show actual unique askers, not inflated count
                        actual_askers = min(topic.get('unique_askers', 0), dept_employee_count)
                        st.markdown(f"- {topic.get('topic', 'Unknown')} {sentiment_emoji} ({actual_askers} employees)")
            else:
                st.info("No department-specific issues detected")
        
        with topic_tab3:
            individual_issues = [t for t in topic_analysis if t.get('category') == 'individual' and t.get('total_questions', 0) > 1]
            if individual_issues:
                for topic in individual_issues[:5]:
                    # Find the specific employee asking about this topic
                    employee_convos = [c for c in conversations if c.get('topic') == topic.get('topic')]
                    
                    # Group by employee
                    employee_groups = {}
                    for conv in employee_convos:
                        emp_id = conv.get('employee_id', 'Unknown')
                        if emp_id not in employee_groups:
                            employee_groups[emp_id] = {
                                'name': conv.get('employee_name', 'Unknown'),
                                'department': conv.get('department', 'Unknown'),
                                'questions': []
                            }
                        employee_groups[emp_id]['questions'].append(conv)
                    
                    # Show each employee with repeated questions on this topic (UPDATED: More than 4 questions)
                    for emp_id, emp_data in employee_groups.items():
                        if len(emp_data['questions']) > 4:  # Only show if employee asked more than 4 times
                            st.markdown(f"""
                            🔍 **{emp_data['name']}** ({emp_data['department']})  
                            - {len(emp_data['questions'])} questions about **{topic.get('topic', 'Unknown')}**
                            """)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("View Thread", key=f"view_{emp_id}_{topic.get('topic', '')}"):
                                    st.session_state.selected_employee = emp_id
                                    st.session_state.selected_topic = topic.get('topic')
                            with col2:
                                if st.button("Schedule Follow-up", key=f"followup_{emp_id}_{topic.get('topic', '')}"):
                                    st.success(f"Follow-up task created for {emp_data['name']}")
                            with col3:
                                if st.button("Email Employee", key=f"email_{emp_id}_{topic.get('topic', '')}"):
                                    st.success(f"Email template created for {emp_data['name']}")
            else:
                st.info("No individual attention needed at this time")
    
    def render_risk_radar(self, risk_analysis):
        """Render risk radar section with emergency tickets"""
        st.subheader("🚨 Risk Radar")
        
        # Get emergency tickets
        emergency_tickets = self.emergency_handler.get_all_emergency_tickets(status='OPEN')
        
        # Add emergency tickets to risk analysis
        emergency_risks = []
        for ticket in emergency_tickets:
            risk_level = 'high' if ticket.get('urgency', '').lower() in ['critical', 'high'] else 'medium'
            emergency_risks.append({
                'risk_type': 'emergency_ticket',
                'risk_level': risk_level,
                'description': f"Emergency: {', '.join(ticket['categories'])} - {ticket['employee_name']} ({ticket['department']})",
                'affected_count': 1,
                'trend': 'new',
                'ticket_id': ticket['id'],
                'timestamp': ticket['timestamp'],
                'message': ticket['message'][:200] + '...' if len(ticket['message']) > 200 else ticket['message'],
                'employee_id': ticket['employee_id'],
                'employee_name': ticket['employee_name'],
                'department': ticket['department'],
                'categories': ticket['categories'],
                'urgency': ticket['urgency']
            })
        
        # Combine all risks
        all_risks = emergency_risks + risk_analysis if risk_analysis else emergency_risks
        
        if not all_risks:
            st.info("No emerging risks or emergency tickets detected")
            return
        
        # Sort risks by severity
        risks = sorted(all_risks, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['risk_level']])
        
        # Display emergency tickets
        emergency_count = len(emergency_risks)
        if emergency_count > 0:
            st.error(f"⚠️ {emergency_count} EMERGENCY TICKETS REQUIRING IMMEDIATE ATTENTION")
        
        for risk in risks:
            risk_color = {
                'high': '#F44336',
                'medium': '#FFC107',
                'low': '#4CAF50'
            }.get(risk['risk_level'], '#757575')
            
            risk_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(risk['risk_level'], '⚪')
            
            if risk['risk_type'] == 'emergency_ticket':
                # Enhanced emergency ticket display
                with st.expander(f"{risk_icon} EMERGENCY - {risk['employee_name']} ({risk['department']})", expanded=risk['risk_level'] == 'high'):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Ticket ID:** {risk['ticket_id']}  
                        **Categories:** {', '.join(risk['categories'])}  
                        **Urgency:** {risk['urgency']}  
                        **Submitted:** {risk['timestamp']}  
                        
                        **Message Preview:**  
                        {risk['message']}
                        """)
                    
                    with col2:
                        st.markdown("**Actions:**")
                        if st.button("📋 View Details", key=f"detail_{risk['ticket_id']}"):
                            st.session_state.selected_ticket = risk['ticket_id']
                            st.session_state.show_ticket_details = True
                            st.rerun()
                        
                        if st.button("✅ Resolve", key=f"resolve_{risk['ticket_id']}"):
                            with st.form(key=f"resolve_form_{risk['ticket_id']}"):
                                resolution = st.text_area("Resolution Notes")
                                if st.form_submit_button("Submit"):
                                    self.emergency_handler.update_ticket_status(
                                        risk['ticket_id'], 
                                        'RESOLVED', 
                                        resolution_notes=resolution
                                    )
                                    st.success("Ticket resolved")
                                    time.sleep(1)
                                    st.rerun()
            else:
                # Regular risks
                st.markdown(f"""
                <div style='padding: 10px; margin-bottom: 10px; border-left: 4px solid {risk_color}; background-color: #f8f9fa;'>
                    <strong>{risk_icon} {risk['risk_type'].replace('_', ' ').title()}</strong><br>
                    {risk['description']}<br>
                    <small>Impact: {risk['affected_count']} employees | Trend: {risk['trend']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Show ticket details if selected
        if st.session_state.get('show_ticket_details', False):
            ticket_id = st.session_state.get('selected_ticket')
            if ticket_id:
                self.emergency_handler.render_ticket_details(ticket_id)
                if st.button("← Back to Dashboard"):
                    st.session_state.show_ticket_details = False
                    st.rerun()
    
    def render_sentiment_analysis(self):
        """Render the detailed sentiment analysis view"""
        st.subheader("Deep Sentiment Analysis")
        
        # Add timeframe selector
        timeframe = st.radio(
            "Analysis Timeframe",
            ["Last 7 Days", "Last 30 Days", "All Time"],
            horizontal=True,
            key="sentiment_timeframe"
        )
        
        # Add department filter
        departments = ["All Departments"]
        try:
            all_convos = self.db_manager.get_all_conversations(limit=1000)
            dept_set = set([conv.get("department", "Unknown") for conv in all_convos if conv.get("department")])
            departments.extend(sorted(list(dept_set)))
        except:
            pass
        
        department = st.selectbox("Department Filter", departments, key="sentiment_department")
        
        # Add run analysis button
        if st.button("Run Sentiment Analysis", type="primary", key="run_sentiment"):
            with st.spinner("Analyzing conversations..."):
                # Get conversations based on timeframe
                days = 7 if timeframe == "Last 7 Days" else 30 if timeframe == "Last 30 Days" else 3650
                tf_param = timeframe.lower().replace(" ", "_")
                
                # Get conversations
                conversations = self.db_manager.get_all_conversations(limit=5000)
                
                # Filter by timeframe
                cutoff_date = datetime.now() - timedelta(days=days)
                filtered_convos = []
                for c in conversations:
                    try:
                        conv_date = datetime.strptime(c['date_time'].split()[0], "%Y-%m-%d")
                        if conv_date >= cutoff_date:
                            filtered_convos.append(c)
                    except:
                        continue
                
                # Filter by department if needed
                if department != "All Departments":
                    filtered_convos = [c for c in filtered_convos if c.get("department", "Unknown") == department]
                
                # Check if we have conversations to analyze
                if not filtered_convos:
                    st.warning("No conversations found for the selected timeframe and filters.")
                    return
                
                # Show progress during analysis
                total_convos = len(filtered_convos)
                if total_convos > 100:
                    filtered_convos = filtered_convos[:100]
                    st.info(f"Analyzing 100 most recent conversations out of {total_convos} total.")
                
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                # Check for cached results
                cache_key = f"sentiment_analysis_{timeframe}_{department}"
                
                if cache_key in st.session_state:
                    st.success("Using cached analysis results.")
                    analyzed_conversations = st.session_state[cache_key]["conversations"]
                    report = st.session_state[cache_key]["report"]
                    recommendations = st.session_state[cache_key]["recommendations"]
                else:
                    analyzed_conversations = []
                    
                    for i, convo in enumerate(filtered_convos):
                        progress = (i + 1) / len(filtered_convos)
                        progress_bar.progress(progress)
                        progress_text.text(f"Analyzing conversation {i+1} of {len(filtered_convos)}")
                        
                        if "sentiment" in convo:
                            analyzed_conversations.append(convo)
                            continue
                        
                        analysis = self.sentiment_analyzer.analyze_conversation(
                            convo["question"], 
                            convo["answer"]
                        )
                        
                        convo_with_sentiment = convo.copy()
                        convo_with_sentiment.update(analysis)
                        analyzed_conversations.append(convo_with_sentiment)
                        
                        time.sleep(0.1)
                    
                    report = self.sentiment_analyzer.generate_sentiment_report(
                        analyzed_conversations, 
                        timeframe=tf_param
                    )
                    
                    recommendations = self.sentiment_analyzer.generate_recommendations(report)
                    
                    st.session_state[cache_key] = {
                        "conversations": analyzed_conversations,
                        "report": report,
                        "recommendations": recommendations
                    }
                
                progress_bar.empty()
                progress_text.empty()
                
                # Display the report
                self.sentiment_analyzer.render_streamlit_report(report, recommendations)
        else:
            # Show instructions
            st.info("""
            This analysis uses AI to evaluate employee conversations and generates insights for HR improvement.
            
            The analysis includes:
            - Overall sentiment metrics
            - Common employee concerns
            - Emotional tones detected
            - Urgent issues requiring attention
            - AI-generated recommendations for HR
            
            Click "Run Sentiment Analysis" to begin.
            """)
            
            with st.expander("Preview Example Report"):
                st.image("https://via.placeholder.com/800x400?text=Sentiment+Analysis+Preview")
                st.caption("Example visualization - the actual report will be generated from your conversation data")
    
    def get_filtered_conversations(self, days, department):
        """Get filtered conversations based on selected criteria"""
        try:
            all_conversations = self.db_manager.get_all_conversations(limit=10000)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            filtered = []
            for conv in all_conversations:
                try:
                    date_str = conv.get('date_time', '')
                    if date_str:
                        try:
                            conv_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                        except:
                            continue
                        
                        if conv_date.date() >= cutoff_date.date():
                            if department == "All Departments" or conv.get('department', '') == department:
                                filtered.append(conv)
                except Exception:
                    continue
            
            return filtered
        except Exception as e:
            st.error(f"Error getting conversations: {str(e)}")
            return []
    
    def analyze_topics_safely(self, conversations):
        """Safely analyze topics with error handling"""
        try:
            return self.topic_analyzer.analyze_topics(conversations)
        except:
            return [{
                'topic': 'Unknown',
                'category': 'individual',
                'score': 0,
                'unique_askers': 0,
                'total_questions': len(conversations),
                'departments': ['Unknown'],
                'is_individual_concern': False,
                'avg_sentiment': 0,
                'max_questions_per_employee': 0
            }]
    
    def calculate_overall_sentiment(self, conversations):
        """Calculate overall sentiment metrics"""
        if not conversations:
            return {'score': 0, 'trend': 'stable', 'percentage': 50}
        
        try:
            scores = []
            for conv in conversations:
                score = conv.get('sentiment_score', 0)
                if isinstance(score, (int, float)):
                    scores.append(score)
                else:
                    scores.append(0)
            
            if not scores:
                return {'score': 0, 'trend': 'stable', 'percentage': 50}
            
            avg_score = sum(scores) / len(scores)
            
            mid_point = len(scores) // 2
            if mid_point > 0:
                first_half_avg = sum(scores[:mid_point]) / mid_point
                second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)
                
                if second_half_avg > first_half_avg + 0.1:
                    trend = 'improving'
                elif second_half_avg < first_half_avg - 0.1:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            percentage = int((avg_score + 1) * 50) if avg_score != 0 else 50
            
            return {
                'score': avg_score,
                'trend': trend,
                'percentage': percentage
            }
        except Exception as e:
            return {'score': 0, 'trend': 'stable', 'percentage': 50}
    
    def get_sentiment_emoji(self, sentiment_score):
        """Convert sentiment score to emoji"""
        if sentiment_score > 0.3:
            return "😊"
        elif sentiment_score < -0.3:
            return "😟"
        else:
            return "😐"
    
    def get_topic_trend(self, topic, conversations):
        """Determine if a topic is trending up or down"""
        topic_convos = [c for c in conversations if c.get('topic') == topic.get('topic')]
        if not topic_convos:
            return "→"
        
        # Sort by date
        sorted_convos = sorted(topic_convos, key=lambda x: x.get('date_time', ''))
        
        # Compare first half vs second half
        mid_point = len(sorted_convos) // 2
        if mid_point == 0:
            return "→"
        
        first_half = sorted_convos[:mid_point]
        second_half = sorted_convos[mid_point:]
        
        first_count = len(first_half)
        second_count = len(second_half)
        
        if second_count > first_count * 1.2:
            return "↗️ Trending Up"
        elif second_count < first_count * 0.8:
            return "↘️ Trending Down"
        else:
            return "→ Stable"
    
    def is_recent(self, date_str, days=7):
        """Check if a date is within the last N days"""
        if not date_str:
            return False
        try:
            date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            return date >= datetime.now() - timedelta(days=days)
        except:
            return False
    
    def detect_unanswered_patterns(self, conversations):
        """Detect patterns in questions that might not be getting satisfactory answers"""
        # This is a simplified version - could be enhanced with NLP
        low_satisfaction = [c for c in conversations if c.get('sentiment_score', 0) < -0.2]
        
        if len(low_satisfaction) > 5:
            topics = [c.get('topic', 'Unknown') for c in low_satisfaction]
            topic_counts = Counter(topics)
            most_common = topic_counts.most_common(1)[0] if topic_counts else None
            
            if most_common and most_common[1] > 3:
                return {
                    'topic': most_common[0],
                    'count': most_common[1]
                }
        return None
    
    def analyze_emerging_risks(self, conversations, topic_analysis):
        """Enhanced version that includes emergency ticket analysis"""
        risks = []
        
        # Get emergency tickets
        emergency_tickets = self.emergency_handler.get_all_emergency_tickets()
        
        # Analyze emergency patterns
        if emergency_tickets:
            # Count categories
            category_counts = {}
            department_counts = {}
            
            for ticket in emergency_tickets:
                for category in ticket.get('categories', []):
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                dept = ticket.get('department', 'Unknown')
                department_counts[dept] = department_counts.get(dept, 0) + 1
            
            # Add risk for frequent emergency categories
            for category, count in category_counts.items():
                if count >= 3:  # If 3 or more tickets of same category
                    risks.append({
                        'risk_type': 'emergency_pattern',
                        'risk_level': 'high',
                        'description': f"Multiple emergency reports about {category} ({count} cases)",
                        'affected_count': count,
                        'trend': 'increasing'
                    })
            
            # Add risk for departments with multiple emergencies
            for dept, count in department_counts.items():
                if count >= 2:  # If 2 or more emergencies in a department
                    risks.append({
                        'risk_type': 'department_emergency',
                        'risk_level':'medium',
                        'description': f"{dept} department has {count} emergency reports",
                        'affected_count': count,
                        'trend': 'stable'
                    })
        
        # Continue with existing risk analysis
        # Analyze sentiment trends
        recent_conversations = [c for c in conversations if self.is_recent(c.get('date_time'), days=7)]
        
        # Risk 1: Rapid negative sentiment increase
        negative_topics = [t for t in topic_analysis if t.get('avg_sentiment', 0) < -0.3]
        for topic in negative_topics:
            topic_convos = [c for c in recent_conversations if c.get('topic') == topic.get('topic')]
            if len(topic_convos) > 5:  # Significant volume
                risks.append({
                    'risk_type': 'negative_sentiment_spike',
                    'risk_level': 'high' if topic.get('avg_sentiment', 0) < -0.5 else 'medium',
                    'description': f"Rapidly increasing negative sentiment about {topic.get('topic')}",
                    'affected_count': topic.get('unique_askers', 0),
                    'trend': 'increasing'
                })
        
        # Risk 2: Department-wide issues
        dept_issues = [t for t in topic_analysis if t.get('category') == 'department_level' and t.get('unique_askers', 0) > 3]
        for issue in dept_issues:
            risks.append({
                'risk_type': 'department_issue',
                'risk_level': 'medium',
                'description': f"Growing concern in {', '.join(issue.get('departments', ['Unknown']))} about {issue.get('topic')}",
                'affected_count': issue.get('unique_askers', 0),
                'trend': 'stable'
            })
        
        # Risk 3: Unanswered questions pattern
        unanswered_pattern = self.detect_unanswered_patterns(conversations)
        if unanswered_pattern:
            risks.append({
                'risk_type': 'knowledge_gap',
                'risk_level': 'low',
                'description': f"Repeated questions about {unanswered_pattern['topic']} may indicate knowledge gap",
                'affected_count': unanswered_pattern['count'],
                'trend': 'stable'
            })
        
        return risks