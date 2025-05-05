import socket
import json
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AuthClient")

class AuthClient:
    """Authentication client for the remote control system"""
    
    def __init__(self, server_ip='10.100.102.12', auth_port=5002):
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
