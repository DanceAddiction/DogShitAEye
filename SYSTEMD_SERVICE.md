# SystemD Service Configuration for Dog Walker Tracker

This allows you to run the Dog Walker Tracker as a background service on Linux systems.

## Installation

1. **Edit the service file** - Copy and customize the example below:

Create `/etc/systemd/system/dog-walker-tracker.service`:

```ini
[Unit]
Description=Dog Walker Tracker
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/DogShitAEye
ExecStart=/usr/bin/python3 /path/to/DogShitAEye/main.py
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

2. **Update the paths and user:**
   - Replace `YOUR_USERNAME` with your Linux username
   - Replace `/path/to/DogShitAEye` with the actual path

3. **Reload systemd:**
```bash
sudo systemctl daemon-reload
```

4. **Enable the service** (start on boot):
```bash
sudo systemctl enable dog-walker-tracker
```

5. **Start the service:**
```bash
sudo systemctl start dog-walker-tracker
```

## Service Management Commands

```bash
# Check status
sudo systemctl status dog-walker-tracker

# Stop the service
sudo systemctl stop dog-walker-tracker

# Restart the service
sudo systemctl restart dog-walker-tracker

# View logs
sudo journalctl -u dog-walker-tracker -f

# Disable auto-start
sudo systemctl disable dog-walker-tracker
```

## Web Dashboard as a Service

Create `/etc/systemd/system/dog-walker-web.service`:

```ini
[Unit]
Description=Dog Walker Web Dashboard
After=network.target dog-walker-tracker.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/DogShitAEye
ExecStart=/usr/bin/python3 /path/to/DogShitAEye/web_interface.py
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dog-walker-web
sudo systemctl start dog-walker-web
```

## Troubleshooting

### Service won't start

Check the logs:
```bash
sudo journalctl -u dog-walker-tracker -n 50
```

Common issues:
- Incorrect path to Python or script
- Missing dependencies (run `pip install -r requirements.txt` as the service user)
- Permission issues (ensure the service user can read/write the database and image directories)

### Can't connect to Frigate

Ensure the service has network access:
```bash
sudo systemctl restart dog-walker-tracker
sudo journalctl -u dog-walker-tracker -f
```

Check the configuration file has correct Frigate IP address.

## Using a Virtual Environment

If you're using a Python virtual environment:

```ini
[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/DogShitAEye
ExecStart=/path/to/DogShitAEye/venv/bin/python /path/to/DogShitAEye/main.py
```

Make sure the virtual environment is created and dependencies installed:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
