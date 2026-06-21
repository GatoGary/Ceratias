"""
login_window.py
Ventana de inicio de sesión PySide6 — diseño clara con logo y estilo moderno.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QDialog, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QLinearGradient

from auth_manager import AuthManager, AuthResult


# ─── PALETA ───────────────────────────────────────────────────────────────────

CLR_BG        = "#F4F7FC"
CLR_PANEL     = "#FFFFFF"
CLR_BORDER    = "#D1D9E6"
CLR_ACCENT    = "#3467FF"
CLR_ACCENT_HV = "#1F4FDD"
CLR_TEXT      = "#1F2937"
CLR_SUBTEXT   = "#53627D"
CLR_ERROR     = "#E11D48"
CLR_SUCCESS   = "#16A34A"
CLR_INPUT_BG  = "#F3F5F8"


# ─── HILO DE AUTENTICACIÓN ────────────────────────────────────────────────────

class LoginWorker(QThread):
    finished = Signal(object)   # AuthResult

    def __init__(self, manager: AuthManager, email: str, password: str):
        super().__init__()
        self.manager  = manager
        self.email    = email
        self.password = password

    def run(self):
        result = self.manager.login(self.email, self.password)
        self.finished.emit(result)


class RestoreSessionWorker(QThread):
    finished = Signal(object)

    def __init__(self, manager: AuthManager):
        super().__init__()
        self.manager = manager

    def run(self):
        result = self.manager.restore_session()
        self.finished.emit(result)


# ─── DIÁLOGO CAMBIO DE CONTRASEÑA ────────────────────────────────────────────

class ChangePasswordDialog(QDialog):
    def __init__(self, manager: AuthManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {CLR_PANEL};
                border: 1px solid {CLR_BORDER};
                border-radius: 12px;
            }}
            QLabel {{ color: {CLR_TEXT}; font-family: 'Segoe UI'; }}
            QLineEdit {{
                background: {CLR_INPUT_BG};
                border: 1px solid {CLR_BORDER};
                border-radius: 8px;
                color: {CLR_TEXT};
                font-size: 13px;
                padding: 10px 14px;
                font-family: 'Segoe UI';
            }}
            QLineEdit:focus {{ border: 1px solid {CLR_ACCENT}; }}
            QPushButton {{
                background: {CLR_ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: {CLR_ACCENT_HV}; }}
            QPushButton#btnCancelar {{
                background: transparent;
                border: 1px solid {CLR_BORDER};
                color: {CLR_SUBTEXT};
            }}
            QPushButton#btnCancelar:hover {{ border-color: {CLR_ACCENT}; color: {CLR_TEXT}; }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel("Cambiar contraseña")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        layout.addWidget(title)

        self.nueva = QLineEdit()
        self.nueva.setPlaceholderText("Nueva contraseña")
        self.nueva.setEchoMode(QLineEdit.Password)
        self.nueva.setMinimumHeight(44)
        layout.addWidget(self.nueva)

        self.confirmar = QLineEdit()
        self.confirmar.setPlaceholderText("Confirmar nueva contraseña")
        self.confirmar.setEchoMode(QLineEdit.Password)
        self.confirmar.setMinimumHeight(44)
        layout.addWidget(self.confirmar)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(f"color: {CLR_ERROR}; font-size: 12px;")
        self.lbl_error.setWordWrap(True)
        layout.addWidget(self.lbl_error)

        btn_row = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar = QPushButton("Guardar contraseña")
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.clicked.connect(self._guardar)

        btn_row.addWidget(btn_cancelar)
        btn_row.addWidget(self.btn_guardar)
        layout.addLayout(btn_row)

    def _guardar(self):
        nueva     = self.nueva.text().strip()
        confirmar = self.confirmar.text().strip()

        if len(nueva) < 8:
            self.lbl_error.setText("La contraseña debe tener al menos 8 caracteres.")
            return
        if nueva != confirmar:
            self.lbl_error.setText("Las contraseñas no coinciden.")
            return

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando…")

        result: AuthResult = self.manager.change_password(nueva)
        if result.success:
            QMessageBox.information(self, "Éxito", "✅ Contraseña actualizada correctamente.")
            self.accept()
        else:
            self.lbl_error.setText(result.error)
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("Guardar contraseña")


# ─── VENTANA PRINCIPAL DE LOGIN ───────────────────────────────────────────────

class LoginWindow(QWidget):
    """
    Señal emitida al autenticar correctamente.
    Entrega el dict user_data con nombre, mensaje, vencimiento, etc.
    """
    login_exitoso = Signal(dict)

    def __init__(self, manager: AuthManager = None):
        super().__init__()
        self.manager = manager or AuthManager()
        self._worker = None

        self.setWindowTitle("Ceratias — Inicio de sesión")
        self.setFixedSize(440, 640)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()
        self._apply_styles()
        self._try_restore_session()

    # ── CONSTRUCCIÓN DE UI ────────────────────────────────────────────────────

    def _build_ui(self):
        # Contenedor principal con sombra
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        self.panel = QFrame()
        self.panel.setObjectName("panel")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.panel.setGraphicsEffect(shadow)
        outer.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setSpacing(0)
        layout.setContentsMargins(28, 26, 28, 26)

        # Botón cerrar
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setObjectName("btnCerrar")
        btn_cerrar.setFixedSize(28, 28)
        btn_cerrar.clicked.connect(self.close)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(btn_cerrar)
        layout.addLayout(close_row)

        # Área de arrastre (invisible pero funcional)
        drag_area = QFrame()
        drag_area.setObjectName("dragArea")
        drag_area.setFixedHeight(135)
        drag_area.setCursor(Qt.OpenHandCursor)
        drag_layout = QVBoxLayout(drag_area)
        drag_layout.setContentsMargins(0, 0, 0, 0)
        drag_layout.setSpacing(0)
        self._drag_area = drag_area

        # Logo y subtítulo dentro del área de arrastre
        lbl_logo = QLabel()
        lbl_logo.setObjectName("lblLogo")
        lbl_logo.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_seratias.png")
        logo_loaded = False
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl_logo.setPixmap(pixmap)
                logo_loaded = True
        if not logo_loaded:
            lbl_logo.setText("Ceratias")
        lbl_logo.setFixedHeight(95)
        drag_layout.addWidget(lbl_logo)

        lbl_sub = QLabel("Tu asistente de sublimacion digital")
        lbl_sub.setObjectName("lblSub")
        lbl_sub.setAlignment(Qt.AlignCenter)
        drag_layout.addWidget(lbl_sub)
        drag_layout.addStretch()
        
        layout.addWidget(drag_area)
        layout.addSpacing(12)

        # Campo email
        lbl_email = QLabel("Correo electrónico")
        lbl_email.setObjectName("lblField")
        layout.addWidget(lbl_email)
        layout.addSpacing(6)

        self.input_email = QLineEdit()
        self.input_email.setObjectName("inputField")
        self.input_email.setPlaceholderText("usuario@correo.com")
        self.input_email.setFixedHeight(40)
        layout.addWidget(self.input_email)

        layout.addSpacing(12)

        # Campo contraseña
        lbl_pwd = QLabel("Contraseña")
        lbl_pwd.setObjectName("lblField")
        layout.addWidget(lbl_pwd)
        layout.addSpacing(6)

        pwd_row = QHBoxLayout()
        self.input_pwd = QLineEdit()
        self.input_pwd.setObjectName("inputField")
        self.input_pwd.setPlaceholderText("••••••••")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setFixedHeight(40)
        self.input_pwd.returnPressed.connect(self._do_login)

        self.btn_toggle_pwd = QPushButton("👁")
        self.btn_toggle_pwd.setObjectName("btnTogglePwd")
        self.btn_toggle_pwd.setFixedSize(40, 40)
        self.btn_toggle_pwd.setCheckable(True)
        self.btn_toggle_pwd.toggled.connect(self._toggle_password_visibility)

        pwd_row.addWidget(self.input_pwd)
        pwd_row.addWidget(self.btn_toggle_pwd)
        pwd_row.setSpacing(8)
        layout.addLayout(pwd_row)

        layout.addSpacing(10)

        # Opciones
        opts_row = QHBoxLayout()
        self.chk_guardar = QCheckBox("Mantener sesión")
        self.chk_guardar.setObjectName("chkGuardar")
        self.chk_guardar.setChecked(True)

        btn_cambiar_pwd = QPushButton("Cambiar contraseña")
        btn_cambiar_pwd.setObjectName("btnLink")
        btn_cambiar_pwd.clicked.connect(self._abrir_cambio_pwd)

        opts_row.addWidget(self.chk_guardar)
        opts_row.addStretch()
        opts_row.addWidget(btn_cambiar_pwd)
        layout.addLayout(opts_row)

        layout.addSpacing(16)

        # Mensaje de estado (solo visible cuando hay error/info)
        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("lblStatus")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setVisible(False)
        layout.addWidget(self.lbl_status)

        # Botón ingresar
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setObjectName("btnLogin")
        self.btn_login.setFixedHeight(44)
        self.btn_login.clicked.connect(self._do_login)
        layout.addWidget(self.btn_login)

        layout.addStretch()

        # Pie
        lbl_footer = QLabel("© 2026 Ceratias · Todos los derechos reservados")
        lbl_footer.setObjectName("lblFooter")
        lbl_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_footer)

        # Barra de arrastre
        self._drag_pos = None
        self._drag_area.mousePressEvent = self._drag_press
        self._drag_area.mouseMoveEvent = self._drag_move
        self._drag_area.mouseReleaseEvent = self._drag_release

    # ── ESTILOS ───────────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
            QFrame#panel {{
                background-color: {CLR_PANEL};
                border-radius: 20px;
                border: 1px solid {CLR_BORDER};
            }}
            QPushButton#btnCerrar {{
                background: transparent;
                color: {CLR_SUBTEXT};
                border: none;
                font-size: 14px;
                border-radius: 6px;
            }}
            QPushButton#btnCerrar:hover {{
                background: rgba(225, 29, 72, 0.12);
                color: {CLR_ERROR};
            }}
            QLabel#lblLogo {{
                font-size: 32px;
                color: {CLR_ACCENT};
                font-family: 'Segoe UI';
            }}
            QLabel#lblTitulo {{
                font-size: 28px;
                font-weight: 700;
                color: {CLR_TEXT};
                font-family: 'Segoe UI';
                letter-spacing: 0.5px;
            }}
            QLabel#lblSub {{
                font-size: 13px;
                color: {CLR_SUBTEXT};
                font-family: 'Segoe UI';
            }}
            QLabel#lblField {{
                font-size: 12px;
                font-weight: 600;
                color: {CLR_TEXT};
                font-family: 'Segoe UI';
                letter-spacing: 0.4px;
            }}
            QLineEdit#inputField {{
                background: {CLR_INPUT_BG};
                border: 1px solid {CLR_BORDER};
                border-radius: 12px;
                color: {CLR_TEXT};
                font-size: 14px;
                padding: 0 16px;
                font-family: 'Segoe UI';
            }}
            QLineEdit#inputField:focus {{
                border: 1.5px solid {CLR_ACCENT};
                background: white;
            }}
            QPushButton#btnTogglePwd {{
                background: {CLR_INPUT_BG};
                border: 1px solid {CLR_BORDER};
                border-radius: 12px;
                color: {CLR_SUBTEXT};
                font-size: 16px;
            }}
            QPushButton#btnTogglePwd:checked {{
                color: {CLR_ACCENT};
                border-color: {CLR_ACCENT};
            }}
            QCheckBox#chkGuardar {{
                color: {CLR_SUBTEXT};
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QCheckBox#chkGuardar::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {CLR_BORDER};
                border-radius: 4px;
                background: {CLR_PANEL};
            }}
            QCheckBox#chkGuardar::indicator:checked {{
                background: {CLR_SUCCESS};
                border-color: {CLR_SUCCESS};
            }}
            QPushButton#btnLink {{
                background: transparent;
                border: none;
                color: {CLR_ACCENT};
                font-size: 12px;
                font-family: 'Segoe UI';
                text-decoration: underline;
                padding: 0;
            }}
            QPushButton#btnLink:hover {{ color: {CLR_ACCENT_HV}; }}
            QLabel#lblStatus {{
                font-size: 12px;
                color: {CLR_ERROR};
                font-family: 'Segoe UI';
                border-radius: 6px;
                padding: 6px 10px;
                background: rgba(225, 29, 72, 0.08);
                margin: 8px 0;
            }}
            QFrame#dragArea {{
                background: transparent;
                border: none;
            }}
            QPushButton#btnLogin {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CLR_ACCENT}, stop:1 #7C5CFC
                );
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
                font-family: 'Segoe UI';
                letter-spacing: 0.5px;
            }}
            QPushButton#btnLogin:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CLR_ACCENT_HV}, stop:1 #9575FF
                );
            }}
            QPushButton#btnLogin:disabled {{
                background: {CLR_BORDER};
                color: {CLR_SUBTEXT};
            }}
            QLabel#lblFooter {{
                font-size: 10px;
                color: {CLR_BORDER};
                font-family: 'Segoe UI';
            }}
        """)

    # ── EVENTOS DE ARRASTRE (área específica) ───────────────────────────────────

    def _drag_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _drag_move(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _drag_release(self, event):
        self._drag_pos = None

    # ── RESTAURAR SESIÓN ──────────────────────────────────────────────────────

    def _try_restore_session(self):
        self._set_loading(True, "Verificando sesión guardada…")
        self._worker = RestoreSessionWorker(self.manager)
        self._worker.finished.connect(self._on_restore_done)
        self._worker.start()

    def _on_restore_done(self, result: AuthResult):
        if result.success:
            self._set_status("✅ Sesión restaurada. Iniciando…", CLR_SUCCESS)
            self.btn_login.setEnabled(False)
            # Pequeña pausa visual antes de continuar
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, lambda: self.login_exitoso.emit(result.user_data))
        else:
            self._set_loading(False)
            self.lbl_status.setText("")

    # ── ACCIÓN LOGIN ──────────────────────────────────────────────────────────

    def _do_login(self):
        email    = self.input_email.text().strip()
        password = self.input_pwd.text()

        if not email or not password:
            self._set_status("Por favor ingresa correo y contraseña.", CLR_ERROR)
            return

        self._set_loading(True, "Verificando credenciales…")

        self._worker = LoginWorker(self.manager, email, password)
        self._worker.finished.connect(self._on_login_done)
        self._worker.start()

    def _on_login_done(self, result: AuthResult):
        self._set_loading(False)
        if result.success:
            # Si no quiere guardar sesión, limpiar archivo local
            if not self.chk_guardar.isChecked():
                from auth_manager import _clear_session
                _clear_session()
            self._set_status("✅ Acceso concedido.", CLR_SUCCESS)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.login_exitoso.emit(result.user_data))
        else:
            self._set_status(f"❌ {result.error}", CLR_ERROR)

    # ── CAMBIO DE CONTRASEÑA ──────────────────────────────────────────────────

    def _abrir_cambio_pwd(self):
        dlg = ChangePasswordDialog(self.manager, self)
        dlg.exec()

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _toggle_password_visibility(self, checked: bool):
        self.input_pwd.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _set_loading(self, loading: bool, msg: str = ""):
        self.btn_login.setEnabled(not loading)
        self.input_email.setEnabled(not loading)
        self.input_pwd.setEnabled(not loading)
        if loading and msg:
            self._set_status(msg, CLR_SUBTEXT)
        self.btn_login.setText("Verificando…" if loading else "Ingresar")

    def _set_status(self, msg: str, color: str = CLR_ERROR):
        self.lbl_status.setText(msg)
        self.lbl_status.setVisible(bool(msg))  # Solo visible si hay mensaje
        bg_color = "rgba(225, 29, 72, 0.08)" if color == CLR_ERROR else "transparent"
        self.lbl_status.setStyleSheet(
            f"font-size: 12px; color: {color}; font-family: 'Segoe UI';"
            f" border-radius: 6px; padding: 6px 10px; margin: 8px 0; background: {bg_color};"
        )
