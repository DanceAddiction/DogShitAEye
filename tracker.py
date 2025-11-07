"""
Walker tracking logic - identifies and tracks unique walkers across cameras
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from database import Walker, Detection, WalkerImage, WalkSession
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)


class WalkerTracker:
    """Tracks dog walkers across multiple cameras and sessions"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.active_sessions = {}  # walker_id -> session info
        self.recent_detections = []  # Recent detections for cross-camera matching
        
    def process_detection(self, camera: str, zone: str, path_name: str,
                         has_person: bool, has_dog: bool,
                         person_confidence: float = 0.0,
                         dog_confidence: float = 0.0,
                         event_id: str = None) -> Optional[int]:
        """
        Process a new detection event
        Returns walker_id if successfully tracked
        """
        if not has_person:
            return None
            
        # Check if this matches an existing active walker
        walker_id = self._match_to_walker(camera, zone, has_dog)
        
        if walker_id is None:
            # Create new walker
            walker = Walker(
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                total_walks=1
            )
            self.db.add(walker)
            self.db.commit()
            walker_id = walker.id
            logger.info(f"Created new walker: {walker_id}")
        else:
            # Update existing walker
            walker = self.db.query(Walker).filter(Walker.id == walker_id).first()
            walker.last_seen = datetime.utcnow()
            self.db.commit()
            logger.info(f"Matched to existing walker: {walker_id}")
        
        # Record detection
        detection = Detection(
            walker_id=walker_id,
            camera=camera,
            zone=zone,
            path_name=path_name,
            timestamp=datetime.utcnow(),
            event_type='enter',
            has_dog=has_dog,
            person_confidence=person_confidence,
            dog_confidence=dog_confidence if has_dog else None
        )
        self.db.add(detection)
        self.db.commit()
        
        # Track recent detections for cross-camera matching
        self.recent_detections.append({
            'walker_id': walker_id,
            'camera': camera,
            'timestamp': datetime.utcnow(),
            'has_dog': has_dog
        })
        
        # Clean old detections
        self._clean_recent_detections()
        
        # Manage walk session
        self._update_walk_session(walker_id, camera, path_name, has_dog)
        
        return walker_id
    
    def record_exit(self, walker_id: int, camera: str, zone: str, path_name: str):
        """Record when a walker exits a camera zone"""
        detection = Detection(
            walker_id=walker_id,
            camera=camera,
            zone=zone,
            path_name=path_name,
            timestamp=datetime.utcnow(),
            event_type='leave',
            has_dog=False  # We don't re-detect on exit
        )
        self.db.add(detection)
        self.db.commit()
        logger.info(f"Recorded exit for walker {walker_id} from {camera}")
    
    def _match_to_walker(self, camera: str, zone: str, has_dog: bool) -> Optional[int]:
        """
        Try to match current detection to an existing walker
        Uses cross-camera time window and dog presence
        """
        window = self.config['tracking']['cross_camera_window']
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        
        # Look for recent detections that might be the same walker
        for detection in reversed(self.recent_detections):
            if detection['timestamp'] < cutoff_time:
                continue
                
            # Match criteria:
            # 1. Within time window
            # 2. Has dog status matches (important!)
            # 3. Not the exact same camera (unless it's been a while)
            time_diff = (datetime.utcnow() - detection['timestamp']).total_seconds()
            
            if detection['has_dog'] == has_dog:
                if detection['camera'] != camera:
                    # Different camera, likely same walker
                    return detection['walker_id']
                elif time_diff > 60:
                    # Same camera but sufficient time gap (walking loop?)
                    return detection['walker_id']
        
        return None
    
    def _clean_recent_detections(self):
        """Remove old detections from recent list"""
        window = self.config['tracking']['cross_camera_window']
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        self.recent_detections = [
            d for d in self.recent_detections 
            if d['timestamp'] >= cutoff_time
        ]
    
    def _update_walk_session(self, walker_id: int, camera: str, path_name: str, has_dog: bool):
        """Update or create walk session for a walker"""
        # Check for active session
        active = self.db.query(WalkSession).filter(
            WalkSession.walker_id == walker_id,
            WalkSession.end_time == None
        ).first()
        
        if active:
            # Update existing session
            cameras = set(active.cameras_visited.split(',') if active.cameras_visited else [])
            cameras.add(camera)
            active.cameras_visited = ','.join(cameras)
            
            paths = set(active.paths_taken.split(',') if active.paths_taken else [])
            paths.add(path_name)
            active.paths_taken = ','.join(paths)
            
            active.has_dog = active.has_dog or has_dog
        else:
            # Create new session
            session = WalkSession(
                walker_id=walker_id,
                start_time=datetime.utcnow(),
                cameras_visited=camera,
                paths_taken=path_name,
                has_dog=has_dog
            )
            self.db.add(session)
        
        self.db.commit()
    
    def close_session(self, walker_id: int):
        """Close active walk session for a walker"""
        session = self.db.query(WalkSession).filter(
            WalkSession.walker_id == walker_id,
            WalkSession.end_time == None
        ).first()
        
        if session:
            session.end_time = datetime.utcnow()
            self.db.commit()
            logger.info(f"Closed walk session for walker {walker_id}")
    
    def save_walker_image(self, walker_id: int, image_path: str, 
                         image_type: str, camera: str, quality_score: float = 0.5):
        """Save image reference for a walker"""
        walker_image = WalkerImage(
            walker_id=walker_id,
            image_path=image_path,
            image_type=image_type,
            timestamp=datetime.utcnow(),
            camera=camera,
            quality_score=quality_score
        )
        self.db.add(walker_image)
        self.db.commit()
        
        # Limit images per walker
        max_images = self.config['images']['max_images_per_walker']
        self._cleanup_old_images(walker_id, max_images)
    
    def _cleanup_old_images(self, walker_id: int, max_images: int):
        """Remove old images if exceeding limit"""
        images = self.db.query(WalkerImage).filter(
            WalkerImage.walker_id == walker_id
        ).order_by(WalkerImage.quality_score.desc(), WalkerImage.timestamp.desc()).all()
        
        if len(images) > max_images:
            for img in images[max_images:]:
                # Delete file if exists
                if os.path.exists(img.image_path):
                    os.remove(img.image_path)
                self.db.delete(img)
            self.db.commit()
    
    def get_walker_stats(self, walker_id: int) -> Dict[str, Any]:
        """Get statistics for a walker"""
        walker = self.db.query(Walker).filter(Walker.id == walker_id).first()
        if not walker:
            return {}
        
        detections = self.db.query(Detection).filter(
            Detection.walker_id == walker_id
        ).all()
        
        sessions = self.db.query(WalkSession).filter(
            WalkSession.walker_id == walker_id
        ).all()
        
        cameras_used = set(d.camera for d in detections)
        paths_taken = set(d.path_name for d in detections)
        
        return {
            'walker_id': walker_id,
            'first_seen': walker.first_seen,
            'last_seen': walker.last_seen,
            'total_walks': len(sessions),
            'total_detections': len(detections),
            'cameras': list(cameras_used),
            'paths': list(paths_taken),
            'has_dog': any(d.has_dog for d in detections)
        }
    
    def get_all_walkers(self) -> List[Dict[str, Any]]:
        """Get statistics for all walkers"""
        walkers = self.db.query(Walker).all()
        return [self.get_walker_stats(w.id) for w in walkers]
