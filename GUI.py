#!/usr/bin/env python
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QVBoxLayout, QPushButton, QLabel, QSizePolicy, QFrame, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QPainter
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

# Load environment variables
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Assistant")

# Global paths
current_dir = os.getcwd()
TempoDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")
old_chat_message = ""

# Utility functions
def AnswerModifier(answer):
    return '\n'.join([line for line in answer.split('\n') if line.strip()])

def QueryModifier(query):
    query = query.lower().strip()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    if any(query.startswith(word) for word in question_words):
        return query.rstrip('.!?') + "?"
    else:
        return query.rstrip('.!?') + "."

def writeToFile(path, data):
    with open(path, "w", encoding="utf-8") as file:
        file.write(data)

def readFromFile(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

def SetMicrophoneStatus(status):
    writeToFile(os.path.join(TempoDirPath, "Mic.data"), status)

def GetMicrophoneStatus():
    return readFromFile(os.path.join(TempoDirPath, "Mic.data"))

def SetAssistantStatus(status):
    writeToFile(os.path.join(TempoDirPath, "Status.data"), status)

def GetAssistantStatus():
    return readFromFile(os.path.join(TempoDirPath, "Status.data"))

def GraphicsDirectoryPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def TempDirectoryPath(filename):
    return os.path.join(TempoDirPath, filename)

def ShowTextToScreen(text):
    writeToFile(os.path.join(TempoDirPath, "Responses.data"), text)

# Chat Section class
class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        layout.addWidget(self.chat_text_edit)

        self.gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath("Jarvis.gif"))
        movie.setScaledSize(QSize(480, 270))
        self.gif_label.setMovie(movie)
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        movie.start()
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.updateStatusLabel)
        self.timer.start(500)

    def loadMessages(self):
        global old_chat_message
        path = TempDirectoryPath("Response.data")
        if not os.path.exists(path):
            return

        messages = readFromFile(path)
        if messages and messages != old_chat_message:
            self.addMessage(messages, 'white')
            old_chat_message = messages

    def updateStatusLabel(self):
        self.label.setText(GetAssistantStatus())

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)
        cursor.setCharFormat(format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

# Initial Screen
class InitialScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath("Jarvis.gif"))
        movie.setScaledSize(QSize(800, 450))
        self.gif_label.setMovie(movie)
        self.gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(100, 100)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.toggled = True
        self.toggle_icon()
        self.icon_label.mousePressEvent = self.toggle_icon_event

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStatusLabel)
        self.timer.start(500)

    def updateStatusLabel(self):
        self.label.setText(GetAssistantStatus())

    def load_icon(self, path):
        pixmap = QPixmap(path)
        self.icon_label.setPixmap(pixmap.scaled(60, 60, Qt.KeepAspectRatio))

    def toggle_icon(self):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath("Mic_off.png"))
            SetMicrophoneStatus("False")
        else:
            self.load_icon(GraphicsDirectoryPath("Mic_on.png"))
            SetMicrophoneStatus("True")
        self.toggled = not self.toggled

    def toggle_icon_event(self, event):
        self.toggle_icon()

# Message Screen
class MessageScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(ChatSection())
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(0, 0, 1280, 720)

        self.stacked_widget = QStackedWidget()
        self.initial_screen = InitialScreen()
        self.message_screen = MessageScreen()

        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.message_screen)
        self.setCentralWidget(self.stacked_widget)
        self.setStyleSheet("background-color: black;")

        self.showInitialScreen()

    def showInitialScreen(self):
        self.stacked_widget.setCurrentIndex(0)

    def showMessageScreen(self):
        self.stacked_widget.setCurrentIndex(1)

# Entry point
def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()
