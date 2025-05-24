import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class HealthAnalytics:
    def __init__(self, health_data: Dict):
        self.data = health_data
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert health data to pandas DataFrame"""
        if not self.data:
            return pd.DataFrame()
        
        rows = []
        for user_id, user_data in self.data.items():
            for date, entry in user_data.items():
                row = {'user_id': user_id, 'date': date}
                row.update(entry)
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['user_id', 'date'])
        
        return df
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """Get comprehensive statistics for a specific user"""
        user_df = self.df[self.df['user_id'] == user_id].copy()
        if user_df.empty:
            return {}
        
        # Convert categorical to numerical
        mood_map = {'Poor': 1, 'Low': 2, 'Neutral': 3, 'Good': 4, 'Excellent': 5}
        user_df['mood_score'] = user_df['mood'].map(mood_map)
        
        stats = {
            'total_checkins': len(user_df),
            'date_range': {
                'start': user_df['date'].min().strftime('%Y-%m-%d'),
                'end': user_df['date'].max().strftime('%Y-%m-%d')
            },
            'averages': {
                'mood': user_df['mood_score'].mean(),
                'sleep_hours': user_df['sleep_hours'].mean(),
                'water_glasses': user_df['water_glasses'].mean(),
                'breaks_taken': user_df['breaks_taken'].mean(),
                'work_screen_time': user_df['work_screen_time'].mean(),
                'leisure_screen_time': user_df['leisure_screen_time'].mean()
            },
            'activity_rate': (user_df['physical_activity'] == 'Yes').mean(),
            'outdoor_rate': (user_df['outdoors_time'] == 'Yes').mean(),
            'streaks': self._calculate_streaks(user_df)
        }
        
        return stats
    
    def _calculate_streaks(self, user_df: pd.DataFrame) -> Dict:
        """Calculate various streaks for user"""
        streaks = {}
        
        # Activity streak
        activity_values = (user_df['physical_activity'] == 'Yes').astype(int)
        streaks['current_activity_streak'] = self._current_streak(activity_values.values)
        streaks['max_activity_streak'] = self._max_streak(activity_values.values)
        
        # Sleep quality streak (7+ hours)
        sleep_quality = (user_df['sleep_hours'] >= 7).astype(int)
        streaks['current_sleep_streak'] = self._current_streak(sleep_quality.values)
        streaks['max_sleep_streak'] = self._max_streak(sleep_quality.values)
        
        return streaks
    
    def _current_streak(self, binary_array: np.array) -> int:
        """Calculate current streak from end of array"""
        if len(binary_array) == 0:
            return 0
        
        streak = 0
        for i in range(len(binary_array) - 1, -1, -1):
            if binary_array[i] == 1:
                streak += 1
            else:
                break
        return streak
    
    def _max_streak(self, binary_array: np.array) -> int:
        """Calculate maximum streak in array"""
        if len(binary_array) == 0:
            return 0
        
        max_streak = current_streak = 0
        for value in binary_array:
            if value == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak
    
    def get_correlation_analysis(self, user_id: str) -> Dict:
        """Analyze correlations between different health metrics"""
        user_df = self.df[self.df['user_id'] == user_id].copy()
        if len(user_df) < 5:  # Need minimum data points
            return {}
        
        # Prepare numerical data
        mood_map = {'Poor': 1, 'Low': 2, 'Neutral': 3, 'Good': 4, 'Excellent': 5}
        stress_map = {'Very Low': 1, 'Low': 2, 'Moderate': 3, 'High': 4, 'Very High': 5}
        
        user_df['mood_score'] = user_df['mood'].map(mood_map)
        user_df['stress_score'] = user_df['stress_level'].map(stress_map)
        user_df['activity_score'] = (user_df['physical_activity'] == 'Yes').astype(int)
        
        # Calculate correlations
        correlations = {}
        numeric_cols = ['mood_score', 'sleep_hours', 'stress_score', 'water_glasses', 
                       'breaks_taken', 'activity_score', 'work_screen_time', 'leisure_screen_time']
        
        for col in numeric_cols:
            if col in user_df.columns:
                correlations[f'mood_vs_{col}'] = user_df['mood_score'].corr(user_df[col])
        
        return correlations
    
    def generate_insights(self, user_id: str) -> List[Dict]:
        """Generate data-driven insights for user"""
        stats = self.get_user_statistics(user_id)
        correlations = self.get_correlation_analysis(user_id)
        
        insights = []
        
        if stats:
            # Sleep insight
            avg_sleep = stats['averages']['sleep_hours']
            if avg_sleep < 6.5:
                insights.append({
                    'type': 'warning',
                    'title': 'Sleep Deficit Pattern',
                    'description': f'Your average sleep is {avg_sleep:.1f} hours. Consider prioritizing sleep hygiene.',
                    'action': 'Set a consistent bedtime routine'
                })
            elif avg_sleep > 8.5:
                insights.append({
                    'type': 'info',
                    'title': 'High Sleep Duration',
                    'description': f'You sleep {avg_sleep:.1f} hours on average. Monitor if you feel rested.',
                    'action': 'Consider sleep quality over quantity'
                })
            
            # Activity insight
            if stats['activity_rate'] < 0.3:
                insights.append({
                    'type': 'warning',
                    'title': 'Low Activity Level',
                    'description': f'You\'re active only {stats["activity_rate"]*100:.0f}% of the time.',
                    'action': 'Start with 15-minute daily walks'
                })
            elif stats['activity_rate'] > 0.8:
                insights.append({
                    'type': 'positive',
                    'title': 'Excellent Activity Consistency',
                    'description': f'You maintain {stats["activity_rate"]*100:.0f}% activity rate. Great job!',
                    'action': 'Keep up the excellent routine'
                })
        
        return insights

def generate_company_insights(all_user_data: Dict) -> List[Dict]:
    """Generate company-wide insights"""
    analytics = HealthAnalytics(all_user_data)
    
    if analytics.df.empty:
        return []
    
    insights = []
    
    # Overall mood trend
    mood_map = {'Poor': 1, 'Low': 2, 'Neutral': 3, 'Good': 4, 'Excellent': 5}
    analytics.df['mood_score'] = analytics.df['mood'].map(mood_map)
    avg_mood = analytics.df['mood_score'].mean()
    
    if avg_mood >= 4:
        insights.append({
            'type': 'positive',
            'title': 'High Employee Morale',
            'description': f'Company-wide average mood is {avg_mood:.1f}/5',
            'impact': 'High'
        })
    elif avg_mood < 3:
        insights.append({
            'type': 'warning',
            'title': 'Mood Concerns Detected',
            'description': f'Company-wide average mood is {avg_mood:.1f}/5',
            'impact': 'High'
        })
    
    # Sleep patterns
    avg_sleep = analytics.df['sleep_hours'].mean()
    low_sleep_rate = (analytics.df['sleep_hours'] < 6.5).mean()
    
    if low_sleep_rate > 0.3:
        insights.append({
            'type': 'warning',
            'title': 'Widespread Sleep Issues',
            'description': f'{low_sleep_rate*100:.0f}% of employees get insufficient sleep',
            'impact': 'High'
        })
    
    # Screen time analysis
    avg_total_screen = (analytics.df['work_screen_time'] + analytics.df['leisure_screen_time']).mean()
    if avg_total_screen > 12:
        insights.append({
            'type': 'info',
            'title': 'High Screen Time Exposure',
            'description': f'Average daily screen time is {avg_total_screen:.1f} hours',
            'impact': 'Medium'
        })
    
    return insights