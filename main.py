"""
Main application for Dog Walker Tracker
"""
import yaml
import logging
import signal
import sys
import os
from datetime import datetime
from frigate_client import FrigateClient
from database import init_database
from tracker import WalkerTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dog_walker_tracker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DogWalkerTrackerApp:
    """Main application for tracking dog walkers"""
    
    def __init__(self, config_path='config.yaml'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize database
        db_path = self.config['database']['path']
        self.engine, SessionClass = init_database(db_path)
        self.db_session = SessionClass()
        
        # Initialize tracker
        self.tracker = WalkerTracker(self.db_session, self.config)
        
        # Initialize Frigate client
        self.frigate = FrigateClient(self.config)
        
        # Create image storage directory
        img_path = self.config['images']['storage_path']
        os.makedirs(img_path, exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Dog Walker Tracker initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received, cleaning up...")
        self.shutdown()
        sys.exit(0)
    
    def start(self):
        """Start the tracker application"""
        logger.info("Starting Dog Walker Tracker...")
        
        # Connect to Frigate MQTT
        self.frigate.connect_mqtt(self._handle_frigate_event)
        
        logger.info("Dog Walker Tracker is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        try:
            signal.pause()
        except AttributeError:
            # Windows doesn't have signal.pause()
            import time
            while True:
                time.sleep(1)
    
    def _handle_frigate_event(self, topic: str, payload: dict):
        """Handle events from Frigate"""
        try:
            # Parse topic to get camera and object type
            parts = topic.split('/')
            
            if topic == "frigate/events":
                # Full event data
                self._process_event(payload)
            elif len(parts) == 3 and parts[0] == "frigate":
                # Topic format: frigate/{camera}/{object_type}
                camera = parts[1]
                object_type = parts[2]
                self._process_detection(camera, object_type, payload)
                
        except Exception as e:
            logger.error(f"Error handling Frigate event: {e}", exc_info=True)
    
    def _process_event(self, event_data: dict):
        """Process a full event from Frigate"""
        event_type = event_data.get('type')
        
        if event_type == 'new':
            # New event started
            after = event_data.get('after', {})
            camera = after.get('camera')
            label = after.get('label')
            event_id = after.get('id')
            
            logger.info(f"New {label} event on {camera}: {event_id}")
            
        elif event_type == 'end':
            # Event ended - good time to capture snapshot
            after = event_data.get('after', {})
            camera = after.get('camera')
            label = after.get('label')
            event_id = after.get('id')
            has_snapshot = after.get('has_snapshot', False)
            
            logger.info(f"Event ended on {camera}: {event_id}")
            
            if has_snapshot and label in ['person', 'dog']:
                self._capture_event_snapshot(event_id, camera, label)
    
    def _process_detection(self, camera: str, object_type: str, payload: dict):
        """Process a detection event (person or dog)"""
        # Check if camera is configured
        camera_config = self.config['cameras'].get(camera)
        if not camera_config:
            logger.debug(f"Ignoring detection from unconfigured camera: {camera}")
            return
        
        zone = camera_config['zone']
        path_name = camera_config['path_name']
        
        # Payload contains detection count
        count = payload if isinstance(payload, int) else 0
        
        if object_type == 'person' and count > 0:
            # Person detected
            min_conf = self.config['tracking']['min_person_confidence']
            
            # Check for dog in same frame
            # Note: We need to track both person and dog detections together
            # This is a simplified version - in production, you'd want to 
            # correlate timestamps more carefully
            
            logger.info(f"Person detected on {camera} (zone: {zone})")
            
            # For now, assume person without dog (will be updated if dog detected)
            walker_id = self.tracker.process_detection(
                camera=camera,
                zone=zone,
                path_name=path_name,
                has_person=True,
                has_dog=False,
                person_confidence=min_conf
            )
            
            if walker_id:
                # Capture current frame
                self._capture_latest_frame(walker_id, camera, 'person')
    
    def _capture_event_snapshot(self, event_id: str, camera: str, label: str):
        """Capture snapshot from a completed event"""
        img_dir = self.config['images']['storage_path']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{camera}_{label}_{timestamp}_{event_id}.jpg"
        save_path = os.path.join(img_dir, filename)
        
        success = self.frigate.get_event_snapshot(event_id, save_path)
        
        if success:
            logger.info(f"Captured {label} snapshot from {camera}")
    
    def _capture_latest_frame(self, walker_id: int, camera: str, image_type: str):
        """Capture latest frame for a walker"""
        img_dir = self.config['images']['storage_path']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"walker_{walker_id}_{camera}_{image_type}_{timestamp}.jpg"
        save_path = os.path.join(img_dir, filename)
        
        success = self.frigate.get_latest_frame(camera, save_path)
        
        if success:
            self.tracker.save_walker_image(
                walker_id=walker_id,
                image_path=save_path,
                image_type=image_type,
                camera=camera,
                quality_score=0.7
            )
            logger.info(f"Captured and saved image for walker {walker_id}")
    
    def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down Dog Walker Tracker...")
        
        # Disconnect from Frigate
        self.frigate.disconnect()
        
        # Close database
        self.db_session.close()
        
        logger.info("Shutdown complete")
    
    def print_stats(self):
        """Print statistics about tracked walkers"""
        walkers = self.tracker.get_all_walkers()
        
        print("\n" + "="*60)
        print("DOG WALKER STATISTICS")
        print("="*60)
        print(f"Total walkers tracked: {len(walkers)}")
        print()
        
        for walker in walkers:
            print(f"Walker #{walker['walker_id']}:")
            print(f"  First seen: {walker['first_seen']}")
            print(f"  Last seen: {walker['last_seen']}")
            print(f"  Total walks: {walker['total_walks']}")
            print(f"  Has dog: {walker['has_dog']}")
            print(f"  Cameras: {', '.join(walker['cameras'])}")
            print(f"  Paths: {', '.join(walker['paths'])}")
            print()


def main():
    """Main entry point"""
    config_file = 'config.yaml'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats':
            # Just print statistics
            app = DogWalkerTrackerApp(config_file)
            app.print_stats()
            return
    
    # Start the tracker
    app = DogWalkerTrackerApp(config_file)
    app.start()


if __name__ == '__main__':
    main()
