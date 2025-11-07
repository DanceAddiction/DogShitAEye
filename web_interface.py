"""
Web interface for viewing tracked dog walkers
"""
from flask import Flask, render_template, jsonify, send_from_directory
import yaml
import os
from datetime import datetime
from database import init_database, Walker, Detection, WalkerImage, WalkSession
from tracker import WalkerTracker

app = Flask(__name__)

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize database
db_path = config['database']['path']
engine, SessionClass = init_database(db_path)
db_session = SessionClass()

# Initialize tracker for stats
tracker = WalkerTracker(db_session, config)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/walkers')
def get_walkers():
    """Get all tracked walkers"""
    walkers = tracker.get_all_walkers()
    
    # Convert datetime to string for JSON
    for walker in walkers:
        walker['first_seen'] = walker['first_seen'].isoformat() if walker['first_seen'] else None
        walker['last_seen'] = walker['last_seen'].isoformat() if walker['last_seen'] else None
    
    return jsonify(walkers)


@app.route('/api/walker/<int:walker_id>')
def get_walker_detail(walker_id):
    """Get detailed information about a specific walker"""
    walker = db_session.query(Walker).filter(Walker.id == walker_id).first()
    
    if not walker:
        return jsonify({'error': 'Walker not found'}), 404
    
    # Get detections
    detections = db_session.query(Detection).filter(
        Detection.walker_id == walker_id
    ).order_by(Detection.timestamp.desc()).all()
    
    # Get images
    images = db_session.query(WalkerImage).filter(
        WalkerImage.walker_id == walker_id
    ).order_by(WalkerImage.quality_score.desc()).all()
    
    # Get sessions
    sessions = db_session.query(WalkSession).filter(
        WalkSession.walker_id == walker_id
    ).order_by(WalkSession.start_time.desc()).all()
    
    return jsonify({
        'walker_id': walker.id,
        'first_seen': walker.first_seen.isoformat(),
        'last_seen': walker.last_seen.isoformat(),
        'total_walks': walker.total_walks,
        'detections': [{
            'id': d.id,
            'camera': d.camera,
            'zone': d.zone,
            'path_name': d.path_name,
            'timestamp': d.timestamp.isoformat(),
            'event_type': d.event_type,
            'has_dog': d.has_dog
        } for d in detections],
        'images': [{
            'id': img.id,
            'image_path': os.path.basename(img.image_path),
            'image_type': img.image_type,
            'timestamp': img.timestamp.isoformat(),
            'camera': img.camera,
            'quality_score': img.quality_score
        } for img in images],
        'sessions': [{
            'id': s.id,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'cameras_visited': s.cameras_visited,
            'paths_taken': s.paths_taken,
            'has_dog': s.has_dog
        } for s in sessions]
    })


@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """Serve walker images"""
    img_dir = config['images']['storage_path']
    return send_from_directory(img_dir, filename)


@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    walkers = db_session.query(Walker).all()
    detections = db_session.query(Detection).all()
    sessions = db_session.query(WalkSession).all()
    
    walkers_with_dogs = sum(1 for w in walkers if any(d.has_dog for d in w.detections))
    
    return jsonify({
        'total_walkers': len(walkers),
        'total_detections': len(detections),
        'total_sessions': len(sessions),
        'walkers_with_dogs': walkers_with_dogs,
        'walkers_without_dogs': len(walkers) - walkers_with_dogs
    })


if __name__ == '__main__':
    # Note: Set debug=False in production to prevent security vulnerabilities
    # Debug mode allows arbitrary code execution through the debugger
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
