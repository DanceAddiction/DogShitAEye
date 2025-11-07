"""
Frigate integration module for receiving events and capturing images
"""
import paho.mqtt.client as mqtt
import requests
import json
import logging
from datetime import datetime
from typing import Callable, Dict, Any
import os

logger = logging.getLogger(__name__)


class FrigateClient:
    """Client for interacting with Frigate NVR"""
    
    def __init__(self, config: Dict[str, Any]):
        self.frigate_host = config['frigate']['host']
        self.frigate_port = config['frigate']['port']
        self.mqtt_host = config['frigate']['mqtt_host']
        self.mqtt_port = config['frigate']['mqtt_port']
        self.mqtt_user = config['frigate'].get('mqtt_user', '')
        self.mqtt_password = config['frigate'].get('mqtt_password', '')
        
        self.base_url = f"http://{self.frigate_host}:{self.frigate_port}"
        self.mqtt_client = None
        self.event_callback = None
        
    def connect_mqtt(self, event_callback: Callable):
        """Connect to Frigate MQTT broker"""
        self.event_callback = event_callback
        
        self.mqtt_client = mqtt.Client()
        
        if self.mqtt_user:
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        
        logger.info(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.mqtt_client.loop_start()
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT"""
        logger.info(f"Connected to MQTT with result code {rc}")
        # Subscribe to all Frigate events
        client.subscribe("frigate/events")
        client.subscribe("frigate/+/person")
        client.subscribe("frigate/+/dog")
        
    def _on_message(self, client, userdata, msg):
        """Callback when MQTT message received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            if self.event_callback:
                self.event_callback(topic, payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def get_event_snapshot(self, event_id: str, save_path: str) -> bool:
        """Download snapshot image for an event"""
        try:
            url = f"{self.base_url}/api/events/{event_id}/snapshot.jpg"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved snapshot to {save_path}")
                return True
            else:
                logger.warning(f"Failed to get snapshot: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading snapshot: {e}")
            return False
    
    def get_latest_frame(self, camera: str, save_path: str) -> bool:
        """Get latest frame from a camera"""
        try:
            url = f"{self.base_url}/api/{camera}/latest.jpg"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved latest frame to {save_path}")
                return True
            else:
                logger.warning(f"Failed to get latest frame: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading frame: {e}")
            return False
    
    def get_event_clip(self, event_id: str, save_path: str) -> bool:
        """Download video clip for an event"""
        try:
            url = f"{self.base_url}/api/events/{event_id}/clip.mp4"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved clip to {save_path}")
                return True
            else:
                logger.warning(f"Failed to get clip: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading clip: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("Disconnected from MQTT")
