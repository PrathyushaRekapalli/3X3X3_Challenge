from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import json
import os
import openai
from dotenv import load_dotenv
import pandas as pd
import random
import uuid
import re
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter
import time

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Data storage (in production, use a database)
DATA_FILE = 'health_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def analyze_typing_metrics(text, typing_time):
    """Analyze typing patterns for stress assessment"""
    if not text or typing_time <= 0:
        return {
            'wpm': 0,
            'accuracy': 100,
            'stress_indicators': [],
            'stress_score': 1
        }
    
    words = len(text.split())
    typing_time_minutes = typing_time / 60000  # Convert ms to minutes
    wpm = words / typing_time_minutes if typing_time_minutes > 0 else 0
    
    # Analyze text complexity and patterns
    sentences = text.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    
    # Count potential typos/corrections (simple heuristic)
    repeated_chars = len(re.findall(r'(.)\1{2,}', text))
    short_words = len([w for w in text.split() if len(w) < 3])
    
    # Stress indicators
    stress_indicators = []
    stress_score = 1  # Scale 1-5
    
    if wpm < 20:
        stress_indicators.append("Slow typing speed may indicate fatigue or stress")
        stress_score += 1
    elif wpm > 80:
        stress_indicators.append("Very fast typing may indicate rushing or anxiety")
        stress_score += 0.5
    
    if repeated_chars > 2:
        stress_indicators.append("Multiple repeated characters detected")
        stress_score += 0.5
    
    if avg_sentence_length < 5:
        stress_indicators.append("Short sentences may indicate rushed thinking")
        stress_score += 0.5
    
    if short_words / len(text.split()) > 0.4:
        stress_indicators.append("High proportion of short words")
        stress_score += 0.5
    
    # Calculate approximate accuracy (simplified)
    accuracy = max(0, 100 - (repeated_chars * 5) - (short_words * 2))
    
    return {
        'wpm': round(wpm, 1),
        'accuracy': round(accuracy, 1),
        'stress_indicators': stress_indicators,
        'stress_score': min(stress_score, 5),
        'word_count': words,
        'avg_sentence_length': round(avg_sentence_length, 1)
    }

def perform_sentiment_analysis(text):
    """Analyze sentiment using OpenAI"""
    if not text or len(text.strip()) < 10:
        return {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'emotional_indicators': []
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Analyze the sentiment and emotional state of the text. Return a JSON response with sentiment (positive/negative/neutral), confidence (0-1), and emotional_indicators (array of strings describing emotional cues)."
                },
                {"role": "user", "content": f"Analyze this text: {text}"}
            ],
            temperature=0.3
        )
        
        # Parse the response (simplified - in production, use proper JSON parsing)
        content = response.choices[0].message.content
        
        # Extract sentiment indicators
        positive_words = ['good', 'great', 'excellent', 'happy', 'productive', 'energetic', 'motivated']
        negative_words = ['tired', 'stressed', 'anxious', 'overwhelmed', 'frustrated', 'difficult', 'exhausted']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative' 
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        emotional_indicators = []
        if positive_count > 0:
            emotional_indicators.append(f"Positive language detected ({positive_count} indicators)")
        if negative_count > 0:
            emotional_indicators.append(f"Negative language detected ({negative_count} indicators)")
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'emotional_indicators': emotional_indicators
        }
        
    except Exception as e:
        # Fallback analysis
        return {
            'sentiment': 'neutral',
            'confidence': 0.5,
            'emotional_indicators': ['Automated analysis unavailable']
        }

def generate_sample_company_data():
    """Generate comprehensive sample data for company dashboard"""
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Design', 'Finance', 'Operations', 'Customer Success']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    projects = ['Project Alpha', 'Project Beta', 'Project Gamma', 'Project Delta', 'Project Epsilon']
    
    # Generate historical data for the past 3 months
    company_data = {
        'departments': {},
        'regions': {},
        'projects': {},
        'trends': {
            'dates': [],
            'overall_mood': [],
            'productivity_score': [],
            'stress_levels': [],
            'collaboration_score': []
        }
    }
    
    # Generate trends data
    base_date = datetime.now() - timedelta(days=90)
    for i in range(90):
        date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        company_data['trends']['dates'].append(date)
        
        # Simulate realistic trends with some variation
        mood_base = 3.2 + 0.3 * random.random() + 0.1 * (i / 90)  # Slight improvement over time
        company_data['trends']['overall_mood'].append(round(mood_base, 2))
        
        productivity_base = 72 + 8 * random.random() + 5 * (i / 90)
        company_data['trends']['productivity_score'].append(round(productivity_base, 1))
        
        stress_base = 2.8 - 0.2 * random.random() - 0.1 * (i / 90)  # Decreasing stress
        company_data['trends']['stress_levels'].append(round(max(1, stress_base), 2))
        
        collab_base = 3.5 + 0.4 * random.random()
        company_data['trends']['collaboration_score'].append(round(collab_base, 2))
    
    # Department data
    for dept in departments:
        company_data['departments'][dept] = {
            'employee_count': random.randint(15, 45),
            'avg_mood': round(3.0 + random.random() * 1.5, 2),
            'avg_productivity': round(70 + random.random() * 20, 1),
            'avg_stress': round(2.0 + random.random() * 2, 2),
            'collaboration_score': round(3.0 + random.random() * 1.8, 2),
            'top_concerns': random.sample(['Work-life balance', 'Workload', 'Communication', 'Tools', 'Management'], 2)
        }
    
    # Region data
    for region in regions:
        company_data['regions'][region] = {
            'employee_count': random.randint(50, 150),
            'avg_mood': round(3.0 + random.random() * 1.5, 2),
            'avg_productivity': round(70 + random.random() * 20, 1),
            'peak_hours': f"{random.randint(9, 11)}:00 - {random.randint(14, 17)}:00",
            'cultural_factors': random.choice(['High collaboration', 'Independent work style', 'Mixed preferences'])
        }
    
    # Project data
    for project in projects:
        company_data['projects'][project] = {
            'team_size': random.randint(5, 25),
            'avg_mood': round(3.0 + random.random() * 1.5, 2),
            'productivity_trend': random.choice(['Increasing', 'Stable', 'Decreasing']),
            'deadline_pressure': random.choice(['Low', 'Medium', 'High']),
            'collaboration_quality': round(3.0 + random.random() * 1.8, 2)
        }
    
    return company_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_in', methods=['GET', 'POST'])
def check_in():
    if request.method == 'POST':
        user_id = request.form.get('user_id', 'default_user')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check if user already submitted today
        data = load_data()
        if user_id in data and today in data[user_id]:
            return render_template('check_in.html', 
                                 error="You have already completed your check-in for today. Come back tomorrow!")
        
        # Get form data
        mood = request.form.get('mood', 'Neutral')
        sleep_hours = float(request.form.get('sleep_hours', 7))
        work_screen_time = float(request.form.get('work_screen_time', 8))
        leisure_screen_time = float(request.form.get('leisure_screen_time', 3))
        physical_activity = request.form.get('physical_activity', 'No')
        water_glasses = int(request.form.get('water_glasses', 4))
        breaks_taken = int(request.form.get('breaks_taken', 2))
        outdoors_time = request.form.get('outdoors_time', 'No')
        stress_level = request.form.get('stress_level', 'Moderate')
        social_interaction = request.form.get('social_interaction', 'Moderate')
        additional_notes = request.form.get('additional_notes', '')
        
        # New fields
        typing_time = int(request.form.get('typing_time', 0))  # in milliseconds
        work_satisfaction = request.form.get('work_satisfaction', 'Neutral')
        energy_level = request.form.get('energy_level', 'Moderate')
        focus_quality = request.form.get('focus_quality', 'Good')
        
        # Analyze typing metrics and sentiment
        typing_analysis = analyze_typing_metrics(additional_notes, typing_time)
        sentiment_analysis = perform_sentiment_analysis(additional_notes)
        
        # Initialize user data if needed
        if user_id not in data:
            data[user_id] = {}
        
        # Store today's data
        data[user_id][today] = {
            'mood': mood,
            'sleep_hours': sleep_hours,
            'work_screen_time': work_screen_time,
            'leisure_screen_time': leisure_screen_time,
            'total_screen_time': work_screen_time + leisure_screen_time,
            'physical_activity': physical_activity,
            'water_glasses': water_glasses,
            'breaks_taken': breaks_taken,
            'outdoors_time': outdoors_time,
            'stress_level': stress_level,
            'social_interaction': social_interaction,
            'additional_notes': additional_notes,
            'work_satisfaction': work_satisfaction,
            'energy_level': energy_level,
            'focus_quality': focus_quality,
            'typing_analysis': typing_analysis,
            'sentiment_analysis': sentiment_analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate comprehensive recommendations
        recommendations = analyze_comprehensive_health_data(data[user_id][today])
        data[user_id][today]['recommendations'] = recommendations
        
        save_data(data)
        session['recommendations'] = recommendations
        
        return redirect(url_for('recommendations'))
    
    return render_template('check_in.html')

# def analyze_comprehensive_health_data(health_data):
#     """Generate comprehensive recommendations using all available data"""
    
#     prompt = f"""
#     Analyze this comprehensive health and productivity data for a remote worker:
    
#     BASIC METRICS:
#     - Mood: {health_data['mood']}
#     - Sleep: {health_data['sleep_hours']} hours
#     - Work screen time: {health_data['work_screen_time']} hours
#     - Leisure screen time: {health_data['leisure_screen_time']} hours
#     - Physical activity (45+ min): {health_data['physical_activity']}
#     - Water intake: {health_data['water_glasses']} glasses
#     - Movement breaks: {health_data['breaks_taken']}
#     - Outdoor time: {health_data['outdoors_time']}
#     - Stress level: {health_data['stress_level']}
#     - Social interaction: {health_data['social_interaction']}
    
#     PRODUCTIVITY METRICS:
#     - Work satisfaction: {health_data['work_satisfaction']}
#     - Energy level: {health_data['energy_level']}
#     - Focus quality: {health_data['focus_quality']}
    
#     TYPING ANALYSIS:
#     - Words per minute: {health_data['typing_analysis']['wpm']}
#     - Typing accuracy: {health_data['typing_analysis']['accuracy']}%
#     - Stress indicators: {health_data['typing_analysis']['stress_indicators']}
#     - Stress score: {health_data['typing_analysis']['stress_score']}/5
    
#     SENTIMENT ANALYSIS:
#     - Overall sentiment: {health_data['sentiment_analysis']['sentiment']}
#     - Confidence: {health_data['sentiment_analysis']['confidence']}
#     - Emotional indicators: {health_data['sentiment_analysis']['emotional_indicators']}
    
#     NOTES: {health_data['additional_notes']}
    
#     Provide 4-6 specific, actionable recommendations prioritized by importance. 
#     Consider the interconnection between physical health, mental well-being, and productivity.
#     Format as a numbered list with brief explanations.
#     """
    
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a comprehensive health and productivity coach for remote workers. Provide personalized, actionable advice considering physical, mental, and productivity metrics."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         return generate_fallback_recommendations(health_data)

def analyze_comprehensive_health_data(health_data):
    """Generate comprehensive recommendations using all available data"""
    
    prompt = f"""
    Analyze this comprehensive health and productivity data for a remote worker:
    
    BASIC METRICS:
    - Mood: {health_data['mood']}
    - Sleep: {health_data['sleep_hours']} hours
    - Work screen time: {health_data['work_screen_time']} hours
    - Leisure screen time: {health_data['leisure_screen_time']} hours
    - Physical activity (45+ min): {health_data['physical_activity']}
    - Water intake: {health_data['water_glasses']} glasses
    - Movement breaks: {health_data['breaks_taken']}
    - Outdoor time: {health_data['outdoors_time']}
    - Stress level: {health_data['stress_level']}
    - Social interaction: {health_data['social_interaction']}
    
    PRODUCTIVITY METRICS:
    - Work satisfaction: {health_data['work_satisfaction']}
    - Energy level: {health_data['energy_level']}
    - Focus quality: {health_data['focus_quality']}
    
    TYPING ANALYSIS:
    - Words per minute: {health_data['typing_analysis']['wpm']}
    - Typing accuracy: {health_data['typing_analysis']['accuracy']}%
    - Stress indicators: {health_data['typing_analysis']['stress_indicators']}
    - Stress score: {health_data['typing_analysis']['stress_score']}/5
    
    SENTIMENT ANALYSIS:
    - Overall sentiment: {health_data['sentiment_analysis']['sentiment']}
    - Confidence: {health_data['sentiment_analysis']['confidence']}
    - Emotional indicators: {health_data['sentiment_analysis']['emotional_indicators']}
    
    NOTES: {health_data['additional_notes']}
    
    Provide 4-6 specific, actionable recommendations prioritized by importance. 
    Format as numbered list (1., 2., 3., etc.) with clear titles using this format:
    
    1. **Title**: Description and actionable advice.
    2. **Title**: Description and actionable advice.
    
    Focus on the most impactful changes they can make.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a comprehensive health and productivity coach for remote workers. Provide personalized, actionable advice. Use numbered lists with bold titles for clarity."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return generate_fallback_recommendations(health_data)

def generate_fallback_recommendations(health_data):
    """Generate fallback recommendations if API fails"""
    recommendations = []
    
    if health_data['sleep_hours'] < 7:
        recommendations.append("**Improve Sleep Quality**: Aim for 7-9 hours of sleep nightly. Your current sleep may be affecting mood and productivity.")
    
    if health_data['total_screen_time'] > 10:
        recommendations.append("**Reduce Screen Time**: Consider the 20-20-20 rule - every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    if health_data['physical_activity'] == 'No':
        recommendations.append("**Add Physical Activity**: Even 30 minutes of movement can significantly boost mood and energy levels.")
    
    if health_data['water_glasses'] < 6:
        recommendations.append("**Increase Hydration**: Aim for 8+ glasses of water daily to maintain energy and focus.")
    
    if health_data['typing_analysis']['stress_score'] > 3:
        recommendations.append("**Manage Typing Stress**: Take more frequent breaks and practice mindful typing to reduce stress indicators.")
    
    return "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])

def generate_fallback_recommendations(health_data):
    """Generate fallback recommendations if API fails"""
    recommendations = []
    
    if health_data['sleep_hours'] < 7:
        recommendations.append("**Improve Sleep Quality**: Aim for 7-9 hours of sleep nightly. Your current sleep may be affecting mood and productivity.")
    
    if health_data['total_screen_time'] > 10:
        recommendations.append("**Reduce Screen Time**: Consider the 20-20-20 rule - every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    if health_data['physical_activity'] == 'No':
        recommendations.append("**Add Physical Activity**: Even 30 minutes of movement can significantly boost mood and energy levels.")
    
    if health_data['water_glasses'] < 6:
        recommendations.append("**Increase Hydration**: Aim for 8+ glasses of water daily to maintain energy and focus.")
    
    if health_data['typing_analysis']['stress_score'] > 3:
        recommendations.append("**Manage Typing Stress**: Take more frequent breaks and practice mindful typing to reduce stress indicators.")
    
    return "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])

@app.route('/recommendations')
def recommendations():
    recommendations = session.get('recommendations', 'No recommendations available')
    return render_template('recommendations.html', recommendations=recommendations)

# @app.route('/dashboard')
# def dashboard():
#     user_id = request.args.get('user_id', 'default_user')
#     data = load_data()
    
#     if user_id not in data or not data[user_id]:
#         # Generate sample historical data for demo
#         data[user_id] = generate_sample_user_data()
#         save_data(data)
    
#     # Process data for visualization
#     chart_data = process_user_data_for_charts(data[user_id])
#     chart_json = json.dumps(chart_data)
    
#     return render_template('dashboard.html', 
#                           has_data=True,
#                           chart_data=chart_json)
@app.route('/dashboard')
@app.route('/dashboard')
def dashboard():
    user_id = request.args.get('user_id', 'default_user')
    data = load_data()
    
    # Always return the template, let JavaScript handle data loading
    chart_data = None
    has_data = False
    
    if user_id in data and data[user_id]:
        # Process real data
        chart_data = process_user_data_for_charts(data[user_id])
        has_data = True
    
    return render_template('dashboard.html', 
                          has_data=has_data,
                          chart_data=json.dumps(chart_data) if chart_data else None)

def generate_sample_user_data():
    """Generate sample data when no real data exists"""
    sample_data = {
        'dates': [],
        'moods': [],
        'sleep_hours': [],
        'work_screen': [],
        'leisure_screen': [],
        'physical_activity': [],
        'water_glasses': [],
        'breaks_taken': [],
        'outdoors_time': [],
        'stress_levels': [],
        'social_interaction': [],
        'work_satisfaction': [],
        'energy_levels': [],
        'focus_quality': []
    }
    
    # Generate 30 days of sample data
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        sample_data['dates'].append(date)
        sample_data['moods'].append(random.randint(2, 5))
        sample_data['sleep_hours'].append(round(random.uniform(5.5, 9.0), 1))
        sample_data['work_screen'].append(round(random.uniform(6, 12), 1))
        sample_data['leisure_screen'].append(round(random.uniform(1, 5), 1))
        sample_data['physical_activity'].append(random.randint(0, 1))
        sample_data['water_glasses'].append(random.randint(3, 10))
        sample_data['breaks_taken'].append(random.randint(1, 8))
        sample_data['outdoors_time'].append(random.randint(0, 1))
        sample_data['stress_levels'].append(random.randint(1, 5))
        sample_data['social_interaction'].append(random.randint(1, 4))
        sample_data['work_satisfaction'].append(random.randint(1, 5))
        sample_data['energy_levels'].append(random.randint(1, 5))
        sample_data['focus_quality'].append(random.randint(1, 5))
    
    # Reverse to show chronological order
    for key in sample_data:
        sample_data[key].reverse()
    
    return sample_data

def process_user_data_for_charts(user_data):
    """Process user data for chart visualization"""
    chart_data = {
        'dates': [],
        'moods': [],
        'sleep_hours': [],
        'work_screen': [],
        'leisure_screen': [],
        'physical_activity': [],
        'water_glasses': [],
        'breaks_taken': [],
        'outdoors_time': [],
        'stress_levels': [],
        'social_interaction': [],
        'work_satisfaction': [],
        'energy_levels': [],
        'focus_quality': []
    }
    
    # Mapping dictionaries
    mood_map = {'Excellent': 5, 'Good': 4, 'Neutral': 3, 'Low': 2, 'Poor': 1}
    stress_map = {'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
    social_map = {'None': 1, 'Little': 2, 'Moderate': 3, 'Significant': 4}
    satisfaction_map = {'Very Low': 1, 'Low': 2, 'Neutral': 3, 'High': 4, 'Very High': 5}
    energy_map = {'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
    focus_map = {'Poor': 1, 'Fair': 2, 'Good': 3, 'Very Good': 4, 'Excellent': 5}
    yes_no_map = {'Yes': 1, 'No': 0}
    
    for date, entry in sorted(user_data.items()):
        chart_data['dates'].append(date)
        
        # Convert categorical data to numerical
        chart_data['moods'].append(mood_map.get(entry.get('mood'), 3))
        chart_data['sleep_hours'].append(entry.get('sleep_hours', 7))
        chart_data['work_screen'].append(entry.get('work_screen_time', 8))
        chart_data['leisure_screen'].append(entry.get('leisure_screen_time', 3))
        chart_data['physical_activity'].append(yes_no_map.get(entry.get('physical_activity'), 0))
        chart_data['water_glasses'].append(entry.get('water_glasses', 4))
        chart_data['breaks_taken'].append(entry.get('breaks_taken', 2))
        chart_data['outdoors_time'].append(yes_no_map.get(entry.get('outdoors_time'), 0))
        chart_data['stress_levels'].append(stress_map.get(entry.get('stress_level'), 3))
        chart_data['social_interaction'].append(social_map.get(entry.get('social_interaction'), 2))
        chart_data['work_satisfaction'].append(satisfaction_map.get(entry.get('work_satisfaction'), 3))
        chart_data['energy_levels'].append(energy_map.get(entry.get('energy_level'), 3))
        chart_data['focus_quality'].append(focus_map.get(entry.get('focus_quality'), 3))
    
    return chart_data

def generate_sample_user_data():
    """Generate sample historical data for a user"""
    sample_data = {}
    mood_options = ['Excellent', 'Good', 'Neutral', 'Low', 'Poor']
    stress_options = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
    
    for i in range(30):  # 30 days of data
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        sample_data[date] = {
            'mood': random.choice(mood_options),
            'sleep_hours': round(random.uniform(5.5, 9.0), 1),
            'work_screen_time': round(random.uniform(6, 12), 1),
            'leisure_screen_time': round(random.uniform(1, 5), 1),
            'physical_activity': random.choice(['Yes', 'No']),
            'water_glasses': random.randint(3, 10),
            'breaks_taken': random.randint(1, 8),
            'outdoors_time': random.choice(['Yes', 'No']),
            'stress_level': random.choice(stress_options),
            'social_interaction': random.choice(['None', 'Little', 'Moderate', 'Significant']),
            'work_satisfaction': random.choice(['Very Low', 'Low', 'Neutral', 'High', 'Very High']),
            'energy_level': random.choice(['Very Low', 'Low', 'Moderate', 'High', 'Very High']),
            'focus_quality': random.choice(['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'])
        }
    
    return sample_data

def process_user_data_for_charts(user_data):
    """Process user data for chart visualization"""
    chart_data = {
        'dates': [],
        'moods': [],
        'sleep_hours': [],
        'work_screen': [],
        'leisure_screen': [],
        'physical_activity': [],
        'water_glasses': [],
        'breaks_taken': [],
        'outdoors_time': [],
        'stress_levels': [],
        'social_interaction': [],
        'work_satisfaction': [],
        'energy_levels': [],
        'focus_quality': []
    }
    
    # Mapping dictionaries
    mood_map = {'Excellent': 5, 'Good': 4, 'Neutral': 3, 'Low': 2, 'Poor': 1}
    stress_map = {'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
    social_map = {'None': 1, 'Little': 2, 'Moderate': 3, 'Significant': 4}
    satisfaction_map = {'Very Low': 1, 'Low': 2, 'Neutral': 3, 'High': 4, 'Very High': 5}
    energy_map = {'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
    focus_map = {'Poor': 1, 'Fair': 2, 'Good': 3, 'Very Good': 4, 'Excellent': 5}
    yes_no_map = {'Yes': 1, 'No': 0}
    
    for date, entry in sorted(user_data.items()):
        chart_data['dates'].append(date)
        
        # Convert categorical data to numerical
        chart_data['moods'].append(mood_map.get(entry.get('mood'), 3))
        chart_data['sleep_hours'].append(entry.get('sleep_hours', 7))
        chart_data['work_screen'].append(entry.get('work_screen_time', 8))
        chart_data['leisure_screen'].append(entry.get('leisure_screen_time', 3))
        chart_data['physical_activity'].append(yes_no_map.get(entry.get('physical_activity'), 0))
        chart_data['water_glasses'].append(entry.get('water_glasses', 4))
        chart_data['breaks_taken'].append(entry.get('breaks_taken', 2))
        chart_data['outdoors_time'].append(yes_no_map.get(entry.get('outdoors_time'), 0))
        chart_data['stress_levels'].append(stress_map.get(entry.get('stress_level'), 3))
        chart_data['social_interaction'].append(social_map.get(entry.get('social_interaction'), 2))
        chart_data['work_satisfaction'].append(satisfaction_map.get(entry.get('work_satisfaction'), 3))
        chart_data['energy_levels'].append(energy_map.get(entry.get('energy_level'), 3))
        chart_data['focus_quality'].append(focus_map.get(entry.get('focus_quality'), 3))
    
    return chart_data

@app.route('/company_dashboard')
def company_dashboard():
    """Enhanced company dashboard with comprehensive analytics"""
    company_data = generate_sample_company_data()
    return render_template('company_dashboard.html', company_data=json.dumps(company_data))

@app.route('/chat')
def health_chat():
    """Health chatbot interface"""
    return render_template('health_chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Chat API endpoint"""
    user_message = request.json.get('message', '')
    user_id = request.json.get('user_id', 'default_user')
    
    # Get user's health data for context
    data = load_data()
    user_data = data.get(user_id, {})
    
    # Get recent health data
    recent_data = None
    if user_data:
        recent_date = max(user_data.keys())
        recent_data = user_data[recent_date]
    
    try:
        # Create context-aware prompt
        context = ""
        if recent_data:
            context = f"""
            User's recent health data:
            - Mood: {recent_data.get('mood', 'Unknown')}
            - Sleep: {recent_data.get('sleep_hours', 'Unknown')} hours
            - Stress level: {recent_data.get('stress_level', 'Unknown')}
            - Physical activity: {recent_data.get('physical_activity', 'Unknown')}
            """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": f"""You are a supportive health and wellness chatbot for remote workers. 
                    Provide helpful, empathetic responses about health, wellness, productivity, and work-life balance.
                    
                    {context}
                    
                    Guidelines:
                    - Be supportive and understanding
                    - Provide practical, actionable advice
                    - Don't diagnose medical conditions
                    - If asked about serious medical issues, suggest consulting a healthcare professional
                    - Keep responses concise but helpful
                    - Focus on remote work wellness, mental health, and productivity
                    """
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        bot_response = response.choices[0].message.content
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'response': "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            'status': 'error'
        })

if __name__ == '__main__':
    app.run(debug=True)