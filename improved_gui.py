import sys
import os
import cv2
import numpy as np
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDesktopWidget, QStackedWidget, 
    QFormLayout, QGroupBox, QFrame, QGridLayout, QSpacerItem, QSizePolicy,
    QTabWidget, QCheckBox, QComboBox, QStatusBar, QToolBar, QAction, QShortcut,
    QDialog
)
from PyQt5.QtGui import (
    QPixmap, QFont, QPalette, QColor, QImage, QIcon, QPainter, 
    QBrush, QLinearGradient, QRadialGradient, QPen, QKeySequence
)
from PyQt5.QtCore import (
    Qt, QTimer, QSize, QThread, pyqtSignal, QRect, QPoint, QEvent
)
import threading
import time

# Import our extracted client classes
from remote_client import RemoteControlClient
from auth_client import AuthClient

# Background thread for frame updates
class VideoThread(QThread):
    update_frame = pyqtSignal(np.ndarray)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True
    
    def run(self):
        while self.running:
            try:
                frame = self.client.get_latest_frame()
                if frame is not None:
                    self.update_frame.emit(frame)
            except Exception as e:
                print(f"Video thread error: {e}")
            self.msleep(30)  # ~30 FPS
    
    def stop(self):
        self.running = False
        self.wait()

# Full-screen remote display window
class RemoteDisplayWindow(QMainWindow):
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remote Display")
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Get screen size for responsive design
        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Set window size to 90% of screen size
        self.window_width = int(self.screen_width * 0.9)
        self.window_height = int(self.screen_height * 0.9)
        self.setGeometry(
            (self.screen_width - self.window_width) // 2,
            (self.screen_height - self.window_height) // 2,
            self.window_width, 
            self.window_height
        )
        
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Status bar for information
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create a toolbar with controls
        self.toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # Add fullscreen action
        self.fullscreen_action = QAction("Fullscreen", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.toolbar.addAction(self.fullscreen_action)
        
        # Add control toggle action
        self.control_action = QAction("Control Enabled", self)
        self.control_action.setCheckable(True)
        self.control_action.setChecked(True)
        self.control_action.triggered.connect(self.toggle_control)
        self.toolbar.addAction(self.control_action)
        
        # Add mode toggle action
        self.mode_action = QAction("Mode: Typing", self)
        self.mode_action.setCheckable(True)
        self.mode_action.setChecked(False)  # Typing mode is unchecked by default
        self.mode_action.triggered.connect(self.toggle_mode)
        self.toolbar.addAction(self.mode_action)

        # Current keyboard mode (typing or command)
        self.current_mode = "typing"
        
        # Spacer to push disconnect to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Add disconnect action
        self.disconnect_action = QAction("Disconnect", self)
        self.disconnect_action.triggered.connect(self.close)
        self.toolbar.addAction(self.disconnect_action)
        
        # Frame display
        self.frame_display = QLabel("Connecting to remote computer...")
        self.frame_display.setAlignment(Qt.AlignCenter)
        self.frame_display.setMinimumSize(800, 600)
        self.frame_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.frame_display)
        
        # Settings for handling mouse events
        self.setMouseTracking(True)
        self.frame_display.setMouseTracking(True)
        
        # Install event filter to catch all events
        self.frame_display.installEventFilter(self)
        
        # F11 shortcut for fullscreen
        self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        
        # Escape shortcut to exit fullscreen
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.exit_fullscreen)
        
        # Add shortcut for toggle control (Ctrl+T)
        self.control_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.control_shortcut.activated.connect(self.toggle_control)
        
        # Reference to remote client
        self.remote_client = None
        self.control_enabled = True
        
        # Set a timer to update frame geometry periodically
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frame_geometry)
        self.update_timer.start(1000)  # Update every second
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar.show()
            self.statusBar().show()
            self.fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self.toolbar.hide()
            self.statusBar().hide()
            self.fullscreen_action.setChecked(True)
        
        # Update frame geometry after toggling fullscreen
        QTimer.singleShot(200, self.update_frame_geometry)
    
    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar.show()
            self.statusBar().show()
            self.fullscreen_action.setChecked(False)
            
            # Update frame geometry after exiting fullscreen
            QTimer.singleShot(200, self.update_frame_geometry)
    
    def toggle_control(self):
        self.control_enabled = not self.control_enabled
        if self.control_enabled:
            self.control_action.setText("Control Enabled")
            self.status_bar.showMessage("Remote control enabled", 3000)
        else:
            self.control_action.setText("Control Disabled")
            self.status_bar.showMessage("Remote control disabled", 3000)
        
        self.control_action.setChecked(self.control_enabled)
        
        # Update control status in the remote client
        if self.remote_client:
            self.remote_client.control_enabled = self.control_enabled
    
    def toggle_mode(self):
        """Toggle between typing and command mode"""
        if self.current_mode == "typing":
            self.current_mode = "command"
            self.mode_action.setText("Mode: Command")
            self.mode_action.setChecked(True)
            self.status_bar.showMessage("COMMAND MODE - Special keys active (q=quit, c=toggle control, u/d=offset)", 3000)
        else:
            self.current_mode = "typing"
            self.mode_action.setText("Mode: Typing")
            self.mode_action.setChecked(False)
            self.status_bar.showMessage("TYPING MODE - All keys sent to remote computer", 3000)
        
        # Update mode in the remote client
        if self.remote_client:
            self.remote_client.keyboard_mode = self.current_mode
            # Call the client's show_status method to display on screen
            self.remote_client.show_status(f"{self.current_mode.upper()} MODE", 3.0)
    
    def set_remote_client(self, client):
        self.remote_client = client
        self.update_frame_geometry()
    
    def update_frame(self, frame):
        """Update the displayed frame with status overlay if needed"""
        try:
            if frame is None:
                return
                
            # Make a copy of the frame for overlay display
            display_frame = frame.copy()
            
            # Add mode indicator to the frame
            font = cv2.FONT_HERSHEY_SIMPLEX
            mode_text = f"MODE: {self.current_mode.upper()}"
            text_size = cv2.getTextSize(mode_text, font, 0.7, 2)[0]
            
            # Add a semi-transparent background for better visibility
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (10, 10), (30 + text_size[0], 40), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, display_frame, 0.4, 0, display_frame)
            
            # Add mode text
            cv2.putText(display_frame, mode_text, (20, 30), font, 0.7, 
                        (0, 255, 0) if self.current_mode == "typing" else (0, 165, 255), 
                        2, cv2.LINE_AA)
            
            # Add control status if disabled
            if not self.control_enabled:
                control_text = "CONTROL DISABLED"
                control_size = cv2.getTextSize(control_text, font, 0.7, 2)[0]
                
                # Add background for control status
                overlay = display_frame.copy()
                cv2.rectangle(overlay, (10, 50), (30 + control_size[0], 80), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, display_frame, 0.4, 0, display_frame)
                
                # Add control status text
                cv2.putText(display_frame, control_text, (20, 70), font, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Convert OpenCV BGR format to RGB for Qt
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            
            # Create QImage from the RGB data
            qt_image = QImage(rgb_frame.data, w, h, w * ch, QImage.Format_RGB888)
            
            # Convert to pixmap and display
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale pixmap to fit the label while maintaining aspect ratio
            pixmap = pixmap.scaled(
                self.frame_display.width(),
                self.frame_display.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.frame_display.setPixmap(pixmap)
            
            # Update the frame geometry info in the client
            self.update_frame_geometry()
            
        except Exception as e:
            print(f"Error updating frame: {e}")
            traceback.print_exc()
    
    def update_frame_geometry(self):
        """Update the frame display geometry and inform the remote client about it"""
        if not self.remote_client:
            return
            
        # Get the global position of the frame display
        global_pos = self.frame_display.mapToGlobal(QPoint(0, 0))
        
        # Get the size
        size = self.frame_display.size()
        
        # Get the actual image size (could be smaller due to aspect ratio)
        pixmap = self.frame_display.pixmap()
        if pixmap and not pixmap.isNull():
            # Calculate the actual image rect within the label (centered)
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            
            # Calculate position adjustments for centering
            x_offset = (size.width() - pixmap_width) // 2
            y_offset = (size.height() - pixmap_height) // 2
            
            # Update the global position to account for the image position within the label
            global_pos.setX(global_pos.x() + x_offset)
            global_pos.setY(global_pos.y() + y_offset)
            
            # Use the actual pixmap size
            size.setWidth(pixmap_width)
            size.setHeight(pixmap_height)
        
        # Update the remote client with this information
        self.remote_client.set_gui_window_info(
            global_pos.x(), global_pos.y(),
            size.width(), size.height()
        )
    
    def eventFilter(self, watched, event):
        """Event filter to handle mouse and keyboard events"""
        if watched == self.frame_display:
            # Handle key events
            if event.type() == QEvent.KeyPress:
                # Special handling for Tab key
                if event.key() == Qt.Key_Tab:
                    self.toggle_mode()
                    return True
                
                # In command mode, handle special keys
                if self.current_mode == "command":
                    if event.key() == Qt.Key_Q:  # 'q' to disconnect
                        self.close()
                        return True
                    elif event.key() == Qt.Key_C:  # 'c' to toggle control
                        self.toggle_control()
                        return True
                    elif event.key() == Qt.Key_U:  # 'u' to adjust mouse position
                        if self.remote_client:
                            self.remote_client.ui_offset_y -= 5
                            self.remote_client.show_status(f"Y offset: {self.remote_client.ui_offset_y}")
                        return True
                    elif event.key() == Qt.Key_D:  # 'd' to adjust mouse position
                        if self.remote_client:
                            self.remote_client.ui_offset_y += 5
                            self.remote_client.show_status(f"Y offset: {self.remote_client.ui_offset_y}")
                        return True
                    
            # Handle mouse events
            elif event.type() == QEvent.MouseButtonPress and self.control_enabled:
                # These events are handled by the pynput library in RemoteControlClient
                pass
            elif event.type() == QEvent.MouseMove and self.control_enabled:
                # Mouse move is also handled by pynput
                pass
        
        # Let the event continue to be processed normally
        return super().eventFilter(watched, event)
    
    def keyPressEvent(self, event):
        """Handle key press events at the window level"""
        # Handle Tab key for mode toggle
        if event.key() == Qt.Key_Tab:
            self.toggle_mode()
            event.accept()
        else:
            # Apply command keys in command mode
            if self.current_mode == "command":
                if event.key() == Qt.Key_Q:  # 'q' to disconnect
                    self.close()
                    event.accept()
                    return
                elif event.key() == Qt.Key_C:  # 'c' to toggle control
                    self.toggle_control()
                    event.accept()
                    return
                elif event.key() == Qt.Key_U:  # 'u' to adjust mouse position DOWN
                    if self.remote_client:
                        self.remote_client.ui_offset_y -= 5
                        self.remote_client.show_status(f"Y offset: {self.remote_client.ui_offset_y}")
                    event.accept()
                    return
                elif event.key() == Qt.Key_D:  # 'd' to adjust mouse position UP
                    if self.remote_client:
                        self.remote_client.ui_offset_y += 5
                        self.remote_client.show_status(f"Y offset: {self.remote_client.ui_offset_y}")
                    event.accept()
                    return
            
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.closed.emit()
        event.accept()

# Main application window
class RemoteControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set application properties
        self.setWindowTitle("Secure Remote Control")
        
        # Try to load icon if exists, but don't fail if not found
        icon_path = "icons/app_icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Get screen size for responsive design
        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Set window size to 80% of screen size
        self.window_width = int(self.screen_width * 0.8)
        self.window_height = int(self.screen_height * 0.8)
        self.setGeometry(
            (self.screen_width - self.window_width) // 2,
            (self.screen_height - self.window_height) // 2,
            self.window_width, 
            self.window_height
        )
        
        # Apply global stylesheet
        self.apply_stylesheet()
        
        # Create stacked widget for multiple pages
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create help/info action in toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # Add spacer to push the info button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Create info button
        self.info_action = QAction(QIcon(), "ⓘ Info", self)
        self.info_action.setToolTip("About the program")
        self.info_action.triggered.connect(self.show_about_dialog)
        self.toolbar.addAction(self.info_action)
        
        # Initialize client class instances
        self.auth_client = AuthClient()
        self.remote_client = None
        self.video_thread = None
        
        # Remote display window
        self.remote_display = None
        
        # Create pages
        self.login_page = LoginPage(self)
        self.register_page = RegisterPage(self)
        self.connection_page = ConnectionPage(self)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)
        self.stacked_widget.addWidget(self.connection_page)
        
        # Start with login page
        self.show_login_page()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready", 3000)
    
    def apply_stylesheet(self):
        # Modern dark theme with gradients and rounded corners
        self.setStyleSheet("""
            QToolBar {
                background-color: #1a1b20;
                border: none;
                spacing: 5px;
                padding: 2px;
            }
            
            QToolBar QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #2c2d35;
            }
            
            QToolBar QToolButton:pressed {
                background-color: #3c3d45;
            }
            QMainWindow {
                background-color: #1e1f26;
            }
            
            QWidget {
                background-color: #1e1f26;
            }
            
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
                background-color: transparent;
            }
            
            QLabel#header_label {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
            
            QLabel#subtitle_label {
                color: #c0c0c0;
                font-size: 16px;
            }
            
            QLineEdit {
                background-color: #2c2d35;
                color: #ffffff;
                border: 1px solid #3c3d45;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                selection-background-color: #4a5b8f;
            }
            
            QLineEdit:focus {
                border: 1px solid #5b92e5;
            }
            
            QPushButton {
                background-color: #3b66b0;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton:hover {
                background-color: #4b76c0;
            }
            
            QPushButton:pressed {
                background-color: #2b5690;
            }
            
            QPushButton#primary_button {
                background-color: #1f87e5;
            }
            
            QPushButton#primary_button:hover {
                background-color: #2f97f5;
            }
            
            QPushButton#primary_button:pressed {
                background-color: #0f77d5;
            }
            
            QPushButton#secondary_button {
                background-color: #525461;
                color: #e0e0e0;
            }
            
            QPushButton#secondary_button:hover {
                background-color: #626471;
            }
            
            QPushButton#secondary_button:pressed {
                background-color: #424451;
            }
            
            QPushButton#danger_button {
                background-color: #d64045;
            }
            
            QPushButton#danger_button:hover {
                background-color: #e65055;
            }
            
            QPushButton#danger_button:pressed {
                background-color: #c63035;
            }
            
            QFrame#content_frame {
                background-color: #2a2b36;
                border-radius: 8px;
            }
            
            QGroupBox {
                background-color: #2a2b36;
                border: 1px solid #3c3d45;
                border-radius: 8px;
                margin-top: 20px;
                font-size: 14px;
                font-weight: bold;
                color: #e0e0e0;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #3c3d45;
                border-radius: 5px;
                background-color: #2a2b36;
            }
            
            QTabBar::tab {
                background-color: #1e1f26;
                color: #c0c0c0;
                padding: 10px 15px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            
            QTabBar::tab:selected {
                background-color: #2a2b36;
                color: #ffffff;
            }
            
            QTabBar::tab:hover {
                background-color: #3a3b46;
            }
            
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #5b92e5;
            }
            
            QCheckBox::indicator:unchecked {
                background-color: #2c2d35;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3b66b0;
            }
            
            QComboBox {
                background-color: #2c2d35;
                color: #ffffff;
                border: 1px solid #3c3d45;
                border-radius: 5px;
                padding: 8px;
                min-width: 6em;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #3c3d45;
                border-left-style: solid;
            }
            
            QStatusBar {
                background-color: #1a1b20;
                color: #c0c0c0;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #2c2d35;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #5b92e5;
                min-height: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QMessageBox {
                background-color: #2a2b36;
            }
            
            QMessageBox QLabel {
                color: #e0e0e0;
            }
            
            QMessageBox QPushButton {
                min-width: 80px;
                min-height: 30px;
            }
        """)
    
    def show_login_page(self):
        """Switch to login page"""
        self.stacked_widget.setCurrentWidget(self.login_page)
    
    def show_register_page(self):
        """Switch to register page"""
        self.stacked_widget.setCurrentWidget(self.register_page)
    
    def show_connection_page(self):
        """Switch to connection page"""
        self.stacked_widget.setCurrentWidget(self.connection_page)
    
    def handle_login(self, username, password):
        """Handle login process"""
        try:
            # Use the real auth_client.login method
            response = self.auth_client.login(username, password)
            
            if response.get('success'):
                QMessageBox.information(self, "Login Success", f"Welcome back, {username}!")
                self.show_connection_page()
            else:
                QMessageBox.warning(self, "Login Failed", f"Error: {response.get('message')}")
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"Error during login: {str(e)}")
    
    def handle_registration(self, username, password, email, fullname):
        """Handle registration process"""
        try:
            # Use the real auth_client.register method
            response = self.auth_client.register(username, password, email, fullname)
            
            if response.get('success'):
                QMessageBox.information(self, "Registration Success", 
                                      "Your account has been created successfully! You can now login.")
                self.show_login_page()
            else:
                QMessageBox.warning(self, "Registration Failed", f"Error: {response.get('message')}")
        except Exception as e:
            QMessageBox.critical(self, "Registration Error", f"Error during registration: {str(e)}")
    
    def handle_connection(self, server_ip):
        """Handle connection to remote server"""
        try:
            # Create a remote client with our authentication client
            self.remote_client = RemoteControlClient(
                server_ip=server_ip,
                auth_client=self.auth_client
            )
            
            # Create the remote display window
            self.remote_display = RemoteDisplayWindow(self)
            self.remote_display.closed.connect(self.handle_disconnect)
            self.remote_display.set_remote_client(self.remote_client)
            
            # Define a frame update callback for the GUI
            def frame_callback(frame):
                if self.remote_display:
                    self.remote_display.update_frame(frame)
            
            # Start the remote client with our callback
            if self.remote_client.start(frame_callback=frame_callback):
                # Show the remote display window
                self.remote_display.show()
                self.status_bar.showMessage(f"Connected to {server_ip}", 3000)
                
                # Hide the main window to reduce clutter
                # self.hide()
            else:
                if self.remote_display:
                    self.remote_display.close()
                    self.remote_display = None
                QMessageBox.warning(self, "Connection Error", "Failed to start remote client. Authentication may be required.")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            if self.remote_display:
                self.remote_display.close()
                self.remote_display = None
    
    def handle_disconnect(self):
        """Handle disconnection from remote server"""
        try:
            # Close the remote display window if it exists
            if self.remote_display:
                self.remote_display.close()
                self.remote_display = None
            
            if self.remote_client:
                self.remote_client.stop()
                self.remote_client = None
            
            # Show the main window again if it was hidden
            self.show()
            self.status_bar.showMessage("Disconnected from server", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Disconnection Error", f"Error during disconnection: {str(e)}")
    
    def handle_logout(self):
        """Handle logout process"""
        try:
            # Disconnect if connected
            if self.remote_display or self.remote_client:
                self.handle_disconnect()
            
            # Logout from auth server
            if self.auth_client.is_authenticated():
                self.auth_client.logout()
            
            # Go back to login page
            self.show_login_page()
            self.status_bar.showMessage("Logged out successfully", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Logout Error", f"Error during logout: {str(e)}")
    
    def show_about_dialog(self):
        """Show the about/help dialog with information about the program"""
        about_text = """
<h2>Secure Remote Control</h2>
<p>Version 1.2</p>

<h3>About This Program</h3>
<p>This application allows you to securely connect to and control remote computers over a network. 
It provides screen sharing and remote control functionality with authentication.</p>

<h3>How to Use</h3>
<ol>
    <li><b>Login/Create Account</b> - Start by logging in or creating a new account</li>
    <li><b>Connect to Server</b> - Enter the IP address of the remote computer running the server software</li>
    <li><b>Remote Control</b> - Once connected, you can view the remote screen and control it with your mouse and keyboard</li>
    <li><b>Toggle Control</b> - You can temporarily disable mouse and keyboard control while still viewing the screen</li>
    <li><b>Toggle Mode</b> - Switch between Typing mode and Command mode using Tab key or the Mode button</li>
    <li><b>Toggle Fullscreen</b> - Press F11 to enter or exit fullscreen mode</li>
    <li><b>Disconnect</b> - When finished, click the Disconnect button to end the session</li>
</ol>

<h3>Keyboard Modes</h3>
<ul>
    <li><b>Typing Mode</b> - All keystrokes are sent to the remote computer</li>
    <li><b>Command Mode</b> - Special keys are used for local control:
        <ul>
            <li>q - Disconnect from server</li>
            <li>c - Toggle remote control on/off</li>
            <li>u - Adjust mouse position down</li>
            <li>d - Adjust mouse position up</li>
        </ul>
    </li>
</ul>

<h3>Keyboard Shortcuts</h3>
<ul>
    <li><b>Tab</b> - Toggle between typing and command modes</li>
    <li><b>F11</b> - Toggle fullscreen mode</li>
    <li><b>Esc</b> - Exit fullscreen mode</li>
    <li><b>Ctrl+T</b> - Toggle mouse/keyboard control</li>
</ul>

<h3>Security Features</h3>
<ul>
    <li>Secure authentication system</li>
    <li>Encrypted communication</li>
    <li>Session management</li>
</ul>

<h3>Troubleshooting</h3>
<p>If you have trouble connecting:</p>
<ul>
    <li>Verify the server is running on the remote computer</li>
    <li>Check that the IP address is correct</li>
    <li>Ensure firewalls allow the connection</li>
    <li>Check network connectivity</li>
</ul>

<p>For additional help, contact support or visit our website.</p>
        """
        
        QMessageBox.about(self, "About Secure Remote Control", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Close remote display if it exists
            if self.remote_display:
                self.remote_display.close()
                self.remote_display = None
            
            # Stop remote client
            if self.remote_client:
                self.remote_client.stop()
                self.remote_client = None
            
            # Logout
            if self.auth_client.is_authenticated():
                self.auth_client.logout()
            
            event.accept()
        except Exception as e:
            print(f"Error during application shutdown: {e}")
            event.accept()


# Login Page
class LoginPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Large logo at the top
        logo_container = QFrame()
        logo_container.setMinimumHeight(200)
        logo_container.setMaximumHeight(250)
        logo_layout = QVBoxLayout(logo_container)
        
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        
        # Look for a logo file and use it if found
        logo_paths = ["icons/logo.png", "logo.png", "logo_resized.png"]
        logo_found = False
        
        for path in logo_paths:
            if os.path.exists(path):
                logo_pixmap = QPixmap(path)
                # Use a larger scale for the logo
                scaled_logo = logo_pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_logo)
                logo_found = True
                break
        
        # If no logo is found, create a placeholder with text
        if not logo_found:
            self.logo_label.setText("REMOTE CONTROL")
            self.logo_label.setStyleSheet("""
                font-size: 36px;
                font-weight: bold;
                color: #5b92e5;
                background-color: transparent;
            """)
        
        logo_layout.addWidget(self.logo_label)
        main_layout.addWidget(logo_container)
        
        # App title 
        title_label = QLabel("Secure Remote Control")
        title_label.setObjectName("header_label")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Connect and control remote computers securely")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(30)
        
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("content_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Form layout for login
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        form_layout.addRow(QLabel("Username:"), self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Password:"), self.password_input)
        
        content_layout.addLayout(form_layout)
        content_layout.addSpacing(20)
        
        # Login button
        self.login_button = QPushButton("Log In")
        self.login_button.setObjectName("primary_button")
        self.login_button.clicked.connect(self.handle_login)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setObjectName("secondary_button")
        self.register_button.clicked.connect(self.handle_register)
        
        # Add buttons to layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.register_button)
        
        content_layout.addLayout(buttons_layout)
        main_layout.addWidget(content_frame)
        
        # Add spacer to push content to the top
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Set initial focus
        self.username_input.setFocus()
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        self.parent.handle_login(username, password)
    
    def handle_register(self):
        """Handle register button click"""
        self.parent.show_register_page()


# Register Page
class RegisterPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Large logo at the top
        logo_container = QFrame()
        logo_container.setMinimumHeight(150)
        logo_container.setMaximumHeight(200)
        logo_layout = QVBoxLayout(logo_container)
        
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        
        # Look for a logo file and use it if found
        logo_paths = ["icons/logo.png", "logo.png", "logo_resized.png"]
        logo_found = False
        
        for path in logo_paths:
            if os.path.exists(path):
                logo_pixmap = QPixmap(path)
                # Use a larger scale for the logo
                scaled_logo = logo_pixmap.scaled(250, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_logo)
                logo_found = True
                break
        
        # If no logo is found, create a placeholder with text
        if not logo_found:
            self.logo_label.setText("REMOTE CONTROL")
            self.logo_label.setStyleSheet("""
                font-size: 36px;
                font-weight: bold;
                color: #5b92e5;
                background-color: transparent;
            """)
        
        logo_layout.addWidget(self.logo_label)
        main_layout.addWidget(logo_container)
        
        # Header
        header_label = QLabel("Create an Account")
        header_label.setObjectName("header_label")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        subtitle_label = QLabel("Join us to access remote control features")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(20)
        
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("content_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Form layout for registration
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        form_layout.addRow(QLabel("Username:"), self.username_input)
        
        # Full name
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Enter your full name")
        form_layout.addRow(QLabel("Full Name:"), self.fullname_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        form_layout.addRow(QLabel("Email:"), self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Password:"), self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Confirm Password:"), self.confirm_password_input)
        
        content_layout.addLayout(form_layout)
        content_layout.addSpacing(20)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setObjectName("primary_button")
        self.register_button.clicked.connect(self.handle_register)
        
        # Back button
        self.back_button = QPushButton("Back to Login")
        self.back_button.setObjectName("secondary_button")
        self.back_button.clicked.connect(self.handle_back)
        
        # Add buttons to layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.back_button)
        buttons_layout.addWidget(self.register_button)
        
        content_layout.addLayout(buttons_layout)
        main_layout.addWidget(content_frame)
        
        # Add spacer
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Set initial focus
        self.username_input.setFocus()
        
        # Connect Enter key to register
        self.confirm_password_input.returnPressed.connect(self.handle_register)
    
    def handle_register(self):
        """Handle register button click"""
        username = self.username_input.text()
        fullname = self.fullname_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate inputs
        if not username or not fullname or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Registration Error", "All fields are required.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Registration Error", "Passwords do not match.")
            return
        
        # Basic email validation
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Registration Error", "Please enter a valid email address.")
            return
        
        # Register the user
        self.parent.handle_registration(username, password, email, fullname)
    
    def handle_back(self):
        """Handle back button click"""
        self.parent.show_login_page()


# Connection Page
class ConnectionPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Large logo at the top
        logo_container = QFrame()
        logo_container.setMinimumHeight(150)
        logo_container.setMaximumHeight(200)
        logo_layout = QVBoxLayout(logo_container)
        
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        
        # Look for a logo file and use it if found
        logo_paths = ["icons/logo.png", "logo.png", "logo_resized.png"]
        logo_found = False
        
        for path in logo_paths:
            if os.path.exists(path):
                logo_pixmap = QPixmap(path)
                # Use a larger scale for the logo
                scaled_logo = logo_pixmap.scaled(250, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_logo)
                logo_found = True
                break
        
        # If no logo is found, create a placeholder with text
        if not logo_found:
            self.logo_label.setText("REMOTE CONTROL")
            self.logo_label.setStyleSheet("""
                font-size: 36px;
                font-weight: bold;
                color: #5b92e5;
                background-color: transparent;
            """)
        
        logo_layout.addWidget(self.logo_label)
        main_layout.addWidget(logo_container)
        
        # Header
        header_label = QLabel("Connect to Remote Server")
        header_label.setObjectName("header_label")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        subtitle_label = QLabel("Enter the server information to connect")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(20)
        
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("content_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Form layout for connection settings
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Server IP
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText("Enter server IP address")
        self.server_ip_input.setText("127.0.0.1")  # Default to localhost
        form_layout.addRow(QLabel("Server IP:"), self.server_ip_input)
        
        # Add form to content layout
        content_layout.addLayout(form_layout)
        content_layout.addSpacing(20)
        
        # Recent connections (could be populated from saved settings)
        recent_group = QGroupBox("Recent Connections")
        recent_layout = QVBoxLayout()
        
        # This would be dynamically populated in a real application
        recent_button1 = QPushButton("Local Server (127.0.0.1)")
        recent_button1.clicked.connect(lambda: self.server_ip_input.setText("127.0.0.1"))
        
        recent_button2 = QPushButton("Office Server (192.168.1.10)")
        recent_button2.clicked.connect(lambda: self.server_ip_input.setText("192.168.1.10"))
        
        # Help button within the connection page
        help_button = QPushButton("How to Connect?")
        help_button.setIcon(QIcon())  # Add icon if available
        help_button.clicked.connect(self.show_connection_help)
        
        recent_layout.addWidget(recent_button1)
        recent_layout.addWidget(recent_button2)
        recent_layout.addWidget(help_button)
        recent_group.setLayout(recent_layout)
        
        content_layout.addWidget(recent_group)
        content_layout.addSpacing(20)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("primary_button")
        self.connect_button.clicked.connect(self.handle_connect)
        
        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("secondary_button")
        self.logout_button.clicked.connect(self.handle_logout)
        
        # Add buttons to layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.logout_button)
        buttons_layout.addWidget(self.connect_button)
        
        content_layout.addLayout(buttons_layout)
        main_layout.addWidget(content_frame)
        
        # Add spacer
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Set initial focus
        self.server_ip_input.setFocus()
        
        # Connect Enter key to connect
        self.server_ip_input.returnPressed.connect(self.handle_connect)
    
    def handle_connect(self):
        """Handle connect button click"""
        server_ip = self.server_ip_input.text()
        
        if not server_ip:
            QMessageBox.warning(self, "Connection Error", "Please enter a server IP address.")
            return
        
        self.parent.handle_connection(server_ip)
    
    def show_connection_help(self):
        """Show connection help dialog"""
        help_text = """
<h3>How to Connect to a Remote Server</h3>

<p><b>Server IP Address:</b> Enter the IP address of the computer running the Remote Control Server.</p>

<p><b>Finding the Server IP:</b></p>
<ul>
    <li>On the server computer, you can find its IP address by:
        <ul>
            <li>Windows: Open Command Prompt and type <code>ipconfig</code></li>
            <li>Mac/Linux: Open Terminal and type <code>ifconfig</code> or <code>ip addr</code></li>
        </ul>
    </li>
    <li>For local connections, you can use <code>127.0.0.1</code> or <code>localhost</code></li>
    <li>For remote connections, you'll need the public or local network IP</li>
</ul>

<p><b>Connection Issues:</b></p>
<ul>
    <li>Ensure the server is running on the remote computer</li>
    <li>Check firewall settings to allow connections on the required ports</li>
    <li>Verify network connectivity between your computer and the server</li>
</ul>

<p><b>Recent Connections:</b> Click on any saved connection to quickly reconnect to a previous server.</p>
        """
        
        QMessageBox.information(self, "Connection Help", help_text)
    
    def handle_logout(self):
        """Handle logout button click"""
        self.parent.handle_logout()


# Main entry point
if __name__ == "__main__":
    # Handle high DPI displays
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    window = RemoteControlApp()
    window.show()
    sys.exit(app.exec_())
