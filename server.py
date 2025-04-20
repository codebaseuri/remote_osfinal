import cv2
import numpy as np
import socket
import pickle
import struct
import mss
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key
import threading
import time
import select
import traceback
import json
import hashlib
import os
import logging
from datetime import datetime, timedelta

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RemoteServer")

class PickleUserDatabase:
    """Simple user database using pickle for storage"""
    
    def __init__(self, db_file="users.pickle"):
        self.db_file = db_file
        self.users = {}  # username -> user datadnigger 
        self.sessions = {}  # token -> session data
        self.load_database()
        logger.info(f"User database initialized with {len(self.users)} users and {len(self.sessions)} active sessions")
    
    def load_database(self):
        """Load the database from pickle file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'rb') as f:
                    data = pickle.load(f)
                    self.users = data.get('users', {})
                    self.sessions = data.get('sessions', {})
                
                # Clean up expired sessions
                self._clean_expired_sessions()
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            # Initialize empty database
            self.users = {}
            self.sessions = {}
    
    def save_database(self):
        """Save the database to pickle file"""
        try:
            # Clean up expired sessions before saving
            self._clean_expired_sessions()
            
            data = {
                'users': self.users,
                'sessions': self.sessions
            }
            
            with open(self.db_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug("Database saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    def _clean_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if session['expires_at'] < now
        ]
        
        for token in expired_tokens:
            del self.sessions[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
    
    def hash_password(self, password):
        """Create a secure hash of a password"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt + key
    
    def verify_password(self, stored_password, provided_password):
        """Verify a password against its stored hash"""
        salt = stored_password[:32]
        stored_key = stored_password[32:]
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        
        return key == stored_key
    
    def register_user(self, username, password, email, fullname=None):
        """Register a new user"""
        # Check if username already exists
        if username in self.users:
            return False, "Username already exists"
        
        # Check for email uniqueness
        for user in self.users.values():
            if user['email'] == email:
                return False, "Email already exists"
        
        # Create new user entry
        user = {
            'username': username,
            'password': self.hash_password(password),
            'email': email,
            'fullname': fullname,
            'created_at': datetime.now(),
            'last_login': None,
            'is_active': True
        }
        
        # Add to users dictionary
        self.users[username] = user
        
        # Save database
        if self.save_database():
            logger.info(f"New user registered: {username}")
            return True, "User registered successfully"
        else:
            return False, "Error saving user data"
    
    def authenticate(self, username, password):
        """Authenticate a user and create a session"""
        # Check if user exists
        if username not in self.users:
            return False, "Invalid username or password"
        
        user = self.users[username]
        
        # Check if user is active
        if not user['is_active']:
            return False, "Account is deactivated"
        
        # Verify password
        if not self.verify_password(user['password'], password):
            return False, "Invalid username or password"
        
        # Update last login time
        user['last_login'] = datetime.now()
        
        # Create session token
        token = self._create_session(username)
        
        # Save changes to database
        self.save_database()
        
        return True, token
    
    def _create_session(self, username, expiry_hours=24):
        """Create a new session for the user"""
        # Generate a random token
        token = hashlib.sha256(os.urandom(64)).hexdigest()
        
        # Set expiry time
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        # Create session
        session = {
            'username': username,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'is_active': True
        }
        
        # Store session
        self.sessions[token] = session
        
        return token
    
    def validate_session(self, token):
        """Validate a session token"""
        # Check if token exists
        if token not in self.sessions:
            return False, "Invalid session token"
        
        session = self.sessions[token]
        
        # Check if session is active
        if not session['is_active']:
            return False, "Session is inactive"
        
        # Check if session has expired
        if session['expires_at'] < datetime.now():
            # Deactivate session
            session['is_active'] = False
            self.save_database()
            return False, "Session has expired"
        
        # Get user information
        username = session['username']
        if username not in self.users:
            return False, "User not found"
        
        return True, self.users[username]
    
    def invalidate_session(self, token):
        """Invalidate a session (logout)"""
        if token in self.sessions:
            self.sessions[token]['is_active'] = False
            self.save_database()
            return True, "Logged out successfully"
        
        return False, "Session not found"
    
    def get_user_info(self, username):
        """Get basic user information"""
        if username in self.users:
            user = self.users[username]
            # Convert datetime objects to strings to avoid JSON serialization issues
            created_at = user['created_at'].isoformat() if user['created_at'] else None
            last_login = user['last_login'].isoformat() if user['last_login'] else None
            
            return {
                'username': user['username'],
                'email': user['email'],
                'fullname': user['fullname'],
                'created_at': created_at,
                'last_login': last_login
            }
        return None
    
    def user_exists(self, username):
        """Check if a user exists"""
        return username in self.users


class RemoteControlServer:
    """
    Remote control server with pickle-based authentication
    """
    
    def __init__(self, host='0.0.0.0', screen_port=5000, mouse_port=5001, auth_port=5002, db_file="users.pickle"):
        # Initialize controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # Initialize screen sharing socket
        self.socket_screen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_screen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_screen.bind((host, screen_port))
        self.socket_screen.listen(1)
        
        # Initialize mouse control socket
        self.socket_mouse = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_mouse.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_mouse.bind((host, mouse_port))
        self.socket_mouse.listen(1)
        
        # Initialize authentication socket
        self.socket_auth = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_auth.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_auth.bind((host, auth_port))
        self.socket_auth.listen(5)
        
        # Initialize screen capture
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[2]  # Get primary monitor (usually index 1)
        
        # Client connections
        self.screen_client = None
        self.mouse_client = None
        
        # Authenticated sessions
        self.screen_token = None
        self.mouse_token = None
        
        # Flags to control serverniggeer 
        self.running = True
        
        # User database
        self.user_db = PickleUserDatabase(db_file)
        
        # Connection logs directory
        self.logs_dir = "connection_logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        logger.info(f"Screen sharing server listening on {host}:{screen_port}")
        logger.info(f"Mouse control server listening on {host}:{mouse_port}")
        logger.info(f"Authentication server listening on {host}:{auth_port}")
        logger.info(f"Using monitor with resolution: {self.monitor['width']}x{self.monitor['height']}")
    
    def start(self):
        """Start all server components"""
        # Start the authentication server thread
        auth_thread = threading.Thread(target=self.handle_authentication)
        auth_thread.daemon = True
        auth_thread.start()
        
        # Start the mouse control thread
        mouse_thread = threading.Thread(target=self.handle_mouse_control)
        mouse_thread.daemon = True
        mouse_thread.start()
        
        # Handle screen sharing in the main thread
        self.handle_screen_sharing()
    
    def handle_authentication(self):
        """Handle authentication requests"""
        while self.running:
            try:
                # Wait for connections with timeout
                readable, _, _ = select.select([self.socket_auth], [], [], 1)
                
                if readable:
                    client_socket, addr = self.socket_auth.accept()
                    logger.info(f"Auth client connected from {addr}")
                    
                    # Handle this client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_auth_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
            except Exception as e:
                logger.error(f"Authentication server error: {e}")
                traceback.print_exc()
                time.sleep(1)
    
    def handle_auth_client(self, client_socket, addr):
        """Handle a single authentication client"""
        try:
            # Set a timeout on the socket
            client_socket.settimeout(10.0)
            
            # Receive message length
            length_data = self.recv_all(client_socket, 4)
            if not length_data:
                logger.warning("No auth message length received")
                return
            
            message_length = int.from_bytes(length_data, byteorder='big')
            
            # Receive message
            message_data = self.recv_all(client_socket, message_length)
            if not message_data:
                logger.warning("No auth message data received")
                return
            
            # Parse message
            try:
                message = json.loads(message_data.decode('utf-8'))
                action = message.get('action')
                
                response = None
                
                if action == 'register':
                    response = self.handle_register(message, addr[0])
                elif action == 'login':
                    response = self.handle_login(message, addr[0])
                elif action == 'logout':
                    response = self.handle_logout(message)
                elif action == 'validate':
                    response = self.handle_validate(message)
                else:
                    response = {
                        'success': False,
                        'message': f"Unknown action: {action}"
                    }
                
                # Send response
                self.send_json_response(client_socket, response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON request")
                response = {
                    'success': False,
                    'message': "Invalid JSON request"
                }
                self.send_json_response(client_socket, response)
        except Exception as e:
            logger.error(f"Error handling auth client: {e}")
            traceback.print_exc()
        finally:
            client_socket.close()
    
    def handle_register(self, request, ip_address):
        """Handle user registration"""
        username = request.get('username')
        password = request.get('password')
        email = request.get('email')
        fullname = request.get('fullname')
        
        # Validate required fields
        if not username or not password or not email:
            return {
                'success': False,
                'message': "Username, password, and email are required"
            }
        
        # Register user
        success, message = self.user_db.register_user(
            username, password, email, fullname
        )
        
        # Log action
        log_message = f"User registration: {username} - {'Success' if success else 'Failed'}"
        self.log_connection("REGISTER", username, ip_address, "SUCCESS" if success else "FAILED")
        logger.info(log_message)
        
        return {
            'success': success,
            'message': message
        }
    
    def handle_login(self, request, ip_address):
        """Handle user login"""
        username = request.get('username')
        password = request.get('password')
        
        # Validate required fields
        if not username or not password:
            return {
                'success': False,
                'message': "Username and password are required"
            }
        
        # Authenticate user
        success, result = self.user_db.authenticate(username, password)
        
        if success:
            # result is the token
            token = result
            user_info = self.user_db.get_user_info(username)
            
            # Log successful login
            self.log_connection("LOGIN", username, ip_address, "SUCCESS")
            logger.info(f"User login successful: {username}")
            
            return {
                'success': True,
                'message': "Login successful",
                'token': token,
                'user': user_info
            }
        else:
            # Log failed login
            self.log_connection("LOGIN", username, ip_address, "FAILED")
            logger.warning(f"User login failed: {username} - {result}")
            
            return {
                'success': False,
                'message': result
            }
    
    def handle_logout(self, request):
        """Handle user logout"""
        token = request.get('token')
        
        if not token:
            return {
                'success': False,
                'message': "Token is required"
            }
        
        # Invalidate session
        success, message = self.user_db.invalidate_session(token)
        
        if success:
            logger.info(f"User logged out: {token[:8]}...")
        
        return {
            'success': success,
            'message': message
        }
    
    def handle_validate(self, request):
        """Handle session validation"""
        token = request.get('token')
        
        if not token:
            return {
                'success': False,
                'message': "Token is required"
            }
        
        # Validate session
        success, result = self.user_db.validate_session(token)
        
        if success:
            # result is the user data
            user_info = self.user_db.get_user_info(result['username'])
            
            return {
                'success': True,
                'message': "Session is valid",
                'user': user_info
            }
        else:
            return {
                'success': False,
                'message': result
            }
    
    def send_json_response(self, socket, response):
        """Send a JSON response with length prefix"""
        try:
            # Convert to JSON bytes using custom encoder for datetime objects
            response_json = json.dumps(response, cls=DateTimeEncoder).encode('utf-8')
            
            # Create length prefix
            length = len(response_json).to_bytes(4, byteorder='big')
            
            # Send response
            socket.sendall(length + response_json)
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            # Try to send a simplified error response if the original failed
            try:
                error_response = {
                    'success': False,
                    'message': f"Server error: {str(e)}"
                }
                error_json = json.dumps(error_response).encode('utf-8')
                error_length = len(error_json).to_bytes(4, byteorder='big')
                socket.sendall(error_length + error_json)
            except:
                logger.error("Failed to send even the error response")
    
    def handle_screen_sharing(self):
        """Handle screen sharing connections in the main thread"""
        while self.running:
            # Accept a screen sharing connection
            logger.info("Waiting for screen sharing client...")
            try:
                readable, _, _ = select.select([self.socket_screen], [], [], 1)
                
                if readable:
                    self.screen_client, addr = self.socket_screen.accept()
                    logger.info(f"Screen client connected from {addr}")
                    
                    # Authenticate the client
                    authenticated, token, username = self.authenticate_service_client(
                        self.screen_client, "screen"
                    )
                    
                    if not authenticated:
                        logger.warning("Screen client authentication failed")
                        self.screen_client.close()
                        self.screen_client = None
                        continue
                    
                    # Store the token for this connection
                    self.screen_token = token
                    
                    # Log successful connection
                    self.log_connection("SCREEN", username, addr[0], "SUCCESS")
                    
                    # Send monitor information
                    self.send_monitor_info()
                    
                    # Main loop for sending screen captures
                    while self.running and self.screen_client:
                        try:
                            # Capture and send screenshot
                            screenshot_data = self.capture_screenshot()
                            message_size = struct.pack("L", len(screenshot_data))
                            self.screen_client.sendall(message_size + screenshot_data)
                            
                            # Short sleep to limit frame rate
                            time.sleep(0.03)
                            
                        except (ConnectionResetError, BrokenPipeError):
                            logger.info("Screen client disconnected")
                            break
                        except Exception as e:
                            logger.error(f"Screen sharing error: {e}")
                            traceback.print_exc()
                            break
                    
                    # Clean up
                    if self.screen_client:
                        self.screen_client.close()
                    
                    self.screen_client = None
                    self.screen_token = None
            except Exception as e:
                logger.error(f"Screen connection error: {e}")
                traceback.print_exc()
                time.sleep(1)
    
    def handle_mouse_control(self):
        """Handle mouse control connections"""
        while self.running:
            try:
                logger.info("Waiting for mouse control client...")
                self.mouse_client, addr = self.socket_mouse.accept()
                logger.info(f"Mouse control client connected from {addr}")
                
                # Authenticate the client
                authenticated, token, username = self.authenticate_service_client(
                    self.mouse_client, "mouse"
                )
                
                if not authenticated:
                    logger.warning("Mouse client authentication failed")
                    self.mouse_client.close()
                    self.mouse_client = None
                    continue
                
                # Store the token for this connection
                self.mouse_token = token
                
                # Log successful connection
                self.log_connection("MOUSE", username, addr[0], "SUCCESS")
                
                # Main loop for processing mouse/keyboard commands
                while self.running and self.mouse_client:
                    try:
                        # Set a timeout to prevent blocking forever
                        self.mouse_client.settimeout(1.0)
                        
                        # Receive message length
                        length_data = self.recv_all(self.mouse_client, 4)
                        if not length_data:
                            logger.debug("No mouse command length received")
                            break
                        
                        message_length = int.from_bytes(length_data, byteorder='big')
                        
                        # Sanity check length
                        if message_length <= 0 or message_length > 1024:
                            logger.warning(f"Invalid mouse command length: {message_length}")
                            break
                        
                        # Receive message
                        message_data = self.recv_all(self.mouse_client, message_length)
                        if not message_data:
                            logger.debug("No mouse command data received")
                            break
                        
                        # Process command
                        command = message_data.decode('utf-8')
                        self.handle_mouse_command(command)
                        
                    except socket.timeout:
                        # This is expected, just continue
                        continue
                    except (ConnectionResetError, BrokenPipeError):
                        logger.info("Mouse client disconnected")
                        break
                    except Exception as e:
                        logger.error(f"Mouse control error: {e}")
                        traceback.print_exc()
                        break
                
                # Clean up
                if self.mouse_client:
                    self.mouse_client.close()
                
                self.mouse_client = None
                self.mouse_token = None
                
            except Exception as e:
                logger.error(f"Mouse control connection error: {e}")
                traceback.print_exc()
                time.sleep(1)
    
    def authenticate_service_client(self, client_socket, service_type):
        """Authenticate a service client using a token"""
        try:
            # Set a timeout
            client_socket.settimeout(10.0)
            
            # Receive token length
            length_data = self.recv_all(client_socket, 4)
            if not length_data:
                logger.warning(f"No {service_type} auth token length received")
                return False, None, None
            
            token_length = int.from_bytes(length_data, byteorder='big')
            
            # Sanity check length
            if token_length <= 0 or token_length > 1024:
                logger.warning(f"Invalid {service_type} auth token length: {token_length}")
                return False, None, None
            
            # Receive token
            token_data = self.recv_all(client_socket, token_length)
            if not token_data:
                logger.warning(f"No {service_type} auth token received")
                return False, None, None
            
            # Validate token
            token = token_data.decode('utf-8')
            success, user_data = self.user_db.validate_session(token)
            
            # Prepare response
            if success:
                username = user_data['username']
                response = {
                    'success': True,
                    'message': f"{service_type} authentication successful"
                }
            else:
                response = {
                    'success': False,
                    'message': f"{service_type} authentication failed: {user_data}"
                }
                username = None
            
            # Send response
            self.send_json_response(client_socket, response)
            
            return success, token, username
            
        except Exception as e:
            logger.error(f"Error during {service_type} authentication: {e}")
            traceback.print_exc()
            
            # Try to send error response
            try:
                response = {
                    'success': False,
                    'message': f"Authentication error: {str(e)}"
                }
                self.send_json_response(client_socket, response)
            except:
                pass
            
            return False, None, None
    
    def send_monitor_info(self):
        """Send monitor information to the screen client"""
        try:
            # Prepare monitor info
            monitor_info = {
                'width': self.monitor['width'],
                'height': self.monitor['height']
            }
            
            # Pickle the data
            monitor_data = pickle.dumps(monitor_info)
            
            # Send with length prefix
            data_size = struct.pack("L", len(monitor_data))
            self.screen_client.sendall(data_size + monitor_data)
            
            logger.info(f"Sent monitor info: {self.monitor['width']}x{self.monitor['height']}")
            
        except Exception as e:
            logger.error(f"Error sending monitor info: {e}")
            traceback.print_exc()
    
    def capture_screenshot(self):
        """Capture and compress a screenshot"""
        # Capture screen
        screenshot = np.array(self.sct.grab(self.monitor))
        
        # Convert from BGRA (from mss) to BGR (for cv2)
        frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        # Resize to reduce bandwidth (optional)
        scale_percent = 100  # Adjust as needed (lower = smaller size)
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        frame = cv2.resize(frame, (width, height))
        
        # Compress as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]  # 85% quality
        _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
        
        # Serialize the compressed frame
        data = pickle.dumps(encoded_frame)
        return data
    
    def handle_mouse_command(self, command):
        """Process mouse and keyboard commands"""
        try:
            parts = command.split(',')
            action = parts[0]
            
            if action == 'move':
                x, y = int(float(parts[1])), int(float(parts[2]))
                self.mouse.position = (x, y)
            elif action == 'click':
                x, y = int(float(parts[1])), int(float(parts[2]))
                self.mouse.position = (x, y)
                self.mouse.click(MouseButton.left)
            elif action == 'right_click':
                x, y = int(float(parts[1])), int(float(parts[2]))
                self.mouse.position = (x, y)
                self.mouse.click(MouseButton.right)
            elif action == 'scroll':
                dx, dy = int(float(parts[1])), int(float(parts[2]))
                self.mouse.scroll(dx, dy)
            elif action == 'key_press':
                key = parts[1]
                if key.startswith('Key.'):
                    key = getattr(Key, key.split('.')[1])
                self.keyboard.press(key)
            elif action == 'key_release':
                key = parts[1]
                if key.startswith('Key.'):
                    key = getattr(Key, key.split('.')[1])
                self.keyboard.release(key)
            else:
                logger.warning(f"Unknown command: {action}")
                
        except Exception as e:
            logger.error(f"Error processing mouse command: {e}")
            traceback.print_exc()
    
    def recv_all(self, sock, length):
        """Receive exactly 'length' bytes from a socket"""
        data = b''
        remaining = length
        max_attempts = 5
        attempts = 0
        
        while remaining > 0:
            try:
                packet = sock.recv(remaining)
                
                if not packet:
                    # Connection closed
                    if not data:
                        return None
                    return data
                
                data += packet
                remaining = length - len(data)
                attempts = 0
                
            except socket.timeout:
                attempts += 1
                
                if attempts >= max_attempts:
                    # Too many timeouts
                    if not data:
                        return None
                    return data
                
                time.sleep(0.1)
        
        return data
    
    def log_connection(self, service_type, username, ip_address, status):
        """Log connection information to a file"""
        try:
            # Create log filename based on date
            date_str = time.strftime("%Y-%m-%d")
            log_file = os.path.join(self.logs_dir, f"connections_{date_str}.log")
            
            # Create log entry
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} | {service_type} | {username or 'Unknown'} | {ip_address} | {status}\n"
            
            # Write to log file
            with open(log_file, 'a') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Error logging connection: {e}")
    
    def stop(self):
        """Stop the server"""
        logger.info("Stopping server...")
        self.running = False
        
        # Close client connections
        if self.screen_client:
            self.screen_client.close()
        
        if self.mouse_client:
            self.mouse_client.close()
        
        # Close server sockets
        self.socket_screen.close()
        self.socket_mouse.close()
        self.socket_auth.close()
        
        logger.info("Server stopped")


if __name__ == "__main__":
    # Create and start the server
    server = RemoteControlServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.stop()