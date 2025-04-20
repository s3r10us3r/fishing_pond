import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                             QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QRadioButton, QVBoxLayout)


class GameSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Setup")

        # --- Side selection ---
        self.white_radio = QRadioButton("White")
        self.black_radio = QRadioButton("Black")
        self.white_radio.setChecked(True)
        side_layout = QHBoxLayout()
        side_layout.addWidget(self.white_radio)
        side_layout.addWidget(self.black_radio)

        # --- Engine path with browse ---
        self.engine_edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.choose_engine)
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(self.engine_edit)
        engine_layout.addWidget(browse)

        # --- Time control combo box ---
        self.time_combo = QComboBox()
        self.time_combo.addItems(
            ["1 min", "1 | 1", "2 | 1", "3 min", "3 | 2", "5 min", "10 min", "No limit"]
        )

        # --- OK / Cancel ---
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            orientation=Qt.Horizontal,
            parent=self,
        )
        self.ok_button = self.buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)  # start disabled
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # --- Assemble the form ---
        form = QFormLayout()
        form.addRow("Play as:", side_layout)
        form.addRow("Engine path:", engine_layout)
        form.addRow("Time control:", self.time_combo)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        # --- Connect validations ---
        self.engine_edit.textChanged.connect(self.validate)

    def choose_engine(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select UCI Engine", "", "Executables (*)"
        )
        if path:
            self.engine_edit.setText(path)

    def validate(self):
        path = self.engine_edit.text().strip()
        valid = bool(path) and os.path.isfile(path)
        self.ok_button.setEnabled(valid)

    def selected_side(self):
        return "white" if self.white_radio.isChecked() else "black"

    def engine_path(self):
        return self.engine_edit.text().strip()

    def time_control(self):
        return self.time_combo.currentText()
