"""
Analytics module for identifying patterns in walker behavior
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import Walker, Detection, WalkSession
from sqlalchemy.orm import Session
from sqlalchemy import func


class WalkerAnalytics:
    """Provides analytics and insights on walker patterns"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
    
    def get_regular_walkers(self, days: int = None) -> List[Dict[str, Any]]:
        """
        Get walkers who appear regularly
        Returns walkers who have been seen on multiple different days
        """
        if days is None:
            days = self.config['tracking']['regular_walker_days']
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get walkers with multiple sessions
        walkers = self.db.query(Walker).filter(
            Walker.first_seen >= cutoff_date
        ).all()
        
        regular = []
        for walker in walkers:
            sessions = self.db.query(WalkSession).filter(
                WalkSession.walker_id == walker.id,
                WalkSession.start_time >= cutoff_date
            ).all()
            
            if len(sessions) >= 3:  # Seen at least 3 times
                # Count unique days
                unique_days = len(set(s.start_time.date() for s in sessions))
                
                regular.append({
                    'walker_id': walker.id,
                    'sessions_count': len(sessions),
                    'unique_days': unique_days,
                    'first_seen': walker.first_seen,
                    'last_seen': walker.last_seen,
                    'has_dog': any(s.has_dog for s in sessions)
                })
        
        return sorted(regular, key=lambda x: x['sessions_count'], reverse=True)
    
    def get_walker_schedule(self, walker_id: int) -> Dict[str, List[str]]:
        """
        Analyze when a walker typically walks
        Returns typical times by day of week
        """
        sessions = self.db.query(WalkSession).filter(
            WalkSession.walker_id == walker_id
        ).all()
        
        schedule = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [],
            'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        for session in sessions:
            day_name = session.start_time.strftime('%A')
            time_str = session.start_time.strftime('%H:%M')
            schedule[day_name].append(time_str)
        
        return schedule
    
    def get_path_patterns(self, walker_id: int) -> Dict[str, int]:
        """
        Analyze path patterns for a walker
        Returns frequency of each path
        """
        detections = self.db.query(Detection).filter(
            Detection.walker_id == walker_id
        ).all()
        
        paths = {}
        for detection in detections:
            path = detection.path_name
            paths[path] = paths.get(path, 0) + 1
        
        return dict(sorted(paths.items(), key=lambda x: x[1], reverse=True))
    
    def get_walkers_with_dogs(self) -> List[int]:
        """Get list of walker IDs who have been seen with dogs"""
        walkers = self.db.query(Walker).all()
        
        with_dogs = []
        for walker in walkers:
            has_dog = any(d.has_dog for d in walker.detections)
            if has_dog:
                with_dogs.append(walker.id)
        
        return with_dogs
    
    def get_suspicious_walkers(self, threshold: int = None) -> List[Dict[str, Any]]:
        """
        Identify potentially suspicious walkers
        Walkers who regularly have dogs but patterns suggest they might not be cleaning up
        This is based on frequency and timing patterns
        """
        if threshold is None:
            threshold = self.config['analytics']['suspicious_threshold']
        
        dog_walkers = self.get_walkers_with_dogs()
        regular = self.get_regular_walkers()
        
        suspicious = []
        for walker_info in regular:
            walker_id = walker_info['walker_id']
            
            if walker_id in dog_walkers and walker_info['sessions_count'] >= threshold:
                # Add to suspicious list if they're regular with dogs
                sessions = self.db.query(WalkSession).filter(
                    WalkSession.walker_id == walker_id,
                    WalkSession.has_dog == True
                ).all()
                
                suspicious.append({
                    'walker_id': walker_id,
                    'dog_walks': len(sessions),
                    'total_walks': walker_info['sessions_count'],
                    'first_seen': walker_info['first_seen'],
                    'last_seen': walker_info['last_seen']
                })
        
        return suspicious
    
    def get_activity_heatmap(self) -> Dict[str, Dict[int, int]]:
        """
        Generate activity heatmap showing when walkers are most active
        Returns: {day_of_week: {hour: count}}
        """
        sessions = self.db.query(WalkSession).all()
        
        heatmap = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days:
            heatmap[day] = {hour: 0 for hour in range(24)}
        
        for session in sessions:
            day_name = session.start_time.strftime('%A')
            hour = session.start_time.hour
            heatmap[day_name][hour] += 1
        
        return heatmap
    
    def get_camera_coverage(self) -> Dict[str, int]:
        """Get detection count per camera"""
        detections = self.db.query(
            Detection.camera,
            func.count(Detection.id).label('count')
        ).group_by(Detection.camera).all()
        
        return {camera: count for camera, count in detections}
    
    def generate_report(self, walker_id: int) -> Dict[str, Any]:
        """Generate comprehensive report for a walker"""
        walker = self.db.query(Walker).filter(Walker.id == walker_id).first()
        
        if not walker:
            return {}
        
        sessions = self.db.query(WalkSession).filter(
            WalkSession.walker_id == walker_id
        ).all()
        
        detections = self.db.query(Detection).filter(
            Detection.walker_id == walker_id
        ).all()
        
        return {
            'walker_id': walker_id,
            'first_seen': walker.first_seen,
            'last_seen': walker.last_seen,
            'total_sessions': len(sessions),
            'total_detections': len(detections),
            'has_dog': any(s.has_dog for s in sessions),
            'schedule': self.get_walker_schedule(walker_id),
            'path_patterns': self.get_path_patterns(walker_id),
            'cameras_used': list(set(d.camera for d in detections))
        }
