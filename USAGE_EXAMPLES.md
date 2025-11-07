# Usage Examples

This document shows how to use the Dog Walker Tracker system to extract useful information and insights.

## Basic Usage

### Starting the System

```bash
# Terminal 1: Start the tracker
python main.py

# Terminal 2: Start the web dashboard
python web_interface.py
```

Then open http://localhost:5001 in your browser.

### Viewing Statistics

```bash
# Print walker statistics to console
python main.py --stats
```

## Advanced Usage - Python API

You can use the tracker's Python API to build custom queries and reports.

### Example 1: List All Walkers with Dogs

```python
from database import init_database, Walker, Detection
from tracker import WalkerTracker
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize database
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()

# Create tracker
tracker = WalkerTracker(session, config)

# Get all walkers
walkers = session.query(Walker).all()

print("Walkers with dogs:")
for walker in walkers:
    has_dog = any(d.has_dog for d in walker.detections)
    if has_dog:
        print(f"Walker #{walker.id}:")
        print(f"  First seen: {walker.first_seen}")
        print(f"  Last seen: {walker.last_seen}")
        print(f"  Total walks: {walker.total_walks}")
        print()

session.close()
```

### Example 2: Find Regular Dog Walkers

```python
from database import init_database
from analytics import WalkerAnalytics
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()
analytics = WalkerAnalytics(session, config)

# Get regular walkers (seen 3+ times in last 7 days)
regular_walkers = analytics.get_regular_walkers(days=7)

print("Regular walkers:")
for walker_info in regular_walkers:
    print(f"Walker #{walker_info['walker_id']}:")
    print(f"  Sessions: {walker_info['sessions_count']}")
    print(f"  Unique days: {walker_info['unique_days']}")
    print(f"  Has dog: {walker_info['has_dog']}")
    print()

session.close()
```

### Example 3: Analyze Walker Schedule

```python
from database import init_database
from analytics import WalkerAnalytics
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()
analytics = WalkerAnalytics(session, config)

# Get schedule for walker #1
walker_id = 1
schedule = analytics.get_walker_schedule(walker_id)

print(f"Walking schedule for Walker #{walker_id}:")
for day, times in schedule.items():
    if times:
        print(f"{day}: {', '.join(times)}")

session.close()
```

### Example 4: Generate Activity Heatmap

```python
from database import init_database
from analytics import WalkerAnalytics
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()
analytics = WalkerAnalytics(session, config)

# Get activity heatmap
heatmap = analytics.get_activity_heatmap()

print("Activity Heatmap (busiest times):")
for day, hours in heatmap.items():
    busy_hours = [hour for hour, count in hours.items() if count > 0]
    if busy_hours:
        print(f"{day}: Hours {min(busy_hours)}-{max(busy_hours)}")

session.close()
```

### Example 5: Comprehensive Walker Report

```python
from database import init_database
from analytics import WalkerAnalytics
import yaml
import json

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()
analytics = WalkerAnalytics(session, config)

# Generate report for walker #1
walker_id = 1
report = analytics.generate_report(walker_id)

print(json.dumps(report, indent=2, default=str))

session.close()
```

### Example 6: Export Data to CSV

```python
import csv
from database import init_database, Walker, Detection
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize database
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()

# Get all detections
detections = session.query(Detection).order_by(Detection.timestamp).all()

# Export to CSV
with open('detections.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Walker ID', 'Camera', 'Zone', 'Path', 'Timestamp', 'Event Type', 'Has Dog'])
    
    for d in detections:
        writer.writerow([
            d.walker_id,
            d.camera,
            d.zone,
            d.path_name,
            d.timestamp,
            d.event_type,
            d.has_dog
        ])

print(f"Exported {len(detections)} detections to detections.csv")

session.close()
```

## Using the Web API

The web interface also provides a REST API:

```bash
# Get all walkers
curl http://localhost:5001/api/walkers

# Get specific walker details
curl http://localhost:5001/api/walker/1

# Get overall statistics
curl http://localhost:5001/api/stats
```

## Identifying Problem Walkers

Based on the data collected, you can identify potential problem walkers by looking for:

1. **Regular dog walkers**: Those who walk their dog frequently
2. **Time patterns**: Consistent times/days they walk
3. **Path patterns**: Which paths they typically use
4. **Correlation with incidents**: Match walker times with when you observe problems

### Example Analysis Script

```python
from database import init_database
from analytics import WalkerAnalytics
from datetime import datetime, timedelta
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize
engine, SessionClass = init_database(config['database']['path'])
session = SessionClass()
analytics = WalkerAnalytics(session, config)

# Get suspicious walkers (regular dog walkers)
suspicious = analytics.get_suspicious_walkers(threshold=3)

print("Potentially Suspicious Walkers:")
print("(Regular dog walkers - correlation needed with incidents)")
print()

for walker in suspicious:
    report = analytics.generate_report(walker['walker_id'])
    
    print(f"Walker #{walker['walker_id']}:")
    print(f"  Dog walks: {walker['dog_walks']}")
    print(f"  Total walks: {walker['total_walks']}")
    print(f"  Typical schedule:")
    
    for day, times in report['schedule'].items():
        if times:
            print(f"    {day}: {', '.join(sorted(times))}")
    
    print(f"  Paths used: {', '.join(report['path_patterns'].keys())}")
    print()

session.close()
```

## Tips for Effective Use

1. **Run for at least 1-2 weeks** to establish patterns
2. **Note when you observe problems** and correlate with walker data
3. **Review captured images** to identify individuals
4. **Look for patterns**, not just individual incidents
5. **Approach respectfully** if you need to address the issue with neighbors

## Privacy Considerations

Remember to:
- Follow local laws regarding surveillance and recording
- Use this data responsibly and ethically
- Consider privacy implications before sharing images
- Focus on resolving the problem constructively

## Backing Up Data

### Backup the Database

```bash
# Simple backup
cp dog_walker_tracker.db dog_walker_tracker.db.backup

# With timestamp
cp dog_walker_tracker.db "dog_walker_tracker_$(date +%Y%m%d).db"
```

### Backup Images

```bash
# Tar compress images
tar -czf walker_images_backup.tar.gz walker_images/
```

## Troubleshooting Common Issues

### No Data Appearing

1. Check Frigate is detecting people/dogs in the Frigate UI
2. Verify MQTT connection in logs: `tail -f dog_walker_tracker.log`
3. Ensure camera zones in config.yaml match Frigate configuration
4. Test MQTT: `mosquitto_sub -h your-frigate-ip -t "frigate/#" -v`

### Images Not Captured

1. Check Frigate API is accessible: `curl http://frigate-ip:5000/api/config`
2. Verify walker_images directory exists and is writable
3. Check logs for error messages

### False Positives

1. Adjust confidence thresholds in config.yaml
2. Review Frigate's detection settings
3. Consider adjusting zone configurations
