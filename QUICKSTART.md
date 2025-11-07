# Quick Start Guide

## Setup in 5 Minutes

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Frigate Connection

Edit `config.yaml` and set your Frigate server details:

```yaml
frigate:
  host: "192.168.1.100"  # Your Frigate IP
  mqtt_host: "192.168.1.100"  # Usually same as above
```

### 3. Configure Cameras

Add your camera zones in `config.yaml`:

```yaml
cameras:
  front_garden:
    name: "Front Garden"
    zone: "front_garden"
    path_name: "Front Path"
```

Make sure the zone name matches what you have in your Frigate configuration.

### 4. Start the Tracker

```bash
python main.py
```

You should see:
```
INFO - Dog Walker Tracker initialized
INFO - Connecting to MQTT broker at 192.168.1.100:1883
INFO - Connected to MQTT with result code 0
INFO - Dog Walker Tracker is running. Press Ctrl+C to stop.
```

### 5. Open the Web Dashboard

In a new terminal:

```bash
python web_interface.py
```

Open your browser to: http://localhost:5001

**Note:** For development/testing, you can enable debug mode:
```bash
FLASK_DEBUG=true python web_interface.py
```
**Security Warning:** Never run with debug mode in production as it can allow arbitrary code execution.

## Verifying It's Working

### Check Logs

```bash
tail -f dog_walker_tracker.log
```

You should see messages when people are detected:
```
INFO - Person detected on front_garden (zone: front_garden)
INFO - Created new walker: 1
INFO - Captured and saved image for walker 1
```

### Check Database

```bash
python main.py --stats
```

This will print walker statistics to the console.

## Frigate Configuration Tips

### Enable Person and Dog Detection

In your Frigate `config.yaml`, ensure you have:

```yaml
objects:
  track:
    - person
    - dog
```

### Configure Zones

Define zones where you want to track walkers:

```yaml
cameras:
  front_camera:
    zones:
      front_path:
        coordinates: 640,0,640,480,0,480,0,0
```

### MQTT Settings

If Frigate uses MQTT authentication, set credentials in the DogShitAEye `config.yaml`:

```yaml
frigate:
  mqtt_user: "your_username"
  mqtt_password: "your_password"
```

## Troubleshooting

### "Connection refused" Error

- Check Frigate is running: `curl http://your-frigate-ip:5000/api/config`
- Verify MQTT broker is running on the Frigate host
- Check firewall allows port 1883 (MQTT)

### No Detections Appearing

1. Check Frigate is detecting objects: Open Frigate UI and verify detections work
2. Verify camera zones are configured correctly in `config.yaml`
3. Check logs: `tail -f dog_walker_tracker.log`
4. Test MQTT connection: Use an MQTT client like `mosquitto_sub`:
   ```bash
   mosquitto_sub -h your-frigate-ip -t "frigate/#" -v
   ```

### Images Not Saving

1. Check `walker_images` directory is created and writable
2. Verify Frigate API is accessible
3. Check available disk space

## Next Steps

1. **Monitor for a few days** to build up walker profiles
2. **Review the web dashboard** to see patterns
3. **Check walker schedules** to identify regulars
4. **Review images** to visually identify walkers

## Getting More Help

- Check the main README.md for detailed documentation
- Review `dog_walker_tracker.log` for detailed error messages
- Ensure your Frigate version is 0.12.0 or later
