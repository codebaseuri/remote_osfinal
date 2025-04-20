import cv2
import numpy as np
import socket
import pickle
import struct
import threading
import time
import traceback
import json
import logging
import os
import getpass
import sys
from pynput.mouse import Listener as MouseListener, Button as MouseButton
from pynput.keyboard import Listener as KeyboardListener, Key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RemoteClient")

class AuthClient:
    """Authentication client for the remote control system"""
    
    def __init__(self, server_ip='127.0.0.1', auth_port=5002):
        self.server_ip = server_ip
        self.auth_port = auth_port
        self.token = None
        self.user_info = None
        logger.info(f"Auth client initialized for server {server_ip}:{auth_port}")
    
    def register(self, username, password, email, fullname=None):
        """Register a new user"""
        request = {
            'action': 'register',
            'username': username,
            'password': password,
            'email': email,
            'fullname': fullname
        }
        
        logger.info(f"Registering user: {username}")
        return self.send_request(request)
    
    def login(self, username, password):
        """Login with credentials"""
        request = {
            'action': 'login',
            'username': username,
            'password': password
        }
        
        logger.info(f"Logging in user: {username}")
        response = self.send_request(request)
        
        if response.get('success'):
            self.token = response.get('token')
            self.user_info = response.get('user')
            logger.info(f"Login successful for {username}")
        else:
            logger.warning(f"Login failed: {response.get('message')}")
        
        return response
    
    def logout(self):
        """Logout the current user"""
        if not self.token:
            return {'success': False, 'message': 'Not logged in'}
        
        request = {
            'action': 'logout',
            'token': self.token
        }
        
        logger.info("Logging out user")
        response = self.send_request(request)
        
        if response.get('success'):
            self.token = None
            self.user_info = None
            logger.info("Logout successful")
        
        return response
    
    def validate_session(self):
        """Validate the current session"""
        if not self.token:
            return {'success': False, 'message': 'Not logged in'}
        
        request = {
            'action': 'validate',
            'token': self.token
        }
        
        logger.info("Validating session")
        response = self.send_request(request)
        
        if response.get('success'):
            self.user_info = response.get('user')
            logger.info("Session validated successfully")
        else:
            self.token = None
            self.user_info = None
            logger.warning(f"Session validation failed: {response.get('message')}")
        
        return response
    
    def send_request(self, request):
        """Send an authentication request to the server"""
        try:
            # Create socket
            auth_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            auth_socket.settimeout(10.0)  # 10 seconds timeout
            
            # Connect to server
            logger.debug(f"Connecting to auth server at {self.server_ip}:{self.auth_port}")
            auth_socket.connect((self.server_ip, self.auth_port))
            
            # Convert request to JSON
            request_json = json.dumps(request).encode('utf-8')
            
            # Create 4-byte length prefix
            length = len(request_json).to_bytes(4, byteorder='big')
            
            # Send request
            auth_socket.sendall(length + request_json)
            
            # Receive response length
            length_data = auth_socket.recv(4)
            response_length = int.from_bytes(length_data, byteorder='big')
            
            # Receive response
            response_data = b''
            remaining = response_length
            
            while remaining > 0:
                chunk = auth_socket.recv(min(4096, remaining))
                if not chunk:
                    break
                response_data += chunk
                remaining -= len(chunk)
            
            # Parse response
            try:
                response = json.loads(response_data.decode('utf-8'))
                return response
            except json.JSONDecodeError as e:
                # Log the problematic data for debugging
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Response data (first 100 chars): {response_data[:100]}")
                return {'success': False, 'message': f'JSON parsing error: {str(e)}'}
            
        except socket.timeout:
            logger.error("Connection to auth server timed out")
            return {'success': False, 'message': 'Connection timeout'}
        except ConnectionRefusedError:
            logger.error("Connection to auth server refused")
            return {'success': False, 'message': 'Connection refused'}
        except Exception as e:
            logger.error(f"Error connecting to auth server: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
        finally:
            try:
                auth_socket.close()
            except:
                pass
    
    def is_authenticated(self):
        """Check if the client is authenticated"""
        return self.token is not None
    
    def get_token(self):
        """Get the current authentication token"""
        return self.token
    
    def get_user_info(self):
        """Get the user information"""
        return self.user_info


class RemoteControlClient:
    """Client for remote control with authentication"""
    
    def __init__(self, server_ip='127.0.0.1', screen_port=5000, mouse_port=5001, auth_client=None):
        self.server_ip = server_ip
        self.screen_port = screen_port
        self.mouse_port = mouse_port
        
        # Authentication client
        self.auth_client = auth_client
        
        # Flag to control threads
        self.running = True
        
        # Flag to enable/disable mouse and keyboard control
        self.control_enabled = True
        
        # Initialize screen sharing socket
        self.screen_socket = None
        
        # Initialize mouse control socket
        self.mouse_socket = None
        self.mouse_connected = False
        
        # Scale factor for screen resolution differences
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Server screen dimensions
        self.server_width = 0
        self.server_height = 0
        self.server_aspect_ratio = 1.0
        
        # Client window dimensions
        self.window_width = 0
        self.window_height = 0
        
        # GUI window information for better coordinate scaling
        self.gui_window_info = None
        
        # UI correction factor for the window title bar
        self.ui_offset_y = -25
        
        # Track pressed keys to prevent repeats
        self.pressed_keys = set()
        
        # Add a lock for the pressed_keys set
        self.keys_lock = threading.Lock()
        
        # Mouse and keyboard listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Latest frame received
        self.latest_frame = None
        
        # Callback for frame updates
        self.frame_callback = None
        
        # Add a keyboard mode flag
        self.keyboard_mode = "typing"  # "typing" or "command"
        self.keyboard_mode_switch_time = 0
        self.status_message = ""
        self.status_display_time = 0
        
        logger.info(f"Remote control client initialized for server {server_ip}")
    
    def start(self, frame_callback=None):
        """Start the client with threads for screen sharing and mouse control"""
        if not self.auth_client or not self.auth_client.is_authenticated():
            logger.error("Authentication required before starting remote control")
            return False
        
        # Set frame callback
        self.frame_callback = frame_callback
        
        # Create and start mouse control thread
        mouse_thread = threading.Thread(target=self.setup_mouse_control)
        mouse_thread.daemon = True
        mouse_thread.start()
        
        # Short delay to allow mouse connection to establish
        time.sleep(1)
        
        # Create and start screen sharing thread
        screen_thread = threading.Thread(target=self.handle_screen_sharing)
        screen_thread.daemon = True
        screen_thread.start()
        
        return True
    
    def stop(self):
        """Stop the client"""
        logger.info("Stopping remote control client")
        self.running = False
        
        # Clean up listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Close sockets
        if self.screen_socket:
            try:
                self.screen_socket.close()
            except:
                pass
        
        if self.mouse_socket:
            try:
                self.mouse_socket.close()
            except:
                pass
        
        # Close any open windows
        cv2.destroyAllWindows()
        
        logger.info("Remote control client stopped")
    
    def handle_screen_sharing(self):
        """Handle receiving screen shares from the server"""
        try:
            # Create socket
            self.screen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info(f"Connecting to screen sharing server at {self.server_ip}:{self.screen_port}...")
            self.screen_socket.connect((self.server_ip, self.screen_port))
            logger.info("Connected to screen sharing server")
            
            # Authenticate with screen server
            if not self.auth_client or not self.auth_client.is_authenticated():
                logger.error("Authentication required for screen sharing")
                return
            
            # Send authentication token
            token = self.auth_client.get_token()
            token_bytes = token.encode('utf-8')
            token_length = len(token_bytes).to_bytes(4, byteorder='big')
            self.screen_socket.sendall(token_length + token_bytes)
            
            # Receive authentication response
            auth_response = self.receive_json_response(self.screen_socket)
            
            if not auth_response.get('success'):
                logger.error(f"Screen authentication failed: {auth_response.get('message')}")
                return
            
            logger.info("Screen authentication successful")
            
            # Receive monitor information
            data = b""
            payload_size = struct.calcsize("L")
            
            # First message is the server's monitor information
            while len(data) < payload_size:
                packet = self.screen_socket.recv(4096)
                if not packet:
                    raise ConnectionError("Connection closed by server")
                data += packet
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]
            
            # Receive monitor info data
            while len(data) < msg_size:
                packet = self.screen_socket.recv(4096)
                if not packet:
                    raise ConnectionError("Connection closed by server")
                data += packet
            
            monitor_info_data = data[:msg_size]
            data = data[msg_size:]
            
            # Deserialize monitor info
            monitor_info = pickle.loads(monitor_info_data)
            self.server_width = monitor_info['width']
            self.server_height = monitor_info['height']
            self.server_aspect_ratio = self.server_width / self.server_height
            logger.info(f"Server monitor dimensions: {self.server_width}x{self.server_height}, aspect ratio: {self.server_aspect_ratio:.2f}")
            
            # Display initial keyboard mode
            self.show_status("TYPING MODE - Press Tab to enter command mode", 5.0)
            
            # Main loop for receiving frames
            while self.running:
                try:
                    # Receive message size
                    while len(data) < payload_size:
                        packet = self.screen_socket.recv(4096)
                        if not packet:
                            raise ConnectionError("Connection closed by server")
                        data += packet
                    
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("L", packed_msg_size)[0]
                    
                    # Receive frame data
                    while len(data) < msg_size:
                        packet = self.screen_socket.recv(4096)
                        if not packet:
                            raise ConnectionError("Connection closed by server")
                        data += packet
                    
                    frame_data = data[:msg_size]
                    data = data[msg_size:]
                    
                    # Deserialize and display frame
                    encoded_frame = pickle.loads(frame_data)
                    frame = cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)
                    
                    # Store the latest frame
                    self.latest_frame = frame.copy()
                    display_frame = frame.copy()  # Make a copy for status display
                    
                    # Display status message if needed
                    current_time = time.time()
                    if current_time < self.status_display_time:
                        # Add status message overlay to frame
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        # Add a dark background behind the text for better visibility
                        text_size = cv2.getTextSize(self.status_message, font, 1, 2)[0]
                        cv2.rectangle(display_frame, (15, 15), (25 + text_size[0], 60), (0, 0, 0), -1)
                        cv2.putText(display_frame, self.status_message, (20, 50), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    
                    # If a callback is provided, call it with the frame
                    if self.frame_callback:
                        self.frame_callback(display_frame)
                    else:
                        # Display the frame in a named window
                        cv2.imshow('Remote Screen', display_frame)
                        
                        # Update window dimensions for accurate scaling
                        window_rect = cv2.getWindowImageRect('Remote Screen')
                        if window_rect is not None and window_rect[2] > 0 and window_rect[3] > 0:
                            self.window_width = window_rect[2]
                            self.window_height = window_rect[3]
                            
                            # Update scaling factors
                            self.scale_x = self.server_width / self.window_width
                            self.scale_y = self.server_height / self.window_height
                        
                        # Check for key presses
                        key = cv2.waitKey(1) & 0xFF
                        
                        # Handle keyboard mode toggle with Tab key (ASCII 9)
                        if key == 9:  # Tab key
                            self.toggle_keyboard_mode()
                        elif self.keyboard_mode == "command":
                            # In command mode, handle special keys
                            if key == ord('q'):  # 'q' to quit
                                self.show_status("Disconnecting...")
                                logger.info("Received quit command, disconnecting")
                                self.running = False
                                break
                            elif key == ord('c'):  # 'c' to toggle control
                                self.control_enabled = not self.control_enabled
                                status = "enabled" if self.control_enabled else "disabled"
                                self.show_status(f"Control {status}")
                                logger.info(f"Mouse and keyboard control {status}")
                            elif key == ord('u'):  # 'u' to adjust mouse position DOWN
                                self.ui_offset_y -= 5
                                self.show_status(f"Y offset: {self.ui_offset_y}")
                                logger.info(f"UI offset Y changed to {self.ui_offset_y}")
                            elif key == ord('d'):  # 'd' to adjust mouse position UP
                                self.ui_offset_y += 5
                                self.show_status(f"Y offset: {self.ui_offset_y}")
                                logger.info(f"UI offset Y changed to {self.ui_offset_y}")
                        
                except ConnectionError as e:
                    logger.error(f"Screen sharing connection error: {e}")
                    break
                except Exception as e:
                    logger.error(f"Screen sharing error: {e}")
                    traceback.print_exc()
                    continue
            
        except Exception as e:
            logger.error(f"Screen sharing connection failed: {e}")
            traceback.print_exc()
        finally:
            if self.screen_socket:
                self.screen_socket.close()
            if not self.frame_callback:
                cv2.destroyAllWindows()
            self.running = False
    
    def toggle_keyboard_mode(self):
        """Toggle between typing and command mode"""
        if self.keyboard_mode == "typing":
            self.keyboard_mode = "command"
            self.show_status("COMMAND MODE - Press Tab to return to typing mode")
        else:
            self.keyboard_mode = "typing"
            self.show_status("TYPING MODE - Press Tab to enter command mode")
        
        self.keyboard_mode_switch_time = time.time()
        logger.info(f"Keyboard mode switched to: {self.keyboard_mode}")
    
    def show_status(self, message, duration=3.0):
        """Show a status message overlay on the screen"""
        self.status_message = message
        self.status_display_time = time.time() + duration
        logger.info(f"Status message: {message}")
    
    def setup_mouse_control(self):
        """Set up mouse and keyboard control"""
        while self.running:
            try:
                if not self.mouse_connected:
                    # Create a new socket
                    if self.mouse_socket:
                        self.mouse_socket.close()
                    
                    self.mouse_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    logger.info(f"Connecting to mouse control server at {self.server_ip}:{self.mouse_port}...")
                    self.mouse_socket.connect((self.server_ip, self.mouse_port))
                    
                    # Authenticate with mouse server
                    if not self.auth_client or not self.auth_client.is_authenticated():
                        logger.error("Authentication required for mouse control")
                        time.sleep(2)
                        continue
                    
                    # Send authentication token
                    token = self.auth_client.get_token()
                    token_bytes = token.encode('utf-8')
                    token_length = len(token_bytes).to_bytes(4, byteorder='big')
                    self.mouse_socket.sendall(token_length + token_bytes)
                    
                    # Receive authentication response
                    auth_response = self.receive_json_response(self.mouse_socket)
                    
                    if not auth_response.get('success'):
                        logger.error(f"Mouse authentication failed: {auth_response.get('message')}")
                        time.sleep(2)
                        continue
                    
                    logger.info("Mouse authentication successful")
                    self.mouse_connected = True
                    
                    # Start the input listeners
                    self.start_input_listeners()
                
                # Keep checking connection
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Mouse control connection failed: {e}")
                traceback.print_exc()
                self.mouse_connected = False
                time.sleep(2)  # Wait before trying to reconnect
    
    def receive_json_response(self, socket):
        """Receive a JSON response with length prefix"""
        try:
            # Receive length prefix (4 bytes)
            length_data = socket.recv(4)
            if not length_data or len(length_data) != 4:
                return {'success': False, 'message': 'No response received'}
            
            response_length = int.from_bytes(length_data, byteorder='big')
            
            # Sanity check the length
            if response_length <= 0 or response_length > 100000:  # Arbitrary reasonable limit
                return {'success': False, 'message': f'Invalid response length: {response_length}'}
            
            # Receive response data
            response_data = b''
            remaining = response_length
            
            while remaining > 0:
                chunk = socket.recv(min(4096, remaining))
                if not chunk:
                    break
                response_data += chunk
                remaining -= len(chunk)
            
            # Parse JSON response
            if response_data:
                try:
                    return json.loads(response_data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    # Log the problematic data for debugging
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response data (first 100 chars): {response_data[:100]}")
                    return {'success': False, 'message': f'JSON parsing error: {str(e)}'}
            else:
                return {'success': False, 'message': 'Empty response received'}
                
        except Exception as e:
            logger.error(f"Error receiving response: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def set_gui_window_info(self, x, y, width, height):
        """
        Set the frame display dimensions for GUI mode
        Used for proper mouse coordinate scaling
        
        Args:
            x (int): X coordinate of the frame display
            y (int): Y coordinate of the frame display
            width (int): Width of the frame display
            height (int): Height of the frame display
        """
        self.gui_window_info = (x, y, width, height)
        
        # Update scaling factors for GUI mode
        if width > 0 and height > 0:
            self.scale_x = self.server_width / width
            self.scale_y = self.server_height / height
            logger.debug(f"Updated GUI scaling factors: {self.scale_x}, {self.scale_y}")
    
    def start_input_listeners(self):
        """Start the mouse and keyboard listeners"""
        # Define event handlers
        def on_move(x, y):
            if self.control_enabled and self.mouse_connected:
                # Apply scaling to convert client coordinates to server coordinates
                scaled_x, scaled_y = self.scale_mouse_coordinates(x, y)
                if scaled_x is not None and scaled_y is not None:
                    self.send_command(f'move,{scaled_x},{scaled_y}')
        
        def on_click(x, y, button, pressed):
            if self.control_enabled and self.mouse_connected:
                if pressed:
                    # Apply scaling to convert client coordinates to server coordinates
                    scaled_x, scaled_y = self.scale_mouse_coordinates(x, y)
                    if scaled_x is not None and scaled_y is not None:
                        if button == MouseButton.left:
                            self.send_command(f'click,{scaled_x},{scaled_y}')
                        elif button == MouseButton.right:
                            self.send_command(f'right_click,{scaled_x},{scaled_y}')
            return self.running  # Continue if running
        
        def on_scroll(x, y, dx, dy):
            if self.control_enabled and self.mouse_connected:
                self.send_command(f'scroll,{dx},{dy}')
            return self.running  # Continue if running
        
        def on_press(key):
            # Skip Tab key (used for toggling keyboard modes)
            if key == Key.tab:
                return self.running
                
            # Skip command keys in command mode to avoid sending them to the server
            if self.keyboard_mode == "command":
                if hasattr(key, 'char') and key.char in ['q', 'c', 'u', 'd']:
                    return self.running
            
            if self.control_enabled and self.mouse_connected:
                try:
                    # Convert key to a consistent string representation
                    if hasattr(key, 'char') and key.char is not None:
                        key_str = f"char_{key.char}"
                    else:
                        key_str = f"key_{str(key)}"
                    
                    # Thread-safe check and update of pressed keys
                    with self.keys_lock:
                        # Only send press event if this key is not already pressed
                        if key_str not in self.pressed_keys:
                            if hasattr(key, 'char') and key.char is not None:
                                self.send_command(f'key_press,{key.char}')
                            else:
                                self.send_command(f'key_press,{key}')
                            self.pressed_keys.add(key_str)
                except Exception as e:
                    logger.error(f"Error in key press handler: {e}")
            return self.running  # Continue if running
        
        def on_release(key):
            # Skip Tab key (used for toggling keyboard modes)
            if key == Key.tab:
                return self.running
                
            # Skip command keys in command mode
            if self.keyboard_mode == "command":
                if hasattr(key, 'char') and key.char in ['q', 'c', 'u', 'd']:
                    return self.running
            
            if self.control_enabled and self.mouse_connected:
                try:
                    # Convert key to the same string representation used in on_press
                    if hasattr(key, 'char') and key.char is not None:
                        key_str = f"char_{key.char}"
                    else:
                        key_str = f"key_{str(key)}"
                    
                    # Send the release command
                    if hasattr(key, 'char') and key.char is not None:
                        self.send_command(f'key_release,{key.char}')
                    else:
                        self.send_command(f'key_release,{key}')
                    
                    # Thread-safe update of pressed keys
                    with self.keys_lock:
                        # Remove from pressed keys set
                        if key_str in self.pressed_keys:
                            self.pressed_keys.remove(key_str)
                except Exception as e:
                    logger.error(f"Error in key release handler: {e}")
            return self.running  # Continue if running
        
        # Stop any existing listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Start listeners in non-blocking mode
        self.mouse_listener = MouseListener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.mouse_listener.start()
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
    
    def scale_mouse_coordinates(self, x, y):
        """
        Scale mouse coordinates from client space to server space
        and check if mouse is within the remote screen window
        """
        try:
            # For GUI mode, use the frame dimensions directly instead of OpenCV window
            if self.frame_callback and self.gui_window_info:
                # Get frame display dimensions from the GUI
                frame_x, frame_y, frame_width, frame_height = self.gui_window_info
                
                # Check if coordinates are within frame area
                if (frame_x <= x < frame_x + frame_width and
                    frame_y <= y < frame_y + frame_height):
                    
                    # Convert to relative frame coordinates
                    rel_x = x - frame_x
                    rel_y = y - frame_y
                    
                    # Apply scaling to match server resolution
                    # Make sure we're not dividing by zero
                    if frame_width > 0 and frame_height > 0:
                        # Calculate scaling based on aspect ratio preservation
                        server_aspect = self.server_width / self.server_height
                        frame_aspect = frame_width / frame_height
                        
                        if server_aspect > frame_aspect:
                            # Frame is taller relative to width
                            scale_factor = self.server_width / frame_width
                            # Adjust Y to account for letterboxing
                            effective_height = self.server_width / server_aspect
                            y_offset = (frame_height - (frame_width / server_aspect)) / 2
                            
                            # If the click is in the letterbox area, ignore it
                            if rel_y < y_offset or rel_y > frame_height - y_offset:
                                return None, None
                                
                            # Adjust Y coordinate
                            rel_y = rel_y - y_offset
                            
                            server_x = int(rel_x * (self.server_width / frame_width))
                            server_y = int(rel_y * (self.server_height / (frame_height - 2 * y_offset)))
                        else:
                            # Frame is wider relative to height
                            scale_factor = self.server_height / frame_height
                            # Adjust X to account for pillarboxing
                            effective_width = self.server_height * frame_aspect
                            x_offset = (frame_width - (frame_height * server_aspect)) / 2
                            
                            # If the click is in the pillarbox area, ignore it
                            if rel_x < x_offset or rel_x > frame_width - x_offset:
                                return None, None
                                
                            # Adjust X coordinate
                            rel_x = rel_x - x_offset
                            
                            server_x = int(rel_x * (self.server_width / (frame_width - 2 * x_offset)))
                            server_y = int(rel_y * (self.server_height / frame_height))
                        
                        # Apply UI offset to Y coordinate
                        server_y += self.ui_offset_y
                        
                        # Ensure the coordinates stay within server screen bounds
                        server_x = max(0, min(server_x, self.server_width - 1))
                        server_y = max(0, min(server_y, self.server_height - 1))
                        
                        # Log coordinates for debugging only at debug level
                        logger.debug(f"GUI mode: Mouse at {x},{y} -> server {server_x},{server_y}")
                        
                        return server_x, server_y
            
                return None, None
                
            # For OpenCV window mode
            window_rect = cv2.getWindowImageRect('Remote Screen')
            if window_rect is None:
                return None, None
                
            window_x, window_y, window_width, window_height = window_rect
            
            # Check if coordinates are within window
            if (window_x <= x < window_x + window_width and
                window_y <= y < window_y + window_height):
                
                # Convert to relative window coordinates
                rel_x = x - window_x
                rel_y = y - window_y
                
                # Calculate how much of the window is actually displaying the image
                # (accounting for letterboxing/pillarboxing)
                server_aspect = self.server_width / self.server_height
                window_aspect = window_width / window_height
                
                if server_aspect > window_aspect:
                    # Window is taller relative to width (letterboxing)
                    effective_height = window_width / server_aspect
                    vertical_padding = (window_height - effective_height) / 2
                    
                    # Check if click is in the letterbox area
                    if rel_y < vertical_padding or rel_y > (window_height - vertical_padding):
                        return None, None
                    
                    # Adjust y coordinate to account for letterboxing
                    rel_y = rel_y - vertical_padding
                    
                    # Scale coordinates
                    server_x = int(rel_x * (self.server_width / window_width))
                    server_y = int(rel_y * (self.server_height / effective_height)) + self.ui_offset_y
                else:
                    # Window is wider relative to height (pillarboxing)
                    effective_width = window_height * server_aspect
                    horizontal_padding = (window_width - effective_width) / 2
                    
                    # Check if click is in the pillarbox area
                    if rel_x < horizontal_padding or rel_x > (window_width - horizontal_padding):
                        return None, None
                    
                    # Adjust x coordinate to account for pillarboxing
                    rel_x = rel_x - horizontal_padding
                    
                    # Scale coordinates
                    server_x = int(rel_x * (self.server_width / effective_width))
                    server_y = int(rel_y * (self.server_height / window_height)) + self.ui_offset_y
                
                # Ensure the coordinates stay within server screen bounds
                server_x = max(0, min(server_x, self.server_width - 1))
                server_y = max(0, min(server_y, self.server_height - 1))
                
                # Log coordinates for debugging
                logger.debug(f"OpenCV mode: Mouse at {x},{y} -> server {server_x},{server_y}")
                
                return server_x, server_y
            
            return None, None
        except Exception as e:
            logger.error(f"Error scaling mouse coordinates: {e}")
            traceback.print_exc()
            return None, None
    
    def send_command(self, command):
        """Send a command to the server with a length prefix"""
        if self.mouse_socket and self.mouse_connected:
            try:
                # Encode the command string to bytes
                command_bytes = command.encode('utf-8')
                
                # Create the 4-byte length prefix
                length = len(command_bytes).to_bytes(4, byteorder='big')
                
                # Combine length prefix and command data
                complete_message = length + command_bytes
                
                # Use sendall to ensure the entire message is sent
                self.mouse_socket.sendall(complete_message)
                
            except (ConnectionResetError, BrokenPipeError) as e:
                logger.error(f"Lost connection to server: {e}")
                self.mouse_connected = False
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                traceback.print_exc()
                self.mouse_connected = False
    
    def get_latest_frame(self):
        """Get the latest received frame"""
        return self.latest_frame
    
    def is_connected(self):
        """Check if the client is connected to the server"""
        return self.screen_socket is not None and self.mouse_connected
    
    def toggle_control(self):
        """Toggle mouse and keyboard control"""
        self.control_enabled = not self.control_enabled
        status = "enabled" if self.control_enabled else "disabled"
        logger.info(f"Mouse and keyboard control {status}")
        return self.control_enabled


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print a banner for the console interface"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║               REMOTE CONTROL CLIENT                   ║
║                                                       ║
║  Connect to and control remote computers securely     ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)


def login_menu(auth_client, server_ip):
    """Handle user login"""
    clear_screen()
    print_banner()
    print("LOGIN")
    print("=====")
    
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    print("\nLogging in...")
    result = auth_client.login(username, password)
    
    if result.get('success'):
        print("\n✓ Login successful!")
        time.sleep(1)
        return True
    else:
        print(f"\n✗ Login failed: {result.get('message')}")
        input("\nPress Enter to continue...")
        return False


def register_menu(auth_client, server_ip):
    """Handle user registration"""
    clear_screen()
    print_banner()
    print("REGISTER NEW ACCOUNT")
    print("===================")
    
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    
    if password != confirm_password:
        print("\n✗ Passwords do not match!")
        input("\nPress Enter to continue...")
        return False
    
    email = input("Email: ")
    fullname = input("Full Name (optional): ")
    
    print("\nRegistering account...")
    result = auth_client.register(
        username=username,
        password=password,
        email=email,
        fullname=fullname if fullname else None
    )
    
    if result.get('success'):
        print("\n✓ Registration successful! You can now login.")
        input("\nPress Enter to continue...")
        return True
    else:
        print(f"\n✗ Registration failed: {result.get('message')}")
        input("\nPress Enter to continue...")
        return False


def show_menu():
    """Show the main menu"""
    clear_screen()
    print_banner()
    print("MAIN MENU")
    print("=========")
    print("1. Login")
    print("2. Register New Account")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    return choice


def start_remote_control(auth_client, server_ip):
    """Start the remote control client"""
    if not auth_client.is_authenticated():
        print("Authentication required. Please login first.")
        return
    
    clear_screen()
    print_banner()
    print("REMOTE CONTROL")
    print("==============")
    
    user_info = auth_client.get_user_info()
    username = user_info.get('username', 'Unknown')
    print(f"Logged in as: {username}")
    
    print(f"\nConnecting to server at {server_ip}...")
    
    # Create and start remote client
    remote_client = RemoteControlClient(
        server_ip=server_ip,
        auth_client=auth_client
    )
    
    try:
        if not remote_client.start():
            print("\n✗ Failed to start remote client.")
            input("\nPress Enter to continue...")
            return
            
        print("\n✓ Connected to remote server!")
        print("\nRemote screen should now be visible in a separate window.")
        print("\nKEYBOARD MODES:")
        print("- Press Tab to switch between Typing mode and Command mode")
        print("- In Command mode, you can use these keys:")
        print("  q: Quit/disconnect")
        print("  c: Toggle control on/off")
        print("  u: Adjust mouse position down")
        print("  d: Adjust mouse position up")
        print("\nBy default, you start in Typing mode where all keys are sent to the remote computer.")
        
        # Keep main thread alive until client stops
        while remote_client.running:
            time.sleep(0.1)
        
        print("\nDisconnected from server.")
        
    except Exception as e:
        print(f"\n✗ Error connecting to server: {e}")
    finally:
        remote_client.stop()
    
    input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    # Parse command line arguments for server IP
    server_ip = "10.100.102.12"  # Default value
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    
    # Create authentication client
    auth_client = AuthClient(server_ip=server_ip)
    
    # Main application loop
    while True:
        if auth_client.is_authenticated():
            clear_screen()
            print_banner()
            
            user_info = auth_client.get_user_info()
            username = user_info.get('username', 'Unknown')
            print(f"Logged in as: {username}")
            
            print("\nOPTIONS")
            print("=======")
            print("1. Start Remote Control")
            print("2. Logout")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == '1':
                start_remote_control(auth_client, server_ip)
            elif choice == '2':
                print("\nLogging out...")
                auth_client.logout()
                print("✓ Logged out successfully.")
                time.sleep(1)
            elif choice == '3':
                break
            else:
                print("\nInvalid choice. Please try again.")
                time.sleep(1)
        else:
            choice = show_menu()
            
            if choice == '1':
                login_menu(auth_client, server_ip)
            elif choice == '2':
                register_menu(auth_client, server_ip)
            elif choice == '3':
                break
            else:
                print("\nInvalid choice. Please try again.")
                time.sleep(1)
    
    clear_screen()
    print("Thank you for using Remote Control Client.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...\n")
        sys.exit(0)
