from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QComboBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..models import AppConfig, TextItem
from ..utils import get_font_list


class TextPanel(QWidget):
    text_added = pyqtSignal(object)
    text_updated = pyqtSignal(object)
    text_deleted = pyqtSignal()
    
    def __init__(self, app_config: AppConfig, parent=None):
        super().__init__(parent)
        self.app_config = app_config
        self._current_item: Optional[TextItem] = None
        self._is_updating = False
        
        self._fonts = get_font_list()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Text")
        group_layout = QFormLayout(group)
        
        self.content_edit = QLineEdit()
        self.content_edit.setText("Text")
        self.content_edit.textChanged.connect(self._on_content_changed)
        group_layout.addRow("Content:", self.content_edit)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(self._fonts)
        if "Arial" in self._fonts:
            self.font_combo.setCurrentText("Arial")
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        group_layout.addRow("Font:", self.font_combo)
        
        style_row = QWidget()
        style_layout = QHBoxLayout(style_row)
        style_layout.setContentsMargins(0, 0, 0, 0)
        
        self.bold_check = QCheckBox("Bold")
        self.bold_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self.bold_check)
        
        self.italic_check = QCheckBox("Italic")
        self.italic_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self.italic_check)
        
        self.underline_check = QCheckBox("Underline")
        self.underline_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self.underline_check)
        
        group_layout.addRow("Style:", style_row)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(4, 200)
        self.size_spin.setValue(16)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        group_layout.addRow("Size:", self.size_spin)
        
        self.kerning_spin = QDoubleSpinBox()
        self.kerning_spin.setRange(0, 50)
        self.kerning_spin.setSingleStep(0.5)
        self.kerning_spin.setValue(0)
        self.kerning_spin.valueChanged.connect(self._on_kerning_changed)
        group_layout.addRow("Kerning:", self.kerning_spin)
        
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self.add_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_button)
        
        group_layout.addRow("", button_row)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def _get_current_text_item(self) -> TextItem:
        return TextItem(
            content=self.content_edit.text(),
            font_family=self.font_combo.currentText(),
            font_size=self.size_spin.value(),
            font_weight="bold" if self.bold_check.isChecked() else "normal",
            font_slant="italic" if self.italic_check.isChecked() else "roman",
            underline=self.underline_check.isChecked(),
            kerning=self.kerning_spin.value()
        )
    
    def _on_content_changed(self, _):
        if self._current_item and not self._is_updating:
            self._current_item.content = self.content_edit.text()
            self.text_updated.emit(self._current_item)
    
    def _on_font_changed(self, _):
        if self._current_item and not self._is_updating:
            self._current_item.font_family = self.font_combo.currentText()
            self.text_updated.emit(self._current_item)
    
    def _on_style_changed(self, _):
        if self._current_item and not self._is_updating:
            self._current_item.font_weight = "bold" if self.bold_check.isChecked() else "normal"
            self._current_item.font_slant = "italic" if self.italic_check.isChecked() else "roman"
            self._current_item.underline = self.underline_check.isChecked()
            self.text_updated.emit(self._current_item)
    
    def _on_size_changed(self, _):
        if self._current_item and not self._is_updating:
            self._current_item.font_size = self.size_spin.value()
            self.text_updated.emit(self._current_item)
    
    def _on_kerning_changed(self, _):
        if self._current_item and not self._is_updating:
            self._current_item.kerning = self.kerning_spin.value()
            self.text_updated.emit(self._current_item)
    
    def _on_add_clicked(self):
        if self._current_item:
            self._current_item.content = self.content_edit.text()
            self._current_item.font_family = self.font_combo.currentText()
            self._current_item.font_size = self.size_spin.value()
            self._current_item.font_weight = "bold" if self.bold_check.isChecked() else "normal"
            self._current_item.font_slant = "italic" if self.italic_check.isChecked() else "roman"
            self._current_item.underline = self.underline_check.isChecked()
            self._current_item.kerning = self.kerning_spin.value()
            self.text_updated.emit(self._current_item)
            self.add_button.setText("Add")
            self._current_item = None
        else:
            item = self._get_current_text_item()
            self.text_added.emit(item)
    
    def _on_delete_clicked(self):
        self.text_deleted.emit()
        self.clear_selection()
    
    def load_text_item(self, item):
        self._is_updating = True
        self._current_item = item.get_text_data() if hasattr(item, 'get_text_data') else item
        
        self.content_edit.setText(self._current_item.content)
        self.font_combo.setCurrentText(self._current_item.font_family)
        self.size_spin.setValue(self._current_item.font_size)
        self.bold_check.setChecked(self._current_item.font_weight == "bold")
        self.italic_check.setChecked(self._current_item.font_slant == "italic")
        self.underline_check.setChecked(self._current_item.underline)
        self.kerning_spin.setValue(self._current_item.kerning)
        
        self.add_button.setText("Update")
        self._is_updating = False
    
    def clear_selection(self):
        self._is_updating = True
        self._current_item = None
        self.add_button.setText("Add")
        self._is_updating = False
