"""
app_cliente.py
Punto de entrada principal — muestra login y lanza la app principal al autenticar.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox

from auth_manager import AuthManager
from login_window import LoginWindow

# Importar MainWindow de ceratias.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ceratias import MainWindow as CeratiaMainWindow


# ─── CONTROLADOR DE LA APLICACIÓN ────────────────────────────────────────────

class AppController:
    """
    Controlador que gestiona el flujo entre LoginWindow y la aplicación principal.
    """
    def __init__(self, app: QApplication):
        self.app = app
        self.manager = AuthManager()
        self.login_window = None
        self.main_window = None

    def start(self):
        """Inicia la aplicación mostrando el LoginWindow."""
        try:
            self.login_window = LoginWindow(self.manager)
            
            # Conectar la señal de login exitoso
            self.login_window.login_exitoso.connect(self._on_login_success)
            
            # Mostrar la ventana de login
            self.login_window.show()
        except Exception as e:
            print(f"❌ Error al iniciar LoginWindow: {e}")
            raise

    def _on_login_success(self, user_data: dict):
        """
        Callback cuando el login es exitoso.
        Cierra el login y abre la aplicación principal.
        """
        try:
            # Cerrar la ventana de login
            if self.login_window:
                self.login_window.close()
            
            # Crear y mostrar la ventana principal de ceratias con los datos del usuario
            print(f"✓ Autenticado como: {user_data.get('nombre', 'usuario')}")
            self.main_window = CeratiaMainWindow(user_data=user_data)
            self.main_window.show()
            
            # Cuando se cierre la ventana principal, salir de la aplicación
            self.main_window.destroyed.connect(self.app.quit)
        except Exception as e:
            print(f"❌ Error al abrir ventana principal: {e}")
            QMessageBox.critical(None, "Error", f"No se pudo abrir la aplicación: {e}")
            self.app.quit()


def main():
    """Función principal que inicia la aplicación."""
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Crear y ejecutar el controlador
        controller = AppController(app)
        controller.start()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ Error fatal en la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
