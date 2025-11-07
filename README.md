# DogShitAEye - Dog Walker Tracker

A comprehensive system that integrates with Frigate NVR to track dog walkers across multiple cameras, helping identify individuals who may not be cleaning up after their dogs.

## 🎯 Features

- **Multi-Camera Tracking**: Track dog walkers across multiple Frigate camera zones
- **Person & Dog Detection**: Automatically detects both persons and dogs in the scene
- **Time-Based Analytics**: Records entry and exit times for each walker on each camera
- **Image Capture**: Saves high-quality snapshots of walkers and their dogs
- **Walker Profiles**: Builds profiles of regular walkers with walking patterns
- **Path Analysis**: Tracks which paths walkers typically take
- **Web Dashboard**: User-friendly interface to view tracked walkers and statistics
- **Pattern Recognition**: Helps identify walkers who appear regularly with dogs

## 🏗️ Architecture

The system consists of several components:

1. **Frigate Client** (`frigate_client.py`): Connects to Frigate via MQTT and HTTP API
2. **Database** (`database.py`): SQLAlchemy models for storing walker data
3. **Tracker** (`tracker.py`): Core logic for tracking walkers across cameras
4. **Main Application** (`main.py`): Coordinates all components
5. **Web Interface** (`web_interface.py`): Flask-based dashboard

## 📋 Prerequisites

- Python 3.8 or higher
- Frigate NVR (v0.12.0 or later) running and configured
- MQTT broker (often included with Frigate)
- Cameras configured in Frigate with person and dog detection enabled

## 🚀 Installation

1. Clone this repository:
```bash
git clone https://github.com/DanceAddiction/DogShitAEye.git
cd DogShitAEye
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system by editing `config.yaml`:
```yaml
frigate:
  host: "your-frigate-host"  # e.g., "192.168.1.100"
  port: 5000
  mqtt_host: "your-mqtt-host"  # Often same as Frigate host
  mqtt_port: 1883

cameras:
  front_path:
    name: "Front Path Camera"
    zone: "front_path"
    path_name: "Main Path"
  # Add more cameras as needed
```

## 🎮 Usage

### Starting the Tracker

Run the main tracker application:
```bash
python main.py
```

This will:
- Connect to Frigate's MQTT broker
- Start listening for person and dog detection events
- Automatically track walkers and save images
- Log all activity to `dog_walker_tracker.log`

### Starting the Web Dashboard

In a separate terminal, run:
```bash
python web_interface.py
```

Then open your browser to `http://localhost:5001` to view the dashboard.

### Viewing Statistics

To print walker statistics to the console:
```bash
python main.py --stats
```

## 📊 Database Schema

The system uses SQLite to store tracking data:

- **walkers**: Unique walker profiles
- **detections**: Individual detection events (entry/exit per camera)
- **walker_images**: Captured images of walkers and dogs
- **walk_sessions**: Complete walk sessions across multiple cameras

## 🎨 Web Dashboard Features

The web interface provides:
- **Overview Statistics**: Total walkers, detections, and sessions
- **Walker List**: All tracked walkers with key information
- **Walker Details**: Detailed view of each walker's activity (coming soon)
- **Auto-Refresh**: Updates every 30 seconds

## 🔧 Configuration Options

### Tracking Configuration

```yaml
tracking:
  # Time window to consider same person across cameras (seconds)
  cross_camera_window: 300
  
  # Minimum confidence for detections
  min_person_confidence: 0.7
  min_dog_confidence: 0.6
  
  # Time to consider a "regular" walker (days)
  regular_walker_days: 7
```

### Image Storage

```yaml
images:
  storage_path: "walker_images"
  max_images_per_walker: 50
```

Images are automatically managed - when a walker exceeds the maximum, lower quality images are removed.

## 📝 How It Works

1. **Detection**: Frigate detects persons and dogs in camera zones
2. **Event Processing**: The tracker receives MQTT events from Frigate
3. **Walker Matching**: Uses time-based correlation to match the same person across cameras
4. **Image Capture**: Saves snapshots when walkers are detected
5. **Session Tracking**: Groups detections into walk sessions
6. **Data Storage**: All information is stored in the SQLite database

## 🔍 Identifying Problematic Walkers

The system helps identify walkers who may not be cleaning up by:

1. **Pattern Analysis**: Track which walkers regularly have dogs
2. **Time Tracking**: See exact times when walkers pass each camera
3. **Path Mapping**: Understand their typical routes
4. **Image Evidence**: Visual records of walkers and their dogs

Use this information responsibly and in accordance with local privacy laws.

## 🛠️ Troubleshooting

### No Detections Appearing

1. Check Frigate is running: `curl http://your-frigate-host:5000/api/config`
2. Verify MQTT connection in logs: `tail -f dog_walker_tracker.log`
3. Ensure cameras are configured in `config.yaml`
4. Check Frigate has person/dog detection enabled

### MQTT Connection Issues

1. Verify MQTT broker is running
2. Check credentials if MQTT requires authentication
3. Ensure firewall allows MQTT port (default 1883)

### Images Not Saving

1. Check `walker_images` directory exists and is writable
2. Verify Frigate API is accessible
3. Check disk space

## 📄 License

This project is intended for personal use only. Ensure compliance with local privacy and surveillance laws.

## ⚠️ Privacy and Legal Considerations

- This system captures and stores images of people in public or semi-public spaces
- Ensure you have the legal right to monitor and record in your area
- Be aware of GDPR, local privacy laws, and regulations
- Consider posting notices about video surveillance
- Use this responsibly and ethically

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This system is designed to help identify patterns, not to make accusations. Always approach neighbors respectfully and consider community solutions to shared problems.
