import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

def calculate_wellness_score(health_data: Dict) -> float:
    """Calculate comprehensive wellness score from health data"""
    score_components = []
    
    # Mood score (0-1)
    mood_map = {'Poor': 0.2, 'Low': 0.4, 'Neutral': 0.6, 'Good': 0.8, 'Excellent': 1.0}
    mood_score = mood_map.get(health_data.get('mood'), 0.6)
    score_components.append(mood_score * 0.25)  # 25% weight
    
    # Sleep score (0-1)
    sleep_hours = health_data.get('sleep_hours', 7)
    sleep_score = min(1.0, max(0.0, (sleep_hours - 4) / 5))  # 4-9 hours range
    if 7 <= sleep_hours <= 8:
        sleep_score = 1.0  # Optimal range
    score_components.append(sleep_score * 0.20)  # 20% weight
    
    # Activity score (0-1)
    activity_score = 1.0 if health_data.get('physical_activity') == 'Yes' else 0.3
    score_components.append(activity_score * 0.15)  # 15% weight
    
    # Stress score (0-1, inverted)
    stress_map = {'Very High': 0.1, 'High': 0.3, 'Moderate': 0.6, 'Low': 0.8, 'Very Low': 1.0}
    stress_score = stress_map.get(health_data.get('stress_level'), 0.6)
    score_components.append(stress_score * 0.20)  # 20% weight
    
    # Screen time score (0-1, inverted)
    total_screen = health_data.get('work_screen_time', 8) + health_data.get('leisure_screen_time', 3)
    screen_score = max(0.0, 1.0 - (max(0, total_screen - 8) / 8))  # Penalty after 8 hours
    score_components.append(screen_score * 0.10)  # 10% weight
    
    # Hydration score (0-1)
    water_glasses = health_data.get('water_glasses', 4)
    hydration_score = min(1.0, water_glasses / 8)  # Target 8 glasses
    score_components.append(hydration_score * 0.10)  # 10% weight
    
    return sum(score_components) * 100  # Convert to 0-100 scale

def analyze_health_trends(user_data: Dict, days: int = 30) -> Dict:
    """Analyze health trends over specified period"""
    if not user_data:
        return {}
    
    # Get recent data
    recent_dates = sorted(user_data.keys())[-days:]
    if len(recent_dates) < 2:
        return {}
    
    trends = {}
    
    # Mood trend
    moods = [get_mood_score(user_data[date].get('mood')) for date in recent_dates]
    trends['mood'] = {
        'current': moods[-1] if moods else 3,
        'average': statistics.mean(moods) if moods else 3,
        'trend': 'improving' if len(moods) > 1 and moods[-1] > moods[0] else 'declining' if len(moods) > 1 and moods[-1] < moods[0] else 'stable'
    }
    
    # Sleep trend
    sleep_hours = [user_data[date].get('sleep_hours', 7) for date in recent_dates]
    trends['sleep'] = {
        'current': sleep_hours[-1] if sleep_hours else 7,
        'average': statistics.mean(sleep_hours) if sleep_hours else 7,
        'trend': 'improving' if len(sleep_hours) > 1 and sleep_hours[-1] > sleep_hours[0] else 'declining' if len(sleep_hours) > 1 and sleep_hours[-1] < sleep_hours[0] else 'stable'
    }
    
    # Activity trend
    activities = [1 if user_data[date].get('physical_activity') == 'Yes' else 0 for date in recent_dates]
    activity_rate = statistics.mean(activities) if activities else 0
    trends['activity'] = {
        'rate': activity_rate,
        'trend': 'consistent' if activity_rate > 0.7 else 'inconsistent' if activity_rate > 0.3 else 'low'
    }
    
    return trends

def get_mood_score(mood_str: str) -> int:
    """Convert mood string to numeric score"""
    mood_map = {'Poor': 1, 'Low': 2, 'Neutral': 3, 'Good': 4, 'Excellent': 5}
    return mood_map.get(mood_str, 3)

def generate_health_recommendations(health_data: Dict, trends: Dict = None) -> List[str]:
    """Generate personalized health recommendations"""
    recommendations = []
    
    # Sleep recommendations
    sleep_hours = health_data.get('sleep_hours', 7)
    if sleep_hours < 6:
        recommendations.append("🛏️ **Critical**: Prioritize sleep - aim for 7-9 hours nightly. Poor sleep affects all aspects of health.")
    elif sleep_hours < 7:
        recommendations.append("😴 **Sleep Boost**: Try to get an extra hour of sleep. Your body and mind will thank you.")
    
    # Mood and stress recommendations
    mood = health_data.get('mood', 'Neutral')
    stress = health_data.get('stress_level', 'Moderate')
    
    if mood in ['Poor', 'Low'] or stress in ['High', 'Very High']:
        recommendations.append("🧘 **Mental Wellness**: Consider stress-reduction techniques like meditation, deep breathing, or talking to someone you trust.")
    
    # Activity recommendations
    if health_data.get('physical_activity') == 'No':
        recommendations.append("🏃 **Move More**: Even 15-20 minutes of movement can boost mood and energy. Try desk exercises or a short walk.")
    
    # Hydration recommendations
    water_glasses = health_data.get('water_glasses', 4)
    if water_glasses < 6:
        recommendations.append("💧 **Stay Hydrated**: Aim for 8 glasses of water daily. Set reminders if needed.")
    
    # Screen time recommendations
    total_screen = health_data.get('work_screen_time', 8) + health_data.get('leisure_screen_time', 3)
    if total_screen > 12:
        recommendations.append("📱 **Digital Balance**: Consider reducing screen time. Follow the 20-20-20 rule for eye health.")
    
    # Social recommendations
    social = health_data.get('social_interaction', 'Moderate')
    if social == 'None':
        recommendations.append("👥 **Social Connection**: Reach out to friends, family, or colleagues. Social connection is vital for mental health.")
    
    return recommendations[:5]  # Limit to top 5 recommendations

def export_health_data(user_data: Dict, format: str = 'json') -> str:
    """Export user health data in specified format"""
    if format == 'json':
        return json.dumps(user_data, indent=2, default=str)
    elif format == 'csv':
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        if not user_data:
            return ""
        
        # Get all possible fields
        all_fields = set()
        for date_data in user_data.values():
            all_fields.update(date_data.keys())
        
        fieldnames = ['date'] + sorted(list(all_fields))
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for date, data in sorted(user_data.items()):
            row = {'date': date}
            row.update(data)
            writer.writerow(row)
        
        return output.getvalue()
    
    return ""