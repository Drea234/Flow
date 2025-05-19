from collections import Counter
from datetime import datetime
import pandas as pd

class SmartTopicAnalyzer:
    """Enhanced analyzer that prevents topic inflation and provides better insights"""
    
    def analyze_topics(self, conversations):
        """Analyze topics with employee distribution"""
        try:
            topic_stats = {}
            
            # Process each conversation
            for conv in conversations:
                topic = conv.get('topic', 'Unknown')
                employee_id = conv.get('employee_id', 'Unknown')
                department = conv.get('department', 'Unknown')
                
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        'employee_ids': set(),
                        'questions': [],
                        'employee_question_counts': {},
                        'departments': set(),
                        'sentiment_scores': [],
                        'dates': []
                    }
                
                topic_stats[topic]['employee_ids'].add(employee_id)
                topic_stats[topic]['questions'].append(conv.get('question', ''))
                topic_stats[topic]['departments'].add(department)
                
                # Add sentiment score if available
                sentiment_score = conv.get('sentiment_score', 0)
                if isinstance(sentiment_score, (int, float)):
                    topic_stats[topic]['sentiment_scores'].append(sentiment_score)
                
                # Add date for trend analysis
                date_str = conv.get('date_time', '')
                if date_str:
                    topic_stats[topic]['dates'].append(date_str)
                
                # Track per-employee question count
                if employee_id not in topic_stats[topic]['employee_question_counts']:
                    topic_stats[topic]['employee_question_counts'][employee_id] = 0
                topic_stats[topic]['employee_question_counts'][employee_id] += 1
            
            # Calculate scores and classify
            topic_analysis = []
            for topic, data in topic_stats.items():
                score_data = self.calculate_topic_score(data)
                
                # Classify based on unique employees
                if score_data['unique_askers'] >= 10:
                    category = 'company_wide'
                elif score_data['unique_askers'] >= 3:
                    category = 'department_level'
                else:
                    category = 'individual'
                
                # Calculate average sentiment
                sentiment_scores = data['sentiment_scores']
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                
                topic_analysis.append({
                    'topic': topic,
                    'category': category,
                    'score': score_data['score'],
                    'unique_askers': score_data['unique_askers'],
                    'total_questions': score_data['total_questions'],
                    'departments': list(data['departments']),
                    'is_individual_concern': score_data['is_individual_concern'],
                    'avg_sentiment': avg_sentiment,
                    'max_questions_per_employee': score_data['max_questions_per_employee'],
                    'dates': data['dates']
                })
            
            return sorted(topic_analysis, key=lambda x: x['score'], reverse=True)
        except Exception as e:
            print(f"Error analyzing topics: {e}")
            return []
    
    def calculate_topic_score(self, topic_data):
        """Calculate weighted score to prevent individual employee skewing"""
        try:
            unique_employees = len(topic_data.get('employee_ids', set()))
            total_questions = len(topic_data.get('questions', []))
            
            if total_questions == 0:
                return {
                    'score': 0,
                    'unique_askers': 0,
                    'total_questions': 0,
                    'is_individual_concern': False,
                    'max_questions_per_employee': 0
                }
            
            # Base score: unique employees asking about the topic
            base_score = unique_employees
            
            # Additional weight for multiple questions from different employees
            diversity_factor = unique_employees / max(1, total_questions)
            
            # Penalize when one employee dominates the topic
            employee_question_counts = topic_data.get('employee_question_counts', {})
            max_questions_per_employee = max(employee_question_counts.values()) if employee_question_counts else 0
            dominance_penalty = 1 - (max_questions_per_employee / total_questions) if total_questions > 0 else 1
            
            # Final score
            weighted_score = base_score * diversity_factor * dominance_penalty
            
            return {
                'score': weighted_score,
                'unique_askers': unique_employees,
                'total_questions': total_questions,
                'is_individual_concern': unique_employees == 1,
                'max_questions_per_employee': max_questions_per_employee
            }
        except Exception as e:
            print(f"Error calculating topic score: {e}")
            return {
                'score': 0,
                'unique_askers': 0,
                'total_questions': 0,
                'is_individual_concern': False,
                'max_questions_per_employee': 0
            }
    
    def generate_alerts(self, topic_analysis):
        """Generate alerts based on topic analysis"""
        try:
            alerts = []
            
            for topic in topic_analysis:
                if topic.get('is_individual_concern', False) and topic.get('total_questions', 0) > 5:
                    alerts.append({
                        'type': 'individual_follow_up',
                        'message': f"Employee needs personal support with {topic.get('topic', 'unknown topic')}",
                        'priority': 'medium',
                        'details': f"{topic.get('total_questions', 0)} questions from 1 employee"
                    })
                elif topic.get('category') == 'company_wide' and topic.get('avg_sentiment', 0) < -0.3:
                    alerts.append({
                        'type': 'urgent_company_issue',
                        'message': f"Widespread negative sentiment about {topic.get('topic', 'unknown topic')}",
                        'priority': 'high',
                        'details': f"{topic.get('unique_askers', 0)} employees expressing concerns"
                    })
                elif topic.get('category') == 'department_level' and topic.get('total_questions', 0) > 10:
                    alerts.append({
                        'type': 'department_attention',
                        'message': f"Department issue with {topic.get('topic', 'unknown topic')}",
                        'priority': 'medium',
                        'details': f"Affecting {', '.join(topic.get('departments', ['Unknown']))}"
                    })
            
            return alerts
        except Exception as e:
            print(f"Error generating alerts: {e}")
            return []