# utils/ai_insights.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from collections import Counter
import re
from openai import OpenAI
from io import BytesIO
from fpdf import FPDF

class AIPoweredInsights:
    """AI-powered insights generator for HR dashboard"""
    
    def __init__(self, db_manager, topic_analyzer):
        self.db_manager = db_manager
        self.topic_analyzer = topic_analyzer
        self.client = self._get_openai_client()
        self.emergency_handler = None  # Will be injected from dashboard
        
        # Initialize session state for insights
        if 'show_insights_modal' not in st.session_state:
            st.session_state.show_insights_modal = False
        if 'current_insights' not in st.session_state:
            st.session_state.current_insights = None
    
    def set_emergency_handler(self, emergency_handler):
        """Set the emergency handler for accessing emergency analytics"""
        self.emergency_handler = emergency_handler
    
    def _get_openai_client(self):
        """Initialize OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("openai_api_key", "")
        return OpenAI(api_key=api_key) if api_key else None
    
    def generate_insights(self, conversations, timeframe="Last 7 Days", start_date=None, end_date=None):
        """Generate AI-powered insights from conversations"""
        insights = {
            'topic_trends': self.analyze_topic_trends(conversations, timeframe, start_date, end_date),
            'deep_analysis': self.perform_deep_topic_analysis(conversations),
            'faq_opportunities': self.identify_faq_opportunities(conversations),
            'emergency_analysis': self.analyze_emergency_situation(),
            'summary': self.generate_quick_summary(conversations),
            'generated_at': datetime.now().isoformat()
        }
        return insights
    
    def analyze_emergency_situation(self):
        """Analyze emergency tickets and patterns"""
        if not self.emergency_handler:
            return {}
        
        analytics = self.emergency_handler.get_emergency_analytics()
        tickets = self.emergency_handler.get_all_emergency_tickets(status='OPEN')
        
        # Analyze urgency distribution
        urgency_analysis = {
            'critical_count': analytics['by_urgency'].get('Critical', 0),
            'high_count': analytics['by_urgency'].get('High', 0),
            'medium_count': analytics['by_urgency'].get('Medium', 0)
        }
        
        # Analyze category patterns
        category_analysis = []
        for category, count in analytics['by_category'].items():
            if count >= 2:  # Only highlight categories with multiple tickets
                category_analysis.append({
                    'category': category,
                    'count': count,
                    'severity': 'high' if count >= 3 else 'medium'
                })
        
        # Analyze department impact
        department_analysis = []
        for dept, count in analytics['by_department'].items():
            if count >= 1:
                department_analysis.append({
                    'department': dept,
                    'count': count,
                    'severity': 'high' if count >= 3 else 'medium' if count >= 2 else 'low'
                })
        
        return {
            'total_tickets': analytics['total_tickets'],
            'open_tickets': analytics['open_tickets'],
            'avg_resolution_time': analytics['avg_resolution_time'],
            'urgency_analysis': urgency_analysis,
            'category_patterns': category_analysis,
            'department_impact': department_analysis,
            'critical_tickets': [t for t in tickets if t.get('urgency') == 'Critical']
        }
    
    def analyze_topic_trends(self, conversations, timeframe="Last 7 Days", start_date=None, end_date=None):
        """Analyze trending topics with time series data"""
        if not conversations:
            return {
                'trending_up': [], 
                'trending_down': [], 
                'new_topics': [],
                'time_series_data': {}
            }
        
        # Filter conversations based on timeframe
        now = datetime.now()
        if timeframe == "Custom Range" and start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d") if isinstance(start_date, str) else start_date
            end = datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date
        else:
            days = 7 if timeframe == "Last 7 Days" else 30 if timeframe == "Last 30 Days" else 3650
            start = now - timedelta(days=days)
            end = now
        
        # Get topic counts by date
        daily_topics = {}
        current_topics = Counter()
        previous_topics = Counter()
        
        cutoff_date = start + (end - start) / 2  # Split period in half for trend comparison
        
        for conv in conversations:
            try:
                conv_date = datetime.strptime(conv['date_time'].split()[0], "%Y-%m-%d")
                if start <= conv_date <= end:
                    topic = conv.get('topic', 'Unknown')
                    date_str = conv_date.strftime("%Y-%m-%d")
                    
                    if date_str not in daily_topics:
                        daily_topics[date_str] = Counter()
                    daily_topics[date_str][topic] += 1
                    
                    # For trend calculation
                    if conv_date >= cutoff_date:
                        current_topics[topic] += 1
                    else:
                        previous_topics[topic] += 1
            except:
                continue
        
        # Generate time series data for all topics
        all_topics = set(current_topics.keys()) | set(previous_topics.keys())
        time_series_data = {}
        
        for topic in all_topics:
            dates = []
            counts = []
            
            current_date = start
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")
                dates.append(date_str)
                count = daily_topics.get(date_str, Counter()).get(topic, 0)
                counts.append(count)
                current_date += timedelta(days=1)
            
            time_series_data[topic] = {
                'dates': dates,
                'counts': counts
            }
        
        # Calculate trends
        trending_up = []
        trending_down = []
        new_topics = []
        
        for topic in current_topics:
            current_count = current_topics[topic]
            previous_count = previous_topics.get(topic, 0)
            
            if previous_count == 0:
                new_topics.append({
                    'topic': topic,
                    'count': current_count
                })
            elif current_count > previous_count * 1.2:  # 20% increase
                trending_up.append({
                    'topic': topic,
                    'current': current_count,
                    'previous': previous_count,
                    'change': f"+{current_count - previous_count}"
                })
            elif current_count < previous_count * 0.8:  # 20% decrease
                trending_down.append({
                    'topic': topic,
                    'current': current_count,
                    'previous': previous_count,
                    'change': f"-{previous_count - current_count}"
                })
        
        return {
            'trending_up': sorted(trending_up, key=lambda x: x['current'], reverse=True)[:5],
            'trending_down': sorted(trending_down, key=lambda x: x['previous'] - x['current'], reverse=True)[:5],
            'new_topics': sorted(new_topics, key=lambda x: x['count'], reverse=True)[:5],
            'time_series_data': time_series_data
        }
    
    def perform_deep_topic_analysis(self, conversations):
        """Perform AI-powered deep analysis on major topics with HR recommendations"""
        if not conversations:
            return []
            
        # Group conversations by topic
        topic_groups = {}
        for conv in conversations:
            topic = conv.get('topic', 'Unknown')
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(conv)
        
        # Analyze top 5 topics
        top_topics = sorted(topic_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        deep_analysis = []
        
        for topic, convs in top_topics:
            # Prepare data for AI analysis
            questions = [c['question'] for c in convs]
            departments = [c.get('department', 'Unknown') for c in convs]
            dept_impact = Counter(departments)
            
            analysis_result = None
            
            # Try AI analysis
            if self.client:
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert HR analyst. Provide deep, actionable insights about employee concerns. Be specific and detailed in your analysis."},
                            {"role": "user", "content": f"""
                            Analyze employee conversations about "{topic}" in depth:
                            
                            Sample questions: {questions[:10]}
                            Departments involved: {list(set(departments))}
                            
                            Provide a comprehensive JSON response with:
                            1. root_cause: Detailed analysis of underlying issues (be specific about the problem)
                            2. impact_level: Impact on productivity/morale (High/Medium/Low)
                            3. related_topics: List of related HR topics
                            4. department_impact: Detailed impact by department with explanations
                            5. hr_recommendations: 3-5 specific, actionable recommendations
                            6. timeline: Realistic timeline for addressing this issue
                            7. resources_needed: Specific resources required
                            8. confidence_score: Your confidence level (0-100)
                            
                            Ensure each field has meaningful, specific content - avoid generic responses.
                            """}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    try:
                        analysis_result = json.loads(response.choices[0].message.content)
                    except json.JSONDecodeError:
                        analysis_result = None
                except Exception as e:
                    print(f"AI analysis failed for {topic}: {str(e)}")
                    analysis_result = None
            
            # Fallback with meaningful content
            if analysis_result is None:
                # Create meaningful fallback content based on the data
                question_count = len(convs)
                
                # Analyze patterns in questions for root cause
                common_words = Counter()
                for q in questions:
                    words = re.findall(r'\b\w+\b', q.lower())
                    common_words.update([w for w in words if len(w) > 3])
                
                # Get most common meaningful words
                top_words = [word for word, _ in common_words.most_common(5)]
                
                root_cause = self._generate_meaningful_root_cause(topic, top_words, question_count)
                recommendations = self._generate_meaningful_recommendations(topic, top_words, dept_impact)
                
                analysis_result = {
                    'root_cause': root_cause,
                    'impact_level': 'High' if question_count > 10 else 'Medium' if question_count > 5 else 'Low',
                    'related_topics': self._infer_related_topics(topic),
                    'department_impact': {dept: f"{count} employees affected" for dept, count in dept_impact.items()},
                    'hr_recommendations': recommendations,
                    'timeline': '1-2 weeks' if question_count > 10 else '2-4 weeks',
                    'resources_needed': self._determine_resources_needed(topic, recommendations),
                    'confidence_score': 85
                }
            
            # Ensure all fields have proper values
            deep_analysis.append({
                'topic': topic,
                'question_count': len(convs),
                'root_cause': analysis_result.get('root_cause', 'Analysis needed for this topic'),
                'impact_level': analysis_result.get('impact_level', 'Medium'),
                'related_topics': analysis_result.get('related_topics', []),
                'department_impact': analysis_result.get('department_impact', {}),
                'hr_recommendations': analysis_result.get('hr_recommendations', []),
                'timeline': analysis_result.get('timeline', '1-2 weeks'),
                'resources_needed': analysis_result.get('resources_needed', 'Standard HR resources'),
                'confidence_score': analysis_result.get('confidence_score', 75)
            })
        
        return deep_analysis
    
    def _generate_meaningful_root_cause(self, topic, common_words, question_count):
        """Generate meaningful root cause analysis based on topic and question patterns"""
        topic_lower = topic.lower()
        
        if 'benefits' in topic_lower:
            if any(word in common_words for word in ['health', 'insurance', 'coverage', 'plan']):
                return "Employees are experiencing confusion about health insurance coverage details, enrollment processes, and plan options. This may indicate unclear communication during benefits enrollment or changes to existing plans."
            elif any(word in common_words for word in ['401k', 'retirement', 'pension']):
                return "Retirement benefit questions suggest employees need better understanding of 401k contributions, matching policies, and retirement planning resources."
            else:
                return f"Multiple inquiries about {topic} benefits indicate employees need clearer communication about benefit packages, eligibility criteria, and enrollment procedures."
        
        elif 'compensation' in topic_lower:
            if any(word in common_words for word in ['pay', 'salary', 'raise', 'bonus']):
                return "Compensation-related questions indicate a need for more transparency around pay structures, performance evaluations, and advancement opportunities."
            elif any(word in common_words for word in ['overtime', 'hours', 'time']):
                return "Overtime and hourly compensation questions suggest employees need clarity on time tracking, overtime policies, and pay calculation methods."
            else:
                return f"Compensation inquiries reveal employee uncertainty about pay processes, potentially affecting morale and retention."
        
        elif 'policy' in topic_lower or 'policies' in topic_lower:
            return f"Policy-related questions indicate that current {topic} documentation may be unclear, outdated, or not easily accessible to employees."
        
        elif 'time off' in topic_lower or 'pto' in topic_lower or 'vacation' in topic_lower:
            return "Time-off inquiries suggest employees need better visibility into PTO balances, accrual rates, and request procedures."
        
        elif 'training' in topic_lower:
            return "Training-related questions indicate employees are seeking professional development opportunities or clarification on mandatory training requirements."
        
        else:
            return f"The volume of questions about {topic} ({question_count} total) suggests this area requires improved communication, documentation, or process clarity to address employee concerns effectively."
    
    def _generate_meaningful_recommendations(self, topic, common_words, dept_impact):
        """Generate meaningful HR recommendations based on topic analysis"""
        recommendations = []
        topic_lower = topic.lower()
        
        if 'benefits' in topic_lower:
            recommendations = [
                f"Create comprehensive {topic} FAQ documentation addressing common questions",
                "Schedule department-specific benefits information sessions",
                "Develop visual aids and infographics to explain benefits packages",
                "Implement a benefits helpdesk or designated contact person",
                "Review and update all benefits communication materials"
            ]
        
        elif 'compensation' in topic_lower:
            recommendations = [
                "Review and clarify compensation policies and procedures",
                "Create transparent pay structure documentation",
                "Implement regular compensation Q&A sessions",
                "Develop clear guidelines for overtime and bonus calculations",
                "Provide managers with compensation communication training"
            ]
        
        elif 'policy' in topic_lower or 'policies' in topic_lower:
            recommendations = [
                f"Update and simplify {topic} policy documentation",
                "Create quick-reference guides for key policies",
                "Implement policy awareness training sessions",
                "Establish regular policy review cycles with employee input",
                "Develop an easily searchable policy database"
            ]
        
        elif 'time off' in topic_lower or 'pto' in topic_lower:
            recommendations = [
                "Implement self-service PTO tracking system",
                "Create clear PTO accrual and usage guidelines",
                "Develop automated PTO balance notifications",
                "Train managers on PTO approval procedures",
                "Publish annual PTO calendar with blackout dates"
            ]
        
        else:
            recommendations = [
                f"Develop comprehensive documentation for {topic}",
                f"Create targeted communication plan for {topic}-related information",
                f"Establish regular {topic} information sessions",
                f"Designate subject matter experts for {topic}",
                f"Review and update all {topic}-related processes"
            ]
        
        # Prioritize based on department impact
        if len(dept_impact) > 3:
            recommendations.insert(0, f"Priority: Address concerns in {', '.join(list(dept_impact.keys())[:3])} departments first")
        
        return recommendations[:5]
    
    def _infer_related_topics(self, topic):
        """Infer related topics based on the main topic"""
        topic_lower = topic.lower()
        
        if 'benefits' in topic_lower:
            return ["Health Insurance", "Retirement Plans", "Employee Wellness", "Open Enrollment"]
        elif 'compensation' in topic_lower:
            return ["Payroll", "Performance Reviews", "Overtime Policy", "Bonus Structure"]
        elif 'time off' in topic_lower or 'pto' in topic_lower:
            return ["Vacation Policy", "Sick Leave", "Holiday Schedule", "Leave of Absence"]
        elif 'policy' in topic_lower or 'policies' in topic_lower:
            return ["Employee Handbook", "Compliance", "HR Procedures", "Workplace Guidelines"]
        elif 'training' in topic_lower:
            return ["Professional Development", "Onboarding", "Skills Assessment", "Career Growth"]
        else:
            return ["HR Policies", "Employee Communication", "Workplace Culture"]
    
    def _determine_resources_needed(self, topic, recommendations):
        """Determine resources needed based on topic and recommendations"""
        resources = []
        
        if any(word in str(recommendations).lower() for word in ['training', 'session', 'workshop']):
            resources.append("Training facilitators")
        
        if any(word in str(recommendations).lower() for word in ['document', 'guide', 'FAQ']):
            resources.append("Technical writers")
        
        if any(word in str(recommendations).lower() for word in ['system', 'software', 'database']):
            resources.append("IT support")
        
        if any(word in str(recommendations).lower() for word in ['communication', 'visual', 'infographic']):
            resources.append("Communications team")
        
        if not resources:
            resources = ["HR staff", "Department managers", "Communication materials"]
        
        return ", ".join(resources)
    
    def identify_faq_opportunities(self, conversations):
        """Identify potential FAQ candidates from repeated questions"""
        if not conversations:
            return []
        
        # Group similar questions
        question_patterns = {}
        
        for conv in conversations:
            question = conv['question']
            # Simple pattern matching (could be enhanced with NLP)
            clean_q = re.sub(r'[^\w\s]', '', question.lower())
            words = clean_q.split()
            
            if len(words) > 3:
                # Create a simple pattern using key words
                key_words = ' '.join(sorted(words[:5]))
                
                if key_words not in question_patterns:
                    question_patterns[key_words] = {
                        'questions': [],
                        'employees': set(),
                        'answer_samples': []
                    }
                
                question_patterns[key_words]['questions'].append(question)
                question_patterns[key_words]['employees'].add(conv.get('employee_id', 'Unknown'))
                question_patterns[key_words]['answer_samples'].append(conv.get('answer', ''))
        
        # Identify FAQ candidates
        faq_candidates = []
        for pattern, data in question_patterns.items():
            if len(data['questions']) >= 3:  # At least 3 similar questions
                # Generate draft answer based on previous responses
                draft_answer = self._generate_draft_answer(data['answer_samples'])
                
                faq_candidates.append({
                    'question': data['questions'][0],  # Representative question
                    'frequency': len(data['questions']),
                    'unique_employees': len(data['employees']),
                    'draft_answer': draft_answer,
                    'variations': data['questions'][:3]  # Show up to 3 variations
                })
        
        return sorted(faq_candidates, key=lambda x: x['frequency'], reverse=True)
    
    def _generate_draft_answer(self, answer_samples):
        """Generate a draft answer based on previous responses"""
        if not answer_samples:
            return "No draft available"
        
        # For simplicity, use the most common answer or combine key points
        # In practice, this could use AI to synthesize the best answer
        return answer_samples[0][:200] + "..." if len(answer_samples[0]) > 200 else answer_samples[0]
    
    def generate_quick_summary(self, conversations):
        """Generate a quick summary of main issues and recommendations"""
        if not conversations:
            return {
                'main_issues': [],
                'department_needing_help': None,
                'recommended_actions': []
            }
        
        # Identify main issues
        topic_counts = Counter(conv.get('topic', 'Unknown') for conv in conversations)
        total_questions = len(conversations)
        main_issues = [
            {
                'topic': topic,
                'percentage': int((count / total_questions) * 100)
            }
            for topic, count in topic_counts.most_common(3)
        ]
        
        # Identify department needing help
        dept_counts = Counter(conv.get('department', 'Unknown') for conv in conversations)
        department_needing_help = dept_counts.most_common(1)[0][0] if dept_counts else None
        
        # Generate recommended actions
        recommended_actions = []
        for issue in main_issues:
            if issue['percentage'] > 30:
                recommended_actions.append(f"Address {issue['topic']} concerns (affecting {issue['percentage']}% of questions)")
            elif issue['percentage'] > 20:
                recommended_actions.append(f"Update documentation for {issue['topic']}")
        
        if department_needing_help:
            recommended_actions.append(f"Schedule HR office hours for {department_needing_help} department")
        
        return {
            'main_issues': main_issues,
            'department_needing_help': department_needing_help,
            'recommended_actions': recommended_actions[:3]  # Top 3 actions
        }
    
    def render_insights_button(self, conversations, timeframe="Last 7 Days"):
        """Render the AI-powered insights button and modal"""
        if st.button("🤖 AI-Powered HR Insights", type="primary"):
            with st.spinner("Generating AI insights..."):
                # Get start and end dates if custom range
                start_date = end_date = None
                if timeframe == "Custom Range":
                    start_date = st.session_state.get('custom_start_date')
                    end_date = st.session_state.get('custom_end_date')
                
                insights = self.generate_insights(conversations, timeframe, start_date, end_date)
                st.session_state.current_insights = insights
                st.session_state.show_insights_modal = True
                st.rerun()
        
        # Check if we should show the modal
        if st.session_state.show_insights_modal and st.session_state.current_insights:
            self._show_insights_modal(st.session_state.current_insights)
    
    def _show_insights_modal(self, insights):
        """Display insights in a professional dashboard layout"""
        st.markdown("---")
        
        # Add close button at the top
        if st.button("❌ Close", key="close_insights"):
            st.session_state.show_insights_modal = False
            st.session_state.current_insights = None
            st.rerun()
        
        st.header("AI-Powered HR Insights")
        
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        .insight-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #0066cc;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
        }
        .trend-up {
            color: #28a745;
            font-weight: bold;
        }
        .trend-down {
            color: #dc3545;
            font-weight: bold;
        }
        .trend-new {
            color: #007bff;
            font-weight: bold;
        }
        .section-header {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #eee;
        }
        .compact-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .compact-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }
        .compact-list li:last-child {
            border-bottom: none;
        }
        .priority-high {
            background-color: #fff5f5;
            border-left: 4px solid #dc3545;
        }
        .priority-medium {
            background-color: #fff8e6;
            border-left: 4px solid #ffc107;
        }
        .priority-low {
            background-color: #f0fff4;
            border-left: 4px solid #28a745;
        }
        .action-item {
            display: flex;
            align-items: center;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
        }
        .action-item-icon {
            margin-right: 1rem;
            font-size: 1.2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Executive Summary
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.subheader("Executive Summary")
        
        # Key metrics in a grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(insights['deep_analysis'])}</div>
                <div class="metric-label">Major Topics</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            emergency_data = insights.get('emergency_analysis', {})
            open_tickets = emergency_data.get('open_tickets', 0)
            color = "#dc3545" if open_tickets > 0 else "#28a745"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color};">{open_tickets}</div>
                <div class="metric-label">Open Emergencies</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            faq_count = len(insights['faq_opportunities'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{faq_count}</div>
                <div class="metric-label">FAQ Opportunities</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            action_count = len(insights['summary']['recommended_actions'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{action_count}</div>
                <div class="metric-label">Action Items</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Create tabs for organized content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "🔍 Deep Topic Analysis", 
            "❓ FAQ Candidates", 
            "🚨 Emergency Analysis", 
            "📋 Action Items"
        ])
        
        with tab1:
            # Dashboard view with trending topics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Trending Topics Overview</div>', unsafe_allow_html=True)
                
                # Create topic trend visualization
                if 'time_series_data' in insights['topic_trends'] and insights['topic_trends']['time_series_data']:
                    time_series_data = insights['topic_trends']['time_series_data']
                    
                    # Create line chart for topic trends
                    fig = go.Figure()
                    
                    for topic, data in list(time_series_data.items())[:5]:  # Show top 5 topics
                        fig.add_trace(go.Scatter(
                            x=data['dates'],
                            y=data['counts'],
                            mode='lines+markers',
                            name=topic,
                            hovertemplate='%{x}<br>%{y} questions<extra></extra>'
                        ))
                    
                    fig.update_layout(
                        title='Topic Trends Over Time',
                        xaxis_title='Date',
                        yaxis_title='Number of Questions',
                        height=400,
                        hovermode='x unified',
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No topic trend data available")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">New Topics This Week</div>', unsafe_allow_html=True)
                
                if insights['topic_trends']['new_topics']:
                    for topic in insights['topic_trends']['new_topics']:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                            <span>{topic['topic']}</span>
                            <span style="background-color: #007bff; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem;">
                                {topic['count']} questions
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No new topics this week")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # Deep Topic Analysis with HR Recommendations
            for analysis in insights['deep_analysis']:
                impact_color = {
                    'High': 'priority-high',
                    'Medium': 'priority-medium',
                    'Low': 'priority-low'
                }.get(analysis['impact_level'], 'priority-medium')
                
                with st.expander(
                    f"{analysis['topic']} - {analysis['question_count']} questions", 
                    expanded=analysis['impact_level'] == 'High'
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="action-item {impact_color}">
                            <div>
                                <strong>Root Cause:</strong><br>
                                {analysis['root_cause']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if analysis['related_topics']:
                            st.markdown("**Related Topics:**")
                            topics_str = ", ".join(analysis['related_topics'])
                            st.markdown(f"_{topics_str}_")
                        
                        st.markdown("**HR Recommendations:**")
                        for i, rec in enumerate(analysis['hr_recommendations'], 1):
                            st.markdown(f"{i}. {rec}")
                        
                        st.markdown(f"**Timeline:** {analysis['timeline']}")
                        st.markdown(f"**Resources Needed:** {analysis['resources_needed']}")
                    
                    with col2:
                        st.markdown(f"**Impact Level:** {analysis['impact_level']}")
                        st.markdown(f"**Confidence:** {analysis['confidence_score']}%")
                        
                        department_impact = analysis.get('department_impact', {})
                        if isinstance(department_impact, dict) and department_impact:
                            st.markdown("**Department Impact:**")
                            for dept, impact in department_impact.items():
                                st.markdown(f"- {dept}: {impact}")
        
        with tab3:
            # FAQ Opportunities
            if insights['faq_opportunities']:
                for i, faq in enumerate(insights['faq_opportunities'][:10]):
                    with st.expander(f"FAQ #{i+1}: {faq['question'][:100]}..."):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Frequency:** {faq['frequency']} times")
                            st.markdown(f"**Unique Employees:** {faq['unique_employees']}")
                            
                            st.markdown("**Question Variations:**")
                            for j, var in enumerate(faq['variations'], 1):
                                st.markdown(f"{j}. {var}")
                            
                            st.markdown("**Draft Answer:**")
                            st.info(faq['draft_answer'])
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-value">{faq['frequency']}</div>
                                <div class="metric-label">Times Asked</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No FAQ opportunities identified")
        
        with tab4:
            # Emergency Analysis
            emergency_data = insights.get('emergency_analysis', {})
            
            if emergency_data.get('open_tickets', 0) > 0:
                # Critical Alerts
                critical_tickets = emergency_data.get('critical_tickets', [])
                if critical_tickets:
                    st.error(f"⚠️ {len(critical_tickets)} CRITICAL EMERGENCY TICKETS")
                    for ticket in critical_tickets[:3]:
                        st.markdown(f"""
                        <div class="action-item priority-high">
                            <div class="action-item-icon">🚨</div>
                            <div>
                                <strong>{ticket['employee_name']} - {ticket['department']}</strong><br>
                                Categories: {', '.join(ticket['categories'])}<br>
                                <small>Submitted: {ticket['timestamp']}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Emergency Metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{emergency_data['total_tickets']}</div>
                        <div class="metric-label">Total Emergencies</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    urgency = emergency_data['urgency_analysis']
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 1.2rem;">
                            <span style="color: #dc3545;">{urgency['critical_count']} Critical</span><br>
                            <span style="color: #ffc107;">{urgency['high_count']} High</span><br>
                            <span style="color: #28a745;">{urgency['medium_count']} Medium</span>
                        </div>
                        <div class="metric-label">By Urgency</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    avg_time = emergency_data['avg_resolution_time']
                    if avg_time > 0:
                        time_display = f"{avg_time:.1f} hrs" if avg_time >= 1 else f"{int(avg_time * 60)} min"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{time_display}</div>
                            <div class="metric-label">Avg Resolution Time</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Pattern Analysis
                if emergency_data['category_patterns'] or emergency_data['department_impact']:
                    st.markdown("### Emergency Patterns")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if emergency_data['category_patterns']:
                            st.markdown("**Issues by Category:**")
                            for pattern in emergency_data['category_patterns']:
                                severity_color = "priority-high" if pattern['severity'] == 'high' else "priority-medium"
                                st.markdown(f"""
                                <div class="action-item {severity_color}" style="margin-bottom: 0.5rem;">
                                    <div>
                                        <strong>{pattern['category']}</strong><br>
                                        {pattern['count']} cases
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    with col2:
                        if emergency_data['department_impact']:
                            st.markdown("**Departments Affected:**")
                            for dept in emergency_data['department_impact']:
                                severity_color = {
                                    'high': 'priority-high',
                                    'medium': 'priority-medium',
                                    'low': 'priority-low'
                                }.get(dept['severity'], 'priority-low')
                                
                                st.markdown(f"""
                                <div class="action-item {severity_color}" style="margin-bottom: 0.5rem;">
                                    <div>
                                        <strong>{dept['department']}</strong><br>
                                        {dept['count']} emergencies
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.success("✅ No emergency tickets at this time")
        
        with tab5:
            # Action Items
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Recommended Actions</div>', unsafe_allow_html=True)
            
            for i, action in enumerate(insights['summary']['recommended_actions'], 1):
                icon = "🎯" if "Address" in action else "📝" if "Update" in action else "📅"
                priority = "priority-high" if "Address" in action else "priority-medium"
                
                st.markdown(f"""
                <div class="action-item {priority}">
                    <div class="action-item-icon">{icon}</div>
                    <div>{action}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Export Options
            st.markdown("### Export Options")
            
            # Create a form to prevent page reload on button clicks
            with st.form("export_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    export_pdf = st.form_submit_button("📄 Export PDF Report", use_container_width=True)
                
                with col2:
                    export_excel = st.form_submit_button("📊 Export Excel", use_container_width=True)
            
            # Handle exports outside the form
            if export_pdf:
                pdf_bytes = self._generate_pdf_report(insights)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"hr_insights_report_{timestamp}.pdf",
                    mime="application/pdf",
                    key=f"pdf_download_{timestamp}"
                )
            
            if export_excel:
                excel_bytes = self._generate_excel_report(insights)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Download Excel Report",
                    data=excel_bytes,
                    file_name=f"hr_insights_report_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"excel_download_{timestamp}"
                )
    
    def _generate_pdf_report(self, insights):
        """Generate PDF report with insights data"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'AI-Powered HR Insights Report', 0, 1, 'C')
        
        # Generation date
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Executive Summary', 0, 1)
        
        pdf.set_font('Arial', '', 12)
        summary_text = f"""
Major Topics: {len(insights['deep_analysis'])}
Open Emergencies: {insights.get('emergency_analysis', {}).get('open_tickets', 0)}
FAQ Opportunities: {len(insights['faq_opportunities'])}
Action Items: {len(insights['summary']['recommended_actions'])}
"""
        for line in summary_text.strip().split('\n'):
            pdf.cell(0, 8, line, 0, 1)
        pdf.ln(5)
        
        # Deep Topic Analysis
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Deep Topic Analysis', 0, 1)
        
        for i, analysis in enumerate(insights['deep_analysis'], 1):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, f"{i}. {analysis['topic']}", 0, 1)
            
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 8, f"Questions: {analysis['question_count']}")
            pdf.multi_cell(0, 8, f"Impact Level: {analysis['impact_level']}")
            pdf.multi_cell(0, 8, f"Root Cause: {analysis['root_cause']}")
            
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "HR Recommendations:", 0, 1)
            pdf.set_font('Arial', '', 11)
            for j, rec in enumerate(analysis['hr_recommendations'], 1):
                pdf.multi_cell(0, 8, f"{j}. {rec}")
            
            pdf.ln(5)
        
        # Emergency Analysis
        emergency_data = insights.get('emergency_analysis', {})
        if emergency_data.get('open_tickets', 0) > 0:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Emergency Analysis', 0, 1)
            
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 8, f"Open Tickets: {emergency_data['open_tickets']}", 0, 1)
            
            if emergency_data.get('critical_tickets'):
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, "Critical Tickets:", 0, 1)
                pdf.set_font('Arial', '', 11)
                
                for ticket in emergency_data['critical_tickets']:
                    pdf.multi_cell(0, 8, f"- {ticket['employee_name']} ({ticket['department']}) - {', '.join(ticket['categories'])}")
                    pdf.multi_cell(0, 8, f"  Submitted: {ticket['timestamp']}")
                    pdf.ln(3)
        
        # FAQ Opportunities
        if insights['faq_opportunities']:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'FAQ Opportunities', 0, 1)
            
            for i, faq in enumerate(insights['faq_opportunities'][:10], 1):
                pdf.set_font('Arial', 'B', 12)
                pdf.multi_cell(0, 8, f"{i}. {faq['question']}")
                
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 8, f"Frequency: {faq['frequency']} times", 0, 1)
                pdf.cell(0, 8, f"Unique Employees: {faq['unique_employees']}", 0, 1)
                pdf.ln(5)
        
        # Recommended Actions
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Recommended Actions', 0, 1)
        
        for i, action in enumerate(insights['summary']['recommended_actions'], 1):
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 8, f"{i}. {action}")
            pdf.ln(3)
        
        # Return PDF bytes
        return pdf.output(dest='S').encode('latin-1')
    
    def _generate_excel_report(self, insights):
        """Generate Excel report with insights data"""
        output = BytesIO()
        
        # Create Excel writer
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Executive Summary
            summary_data = {
                'Metric': ['Major Topics', 'Open Emergencies', 'FAQ Opportunities', 'Action Items'],
                'Count': [
                    len(insights['deep_analysis']),
                    insights.get('emergency_analysis', {}).get('open_tickets', 0),
                    len(insights['faq_opportunities']),
                    len(insights['summary']['recommended_actions'])
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # Deep Topic Analysis
            topic_data = []
            for analysis in insights['deep_analysis']:
                topic_data.append({
                    'Topic': analysis['topic'],
                    'Question Count': analysis['question_count'],
                    'Impact Level': analysis['impact_level'],
                    'Root Cause': analysis['root_cause'],
                    'Timeline': analysis['timeline'],
                    'Resources Needed': analysis['resources_needed'],
                    'Confidence Score': analysis['confidence_score']
                })
            
            df_topics = pd.DataFrame(topic_data)
            df_topics.to_excel(writer, sheet_name='Topic Analysis', index=False)
            
            # HR Recommendations
            recommendations_data = []
            for i, analysis in enumerate(insights['deep_analysis']):
                for j, rec in enumerate(analysis['hr_recommendations']):
                    recommendations_data.append({
                        'Topic': analysis['topic'],
                        'Recommendation #': j + 1,
                        'Recommendation': rec,
                        'Impact Level': analysis['impact_level']
                    })
            
            df_recommendations = pd.DataFrame(recommendations_data)
            df_recommendations.to_excel(writer, sheet_name='HR Recommendations', index=False)
            
            # Emergency Analysis
            emergency_data = insights.get('emergency_analysis', {})
            if emergency_data.get('open_tickets', 0) > 0:
                emergency_tickets = []
                for ticket in emergency_data.get('critical_tickets', []):
                    emergency_tickets.append({
                        'Employee': ticket['employee_name'],
                        'Department': ticket['department'],
                        'Categories': ', '.join(ticket['categories']),
                        'Urgency': ticket['urgency'],
                        'Timestamp': ticket['timestamp']
                    })
                
                if emergency_tickets:
                    df_emergency = pd.DataFrame(emergency_tickets)
                    df_emergency.to_excel(writer, sheet_name='Emergency Tickets', index=False)
            
            # FAQ Opportunities
            if insights['faq_opportunities']:
                faq_data = []
                for faq in insights['faq_opportunities']:
                    faq_data.append({
                        'Question': faq['question'],
                        'Frequency': faq['frequency'],
                        'Unique Employees': faq['unique_employees'],
                        'Draft Answer': faq['draft_answer']
                    })
                
                df_faq = pd.DataFrame(faq_data)
                df_faq.to_excel(writer, sheet_name='FAQ Opportunities', index=False)
            
            # Action Items
            action_data = []
            for i, action in enumerate(insights['summary']['recommended_actions'], 1):
                action_data.append({
                    'Priority': i,
                    'Action Item': action,
                    'Status': 'To Do'
                })
            
            df_actions = pd.DataFrame(action_data)
            df_actions.to_excel(writer, sheet_name='Action Items', index=False)
            
            # Adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(df_summary.columns if sheet_name == 'Executive Summary' else 
                                      df_topics.columns if sheet_name == 'Topic Analysis' else
                                      df_recommendations.columns if sheet_name == 'HR Recommendations' else
                                      df_faq.columns if sheet_name == 'FAQ Opportunities' else
                                      df_actions.columns):
                    column_width = max(len(str(col)), 15)
                    worksheet.set_column(i, i, column_width)
        
        output.seek(0)
        return output.getvalue()