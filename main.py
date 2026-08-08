#!/usr/bin/env python3

import sys, os, time, json, subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QStackedWidget, QFrame, QComboBox, QSlider, 
                             QRadioButton, QButtonGroup, QCheckBox, QColorDialog, 
                             QListView, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

CONFIG_FILE = os.path.expanduser("~/.config/acer_rgb_hub_config.json")

# --- Stylesheet ---
THEME = {
    "@BG_BASE": "#0A0A0A",
    "@BG_SURFACE": "#17181B",
    "@BG_ELEMENT": "#181820",
    "@BG_HOVER": "#384358",
    
    "@BORDER_DEFAULT": "#343036",
    "@BORDER_HOVER": "#FFC19F",
    
    "@TEXT_PRIMARY": "#e6edf3",
    "@TEXT_DISABLED": "#4b5263",
    
    "@ACCENT_PRIMARY": "#FBE4D8",
    "@ACCENT_HOVER": "#E2D5CE",
}

RAW_STYLESHEET = """
* { outline: none; }
QWidget {
    background-color: @BG_BASE;
    color: @TEXT_PRIMARY;
}
QLabel {
    background: transparent;
}
QSlider {
    background: transparent;
}
#sidebar {
    background-color: @BG_SURFACE;
    border-right: 1px solid @BORDER_DEFAULT;
}
#sidebar QPushButton {
    background-color: transparent;
    text-align: left;
    padding: 12px 20px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 10.5pt;
    margin: 4px 10px;
}
#sidebar QPushButton:hover { background-color: @BG_HOVER; }
#sidebar QPushButton:checked {
    background-color: @ACCENT_PRIMARY;
    color: @BG_BASE;
}
#sidebar QPushButton:checked:hover {
    background-color: @ACCENT_HOVER;
    color: @BG_BASE; 
}
QRadioButton:disabled { 
    color: @TEXT_DISABLED; 
}
QRadioButton::indicator:disabled, QRadioButton::indicator:disabled:checked {
    background-color: @BG_ELEMENT;
    border-color: @BORDER_DEFAULT;
}
.Card {
    background-color: @BG_SURFACE;
    border-radius: 12px;
    border: 1px solid @BORDER_DEFAULT;
}
.CardHeader {
    font-size: 13pt; 
    font-weight: bold;
    color: @ACCENT_PRIMARY;
    padding-bottom: 12px;
}
.ZoneBlock {
    background-color: @BG_ELEMENT;
    border: 2px solid @BORDER_DEFAULT;
    border-radius: 10px;
    padding: 10px;
}
.ZoneBlock:hover {
    border: 2px solid @BORDER_HOVER; 
}
.ZoneBlock[active="true"] {
    border: 2px solid @ACCENT_PRIMARY;
    background-color: @BG_HOVER;
}
.ZoneBlock[active="true"]:hover {
    border: 2px solid @ACCENT_HOVER;
}
.ColorSwatch {
    border-radius: 16px;
    border: 2px solid @BORDER_DEFAULT;
    min-width: 32px; max-width: 32px;
    min-height: 32px; max-height: 32px;
}
.ColorSwatch:hover { border: 2px solid @TEXT_PRIMARY; }
.ActionButton {
    background-color: @BG_HOVER;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: bold;
    border: 1px solid @BORDER_DEFAULT;
}
.ActionButton:hover {
    background-color: @BORDER_DEFAULT;
    border: 1px solid @ACCENT_PRIMARY;
}
.PrimaryButton {
    background-color: @ACCENT_PRIMARY;
    color: @BG_BASE;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px 24px;
}
.PrimaryButton:hover { background-color: @ACCENT_HOVER; }
QRadioButton, QCheckBox { spacing: 10px; background: transparent; }
QRadioButton::indicator, QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 2px solid @BORDER_DEFAULT;
    background-color: @BG_ELEMENT;
}
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator:hover, QCheckBox::indicator:hover { border-color: @ACCENT_PRIMARY; }
QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background-color: @ACCENT_PRIMARY;
    border-color: @ACCENT_PRIMARY;
}
QComboBox {
    background-color: transparent;
    border: 1px solid @BORDER_DEFAULT;
    border-radius: 8px;
    padding: 8px 12px;
    color: @TEXT_PRIMARY;
}
QComboBox:hover {
    border: 1px solid @ACCENT_PRIMARY;
    background-color: @BG_ELEMENT;
}
QComboBox QAbstractItemView {
    background-color: @BG_SURFACE; 
    border: 1px solid @BORDER_DEFAULT;
    selection-background-color: @ACCENT_PRIMARY;
    selection-color: @BG_BASE;
    outline: none;
    color: @TEXT_PRIMARY;
}
QSlider::groove:horizontal {
    background: @BORDER_DEFAULT;
    height: 6px; border-radius: 3px;
}
QSlider::handle:horizontal {
    background: @ACCENT_PRIMARY;
    width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: @ACCENT_HOVER;
    width: 18px; height: 18px;
    margin: -6px 0; border-radius: 9px;
}
"""

RAW_DIALOG_STYLE = """
QMessageBox, QInputDialog {
    background-color: @BG_SURFACE;
    color: @TEXT_PRIMARY;
}
QLabel {
    color: @TEXT_PRIMARY;
    font-size: 11pt;
    background: transparent;
}
QLineEdit {
    background-color: @BG_BASE;
    border: 1px solid @BORDER_DEFAULT;
    border-radius: 6px;
    padding: 8px;
    color: @TEXT_PRIMARY;
}
QLineEdit:focus {
    border: 1px solid @ACCENT_PRIMARY;
}
QPushButton {
    background-color: @BG_HOVER;
    border: 1px solid @BORDER_DEFAULT;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    color: @TEXT_PRIMARY;
    min-width: 60px;
}
QPushButton:hover {
    background-color: @BORDER_DEFAULT;
    border: 1px solid @ACCENT_PRIMARY;
}
"""

def apply_theme(stylesheet: str, theme: dict) -> str:
    for var_name, hex_code in theme.items():
        stylesheet = stylesheet.replace(var_name, hex_code)
    return stylesheet

STYLESHEET = apply_theme(RAW_STYLESHEET, THEME)
DIALOG_STYLE = apply_theme(RAW_DIALOG_STYLE, THEME)
class Card(QFrame):
    def __init__(self, title=None):
        super().__init__()
        self.setProperty("class", "Card")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(18, 18, 18, 18)
        
        if title:
            title_label = QLabel(title)
            title_label.setProperty("class", "CardHeader")
            self.layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)
        self.setLayout(self.layout)

class ZoneWidget(QFrame):
    def __init__(self, zone_id, name, default_color, is_on, on_click, on_power_toggle):
        super().__init__()
        self.zone_id = zone_id
        self.color = default_color
        self.on_click = on_click
        self.on_power_toggle = on_power_toggle
        self.is_on = is_on 
        
        self.setProperty("class", "ZoneBlock")
        self.setProperty("active", "false")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.color_bar = QFrame()
        self.color_bar.setFixedHeight(48)
        
        bar_layout = QHBoxLayout(self.color_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setAlignment(Qt.AlignCenter)
        
        self.power_btn = QPushButton("⏻")
        self.power_btn.setFixedSize(36, 36)
        self.power_btn.setCursor(Qt.PointingHandCursor)
        self.power_btn.clicked.connect(self.toggle_power)
        bar_layout.addWidget(self.power_btn)
        
        bottom_layout = QHBoxLayout()
        self.label = QLabel(name)
        self.label.setStyleSheet("font-weight: bold; font-size: 9.5pt; background: transparent;")
        bottom_layout.addWidget(self.label)
        bottom_layout.addStretch()

        layout.addWidget(self.color_bar)
        layout.addSpacing(6)
        layout.addLayout(bottom_layout)
        
        self._update_visual_state()

    def mousePressEvent(self, event):
        self.on_click(self.zone_id)

    def toggle_power(self):
        self.is_on = not self.is_on
        self._update_visual_state()
        self.on_power_toggle(self.zone_id, self.is_on)

    def _update_visual_state(self):
        display_color = self.color if self.is_on else "#000000"
        self.color_bar.setStyleSheet(f"background-color: {display_color}; border-radius: 8px;")
        icon_color = "rgba(0, 0, 0, 0.35)" if self.is_on else "#ff4444"
        self.power_btn.setStyleSheet(f"border: none; color: {icon_color}; font-size: 16pt; font-weight: bold; background: transparent;")

    def set_color(self, hex_color):
        self.color = hex_color
        if self.is_on:
            self.color_bar.setStyleSheet(f"background-color: {hex_color}; border-radius: 8px;")

    def set_active(self, is_active):
        self.setProperty("active", "true" if is_active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

class ModernAcerRGBHub(QMainWindow):
    def __init__(self, build_ui=True):
        super().__init__()
        self.settings = self.load_settings()
        self.active_zone = 0
        
        if build_ui:
            self.init_ui()

    def load_settings(self):
        default_settings = {
            "mode": 0, 
            "mode_name": "Static", 
            "speed": 5, 
            "direction": 1, 
            "brightness": 100, 
            "anim_color": [0, 180, 138],
            "startup_animation": True, 
            "zones": {"1": [137, 180, 250], "2": [243, 139, 168], "3": [166, 227, 161], "4": [203, 166, 247]},
            "zone_state": {"1": True, "2": True, "3": True, "4": True},
            "presets": {
                "Thermal Shift (Warm to Cool)": {
                    "colors": ["#ff0000", "#ff8800", "#8a2be2", "#0000ff"],
                    "states": [True, True, True, True]
                },
                "Cyberpunk Drive": {
                    "colors": ["#ff00ff", "#9400d3", "#0000ff", "#00ffff"],
                    "states": [True, True, True, True]
                },
                "Neon Biohazard": {
                    "colors": ["#ccff00", "#00ff00", "#00fa9a", "#008080"],
                    "states": [True, True, True, True]
                },
                "Molten Core": {
                    "colors": ["#8b0000", "#ff0000", "#ff4500", "#ffae42"],
                    "states": [True, True, True, True]
                },
                "Deep Ocean Abyss": {
                    "colors": ["#00ffff", "#1e90ff", "#0000ff", "#000080"],
                    "states": [True, True, True, True]
                }
            }
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: 
                    saved = json.load(f)
                    return {**default_settings, **saved}
            except json.JSONDecodeError:
                pass 
        return default_settings

    def save_settings(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f: 
            json.dump(self.settings, f, indent=4)

    def run_cmd(self, cmd):
        try:
            subprocess.run(cmd, shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Command execution failed: {e}")

    def apply_saved_settings(self):
        s = self.settings
        b = s.get("brightness", 100)
        
        if s["mode"] == 0:
            for z, rgb in s["zones"].items():
                is_on = s.get("zone_state", {}).get(z, True)
                r, g, b_col = rgb if is_on else [0, 0, 0]
                self.run_cmd(f"facer-rgb -m 0 -b {b} -z {z} -cR {r} -cG {g} -cB {b_col}")
                time.sleep(0.05)
        else:
            rgb = s.get("anim_color", [0, 180, 138])
            self.run_cmd(f"facer-rgb -m {s['mode']} -b {b} -s {s['speed']} -d {s['direction']} -cR {rgb[0]} -cG {rgb[1]} -cB {rgb[2]}")

    def save_and_apply(self):
        self.save_settings()
        self.apply_saved_settings()

    def run_startup_animation(self):
        mode = self.settings.get("mode", 0)
        anim_enabled = self.settings.get("startup_animation", True)
        
        if mode == 0 and anim_enabled:
            time.sleep(0.5) 
            for z_id in range(1, 5):
                rgb = self.settings["zones"].get(str(z_id), [0, 180, 138])
                b = self.settings.get("brightness", 100)
                cmd = f"facer-rgb -m 0 -b {b} -z {z_id} -cR {rgb[0]} -cG {rgb[1]} -cB {rgb[2]}"
                self.run_cmd(cmd)
                time.sleep(0.2) 
            self.apply_saved_settings()
        else:
            self.apply_saved_settings()

    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]

    def rgb_to_hex(self, rgb_list):
        return f"#{rgb_list[0]:02x}{rgb_list[1]:02x}{rgb_list[2]:02x}"

#---------------------------------
    def init_ui(self):
        self.setWindowTitle("Acer-RGB-Hub")
        self.setGeometry(150, 150, 1200, 640) 
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 24, 0, 24)

        title = QLabel("<b>Acer-RGB-Hub</b>")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 15pt; letter-spacing: 2px; margin-bottom: 24px;")
        sidebar_layout.addWidget(title)

        self.btn_static = QPushButton("Static Zones")
        self.btn_anim = QPushButton("Animations")
        self.btn_settings = QPushButton("Settings")

        for btn in (self.btn_static, self.btn_anim, self.btn_settings):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

        self.nav_group = QButtonGroup()
        self.nav_group.addButton(self.btn_static, 0)
        self.nav_group.addButton(self.btn_anim, 1)
        self.nav_group.addButton(self.btn_settings, 2)
        self.nav_group.idClicked.connect(self.switch_tab)

        sidebar_layout.addWidget(self.btn_static)
        sidebar_layout.addWidget(self.btn_anim)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addStretch()

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(28, 28, 28, 28)

        self.stacked_widget = QStackedWidget()
        self.build_static_page()
        self.build_anim_page()
        self.build_settings_page()

        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_container)

        if self.settings.get("mode", 0) > 0:
            self.btn_anim.setChecked(True)
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.btn_static.setChecked(True)
            self.stacked_widget.setCurrentIndex(0)

        self.select_zone(0)

    def switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        current_mode = self.settings.get("mode", 0)
        if index == 0 and current_mode != 0:
            self.settings["mode"] = 0
            self.settings["mode_name"] = "Static"
            self.save_and_apply()
        elif index == 1 and current_mode == 0:
            self.apply_animation()

    def select_zone(self, zone_id):
        self.active_zone = zone_id
        for zid, widget in self.zone_widgets.items():
            widget.set_active(zid == zone_id)

    def toggle_zone_power(self, zone_idx, is_on):
        zone_key = str(zone_idx + 1)
        if "zone_state" not in self.settings:
            self.settings["zone_state"] = {"1": True, "2": True, "3": True, "4": True}
        
        self.settings["zone_state"][zone_key] = is_on
        self.settings["mode"] = 0
        self.settings["mode_name"] = "Static"
        self.save_and_apply()

    def apply_color_to_active_zone(self, hex_color):
        rgb = self.hex_to_rgb(hex_color)
        zone_key = str(self.active_zone + 1)
        self.settings["zones"][zone_key] = rgb
        self.settings["mode"] = 0
        self.settings["mode_name"] = "Static"
        
        self.settings["zone_state"][zone_key] = True
        self.zone_widgets[self.active_zone].is_on = True
        self.zone_widgets[self.active_zone].set_color(hex_color)
        self.zone_widgets[self.active_zone]._update_visual_state()

        self.save_and_apply()

    def open_color_picker(self):
        zone_key = str(self.active_zone + 1)
        curr_rgb = self.settings["zones"].get(zone_key, [0, 180, 138])
        color = QColorDialog.getColor(QColor(*curr_rgb), self, "Select Custom Color")
        if color.isValid():
            self.apply_color_to_active_zone(color.name())

#---------------------------------
    def apply_brightness(self):
        self.settings["brightness"] = self.bright_slider.value()
        self.save_and_apply()

    def update_preset_combo(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("---Select Preset---")
        for preset_name in self.settings.get("presets", {}).keys():
            self.preset_combo.addItem(preset_name)
        self.preset_combo.blockSignals(False)

    def apply_preset(self, preset_name):
        if preset_name == "--- Select Preset ---":
            return
            
        preset_data = self.settings["presets"].get(preset_name)
        if not preset_data:
            return

        colors = preset_data.get("colors", ["#ffffff", "#ffffff", "#ffffff", "#ffffff"])
        states = preset_data.get("states", [True, True, True, True])

        for i in range(4):
            zone_key = str(i + 1)
            hex_color = colors[i]
            is_on = states[i]
            
            self.settings["zones"][zone_key] = self.hex_to_rgb(hex_color)
            self.settings["zone_state"][zone_key] = is_on
            
            self.zone_widgets[i].is_on = is_on
            self.zone_widgets[i].set_color(hex_color)
            self.zone_widgets[i]._update_visual_state()

        self.settings["mode"] = 0
        self.settings["mode_name"] = "Static"
        self.save_and_apply()

    def prompt_save_preset(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Save Preset")
        dialog.setLabelText("Enter preset name:")
        dialog.setStyleSheet(DIALOG_STYLE)
        
        if dialog.exec_() == QInputDialog.Accepted and dialog.textValue().strip():
            name = dialog.textValue().strip()
            
            preset_data = {
                "colors": [
                    self.rgb_to_hex(self.settings["zones"]["1"]),
                    self.rgb_to_hex(self.settings["zones"]["2"]),
                    self.rgb_to_hex(self.settings["zones"]["3"]),
                    self.rgb_to_hex(self.settings["zones"]["4"])
                ],
                "states": [
                    self.settings.get("zone_state", {}).get("1", True),
                    self.settings.get("zone_state", {}).get("2", True),
                    self.settings.get("zone_state", {}).get("3", True),
                    self.settings.get("zone_state", {}).get("4", True)
                ]
            }
            
            if "presets" not in self.settings:
                self.settings["presets"] = {}
                
            self.settings["presets"][name] = preset_data
            self.save_settings()
            self.update_preset_combo()
            
            msg = QMessageBox(self)
            msg.setStyleSheet(DIALOG_STYLE)
            msg.setWindowTitle("Success")
            msg.setText(f"Preset '{name}' saved successfully!")
            msg.setIcon(QMessageBox.Information)
            msg.exec_()

    def delete_preset(self):
        current_text = self.preset_combo.currentText()
        if current_text == "--- Select Preset ---":
            msg = QMessageBox(self)
            msg.setStyleSheet(DIALOG_STYLE)
            msg.setWindowTitle("Error")
            msg.setText("Please select a preset to delete.")
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()
            return
            
        msg = QMessageBox(self)
        msg.setStyleSheet(DIALOG_STYLE)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Are you sure you want to delete '{current_text}'?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setIcon(QMessageBox.Question)
        
        if msg.exec_() == QMessageBox.Yes:
            del self.settings["presets"][current_text]
            self.save_settings()
            self.update_preset_combo()

    def apply_wallpaper_gradient(self):
        try:
            from wallpaper_colors import extract_gradient

            colors = extract_gradient()
            
            for i in range(4):
                zone_key = str(i + 1)
                hex_color = colors[i]
                
                self.settings["zones"][zone_key] = self.hex_to_rgb(hex_color)
                self.settings["zone_state"][zone_key] = True
                
                self.zone_widgets[i].is_on = True
                self.zone_widgets[i].set_color(hex_color)
                self.zone_widgets[i]._update_visual_state()

            self.settings["mode"] = 0
            self.settings["mode_name"] = "Static"
            self.save_and_apply()
            
            msg = QMessageBox(self)
            msg.setStyleSheet(DIALOG_STYLE)
            msg.setWindowTitle("Magic Applied")
            msg.setText("Wallpaper gradient extracted successfully!")
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            
        except ImportError:
            msg = QMessageBox(self)
            msg.setStyleSheet(DIALOG_STYLE)
            msg.setWindowTitle("Missing Dependency")
            msg.setText("Please install Pillow to use this feature:\n\npip install Pillow")
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()

#---------------------------------
    def build_static_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        preview_card = Card("Keyboard Zone Layout")
        zone_layout = QHBoxLayout()
        zone_layout.setSpacing(12)

        self.zone_widgets = {}
        names = ["Zone 1 (Left)", "Zone 2 (Mid-Left)", "Zone 3 (Mid-Right)", "Zone 4 (Right)"]
        
        for i in range(4):
            zone_key = str(i + 1)
            color_hex = self.rgb_to_hex(self.settings["zones"].get(zone_key, [0, 180, 138]))
            is_on = self.settings.get("zone_state", {}).get(zone_key, True)
            zw = ZoneWidget(i, names[i], color_hex, is_on, self.select_zone, self.toggle_zone_power)
            self.zone_widgets[i] = zw
            zone_layout.addWidget(zw)

        preview_card.content_layout.addLayout(zone_layout)
        layout.addWidget(preview_card)

        preset_card = Card("Color Palette")
        
        presets = [
            "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff", "#ff00ff", 
            "#ff8800", "#8a2be2", "#ff1493", "#00ff7f", "#ffffff", "#6F00FF"
        ]
        swatch_layout = QGridLayout()
        swatch_layout.setSpacing(14)
        for idx, hex_code in enumerate(presets):
            btn = QPushButton()
            btn.setProperty("class", "ColorSwatch")
            btn.setStyleSheet(f"background-color: {hex_code};")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, c=hex_code: self.apply_color_to_active_zone(c))
            swatch_layout.addWidget(btn, idx // 6, idx % 6)

        preset_card.content_layout.addLayout(swatch_layout)
        preset_card.content_layout.addSpacing(10)

        action_row = QHBoxLayout()
        picker_btn = QPushButton("Custom Color Picker...")
        picker_btn.setProperty("class", "ActionButton")
        picker_btn.setCursor(Qt.PointingHandCursor)
        picker_btn.clicked.connect(self.open_color_picker)

        magic_btn = QPushButton("✨ Sync with Wallpaper")
        magic_btn.setProperty("class", "ActionButton")
        magic_btn.setStyleSheet("color: #b4befe;") 
        magic_btn.setCursor(Qt.PointingHandCursor)
        magic_btn.clicked.connect(self.apply_wallpaper_gradient)

        action_row.addWidget(picker_btn)
        action_row.addWidget(magic_btn)
        preset_card.content_layout.addLayout(action_row)
        layout.addWidget(preset_card)

        preset_mgr_card = Card("Color Presets")
        pm_layout = QHBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.setView(QListView()) 
        self.preset_combo.setMinimumWidth(200)
        self.preset_combo.activated[str].connect(self.apply_preset)
        
        save_btn = QPushButton("Save Current")
        save_btn.setProperty("class", "ActionButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.prompt_save_preset)
        
        del_btn = QPushButton("Delete")
        del_btn.setProperty("class", "ActionButton")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("color: #ff4444;")
        del_btn.clicked.connect(self.delete_preset)
        
        pm_layout.addWidget(self.preset_combo)
        pm_layout.addWidget(save_btn)
        pm_layout.addWidget(del_btn)
        preset_mgr_card.content_layout.addLayout(pm_layout)
        layout.addWidget(preset_mgr_card)
        
        self.update_preset_combo() 

        bright_card = Card("Global Brightness")
        bright_layout = QHBoxLayout()
        
        bright_icon = QLabel("☀️")
        bright_icon.setStyleSheet("font-size: 14pt;")
        
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(0, 100)
        self.bright_slider.setValue(self.settings.get("brightness", 100))
        self.bright_slider.setSingleStep(10)
        
        bright_val = QLabel(f"{self.settings.get('brightness', 100)}%")
        bright_val.setFixedWidth(40)
        bright_val.setStyleSheet("font-weight: bold;")

        self.bright_slider.valueChanged.connect(lambda v: bright_val.setText(f"{v}%"))
        self.bright_slider.sliderReleased.connect(self.apply_brightness)
        
        bright_layout.addWidget(bright_icon)
        bright_layout.addWidget(self.bright_slider)
        bright_layout.addWidget(bright_val)
        bright_card.content_layout.addLayout(bright_layout)
        layout.addWidget(bright_card)

        layout.addStretch()
        self.stacked_widget.addWidget(page)

#---------------------------------
    def build_anim_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        effect_card = Card("Effect Style")
        combo_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.setView(QListView()) 
        self.mode_combo.setMinimumWidth(250)
        self.mode_combo.addItems(["Wave", "Breath", "Neon", "Shifting", "Zoom"])
        
        saved_mode_name = self.settings.get("mode_name", "Wave")
        if saved_mode_name in ["Wave", "Breath", "Neon", "Shifting", "Zoom"]:
            self.mode_combo.setCurrentText(saved_mode_name)

        combo_layout.addWidget(self.mode_combo)
        combo_layout.addStretch()
        effect_card.content_layout.addLayout(combo_layout)
        layout.addWidget(effect_card)

        prop_card = Card("Properties")
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Speed:"))
        
        saved_speed = self.settings.get("speed", 5)
        self.speed_val = QLabel(str(saved_speed))
        self.speed_val.setStyleSheet("color: #00b48a; font-weight: bold;")
        header_layout.addStretch()
        header_layout.addWidget(self.speed_val)
        prop_card.content_layout.addLayout(header_layout)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 9)
        self.speed_slider.setValue(saved_speed)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setPageStep(1)
        
        prop_card.content_layout.addWidget(self.speed_slider)
        prop_card.content_layout.addSpacing(16)

        prop_card.content_layout.addWidget(QLabel("Direction:"))
        radio_layout = QHBoxLayout()
        self.r1 = QRadioButton("")
        self.r2 = QRadioButton("")
        
        self.dir_btn_group = QButtonGroup()
        self.dir_btn_group.addButton(self.r1, 1)
        self.dir_btn_group.addButton(self.r2, 2)

        if self.settings.get("direction", 1) == 2:
            self.r2.setChecked(True)
        else:
            self.r1.setChecked(True)

        radio_layout.addWidget(self.r1)
        radio_layout.addWidget(self.r2)
        radio_layout.addStretch()
        prop_card.content_layout.addLayout(radio_layout)
        prop_card.content_layout.addSpacing(16)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Custom Color (If Supported):"))
        
        self.anim_color_btn = QPushButton()
        self.anim_color_btn.setProperty("class", "ColorSwatch")
        anim_rgb = self.settings.get("anim_color", [0, 180, 138])
        self.anim_color_btn.setStyleSheet(f"background-color: {self.rgb_to_hex(anim_rgb)};")
        self.anim_color_btn.setCursor(Qt.PointingHandCursor)
        self.anim_color_btn.clicked.connect(self.pick_anim_color)
        
        color_layout.addStretch()
        color_layout.addWidget(self.anim_color_btn)
        prop_card.content_layout.addLayout(color_layout)

        layout.addWidget(prop_card)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

        self.mode_combo.currentIndexChanged.connect(self.update_direction_labels)
        self.mode_combo.currentIndexChanged.connect(self.apply_animation)
        self.speed_slider.valueChanged.connect(lambda v: self.speed_val.setText(str(v)))
        self.speed_slider.sliderReleased.connect(self.apply_animation)
        self.dir_btn_group.idClicked.connect(self.apply_animation)

        self.update_direction_labels()

    def pick_anim_color(self):
        curr_rgb = self.settings.get("anim_color", [0, 180, 138])
        color = QColorDialog.getColor(QColor(*curr_rgb), self, "Select Animation Base Color")
        if color.isValid():
            rgb = [color.red(), color.green(), color.blue()]
            self.settings["anim_color"] = rgb
            self.anim_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.apply_animation() 

    def update_direction_labels(self, index=None):
        mode = self.mode_combo.currentText()

        if mode in ["Breath", "Neon", "Zoom"]:
            self.r1.setEnabled(False)
            self.r2.setEnabled(False)
            self.r1.setText("Direction Not Supported")
            self.r2.setText("Direction Not Supported")
        else:
            self.r1.setEnabled(True)
            self.r2.setEnabled(True)

            self.r1.setText(f"{mode} Left to Right")
            self.r2.setText(f"{mode} Right to Left")

    def apply_animation(self):
        modes = {"Breath": 1, "Neon": 2, "Wave": 3, "Shifting": 4, "Zoom": 5}
        self.settings["mode"] = modes[self.mode_combo.currentText()]
        self.settings["mode_name"] = self.mode_combo.currentText()
        self.settings["speed"] = self.speed_slider.value()
        self.settings["direction"] = self.dir_btn_group.checkedId()
        self.save_and_apply()

#---------------------------------
    def build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        sys_card = Card("Desktop & Startup Behavior")
        anim_toggle = QCheckBox("Enable Startup Wipe Effect")
        anim_toggle.setChecked(self.settings.get("startup_animation", True))
        anim_toggle.setStyleSheet("font-weight: bold;")
        anim_toggle.toggled.connect(self.toggle_startup_anim)
        
        subtitle = QLabel("Runs a smooth transition when powering on.")
        subtitle.setStyleSheet("color: #8b949e; margin-left: 28px; margin-bottom: 12px;")
        sys_card.content_layout.addWidget(anim_toggle)
        sys_card.content_layout.addWidget(subtitle)
        layout.addWidget(sys_card)

        reset_card = Card("Configuration")
        reset_btn = QPushButton("Restore Default Settings")
        reset_btn.setProperty("class", "ActionButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("color: #ff4444; border: 1px solid #ff4444;")
        reset_btn.clicked.connect(self.reset_to_default)
        
        reset_sub = QLabel("Wipes your saved palettes, custom presets, and preferences back to a fresh install state.")
        reset_sub.setStyleSheet("color: #8b949e; margin-top: 6px;")
        
        reset_card.content_layout.addWidget(reset_btn)
        reset_card.content_layout.addWidget(reset_sub)
        layout.addWidget(reset_card)

        diag_card = Card("Diagnostics")
        debug_btn = QPushButton("Check 'facer' Module Status")
        debug_btn.setProperty("class", "ActionButton")
        debug_btn.setCursor(Qt.PointingHandCursor)
        debug_btn.clicked.connect(self.check_facer_module)
        
        diag_sub = QLabel("Verifies if /dev/acer-gkbbl-0 is mounted and accessible by your current user.")
        diag_sub.setStyleSheet("color: #8b949e; margin-top: 6px;")
        diag_card.content_layout.addWidget(debug_btn)
        diag_card.content_layout.addWidget(diag_sub)
        layout.addWidget(diag_card)

        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def toggle_startup_anim(self, checked):
        self.settings["startup_animation"] = checked
        self.save_settings()

    def check_facer_module(self):
        path = "/dev/acer-gkbbl-0"
        msg = QMessageBox(self)
        msg.setStyleSheet(DIALOG_STYLE)
        
        if not os.path.exists(path):
            msg.setWindowTitle("Hardware Error")
            msg.setText(f"Module not found at {path}.\n\nEnsure 'facer-rgb' is installed and the kernel module is loaded.")
            msg.setIcon(QMessageBox.Critical)
        elif not os.access(path, os.W_OK):
            msg.setWindowTitle("Permission Denied")
            msg.setText(f"Device exists but is NOT writable by your user.\n\nYou likely need to configure a udev rule for {path}, or run this script with elevated privileges.")
            msg.setIcon(QMessageBox.Warning)
        else:
            msg.setWindowTitle("System Check")
            msg.setText(f"Success! {path} is loaded and writable.")
            msg.setIcon(QMessageBox.Information)
            
        msg.exec_()

    def reset_to_default(self):
        msg = QMessageBox(self)
        msg.setStyleSheet(DIALOG_STYLE)
        msg.setWindowTitle("Reset Configuration")
        msg.setText("Are you sure you want to reset all settings to their defaults? This will erase your custom presets.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setIcon(QMessageBox.Warning)
        
        if msg.exec_() == QMessageBox.Yes:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            
            self.settings = self.load_settings()
            self.save_and_apply()
            
            self.bright_slider.setValue(self.settings.get("brightness", 100))
            self.speed_slider.setValue(self.settings.get("speed", 5))

            self.update_preset_combo()

            anim_rgb = self.settings.get("anim_color", [0, 180, 138])
            self.anim_color_btn.setStyleSheet(f"background-color: {self.rgb_to_hex(anim_rgb)};")

            for i in range(4):
                zone_key = str(i + 1)
                rgb = self.settings["zones"].get(zone_key, [0, 180, 138])
                is_on = self.settings.get("zone_state", {}).get(zone_key, True)
                
                self.zone_widgets[i].is_on = is_on
                self.zone_widgets[i].set_color(self.rgb_to_hex(rgb))
                self.zone_widgets[i]._update_visual_state()
                
            success_msg = QMessageBox(self)
            success_msg.setStyleSheet(DIALOG_STYLE)
            success_msg.setWindowTitle("Reset Successful")
            success_msg.setText("Settings have been completely restored to factory defaults.")
            success_msg.setIcon(QMessageBox.Information)
            success_msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Acer-RGB-Hub")
    app.setDesktopFileName("Acer-RGB-Hub")

    is_silent = "--silent" in sys.argv

    if is_silent:
        controller = ModernAcerRGBHub(build_ui=False)
        controller.run_startup_animation()
        sys.exit(0)
    else:
        app.setFont(QApplication.font())
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        window = ModernAcerRGBHub(build_ui=True)
        window.show()
        sys.exit(app.exec_())