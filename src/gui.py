from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFrame,
    QScrollArea,
)
from PyQt5.QtGui import QPixmap, QPalette, QColor,QCursor
from PyQt5.QtCore import Qt, QTimer
import sys
import os
import pyperclip  # For clipboard operations

# Ensure the src module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.search import search_by_text
from src.feature_extraction import model, preprocess


class ClickablePath(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ClickablePath {
                color: #cccccc;
                padding: 10px;
                background-color: #353535;
                border-radius: 5px;
                font-size: 12px;
                qproperty-wordWrap: true;
            }
            ClickablePath:hover {
                background-color: #404040;
                color: #ffffff;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.path = ""
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.reset_text)
        self.setToolTip("Click to copy path")

    def set_path(self, path):
        self.path = path
        self.setText(f"Image Path: {path}")
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.path:
            pyperclip.copy(self.path)
            self.setText("✓ Path copied to clipboard!")
            self.setStyleSheet("""
                ClickablePath {
                    color: #ffffff;
                    padding: 10px;
                    background-color: #2d6da3;
                    border-radius: 5px;
                    font-size: 12px;
                }
            """)
            self.timer.start(2000)  # Reset after 2 seconds

    def reset_text(self):
        self.setText(f"Image Path: {self.path}")
        self.setStyleSheet("""
            ClickablePath {
                color: #cccccc;
                padding: 10px;
                background-color: #353535;
                border-radius: 5px;
                font-size: 12px;
                qproperty-wordWrap: true;
            }
            ClickablePath:hover {
                background-color: #404040;
                color: #ffffff;
            }
        """)



class ImageSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Search")
        self.setGeometry(200, 200, 1000, 800)
        self.setup_dark_theme()
        self.initUI()

    def setup_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(dark_palette)

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Image frame
        image_frame = QFrame()
        image_frame.setFrameStyle(QFrame.StyledPanel)
        image_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
            }
        """)
        image_layout = QVBoxLayout(image_frame)

        # Image scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        scroll.setWidget(self.image_label)
        image_layout.addWidget(scroll)
        layout.addWidget(image_frame)

        # Search frame
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        search_layout = QVBoxLayout(search_frame)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter a search description...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                background-color: #353535;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
            }
        """)
        search_layout.addWidget(self.search_bar)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #4a90e2;
                border: none;
                border-radius: 5px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
        """)
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        layout.addWidget(search_frame)

        # Results frame
        results_frame = QFrame()
        results_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        results_layout = QVBoxLayout(results_frame)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #353535;
                border: none;
                border-radius: 5px;
                padding: 5px;
                color: white;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        self.results_list.itemClicked.connect(self.show_file_path)
        results_layout.addWidget(self.results_list)

        # Clickable path label
        self.path_label = ClickablePath()
        results_layout.addWidget(self.path_label)
        layout.addWidget(results_frame)

    def perform_search(self):
        query = self.search_bar.text()
        if query:
            results = search_by_text(query, model, preprocess)
            if results:
                self.results_list.clear()

                # Get the top result
                top_image_path, top_score = results[0]

                # Display path and score in results
                top_item = QListWidgetItem(
                    f"Top Match (Score: {top_score:.2f})"
                )
                top_item.setData(Qt.UserRole, top_image_path)
                self.results_list.addItem(top_item)

                # Show image in QLabel
                if os.path.exists(top_image_path):
                    pixmap = QPixmap(top_image_path)
                    scaled_pixmap = pixmap.scaled(
                        600, 600,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    
                    # Display the clickable path
                    self.path_label.set_path(top_image_path)
            else:
                self.results_list.clear()
                self.results_list.addItem("No matching images found.")
                self.image_label.clear()
                self.path_label.hide()
        else:
            self.results_list.clear()
            self.results_list.addItem("Please enter a search query.")
            self.image_label.clear()
            self.path_label.hide()

    def show_file_path(self, item):
        """Display the full image path in the GUI."""
        file_path = item.data(Qt.UserRole)
        if os.path.exists(file_path):
            self.path_label.set_path(file_path)
        else:
            self.path_label.setText("File not found.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ImageSearchApp()
    window.show()
    sys.exit(app.exec_())