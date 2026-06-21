import sys
import os
import re
import json
import time
import threading
import ctypes
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QTabWidget, QFileDialog,
    QMessageBox, QDialog, QScrollArea, QFrame, QGroupBox, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QInputDialog, QMenu,
    QSizePolicy, QToolBar, QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QPixmap, QFont, QCursor, QPainter, QColor, QPen, QImage,
    QPalette, QBrush
)
from PySide6.QtCore import Qt, QObject, Signal, Slot, QSize

# ------------------------------------------------------------------
# ── PALETTE & DESIGN TOKENS ────────────────────────────────────────
C_BG        = "#F0F4F8"   # Fondo general (azul-gris muy claro)
C_SURFACE   = "#FFFFFF"   # Superficies / cards
C_BORDER    = "#DDE3EC"   # Bordes sutiles
C_GREEN     = "#16A34A"   # Verde primario (marca)
C_GREEN_HV  = "#15803D"   # Verde hover
C_GREEN_PR  = "#166534"   # Verde pressed
C_GREEN_LT  = "#DCFCE7"   # Verde claro (fondos, selección)
C_BLUE      = "#1D4ED8"   # Azul acción
C_BLUE_HV   = "#2563EB"
C_BLUE_PR   = "#1E40AF"
C_RED       = "#DC2626"   # Rojo peligro
C_RED_HV    = "#EF4444"
C_RED_PR    = "#B91C1C"
C_GRAY      = "#64748B"   # Gris neutro
C_GRAY_HV   = "#475569"
C_GRAY_PR   = "#334155"
C_TEXT      = "#1E293B"   # Texto principal
C_TEXT_SEC  = "#64748B"   # Texto secundario
C_HEADER_BG = "#EEF2F7"   # Fondo de encabezados de tabla


def _btn(bg, hv, pr, tc="white", br=9, px=18, py=8):
    """Genera CSS para un QPushButton con sus tres estados."""
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {tc};
            font-weight: 600;
            border-radius: {br}px;
            padding: {py}px {px}px;
            font-size: 9.5pt;
            border: none;
        }}
        QPushButton:hover   {{ background-color: {hv}; }}
        QPushButton:pressed {{ background-color: {pr}; }}
        QPushButton:disabled {{
            background-color: #E2E8F0;
            color: #94A3B8;
        }}
    """


BTN_VERDE      = _btn(C_GREEN, C_GREEN_HV, C_GREEN_PR)
BTN_AZUL       = _btn(C_BLUE,  C_BLUE_HV,  C_BLUE_PR)
BTN_ROJO       = _btn(C_RED,   C_RED_HV,   C_RED_PR)
BTN_GRIS       = _btn(C_GRAY,  C_GRAY_HV,  C_GRAY_PR)
BTN_DANGER_OUT = """
    QPushButton {
        background-color: #FEE2E2;
        color: #DC2626;
        font-weight: 600;
        font-size: 9pt;
        border: 1.5px solid #FECACA;
        border-radius: 8px;
        padding: 4px 14px;
    }
    QPushButton:hover {
        background-color: #FECACA;
        border-color: #FCA5A5;
    }
    QPushButton:pressed { background-color: #FCA5A5; }
"""

# Campos de entrada compactos para la grilla
ENTRY_GRID = """
    QLineEdit {
        background-color: white;
        border: 1.5px solid #DDE3EC;
        border-radius: 7px;
        padding: 5px 4px;
        font-size: 10pt;
        font-weight: 500;
        color: #1E293B;
    }
    QLineEdit:focus {
        border-color: #16A34A;
        background-color: #F0FDF4;
    }
    QLineEdit:hover:!focus { border-color: #94A3B8; }
"""
ENTRY_ERROR = """
    QLineEdit {
        border: 1.5px solid #F87171;
        background-color: #FEF2F2;
        border-radius: 7px;
        padding: 5px 4px;
        font-size: 10pt;
    }
"""

MODERN_STYLESHEET = f"""
/* ══════════════════════════════════════════
   CERATIAS — Tema Moderno Suave
   ══════════════════════════════════════════ */

QMainWindow, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 10pt;
}}

QDialog {{
    background-color: {C_SURFACE};
    color: {C_TEXT};
}}

/* ── Menú ── */
QMenuBar {{
    background-color: {C_SURFACE};
    border-bottom: 1px solid {C_BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{
    padding: 6px 14px;
    border-radius: 6px;
    color: #475569;
}}
QMenuBar::item:selected {{
    background-color: {C_HEADER_BG};
    color: {C_TEXT};
}}
QMenuBar::item:pressed {{ background-color: {C_BORDER}; }}

QMenu {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
    padding: 6px 4px;
}}
QMenu::item {{
    padding: 8px 28px 8px 16px;
    color: #374151;
    border-radius: 6px;
    margin: 1px 4px;
}}
QMenu::item:selected {{
    background-color: {C_GREEN_LT};
    color: #14532D;
}}

/* ── Toolbar ── */
QToolBar {{
    background-color: {C_SURFACE};
    border-bottom: 1px solid {C_BORDER};
    padding: 3px 8px;
    spacing: 4px;
}}

/* ── Pestañas ── */
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    border-top: none;
    border-radius: 0 0 14px 14px;
    background-color: {C_SURFACE};
}}
QTabBar::tab {{
    background-color: {C_HEADER_BG};
    color: {C_TEXT_SEC};
    border: 1px solid {C_BORDER};
    border-bottom: none;
    padding: 8px 22px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 3px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background-color: {C_SURFACE};
    color: {C_GREEN};
    font-weight: 700;
    border-bottom: 2.5px solid {C_GREEN};
}}
QTabBar::tab:hover:!selected {{
    background-color: #E8F5EF;
    color: #334155;
}}

/* ── Botones base (sin color) ── */
QPushButton {{
    border: none;
    border-radius: 9px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 9.5pt;
    color: white;
    background-color: {C_GRAY};
}}
QPushButton:hover   {{ background-color: {C_GRAY_HV}; }}
QPushButton:pressed {{ background-color: {C_GRAY_PR}; }}
QPushButton:disabled {{
    background-color: #E2E8F0;
    color: #94A3B8;
}}
QPushButton:flat {{
    background-color: transparent;
    color: {C_TEXT};
}}
QPushButton:checkable:checked {{
    background-color: {C_RED};
}}
QPushButton:checkable:checked:hover {{
    background-color: {C_RED_HV};
}}

/* ── Inputs ── */
QLineEdit {{
    background-color: {C_SURFACE};
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 12px;
    color: {C_TEXT};
    selection-background-color: #BBF7D0;
}}
QLineEdit:focus {{
    border-color: {C_GREEN};
    background-color: #F0FDF4;
}}
QLineEdit:hover:!focus {{ border-color: #94A3B8; }}

/* ── GroupBox ── */
QGroupBox {{
    border: 1.5px solid {C_BORDER};
    border-radius: 12px;
    margin-top: 18px;
    padding: 18px 14px 12px 14px;
    background-color: {C_SURFACE};
    font-weight: 600;
    color: #475569;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #475569;
    background-color: {C_SURFACE};
}}

/* ── Scroll ── */
QScrollArea {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    background-color: transparent;
}}
QScrollBar:vertical {{
    border: none;
    background: {C_HEADER_BG};
    width: 7px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: #94A3B8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    border: none;
    background: {C_HEADER_BG};
    height: 7px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Lista ── */
QListWidget {{
    border: 1.5px solid {C_BORDER};
    border-radius: 10px;
    background-color: {C_SURFACE};
    padding: 4px;
    outline: none;
    color: #374151;
}}
QListWidget::item {{
    padding: 7px 12px;
    border-radius: 7px;
}}
QListWidget::item:selected {{
    background-color: {C_GREEN_LT};
    color: #14532D;
    font-weight: 600;
}}
QListWidget::item:hover:!selected {{ background-color: #F0FDF4; }}

/* ── Status Bar ── */
QStatusBar {{
    background-color: {C_SURFACE};
    border-top: 1px solid {C_BORDER};
    color: {C_TEXT_SEC};
    font-size: 9pt;
}}

/* ── Splitter ── */
QSplitter::handle:horizontal {{ background-color: {C_BORDER}; width: 1px; }}
QSplitter::handle:vertical   {{ background-color: {C_BORDER}; height: 1px; }}

/* ── Frame separador horizontal ── */
QFrame[frameShape="4"] {{
    color: {C_BORDER};
    background-color: {C_BORDER};
    max-height: 1px;
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: #1E293B;
    color: #F8FAFC;
    border: none;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 9pt;
}}

/* ── Botones dentro de QMessageBox ── */
QMessageBox QPushButton {{
    min-width: 80px;
    min-height: 30px;
    background-color: {C_GREEN};
    border-radius: 8px;
    padding: 6px 16px;
}}
QMessageBox QPushButton:hover {{ background-color: {C_GREEN_HV}; }}

QInputDialog QLineEdit {{ min-width: 280px; }}
"""


# ------------------------------------------------------------------
# --- Imports opcionales del Asistente ---
try:
    import numpy as np
    from PIL import Image, ImageFile
    Image.MAX_IMAGE_PIXELS = None
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    from winotify import Notification
    _TOAST_OK = True
except ImportError:
    _TOAST_OK = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler as _FSEHandler
    _WATCHDOG_OK = True
except ImportError:
    _WATCHDOG_OK = False
    class _FSEHandler:
        pass
    class Observer:
        def schedule(self, *a, **k): pass
        def start(self): pass
        def stop(self): pass
        def join(self): pass

# ------------------------------------------------------------------
# --- RUTAS Y CONSTANTES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERFILES_PATH = os.path.join(BASE_DIR, "perfiles_precios.json")

RANGOS_TALLA = {
    'XL': 'XL-L-M-S', 'L': 'XL-L-M-S', 'M': 'XL-L-M-S', 'S': 'XL-L-M-S',
    'XXL': 'XL-L-M-S', 'XS': 'XL-L-M-S',
    '16': '16-14', 'T16': '16-14', '14': '16-14', 'T14': '16-14',
    '12': '12-10', 'T12': '12-10', '10': '12-10', 'T10': '12-10',
    '8':  '8-6',   'T8':  '8-6',  '6':  '8-6',   'T6':  '8-6',
    '4':  '4-2',   'T4':  '4-2',  '2':  '4-2',   'T2':  '4-2',
    '1':  '1-0',   'T1':  '1-0',  '0':  '1-0',   'T0':  '1-0'
}

PRECIOS_FABRICA = {
    'XL-L-M-S': {'CORTA': 10.00, 'LARGA': 12.00, 'TRUZA': 7.00, 'CERO': 8.00},
    '16-14':    {'CORTA':  8.00, 'LARGA': 11.00, 'TRUZA': 6.00, 'CERO': 7.00},
    '12-10':    {'CORTA':  6.00, 'LARGA':  8.00, 'TRUZA': 5.00, 'CERO': 6.00},
    '8-6':      {'CORTA':  5.00, 'LARGA':  6.00, 'TRUZA': 5.00, 'CERO': 4.00},
    '4-2':      {'CORTA':  4.00, 'LARGA':  5.00, 'TRUZA': 4.00, 'CERO': 3.00},
    '1-0':      {'CORTA':  3.00, 'LARGA':  4.00, 'TRUZA': 3.00, 'CERO': 2.00},
}

# ------------------------------------------------------------------
# --- ASISTENTE: CONSTANTES ---
SUBCARPETAS_ASISTENTE = ["PECHO", "ESPALDA", "TRUZA", "MANGA"]
IMAGE_EXTENSIONS_ASI  = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
ALL_EXTENSIONS_ASI    = IMAGE_EXTENSIONS_ASI + (".pdf",)
FILE_ATTRIBUTE_HIDDEN = 0x02
MASCARAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mascaras_tinta")
os.makedirs(MASCARAS_DIR, exist_ok=True)

CONFIG_ASISTENTE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config_asistente.json"
)


def cargar_config_asistente():
    if os.path.exists(CONFIG_ASISTENTE_FILE):
        try:
            with open(CONFIG_ASISTENTE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"rutas": [], "estados": {"org": False, "rgb": False, "tinta": False}}


def guardar_config_asistente(rutas, estados):
    try:
        with open(CONFIG_ASISTENTE_FILE, "w", encoding="utf-8") as f:
            json.dump({"rutas": rutas, "estados": estados}, f, indent=4)
    except Exception as e:
        print(f"Error guardando config asistente: {e}")


# ------------------------------------------------------------------
# --- ASISTENTE: SEÑALES ---
class SignalEmitter(QObject):
    notificacion_toast = Signal(str, str)
    rgb_detectado      = Signal(str)
    sobrecarga_400     = Signal(str, str)


# ------------------------------------------------------------------
# --- ASISTENTE: UTILIDADES ---
def esperar_escritura_completa(ruta, timeout=30):
    if not os.path.exists(ruta):
        return False
    t0, ultimo = time.time(), -1
    while time.time() - t0 < timeout:
        try:
            tam = os.path.getsize(ruta)
            if tam == ultimo and tam > 0:
                with open(ruta, "rb"):
                    pass
                return True
            ultimo = tam
        except (OSError, PermissionError):
            pass
        time.sleep(0.5)
    return False


# ------------------------------------------------------------------
# --- ASISTENTE: HANDLERS ---
class OrganizadorHandler(_FSEHandler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter

    def procesar_carpeta(self, ruta):
        ruta = os.path.normpath(ruta)
        nombre = os.path.basename(ruta)
        if nombre in SUBCARPETAS_ASISTENTE or nombre.lower() == "nueva carpeta" \
                or not os.path.isdir(ruta):
            return
        try:
            if len(os.listdir(ruta)) == 0:
                for sub in SUBCARPETAS_ASISTENTE:
                    os.makedirs(os.path.join(ruta, sub), exist_ok=True)
                self.signal_emitter.notificacion_toast.emit(
                    "Organizador Activo",
                    f"Carpetas organizadoras creadas en:\n{nombre}"
                )
        except Exception as e:
            print(f"Error en Organizador: {e}")

    def on_created(self, event):
        if event.is_directory:
            time.sleep(0.5)
            self.procesar_carpeta(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            time.sleep(0.5)
            self.procesar_carpeta(event.dest_path)


class RGBHandler(_FSEHandler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter
        self.vistos = set()

    def _analizar_pdf_rgb(self, ruta):
        try:
            from pypdf import PdfReader
            reader = PdfReader(ruta)
            for page in reader.pages:
                res = page.get("/Resources")
                if not res:
                    continue
                res = res.get_object()
                xobj = res.get("/XObject")
                if not xobj:
                    continue
                xobj = xobj.get_object()
                for obj_id in xobj:
                    obj = xobj[obj_id].get_object()
                    if obj.get("/Subtype") == "/Image":
                        cs = obj.get("/ColorSpace")
                        if not cs:
                            continue
                        cs = cs.get_object()
                        if cs == "/DeviceRGB":
                            return True
                        if isinstance(cs, list):
                            if "/DeviceRGB" in cs:
                                return True
                            for item in cs:
                                try:
                                    item_obj = item.get_object()
                                    if isinstance(item_obj, dict) and item_obj.get("/N") == 3:
                                        return True
                                except Exception:
                                    pass
        except Exception as e:
            print(f"Error analizando PDF RGB: {e}")
        return False

    def _analizar(self, ruta):
        if ruta in self.vistos:
            return
        if not esperar_escritura_completa(ruta):
            return
        es_rgb = False
        es_pdf = ruta.lower().endswith(".pdf")
        try:
            if es_pdf:
                es_rgb = self._analizar_pdf_rgb(ruta)
            elif _PIL_OK:
                with Image.open(ruta) as img:
                    es_rgb = (img.mode == "RGB")
            if es_rgb:
                self.vistos.add(ruta)
                self.signal_emitter.rgb_detectado.emit(ruta)
                tipo = "PDF (Imágenes RGB)" if es_pdf else "Imagen RGB"
                self.signal_emitter.notificacion_toast.emit(
                    "Archivo RGB Detectado",
                    f"Tipo: {tipo}\nArchivo: {os.path.basename(ruta)}"
                )
        except Exception:
            pass

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(ALL_EXTENSIONS_ASI):
            threading.Thread(target=self._analizar, args=(event.src_path,), daemon=True).start()


class TintaHandler(_FSEHandler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter
        self.procesados = set()
        self.carpetas_300_notificadas = set()

    def _analizar_cobertura(self, ruta):
        if ruta in self.procesados or "zonas_400" in ruta:
            return
        if not esperar_escritura_completa(ruta):
            return
        ruta_carpeta = os.path.dirname(ruta)
        try:
            if not _PIL_OK:
                return
            with Image.open(ruta) as img:
                img_cmyk = img if img.mode == "CMYK" else img.convert("CMYK")
                img_cmyk.load()
                arr = np.array(img_cmyk, dtype=np.int32)
            self.procesados.add(ruta)
            suma = np.sum(arr, axis=-1)
            mask_400 = suma >= 1018
            num_400  = np.sum(mask_400)
            porcentaje = (suma / 1020) * 400
            num_300 = np.sum(porcentaje > 300)
            if num_400 > 100:
                matriz_inv = np.where(mask_400, 0, 255).astype("uint8")
                img_mask = Image.fromarray(matriz_inv)
                nombre_base = os.path.splitext(os.path.basename(ruta))[0]
                ruta_mask = os.path.join(MASCARAS_DIR, f"zonas_400_{nombre_base}.png")
                try:
                    if os.path.exists(ruta_mask):
                        os.remove(ruta_mask)
                    img_mask.save(ruta_mask, format="PNG")
                    ctypes.windll.kernel32.SetFileAttributesW(ruta_mask, FILE_ATTRIBUTE_HIDDEN)
                except PermissionError:
                    ruta_mask = os.path.join(
                        MASCARAS_DIR, f"zonas_400_{nombre_base}_{int(time.time())}.png"
                    )
                    img_mask.save(ruta_mask, format="PNG")
                    ctypes.windll.kernel32.SetFileAttributesW(ruta_mask, FILE_ATTRIBUTE_HIDDEN)
                self.signal_emitter.notificacion_toast.emit(
                    "ALERTA: CARGA TOTAL (400%)",
                    f"Se encontró carga máxima en: {os.path.basename(ruta)}"
                )
                self.signal_emitter.sobrecarga_400.emit(ruta, ruta_mask)
            elif num_300 > 500:
                if ruta_carpeta not in self.carpetas_300_notificadas:
                    self.signal_emitter.notificacion_toast.emit(
                        "AVISO: Alta Cobertura (>300%)",
                        f"Carpeta: {os.path.basename(ruta_carpeta)}\nRevisar carga de tinta."
                    )
                    self.carpetas_300_notificadas.add(ruta_carpeta)
        except Exception as e:
            print(f"Error Tinta en {os.path.basename(ruta)}: {e}")

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(IMAGE_EXTENSIONS_ASI):
            threading.Thread(
                target=self._analizar_cobertura, args=(event.src_path,), daemon=True
            ).start()


# ------------------------------------------------------------------
# --- GESTOR DE PERFILES ---
class GestorPerfiles:
    def __init__(self):
        self.perfiles = {}
        self.perfil_activo = ""
        self.cargar()

    def cargar(self):
        if os.path.exists(PERFILES_PATH):
            try:
                with open(PERFILES_PATH, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                self.perfiles = datos.get("perfiles", {})
                self.perfil_activo = datos.get("perfil_activo", "")
                if self.perfil_activo not in self.perfiles:
                    self.perfil_activo = list(self.perfiles.keys())[0] if self.perfiles else ""
                return
            except Exception:
                pass
        self.perfiles = {"Estándar EYM": PRECIOS_FABRICA}
        self.perfil_activo = "Estándar EYM"
        self.guardar()

    def guardar(self):
        try:
            with open(PERFILES_PATH, 'w', encoding='utf-8') as f:
                json.dump({"perfil_activo": self.perfil_activo, "perfiles": self.perfiles},
                          f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando perfiles: {e}")

    def tabla_activa(self):
        return self.perfiles.get(self.perfil_activo, PRECIOS_FABRICA)

    def activar(self, nombre):
        if nombre in self.perfiles:
            self.perfil_activo = nombre
            self.guardar()
            return True
        return False

    def crear(self, nombre, tabla=None):
        if nombre in self.perfiles:
            return False, "Ya existe un perfil con ese nombre."
        self.perfiles[nombre] = tabla if tabla else {
            r: {'CORTA': 0.0, 'LARGA': 0.0, 'TRUZA': 0.0, 'CERO': 0.0}
            for r in PRECIOS_FABRICA
        }
        self.guardar()
        return True, ""

    def duplicar(self, nombre_origen, nombre_nuevo):
        if nombre_nuevo in self.perfiles:
            return False, "Ya existe un perfil con ese nombre."
        if nombre_origen not in self.perfiles:
            return False, "Perfil origen no encontrado."
        import copy
        self.perfiles[nombre_nuevo] = copy.deepcopy(self.perfiles[nombre_origen])
        self.guardar()
        return True, ""

    def actualizar(self, nombre, tabla):
        if nombre not in self.perfiles:
            return False, "Perfil no encontrado."
        self.perfiles[nombre] = tabla
        self.guardar()
        return True, ""

    def eliminar(self, nombre):
        if len(self.perfiles) <= 1:
            return False, "Debe existir al menos un perfil."
        if nombre == self.perfil_activo:
            return False, "No se puede eliminar el perfil activo. Activa otro primero."
        del self.perfiles[nombre]
        self.guardar()
        return True, ""

    def renombrar(self, nombre_viejo, nombre_nuevo):
        if nombre_nuevo in self.perfiles:
            return False, "Ya existe un perfil con ese nombre."
        if nombre_viejo not in self.perfiles:
            return False, "Perfil no encontrado."
        self.perfiles[nombre_nuevo] = self.perfiles.pop(nombre_viejo)
        if self.perfil_activo == nombre_viejo:
            self.perfil_activo = nombre_nuevo
        self.guardar()
        return True, ""


gestor = GestorPerfiles()


def get_tabla_precios():
    return gestor.tabla_activa()


# ------------------------------------------------------------------
# --- HELPERS: CONSTRUCCIÓN DE FILAS PARA FICHA ---
def _construir_filas_ficha(entradas_manuales):
    TABLA_PRECIOS = get_tabla_precios()
    filas = []
    orden = 1
    TIPO_LABEL = {'CORTA': 'm. corta', 'LARGA': 'm. larga', 'CERO': 'm. cero', 'TRUZA': None}

    for rango, de_tipos in entradas_manuales.items():
        for tipo in ['CORTA', 'LARGA', 'CERO', 'TRUZA']:
            entry = de_tipos.get(tipo)
            if entry is None:
                continue
            valor = entry.text().strip()
            if not valor:
                continue
            try:
                cant = int(valor)
            except ValueError:
                continue
            if cant <= 0:
                continue

            precio_u = TABLA_PRECIOS.get(rango, {}).get(tipo, 0.0)
            importe  = precio_u * cant
            talla_display = 'L-S' if rango == 'XL-L-M-S' else rango.replace('-', '-')

            if tipo == 'TRUZA':
                descripcion = f"TRUZA talla {talla_display}"
            else:
                descripcion = f"CAMISETA ({TIPO_LABEL[tipo]}) talla {talla_display}"

            filas.append({
                'orden': orden, 'descripcion': descripcion,
                'cantidad': cant, 'precio_unit': precio_u, 'importe': importe,
            })
            orden += 1

    total = sum(f['importe'] for f in filas)
    return filas, total


# ------------------------------------------------------------------
# --- GENERADOR DE IMAGEN ---
def generar_imagen_ficha(entradas_manuales):
    filas, total = _construir_filas_ficha(entradas_manuales)
    if not filas:
        return None, "No hay datos para generar la ficha. Ingresa al menos una cantidad."

    MARGEN        = 30
    ANCHO         = 700
    ALTO_HEADER   = 130
    ALTO_FILA_TH  = 30
    ALTO_FILA     = 28
    ALTO_FOOTER   = 70
    PADDING_BOTTOM = 20
    alto_total = ALTO_HEADER + ALTO_FILA_TH + (ALTO_FILA * len(filas)) + ALTO_FOOTER + PADDING_BOTTOM

    imagen = QImage(ANCHO, alto_total, QImage.Format_RGB32)
    imagen.fill(QColor(255, 255, 255))
    p = QPainter(imagen)
    p.setRenderHint(QPainter.Antialiasing)

    negro = QColor(30, 41, 59)
    gris  = QColor(226, 232, 240)
    verde = QColor(22, 163, 74)

    def set_font(bold=False, size=10):
        f = QFont("Segoe UI", size)
        f.setBold(bold)
        p.setFont(f)

    p.setPen(QPen(gris, 1.5))
    p.drawRect(MARGEN, MARGEN, ANCHO - 2 * MARGEN, alto_total - 2 * MARGEN)

    set_font(bold=True, size=18)
    p.setPen(negro)
    p.drawText(MARGEN, MARGEN + 10, ANCHO - 2 * MARGEN - 120, 40,
               Qt.AlignHCenter | Qt.AlignVCenter, "Ficha detallada")

    logo_x, logo_y, logo_w, logo_h = ANCHO - MARGEN - 110, MARGEN + 8, 100, 70
    LOGO_PATH = os.path.join(BASE_DIR, "logo_seratias2.png")
    logo_pix = QPixmap(LOGO_PATH) if os.path.exists(LOGO_PATH) else QPixmap()
    if not logo_pix.isNull():
        logo_scaled = logo_pix.scaled(logo_w, logo_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(
            logo_x + (logo_w - logo_scaled.width())  // 2,
            logo_y + (logo_h - logo_scaled.height()) // 2,
            logo_scaled
        )
    else:
        p.setPen(QPen(gris, 1, Qt.DashLine))
        p.drawRect(logo_x, logo_y, logo_w, logo_h)
        set_font(bold=False, size=9)
        p.setPen(gris)
        p.drawText(logo_x, logo_y, logo_w, logo_h, Qt.AlignCenter, "logo")

    ahora = datetime.now()
    set_font(bold=False, size=10)
    p.setPen(negro)
    p.drawText(MARGEN + 10, MARGEN + 55, f"Fecha: {ahora.strftime('%d/%m/%y')}")
    p.drawText(MARGEN + 10, MARGEN + 73, f"Hora:  {ahora.strftime('%I:%M %p').lower()}")

    y_sep = MARGEN + ALTO_HEADER - 10
    p.setPen(QPen(gris, 1))
    p.drawLine(MARGEN, y_sep, ANCHO - MARGEN, y_sep)

    cols = [
        ('ORDEN',       60,  Qt.AlignHCenter),
        ('DESCRIPCION', 260, Qt.AlignLeft),
        ('CANTIDAD',    80,  Qt.AlignHCenter),
        ('P. UNITARIO', 100, Qt.AlignHCenter),
        ('IMPORTE',     110, Qt.AlignHCenter),
    ]
    x_cols, x_cur = [], MARGEN
    for _, w, _ in cols:
        x_cols.append(x_cur)
        x_cur += w

    y_th = y_sep
    set_font(bold=True, size=9)
    p.setPen(negro)
    for i, (texto, ancho, alin) in enumerate(cols):
        p.drawText(x_cols[i] + 4, y_th, ancho - 4, ALTO_FILA_TH,
                   alin | Qt.AlignVCenter, texto)
        p.drawLine(x_cols[i], y_th, x_cols[i], y_th + ALTO_FILA_TH)
    p.drawLine(x_cur, y_th, x_cur, y_th + ALTO_FILA_TH)
    p.drawLine(MARGEN, y_th + ALTO_FILA_TH, ANCHO - MARGEN, y_th + ALTO_FILA_TH)

    set_font(bold=False, size=9)
    y_fila = y_th + ALTO_FILA_TH
    for fila in filas:
        valores = [
            (str(fila['orden']),              cols[0][2]),
            (fila['descripcion'],             cols[1][2]),
            (str(fila['cantidad']),           cols[2][2]),
            (f"S/.{fila['precio_unit']:.0f}", cols[3][2]),
            (f"S/.{fila['importe']:.0f}",     cols[4][2]),
        ]
        for i, (texto, alin) in enumerate(valores):
            p.drawText(x_cols[i] + 4, y_fila, cols[i][1] - 4, ALTO_FILA,
                       alin | Qt.AlignVCenter, texto)
            p.drawLine(x_cols[i], y_fila, x_cols[i], y_fila + ALTO_FILA)
        p.drawLine(x_cur, y_fila, x_cur, y_fila + ALTO_FILA)
        p.setPen(QPen(gris, 0.5))
        p.drawLine(MARGEN, y_fila + ALTO_FILA, ANCHO - MARGEN, y_fila + ALTO_FILA)
        p.setPen(QPen(negro, 1))
        y_fila += ALTO_FILA

    y_foot = y_fila + 12
    set_font(bold=False, size=9)
    p.setPen(QColor(100, 116, 139))
    p.drawText(MARGEN + 10, y_foot, "Generado por Cerátias")

    set_font(bold=True, size=13)
    p.setPen(verde)
    p.drawText(MARGEN, y_foot - 5, ANCHO - 2 * MARGEN - 10, 35,
               Qt.AlignRight | Qt.AlignVCenter, f"Total   S/.{total:.0f}")
    p.setPen(QPen(gris, 1))
    p.drawLine(ANCHO - MARGEN - 160, y_foot + 22, ANCHO - MARGEN - 10, y_foot + 22)

    p.end()
    return imagen, ""


# ------------------------------------------------------------------
# --- GENERADOR DE PDF ---
def generar_pdf_ficha(entradas_manuales, ruta_destino):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

        filas, total = _construir_filas_ficha(entradas_manuales)
        if not filas:
            return False, "No hay datos para exportar. Ingresa al menos una cantidad."

        doc = SimpleDocTemplate(ruta_destino, pagesize=A4,
                                rightMargin=2 * cm, leftMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = getSampleStyleSheet()
        story = []

        from reportlab.platypus import Image as RLImage
        LOGO_PATH = os.path.join(BASE_DIR, "logo_seratias.png")

        estilo_titulo = ParagraphStyle('titulo', parent=styles['Title'],
                                       fontSize=20, spaceAfter=0, alignment=TA_CENTER)
        celda_titulo = Paragraph("Ficha detallada", estilo_titulo)
        ancho_pagina = A4[0] - 4 * cm
        LOGO_W, LOGO_H = 2.8 * cm, 2.0 * cm
        celda_logo = (RLImage(LOGO_PATH, width=LOGO_W, height=LOGO_H)
                      if os.path.exists(LOGO_PATH) else Paragraph("", styles['Normal']))

        tabla_header = Table([[celda_titulo, celda_logo]],
                             colWidths=[ancho_pagina - LOGO_W, LOGO_W])
        tabla_header.setStyle(TableStyle([
            ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',   (0, 0), (0, 0),   'CENTER'),
            ('ALIGN',   (1, 0), (1, 0),   'RIGHT'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tabla_header)

        ahora = datetime.now()
        estilo_meta = ParagraphStyle('meta', parent=styles['Normal'], fontSize=9, spaceAfter=10)
        story.append(Paragraph(
            f"Fecha: {ahora.strftime('%d/%m/%y')}     Hora: {ahora.strftime('%I:%M %p').lower()}",
            estilo_meta
        ))
        story.append(Spacer(1, 0.3 * cm))

        cabecera = ['ORDEN', 'DESCRIPCION', 'CANTIDAD', 'P. UNITARIO', 'IMPORTE']
        datos_tabla = [cabecera] + [
            [str(f['orden']), f['descripcion'], str(f['cantidad']),
             f"S/.{f['precio_unit']:.2f}", f"S/.{f['importe']:.2f}"]
            for f in filas
        ]
        col_widths = [ancho_pagina * p for p in (0.09, 0.38, 0.13, 0.18, 0.22)]

        tabla = Table(datos_tabla, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.white),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.black),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  9),
            ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0),  6),
            ('TOPPADDING',    (0, 0), (-1, 0),  6),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('ALIGN',         (0, 1), (0, -1),  'CENTER'),
            ('ALIGN',         (1, 1), (1, -1),  'LEFT'),
            ('ALIGN',         (2, 1), (4, -1),  'CENTER'),
            ('TOPPADDING',    (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW',     (0, 0), (-1, 0),  1.2, colors.black),
        ]))
        story.append(tabla)
        story.append(Spacer(1, 0.5 * cm))

        estilo_footer = ParagraphStyle('footer', parent=styles['Normal'],
                                       fontSize=8, textColor=colors.grey)
        estilo_total  = ParagraphStyle('total', parent=styles['Normal'],
                                       fontSize=13, fontName='Helvetica-Bold',
                                       alignment=TA_RIGHT, spaceBefore=4)
        story.append(Paragraph("Generado por Cerátias", estilo_footer))
        story.append(Paragraph(f"Total &nbsp;&nbsp; S/.{total:.2f}", estilo_total))
        doc.build(story)
        return True, ""
    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------------
# --- LÓGICA AUTOMÁTICA ---
def extraer_cantidad_desde_archivo(nombre_archivo):
    if '--' in nombre_archivo:
        try:
            return int(nombre_archivo.split('--')[-1].strip())
        except ValueError:
            pass
    return 1


def obtener_rango_talla(nombre_archivo):
    match = re.search(r'(\b(?:T\d+|\d+|S|M|L|XL|XS|XXL)\b)', nombre_archivo, re.IGNORECASE)
    if match:
        talla = match.group(1).upper().replace('T', '')
        return RANGOS_TALLA.get(talla, None)
    return None


def calcular_precio_total(ruta_carpeta):
    TABLA_PRECIOS = get_tabla_precios()
    precio_total  = 0.0
    conteo_camisetas_oficial = 0
    tiene_manga_larga = False
    manga_detectada   = False
    conteo_pecho_total = conteo_espalda_total = conteo_truza_total = 0
    archivos_candidatos = []
    conteo_piezas_detalle = {}
    status_msg = "Verificado"

    for root, _, files in os.walk(ruta_carpeta):
        nombre_carpeta = os.path.basename(root).upper()
        for filename in files:
            if not filename.lower().endswith(('.jpg', '.pdf')):
                continue
            nombre_limpio = filename.upper().replace('.JPG', '').replace('.PDF', '')
            cantidad  = extraer_cantidad_desde_archivo(nombre_limpio)
            ruta_full = os.path.join(root, filename)

            if 'CUELLO' in nombre_limpio and '--' in nombre_limpio:
                conteo_camisetas_oficial = cantidad
            if 'MANGA LARGA' in nombre_limpio:
                tiene_manga_larga = True
            if 'MANGA' in nombre_limpio:
                manga_detectada = True

            es_pecho  = 'PECHO'  in nombre_limpio or 'PECHO'  in nombre_carpeta
            es_espalda= 'ESPALDA'in nombre_limpio or 'ESPALDA'in nombre_carpeta
            es_truza  = 'TRUZA'  in nombre_limpio or 'TRUZA'  in nombre_carpeta

            if es_pecho and not es_espalda:    conteo_pecho_total   += cantidad
            elif es_espalda and not es_pecho:  conteo_espalda_total += cantidad
            elif es_truza:                     conteo_truza_total   += cantidad

            archivos_candidatos.append(
                (filename, ruta_full, nombre_limpio, cantidad, es_pecho, es_espalda, es_truza)
            )

    if conteo_camisetas_oficial == 0:
        status_msg = "Advertencia: No se detectó un archivo CUELLO con formato válido (--cantidad)."

    if conteo_pecho_total != conteo_espalda_total:
        return None, (f"ERROR: Desajuste estructural. "
                      f"PECHO ({conteo_pecho_total}) != ESPALDA ({conteo_espalda_total})"), None, None, None

    manga_ausente = not tiene_manga_larga and not manga_detectada
    items_procesados = []
    items_ignorados  = []

    for filename, ruta_full, nombre_limpio, cantidad, es_pecho, es_espalda, es_truza in archivos_candidatos:
        if 'CUELLO' in nombre_limpio:
            continue
        rango = obtener_rango_talla(nombre_limpio)
        if not rango:
            items_ignorados.append(filename)
            continue

        columna_precio = 'CORTA'
        pieza_tipo = None

        if es_pecho or es_espalda:
            pieza_tipo     = 'PECHO/ESPALDA'
            columna_precio = 'LARGA' if tiene_manga_larga else ('CERO' if manga_ausente else 'CORTA')
        elif es_truza:
            pieza_tipo     = 'TRUZA'
            columna_precio = 'TRUZA'

        if pieza_tipo:
            precio_u = TABLA_PRECIOS.get(rango, {}).get(columna_precio, 0.0)
            subtotal = precio_u * cantidad
            precio_total += subtotal
            items_procesados.append({
                'file': filename, 'path': ruta_full, 'rango': rango,
                'tipo': pieza_tipo, 'modo': columna_precio,
                'cant': cantidad, 'subtotal': subtotal
            })
            clave = f"{pieza_tipo} ({columna_precio})"
            conteo_piezas_detalle[clave] = conteo_piezas_detalle.get(clave, 0) + cantidad
        else:
            items_ignorados.append(filename)

    resumen_rapido = {
        'camisetas': conteo_camisetas_oficial,
        'truzas':    conteo_truza_total,
        'total':     precio_total
    }
    return resumen_rapido, items_procesados, items_ignorados, conteo_piezas_detalle, status_msg


# ------------------------------------------------------------------
# --- WIDGET CON FONDO ---
class FondoWidget(QWidget):
    """Widget que pinta una imagen .jpg como fondo muy sutil."""
    def __init__(self, ruta_imagen=None, parent=None):
        super().__init__(parent)
        self._fondo = None
        if ruta_imagen and os.path.exists(ruta_imagen):
            self._fondo = QPixmap(ruta_imagen)

    def paintEvent(self, event):
        if self._fondo and not self._fondo.isNull():
            painter = QPainter(self)
            scaled = self._fondo.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width()  - scaled.width())  // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            # Overlay más opaco → fondo casi invisible, look limpio
            painter.fillRect(self.rect(), QColor(240, 244, 248, 228))
        else:
            super().paintEvent(event)


# ------------------------------------------------------------------
# ── HELPER: shadow para cards ──────────────────────────────────────
def _card_shadow():
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(22)
    sh.setOffset(0, 3)
    sh.setColor(QColor(0, 0, 0, 22))
    return sh


def _make_card(radius=16):
    """Devuelve un QFrame con apariencia de tarjeta blanca."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {C_SURFACE};
            border-radius: {radius}px;
            border: 1px solid {C_BORDER};
        }}
    """)
    card.setGraphicsEffect(_card_shadow())
    return card


# ------------------------------------------------------------------
# ── DIÁLOGO: SELECCIONAR PERFIL ────────────────────────────────────
class SeleccionarPerfilDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Precios Base — Seleccionar Perfil")
        self.setMinimumSize(400, 340)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        lbl = QLabel("Selecciona el perfil de precios activo:")
        lbl.setStyleSheet("font-size: 10pt; font-weight: 600; color: #374151;")
        layout.addWidget(lbl)

        self.lista = QListWidget()
        self.lista.setFont(QFont("Segoe UI", 10))
        for nombre in gestor.perfiles:
            item = QListWidgetItem(nombre)
            if nombre == gestor.perfil_activo:
                item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                item.setText(f"✔  {nombre}  (activo)")
            self.lista.addItem(item)
        self.lista.itemDoubleClicked.connect(self._aplicar)
        layout.addWidget(self.lista)

        lbl_info = QLabel("Doble clic o presiona 'Aplicar' para activar el perfil.")
        lbl_info.setStyleSheet("color: #94A3B8; font-size: 9pt;")
        layout.addWidget(lbl_info)

        btn_row = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(_btn("#E2E8F0", "#CBD5E1", "#94A3B8", tc="#374151"))
        btn_cancelar.clicked.connect(self.reject)

        btn_aplicar = QPushButton("✔  Aplicar")
        btn_aplicar.setStyleSheet(BTN_VERDE)
        btn_aplicar.setFixedHeight(36)
        btn_aplicar.clicked.connect(self._aplicar)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancelar)
        btn_row.addWidget(btn_aplicar)
        layout.addLayout(btn_row)

    def _nombre_limpio(self, item):
        return item.text().replace("✔  ", "").replace("  (activo)", "").strip()

    def _aplicar(self):
        items = self.lista.selectedItems()
        if not items:
            QMessageBox.warning(self, "Sin selección", "Selecciona un perfil de la lista.")
            return
        nombre = self._nombre_limpio(items[0])
        gestor.activar(nombre)
        QMessageBox.information(self, "Perfil Activado",
                                f"Perfil «{nombre}» activado correctamente.")
        self.accept()


# ------------------------------------------------------------------
# ── DIÁLOGO: GESTOR DE PERFILES ────────────────────────────────────
class GestorPerfilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Perfiles de Precios")
        self.setMinimumSize(800, 540)
        self._perfil_editando = None
        self._modificado = False
        self.entradas_tabla = {}
        self.init_ui()
        self._cargar_lista()

    def init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ── Panel izquierdo ──
        panel_izq = QWidget()
        panel_izq.setMinimumWidth(210)
        panel_izq.setMaximumWidth(250)
        lay_izq = QVBoxLayout(panel_izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.setSpacing(8)

        lbl_perfiles = QLabel("Perfiles")
        lbl_perfiles.setStyleSheet("font-size: 12pt; font-weight: 700; color: #1E293B;")
        lay_izq.addWidget(lbl_perfiles)

        self.lista_perfiles = QListWidget()
        self.lista_perfiles.setFont(QFont("Segoe UI", 10))
        self.lista_perfiles.currentTextChanged.connect(self._on_seleccionar_perfil)
        lay_izq.addWidget(self.lista_perfiles)

        acciones = [
            ("＋  Nuevo",     BTN_AZUL,  self._accion_nuevo),
            ("⧉  Duplicar",   BTN_GRIS,  self._accion_duplicar),
            ("✎  Renombrar",  BTN_GRIS,  self._accion_renombrar),
            ("🗑  Eliminar",  BTN_ROJO,  self._accion_eliminar),
        ]
        for texto, estilo, fn in acciones:
            btn = QPushButton(texto)
            btn.setFixedHeight(32)
            btn.setStyleSheet(estilo)
            btn.clicked.connect(fn)
            lay_izq.addWidget(btn)

        splitter.addWidget(panel_izq)

        # ── Panel derecho ──
        panel_der = QWidget()
        lay_der = QVBoxLayout(panel_der)
        lay_der.setContentsMargins(16, 0, 0, 0)
        lay_der.setSpacing(10)

        self.lbl_titulo_perfil = QLabel("← Selecciona un perfil")
        self.lbl_titulo_perfil.setStyleSheet(
            "font-size: 13pt; font-weight: 700; color: #1E293B;"
        )
        lay_der.addWidget(self.lbl_titulo_perfil)

        self.lbl_activo_badge = QLabel("● ACTIVO")
        self.lbl_activo_badge.setStyleSheet(
            f"color: white; background-color: {C_GREEN}; border-radius: 6px;"
            "padding: 3px 10px; font-size: 9pt; font-weight: 600;"
        )
        self.lbl_activo_badge.hide()
        lay_der.addWidget(self.lbl_activo_badge)

        self.grid_precios = QGridLayout()
        self.grid_precios.setHorizontalSpacing(8)
        self.grid_precios.setVerticalSpacing(6)
        lay_der.addLayout(self.grid_precios)
        self._construir_grid_vacio()
        lay_der.addStretch()

        btn_row = QHBoxLayout()
        self.btn_guardar = QPushButton("💾  Guardar Cambios")
        self.btn_guardar.setStyleSheet(BTN_VERDE)
        self.btn_guardar.setFixedHeight(36)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self._accion_guardar)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_guardar)
        lay_der.addLayout(btn_row)

        splitter.addWidget(panel_der)
        splitter.setSizes([220, 580])

    def _construir_grid_vacio(self):
        while self.grid_precios.count():
            item = self.grid_precios.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.entradas_tabla = {}

        tipos = ["CORTA", "LARGA", "TRUZA", "CERO"]
        headers = ["TALLA"] + tipos
        for col, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"background-color: {C_HEADER_BG}; color: #64748B;"
                "padding: 7px 4px; border-radius: 8px; font-weight: 700;"
            )
            self.grid_precios.addWidget(lbl, 0, col)

        for row, rango in enumerate(PRECIOS_FABRICA.keys(), start=1):
            lbl_r = QLabel(rango)
            lbl_r.setFont(QFont("Segoe UI", 9))
            lbl_r.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl_r.setStyleSheet("font-weight: 600; color: #475569; padding-left: 4px;")
            self.grid_precios.addWidget(lbl_r, row, 0)

            self.entradas_tabla[rango] = {}
            for col, tipo in enumerate(tipos, start=1):
                e = QLineEdit("0.00")
                e.setFixedWidth(78)
                e.setAlignment(Qt.AlignCenter)
                e.setEnabled(False)
                e.textChanged.connect(self._marcar_modificado)
                self.grid_precios.addWidget(e, row, col)
                self.entradas_tabla[rango][tipo] = e

    def _poblar_grid(self, tabla):
        for rango, tipos in self.entradas_tabla.items():
            for tipo, entry in tipos.items():
                val = tabla.get(rango, {}).get(tipo, 0.0)
                entry.blockSignals(True)
                entry.setText(f"{val:.2f}")
                entry.setEnabled(True)
                entry.blockSignals(False)

    def _leer_grid(self):
        tabla = {}
        for rango, tipos in self.entradas_tabla.items():
            tabla[rango] = {}
            for tipo, entry in tipos.items():
                try:
                    tabla[rango][tipo] = float(entry.text())
                except ValueError:
                    return None, f"Valor inválido en {rango} - {tipo}"
        return tabla, ""

    def _cargar_lista(self, seleccionar=None):
        self.lista_perfiles.blockSignals(True)
        self.lista_perfiles.clear()
        for nombre in gestor.perfiles:
            self.lista_perfiles.addItem(f"✔ {nombre}" if nombre == gestor.perfil_activo else nombre)
        self.lista_perfiles.blockSignals(False)

        if seleccionar:
            for i in range(self.lista_perfiles.count()):
                if self._item_nombre(self.lista_perfiles.item(i)) == seleccionar:
                    self.lista_perfiles.setCurrentRow(i)
                    break
        elif self.lista_perfiles.count() > 0:
            self.lista_perfiles.setCurrentRow(0)

    def _item_nombre(self, item):
        return item.text().replace("✔ ", "").strip() if item else ""

    def _on_seleccionar_perfil(self, texto):
        if self._modificado:
            r = QMessageBox.question(self, "Cambios sin guardar",
                                     "Hay cambios sin guardar. ¿Descartar?",
                                     QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.No:
                self._cargar_lista(seleccionar=self._perfil_editando)
                return
        nombre = texto.replace("✔ ", "").strip()
        self._perfil_editando = nombre
        self._modificado = False
        self.btn_guardar.setEnabled(False)
        if nombre in gestor.perfiles:
            self.lbl_titulo_perfil.setText(f"Perfil: {nombre}")
            if nombre == gestor.perfil_activo:
                self.lbl_activo_badge.show()
            else:
                self.lbl_activo_badge.hide()
            self._poblar_grid(gestor.perfiles[nombre])

    def _marcar_modificado(self):
        if not self._modificado:
            self._modificado = True
            self.btn_guardar.setEnabled(True)

    def _accion_nuevo(self):
        nombre, ok = QInputDialog.getText(self, "Nuevo Perfil", "Nombre del nuevo perfil:")
        if not ok or not nombre.strip():
            return
        exito, msg = gestor.crear(nombre.strip())
        if not exito:
            QMessageBox.warning(self, "Error", msg)
            return
        self._cargar_lista(seleccionar=nombre.strip())

    def _accion_duplicar(self):
        item = self.lista_perfiles.currentItem()
        if not item:
            return
        origen = self._item_nombre(item)
        nombre, ok = QInputDialog.getText(self, "Duplicar Perfil", "Nombre para la copia:",
                                          text=f"{origen} - Copia")
        if not ok or not nombre.strip():
            return
        exito, msg = gestor.duplicar(origen, nombre.strip())
        if not exito:
            QMessageBox.warning(self, "Error", msg)
            return
        self._cargar_lista(seleccionar=nombre.strip())

    def _accion_renombrar(self):
        item = self.lista_perfiles.currentItem()
        if not item:
            return
        viejo = self._item_nombre(item)
        nuevo, ok = QInputDialog.getText(self, "Renombrar Perfil", "Nuevo nombre:", text=viejo)
        if not ok or not nuevo.strip() or nuevo.strip() == viejo:
            return
        exito, msg = gestor.renombrar(viejo, nuevo.strip())
        if not exito:
            QMessageBox.warning(self, "Error", msg)
            return
        self._perfil_editando = nuevo.strip()
        self._modificado = False
        self._cargar_lista(seleccionar=nuevo.strip())

    def _accion_eliminar(self):
        item = self.lista_perfiles.currentItem()
        if not item:
            return
        nombre = self._item_nombre(item)
        r = QMessageBox.question(self, "Eliminar Perfil",
                                 f"¿Eliminar el perfil «{nombre}»? Esta acción es irreversible.",
                                 QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.No:
            return
        exito, msg = gestor.eliminar(nombre)
        if not exito:
            QMessageBox.warning(self, "No se puede eliminar", msg)
            return
        self._perfil_editando = None
        self._modificado = False
        self._cargar_lista()

    def _accion_guardar(self):
        if not self._perfil_editando:
            return
        tabla, err = self._leer_grid()
        if tabla is None:
            QMessageBox.critical(self, "Error de formato", err)
            return
        exito, msg = gestor.actualizar(self._perfil_editando, tabla)
        if not exito:
            QMessageBox.warning(self, "Error", msg)
            return
        self._modificado = False
        self.btn_guardar.setEnabled(False)
        QMessageBox.information(self, "Guardado",
                                f"Perfil «{self._perfil_editando}» guardado correctamente.")
        self._cargar_lista(seleccionar=self._perfil_editando)


# ------------------------------------------------------------------
# ── DIÁLOGO: CUENTA ────────────────────────────────────────────────
class CuentaDialog(QDialog):
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Mi Cuenta")
        self.setMinimumSize(480, 480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Verificar si la licencia vence en 5 días o menos
        fecha_vcto = self.user_data.get("fecha_vencimiento")
        dias_restantes = self._calcular_dias_restantes(fecha_vcto)
        
        if dias_restantes is not None and dias_restantes <= 5:
            notif_frame = QFrame()
            notif_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: #FEF3C7;
                    border: 1.5px solid #FCD34D;
                    border-radius: 8px;
                    padding: 12px;
                }}
                """
            )
            notif_layout = QHBoxLayout(notif_frame)
            notif_layout.setContentsMargins(14, 10, 14, 10)
            notif_layout.setSpacing(12)
            
            lbl_icono = QLabel("⚠️")
            lbl_icono.setFont(QFont("Segoe UI", 14))
            lbl_icono.setFixedWidth(30)
            
            lbl_msg = QLabel(
                f"Tu licencia vence en {dias_restantes} día{'s' if dias_restantes != 1 else ''}. "
                f"Renuévala pronto para evitar interrupciones."
            )
            lbl_msg.setFont(QFont("Segoe UI", 10))
            lbl_msg.setStyleSheet(f"color: #92400E; font-weight: 500;")
            lbl_msg.setWordWrap(True)
            
            notif_layout.addWidget(lbl_icono)
            notif_layout.addWidget(lbl_msg)
            notif_layout.addStretch()
            
            layout.addWidget(notif_frame)

        # Avatar + nombre
        fila_avatar = QHBoxLayout()
        iniciales = (self.user_data.get("nombre", "?")[:2]).upper()
        lbl_avatar = QLabel(iniciales)
        lbl_avatar.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_avatar.setAlignment(Qt.AlignCenter)
        lbl_avatar.setFixedSize(58, 58)
        lbl_avatar.setStyleSheet(
            f"background-color: {C_BLUE}; color: white; border-radius: 29px;"
            "font-weight: 700; font-size: 18pt;"
        )
        lbl_nombre_val = QLabel(self.user_data.get("nombre", "—"))
        lbl_nombre_val.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_nombre_val.setStyleSheet(f"color: {C_TEXT}; font-weight: 700;")
        fila_avatar.addWidget(lbl_avatar)
        fila_avatar.addSpacing(14)
        fila_avatar.addWidget(lbl_nombre_val)
        fila_avatar.addStretch()
        layout.addLayout(fila_avatar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {C_BORDER};")
        layout.addWidget(sep)

        grp = QGroupBox("Detalles de la cuenta")
        grp.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lay_grp = QVBoxLayout(grp)
        lay_grp.setSpacing(10)

        def fila_dato(icono, etiqueta, valor, color_valor=C_TEXT):
            h = QHBoxLayout()
            lbl_et = QLabel(f"{icono}  {etiqueta}")
            lbl_et.setFont(QFont("Segoe UI", 9))
            lbl_et.setStyleSheet(f"color: {C_TEXT_SEC};")
            lbl_et.setFixedWidth(180)
            lbl_val = QLabel(str(valor) if valor else "—")
            lbl_val.setFont(QFont("Segoe UI", 9))
            lbl_val.setStyleSheet(f"color: {color_valor}; font-weight: 600;")
            lbl_val.setWordWrap(True)
            h.addWidget(lbl_et)
            h.addWidget(lbl_val)
            h.addStretch()
            lay_grp.addLayout(h)

        estado = self.user_data.get("estado", "—")
        color_estado = "#15803D" if estado == "activo" else "#B91C1C"
        fila_dato("🟢" if estado == "activo" else "🔴", "Estado de cuenta",
                  estado.capitalize(), color_estado)
        fila_dato("📅", "Vencimiento de suscripción",
                  self.user_data.get("fecha_vencimiento", "—"))
        layout.addWidget(grp)
        layout.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(36)
        btn_cerrar.setStyleSheet(_btn("#E2E8F0", "#CBD5E1", "#94A3B8", tc="#374151"))
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, 0, Qt.AlignRight)

    def _calcular_dias_restantes(self, fecha_vcto):
        """Calcula los días restantes hasta el vencimiento de la licencia."""
        if not fecha_vcto:
            return None
        
        try:
            # Si es string, convertir a datetime
            if isinstance(fecha_vcto, str):
                # Intentar parsear diferentes formatos
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]:
                    try:
                        fecha_vcto = datetime.strptime(fecha_vcto, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            
            # Si es datetime, calcular días restantes
            if isinstance(fecha_vcto, datetime):
                ahora = datetime.now()
                # Si la fecha tiene timezone, removerla para comparación local
                if fecha_vcto.tzinfo is not None:
                    fecha_vcto = fecha_vcto.replace(tzinfo=None)
                
                dias = (fecha_vcto.date() - ahora.date()).days
                return dias if dias >= 0 else None
        except Exception:
            return None
        
        return None


# ------------------------------------------------------------------
# ── DIÁLOGO: ACERCA DE ─────────────────────────────────────────────
class AcercaDeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de")
        self.setMinimumSize(500, 540)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(14)

        lbl_titulo_app = QLabel("CERATIAS 2.2.5")
        lbl_titulo_app.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_titulo_app.setAlignment(Qt.AlignCenter)
        lbl_titulo_app.setStyleSheet(
            f"color: {C_GREEN}; padding: 8px 0 4px 0; letter-spacing: 1.5px;"
        )
        main_layout.addWidget(lbl_titulo_app)

        texto_desc = (
            "Esta aplicación ha sido diseñada para optimizar el cálculo de precios "
            "relacionados con tallas, Y monitoreo de imagenes"
            "ofreciendo al usuario una experiencia más ágil "
            "Manual y Automático.\n\n"
            "El modo Automático se encuentra en fase de desarrollo (beta)." 
            "Ahora añadimos la nueva funcionalidad de monitoreo de Nuestro "
            "compromiso es seguir mejorando la aplicación y brindar actualizaciones "
            "continuas que amplíen sus funcionalidades."
            
        )
        lbl_desc = QLabel(texto_desc)
        lbl_desc.setFont(QFont("Segoe UI", 9))
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignJustify)
        lbl_desc.setStyleSheet(
            f"background-color: {C_GREEN_LT}; border-left: 4px solid {C_GREEN};"
            "border-radius: 8px; padding: 12px 16px; color: #1E293B;"
        )
        main_layout.addWidget(lbl_desc)

        # Sección de Funcionalidades
        frame_funciones = QFrame()
        frame_funciones.setStyleSheet(
            f"background-color: {C_SURFACE}; border-radius: 10px; border: 1px solid {C_BORDER};"
        )
        lay_funciones = QVBoxLayout(frame_funciones)
        lay_funciones.setContentsMargins(16, 14, 16, 14)
        lay_funciones.setSpacing(10)

        lbl_funciones_titulo = QLabel("🎯 Cómo empezar")
        lbl_funciones_titulo.setStyleSheet("font-weight: 700; font-size: 11pt; color: #1E293B;")
        lay_funciones.addWidget(lbl_funciones_titulo)

        texto_funciones = (
            "• <b>Inicia sesión:</b> Ingresa con tu correo electrónico y contraseña proporcionados por el administrador.\n\n"
            "• <b>Disposición de servicios:</b> Encontraras las opciones disponibles Precios y Monitoreo.\n\n"
            "• <b>Utiliza el servicio que neesites:</b> Cada servicio tiene su propia sección con funcionalidades específicas para optimizar tu experiencia utilzando las pestañas."
           
        )
        lbl_funciones = QLabel(texto_funciones)
        lbl_funciones.setFont(QFont("Segoe UI", 9))
        lbl_funciones.setWordWrap(True)
        lbl_funciones.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lbl_funciones.setStyleSheet(f"color: {C_TEXT}; line-height: 1.5;")
        lay_funciones.addWidget(lbl_funciones)

        lbl_instrucciones_titulo = QLabel("👕 Calculo de tallas")
        lbl_instrucciones_titulo.setStyleSheet("font-weight: 700; font-size: 11pt; color: #1E293B; margin-top: 8px;")
        lay_funciones.addWidget(lbl_instrucciones_titulo)

        texto_instrucciones = (
            "1. <b>Selecciona el modo:</b> Elige entre Manual o Automático según tus necesidades.\n\n"
            "2. <b>Gestión de perfiles:</b> Crea, edita y guarda múltiples perfiles de precios para diferentes escenarios.\n\n"
            "3. <b>Obtén resultados:</b> La app calculará automáticamente los precios ajustados.\n\n"
            "4. <b>Exporta o guarda:</b> Descarga tus resultados o guarda tu configuración."
            "5. <b>Exportación:</b> Descarga tus resultados en diferentes formatos para usar en otros sistemas.\n\n"
        )
        lbl_instrucciones = QLabel(texto_instrucciones)
        lbl_instrucciones.setFont(QFont("Segoe UI", 9))
        lbl_instrucciones.setWordWrap(True)
        lbl_instrucciones.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lbl_instrucciones.setStyleSheet(f"color: {C_TEXT}; line-height: 1.5;")
        lay_funciones.addWidget(lbl_instrucciones)

        main_layout.addWidget(frame_funciones)

        # Sección de Monitoreo
        frame_monitoreo = QFrame()
        frame_monitoreo.setStyleSheet(
            f"background-color: {C_SURFACE}; border-radius: 10px; border: 1px solid {C_BORDER};"
        )
        lay_monitoreo = QVBoxLayout(frame_monitoreo)
        lay_monitoreo.setContentsMargins(16, 14, 16, 14)
        lay_monitoreo.setSpacing(10)

        lbl_monitoreo_titulo = QLabel("🖼️ Monitoreo y Asistente")
        lbl_monitoreo_titulo.setStyleSheet("font-weight: 700; font-size: 11pt; color: #1E293B;")
        lay_monitoreo.addWidget(lbl_monitoreo_titulo)

        texto_monitoreo_desc = (
            "El módulo de Monitoreo es un asistente inteligente que supervisa carpetas seleccionadas y "
            "procesa automáticamente archivos de imágenes, detectando características de color y carga de tinta "
        )
        lbl_monitoreo_desc = QLabel(texto_monitoreo_desc)
        lbl_monitoreo_desc.setFont(QFont("Segoe UI", 9))
        lbl_monitoreo_desc.setWordWrap(True)
        lbl_monitoreo_desc.setAlignment(Qt.AlignJustify)
        lbl_monitoreo_desc.setStyleSheet(f"color: {C_TEXT}; line-height: 1.4;")
        lay_monitoreo.addWidget(lbl_monitoreo_desc)

        lbl_modulos_titulo = QLabel("Módulos disponibles:")
        lbl_modulos_titulo.setStyleSheet("font-weight: 600; font-size: 10pt; color: #1E293B; margin-top: 6px;")
        lay_monitoreo.addWidget(lbl_modulos_titulo)

        texto_modulos = (
            "• <b>🗂 Autogenerar Carpetas:</b> Crea automáticamente la estructura de directorios necesarios "
            "para organizar tus archivos de impresión.\n\n"
            "• <b>🎨 Detector RGB:</b> Analiza los valores de color (RGB) de las imágenes detectadas y ajusta "
            "los precios según la complejidad cromática.\n\n"
            "• <b>💧 Detector de Carga de Tinta:</b> Mide la cantidad de tinta utilizada en cada imagen para "
            "calcular precios más precisos basados en el consumo real."
        )
        lbl_modulos = QLabel(texto_modulos)
        lbl_modulos.setFont(QFont("Segoe UI", 9))
        lbl_modulos.setWordWrap(True)
        lbl_modulos.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lbl_modulos.setStyleSheet(f"color: {C_TEXT}; line-height: 1.5;")
        lay_monitoreo.addWidget(lbl_modulos)

        lbl_uso_titulo = QLabel("Cómo usar el Monitoreo:")
        lbl_uso_titulo.setStyleSheet("font-weight: 600; font-size: 10pt; color: #1E293B; margin-top: 6px;")
        lay_monitoreo.addWidget(lbl_uso_titulo)

        texto_uso = (
            "1. <b>Agrega rutas:</b> Coloca las carpetas que deseas monitorear en la sección 'Rutas Monitoreadas'.\n\n"
            "2. <b>Activa módulos:</b> Selecciona los detectores que necesites (RGB, Tinta, etc.).\n\n"
            "3. <b>Supervisa automáticamente:</b> El asistente monitorea las carpetas y procesa archivos en tiempo real.\n\n"
        )
        lbl_uso = QLabel(texto_uso)
        lbl_uso.setFont(QFont("Segoe UI", 9))
        lbl_uso.setWordWrap(True)
        lbl_uso.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lbl_uso.setStyleSheet(f"color: {C_TEXT}; line-height: 1.5;")
        lay_monitoreo.addWidget(lbl_uso)

        main_layout.addWidget(frame_monitoreo)

        frame_logo = QFrame()
        frame_logo.setStyleSheet(
            f"background-color: {C_HEADER_BG}; border-radius: 10px; border: 1px solid {C_BORDER};"
        )
        lay_logo = QHBoxLayout(frame_logo)
        lay_logo.setContentsMargins(14, 12, 14, 12)

        lbl_img = QLabel()
        ruta_logo = os.path.join(BASE_DIR, "logo.png")
        if os.path.exists(ruta_logo):
            lbl_img.setPixmap(QPixmap(ruta_logo).scaled(48, 48, Qt.KeepAspectRatio,
                                                         Qt.SmoothTransformation))
        else:
            lbl_img.setText("🐱")
            lbl_img.setFont(QFont("Segoe UI", 22))
        lbl_img.setAlignment(Qt.AlignCenter)
        lay_logo.addWidget(lbl_img)

        lbl_nombre = QLabel("@GatoGary")
        lbl_nombre.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl_nombre.setStyleSheet(f"color: {C_TEXT}; font-weight: 700;")
        lay_logo.addWidget(lbl_nombre)
        lay_logo.addStretch()
        main_layout.addWidget(frame_logo)

        frame_redes = QFrame()
        frame_redes.setStyleSheet(
            f"background-color: {C_SURFACE}; border-radius: 10px; border: 1px solid {C_BORDER};"
        )
        lay_redes = QVBoxLayout(frame_redes)
        lay_redes.setContentsMargins(16, 14, 16, 14)

        lbl_redes_titulo = QLabel("Redes sociales")
        lbl_redes_titulo.setStyleSheet("font-weight: 700; font-size: 10pt; color: #374151;")
        lay_redes.addWidget(lbl_redes_titulo)

        grid_redes = QGridLayout()
        grid_redes.setVerticalSpacing(10)
        grid_redes.setHorizontalSpacing(14)

        redes_info = [
            ("github.png",  "GITHUB",  "https://github.com/GatoGary/Asistente-de-impresiones"),
            ("twitter.png", "TWITTER", "https://x.com/CatGary174869"),
            ("reddit.png",  "REDDIT",  "https://www.reddit.com/user/GatoG4ry/"),
        ]
        for i, (img_file, titulo, url) in enumerate(redes_info):
            lbl_icono = QLabel()
            ruta_icono = os.path.join(BASE_DIR, img_file)
            if os.path.exists(ruta_icono):
                lbl_icono.setPixmap(
                    QPixmap(ruta_icono).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                lbl_icono.setText("🔗")
            lbl_icono.setAlignment(Qt.AlignCenter)
            grid_redes.addWidget(lbl_icono, i, 0)

            lbl_tit = QLabel(titulo)
            lbl_tit.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl_tit.setStyleSheet("font-weight: 600; color: #475569;")
            grid_redes.addWidget(lbl_tit, i, 1)

            lbl_link = QLabel(f'<a href="{url}" style="color: {C_BLUE};">{url}</a>')
            lbl_link.setFont(QFont("Segoe UI", 9))
            lbl_link.setOpenExternalLinks(True)
            grid_redes.addWidget(lbl_link, i, 2)

        lay_redes.addLayout(grid_redes)
        main_layout.addWidget(frame_redes)
        main_layout.addStretch()

        for txt in (
            'Desarrollado por "Gary"',
            "@cerátias · todos los derechos reservados"
        ):
            lbl = QLabel(txt)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet(f"color: {C_TEXT_SEC};")
            lbl.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(lbl)


# ------------------------------------------------------------------
# ── VENTANA PRINCIPAL ──────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, user_data: dict = None):
        super().__init__()
        self.user_data = user_data or {}
        self.setWindowTitle("CERATIAS - Sistema Dual")
        self.setMinimumSize(860, 660)

        self.entradas_manuales   = {}
        self.subtotales_manuales = {}
        self.totales_col_cant    = {}
        self.totales_col_precio  = {}

        # Asistente
        self.asi_signals  = SignalEmitter()
        self.asi_rutas    = []
        self.asi_obs_org  = self.asi_obs_rgb = self.asi_obs_tinta = None
        self.asi_signals.notificacion_toast.connect(self._asi_toast)
        self.asi_signals.rgb_detectado.connect(self._asi_alerta_rgb)
        self.asi_signals.sobrecarga_400.connect(self._asi_alerta_400)

        self.init_ui()
        # Aplicar stylesheet global DESPUÉS de crear los widgets
        self.setStyleSheet(MODERN_STYLESHEET)
        self._actualizar_titulo_perfil()
        self._asi_restaurar_estado()

    def _actualizar_titulo_perfil(self):
        self.setWindowTitle(f"EYM  —  Perfil: {gestor.perfil_activo}")

    # ── Toolbar de usuario ──────────────────────────────────────────
    def _crear_toolbar_usuario(self):
        usuario_nombre = self.user_data.get("nombre", "Usuario")
        toolbar = QToolBar("Usuario")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        sep = QWidget()
        sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(sep)

        widget_usuario = QWidget()
        lay_u = QHBoxLayout(widget_usuario)
        lay_u.setContentsMargins(8, 2, 10, 2)
        lay_u.setSpacing(10)

        # Avatar circular con iniciales
        iniciales = (usuario_nombre[:2]).upper()
        lbl_avatar = QLabel(iniciales)
        lbl_avatar.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_avatar.setAlignment(Qt.AlignCenter)
        lbl_avatar.setFixedSize(30, 30)
        lbl_avatar.setStyleSheet(
            f"background-color: {C_GREEN}; color: white; border-radius: 15px;"
            "font-weight: 700; font-size: 9pt;"
        )
        lay_u.addWidget(lbl_avatar)

        lbl_usuario = QLabel(usuario_nombre)
        lbl_usuario.setStyleSheet(
            f"color: {C_TEXT}; font-weight: 500; background: transparent;"
        )
        lay_u.addWidget(lbl_usuario)

        btn_cerrar_sesion = QPushButton("Cerrar sesión")
        btn_cerrar_sesion.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cerrar_sesion.setFixedHeight(28)
        btn_cerrar_sesion.setStyleSheet(BTN_DANGER_OUT)
        btn_cerrar_sesion.clicked.connect(self._cerrar_sesion)
        lay_u.addWidget(btn_cerrar_sesion)

        toolbar.addWidget(widget_usuario)
        self.addToolBar(toolbar)

    def _cerrar_sesion(self):
        respuesta = QMessageBox.question(
            self, "Cerrar sesión", "¿Estás seguro de que deseas cerrar sesión?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.No:
            return
        from auth_manager import AuthManager
        AuthManager().logout()
        QMessageBox.information(self, "Sesión cerrada", "Sesión cerrada exitosamente.")
        self.close()

    # ── Status bar con logo ─────────────────────────────────────────
    def _crear_status_bar_logo(self):
        status_bar = self.statusBar()
        status_bar.setMaximumHeight(60)

        lbl_logo_status = QLabel()
        lbl_logo_status.setFixedSize(100, 56)
        ruta_logo = os.path.join(BASE_DIR, "logo_seratias2.png")
        if os.path.exists(ruta_logo):
            lbl_logo_status.setPixmap(
                QPixmap(ruta_logo).scaled(100, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        status_bar.addWidget(lbl_logo_status, 0)

        mensaje_firebase = self.user_data.get("mensaje", "")
        if mensaje_firebase:
            lbl_mensaje = QLabel(mensaje_firebase)
            lbl_mensaje.setStyleSheet(
                f"color: {C_TEXT_SEC}; font-size: 9pt; padding: 4px 16px;"
                f"background-color: {C_HEADER_BG}; border-left: 2px solid {C_BORDER};"
            )
            lbl_mensaje.setMaximumHeight(50)
            lbl_mensaje.setWordWrap(True)
            status_bar.addPermanentWidget(lbl_mensaje)

    # ── Menú y estructura general ───────────────────────────────────
    def init_ui(self):
        barramenu = self.menuBar()
        configmenu = barramenu.addMenu("Configuración")
        configmenu.addAction("Precios Base").triggered.connect(self.abrir_seleccionar_perfil)
        configmenu.addAction("Gestor de Perfiles").triggered.connect(self.abrir_gestor_perfiles)
        barramenu.addAction("Cuenta").triggered.connect(self.abrir_cuenta)
        barramenu.addAction("Acerca de").triggered.connect(self.abrir_acerca_de)

        self._crear_toolbar_usuario()
        self._crear_status_bar_logo()

        self.notebook = QTabWidget()
        self.setCentralWidget(self.notebook)

        fondos = [
            (os.path.join(BASE_DIR, f"fondo{i}.jpg")
             if os.path.exists(os.path.join(BASE_DIR, f"fondo{i}.jpg")) else None)
            for i in range(1, 6)
        ]

        # Pestaña 1: Precios (sub-tabs Manual + Automático)
        pestana1 = FondoWidget(fondos[0])
        lay1 = QVBoxLayout(pestana1)
        lay1.setContentsMargins(0, 0, 0, 0)
        self.sub_notebook = QTabWidget()
        lay1.addWidget(self.sub_notebook)
        self.notebook.addTab(pestana1, " Precios 🗒️ ")
        self.setup_pestana_manual()
        self.setup_pestana_automatica()

        # Pestaña 2: Monitor / Asistente
        pestana2 = FondoWidget(fondos[1])
        lay2 = QVBoxLayout(pestana2)
        lay2.setContentsMargins(0, 0, 0, 0)
        self.sub_notebook_2 = QTabWidget()
        lay2.addWidget(self.sub_notebook_2)
        self.notebook.addTab(pestana2, " Monitor 🖼️ ")
        self.setup_pestana_asistente()

        # Pestañas 3-5 vacías
        for nombre_tab, fondo_path in [
            (" Generator Mockus 👕 ", fondos[2]),
            (" PESTAÑA 4 ", fondos[3]),
            (" PESTAÑA 5 ", fondos[4]),
        ]:
            pestana_vacia = FondoWidget(fondo_path)
            lay = QVBoxLayout(pestana_vacia)
            lay.setAlignment(Qt.AlignCenter)
            lbl_pronto = QLabel("Próximamente...")
            lbl_pronto.setAlignment(Qt.AlignCenter)
            lbl_pronto.setFont(QFont("Segoe UI", 16, QFont.Bold))
            lbl_pronto.setStyleSheet(f"color: {C_TEXT_SEC}; background: transparent;")
            lay.addWidget(lbl_pronto)
            self.notebook.addTab(pestana_vacia, nombre_tab)

    # ── Pestaña Manual ─────────────────────────────────────────────
    def setup_pestana_manual(self):
        pestana = QWidget()
        pestana.setStyleSheet(f"background-color: {C_BG};")
        outer = QVBoxLayout(pestana)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        # Card principal
        card = _make_card(radius=16)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        outer.addWidget(card)

        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(6)
        grid.setColumnStretch(0, 2)
        for col_idx in range(1, 9):
            grid.setColumnStretch(col_idx, 3)
        layout.addLayout(grid)

        tipos_columnas = ["CORTA", "LARGA", "TRUZA", "CERO"]

        # Header TALLA
        lbl_talla_hdr = QLabel("TALLA")
        lbl_talla_hdr.setFont(QFont("Segoe UI", 9))
        lbl_talla_hdr.setAlignment(Qt.AlignCenter)
        lbl_talla_hdr.setStyleSheet(
            f"background-color: {C_HEADER_BG}; color: {C_TEXT_SEC};"
            "padding: 9px 4px; border-radius: 8px; font-weight: 700;"
        )
        grid.addWidget(lbl_talla_hdr, 0, 0)

        # Headers de columnas (span de 2 para cantidad + subtotal)
        for idx, tipo in enumerate(tipos_columnas):
            lbl_hdr = QLabel(tipo)
            lbl_hdr.setFont(QFont("Segoe UI", 9))
            lbl_hdr.setAlignment(Qt.AlignCenter)
            lbl_hdr.setStyleSheet(
                f"background-color: {C_HEADER_BG}; color: {C_TEXT_SEC};"
                "padding: 9px 4px; border-radius: 8px; font-weight: 700;"
            )
            grid.addWidget(lbl_hdr, 0, 1 + (idx * 2), 1, 2)

        # Filas de tallas
        for r_idx, rango in enumerate(PRECIOS_FABRICA.keys(), start=1):
            lbl_rango = QLabel(rango)
            lbl_rango.setFont(QFont("Segoe UI", 9))
            lbl_rango.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl_rango.setStyleSheet(
                f"font-weight: 600; color: #475569; padding: 4px 0 4px 6px;"
            )
            grid.addWidget(lbl_rango, r_idx, 0)

            self.entradas_manuales[rango]   = {}
            self.subtotales_manuales[rango] = {}

            for c_idx, tipo in enumerate(tipos_columnas):
                entry = QLineEdit()
                entry.setAlignment(Qt.AlignCenter)
                entry.setPlaceholderText("—")
                entry.setStyleSheet(ENTRY_GRID)
                entry.textChanged.connect(self.calcular_manual)
                grid.addWidget(entry, r_idx, 1 + (c_idx * 2))
                self.entradas_manuales[rango][tipo] = entry

                lbl_sub = QLabel("")
                lbl_sub.setAlignment(Qt.AlignCenter)
                lbl_sub.setFont(QFont("Segoe UI", 9))
                lbl_sub.setStyleSheet(f"color: {C_GREEN}; font-weight: 600;")
                grid.addWidget(lbl_sub, r_idx, 2 + (c_idx * 2))
                self.subtotales_manuales[rango][tipo] = lbl_sub

        # Fila TOTALES
        fila_tot = len(PRECIOS_FABRICA) + 1
        lbl_tot_tit = QLabel("TOTALES")
        lbl_tot_tit.setFont(QFont("Segoe UI", 9))
        lbl_tot_tit.setStyleSheet(f"font-weight: 700; color: {C_TEXT}; padding-left: 6px;")
        grid.addWidget(lbl_tot_tit, fila_tot, 0)

        for c_idx, tipo in enumerate(tipos_columnas):
            lbl_c_cant = QLabel("0")
            lbl_c_cant.setFont(QFont("Segoe UI", 9))
            lbl_c_cant.setAlignment(Qt.AlignCenter)
            lbl_c_cant.setStyleSheet(
                f"font-weight: 700; color: {C_TEXT};"
                f"border-top: 2px solid {C_BORDER}; padding-top: 6px;"
            )
            grid.addWidget(lbl_c_cant, fila_tot, 1 + (c_idx * 2))
            self.totales_col_cant[tipo] = lbl_c_cant

            lbl_c_precio = QLabel("S/. 0.00")
            lbl_c_precio.setFont(QFont("Segoe UI", 9))
            lbl_c_precio.setAlignment(Qt.AlignCenter)
            lbl_c_precio.setStyleSheet(
                f"font-weight: 700; color: {C_GREEN};"
                f"border-top: 2px solid {C_BORDER}; padding-top: 6px;"
            )
            grid.addWidget(lbl_c_precio, fila_tot, 2 + (c_idx * 2))
            self.totales_col_precio[tipo] = lbl_c_precio

        layout.addSpacing(8)

        # Fila: TOTAL + Limpiar
        fila_total = QHBoxLayout()
        fila_total.setAlignment(Qt.AlignCenter)
        fila_total.setSpacing(16)

        lbl_total_tit = QLabel("TOTAL")
        lbl_total_tit.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_total_tit.setStyleSheet(f"color: {C_TEXT}; font-weight: 700;")
        fila_total.addWidget(lbl_total_tit)

        self.label_total_manual = QLabel("S/. 0.00")
        self.label_total_manual.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.label_total_manual.setAlignment(Qt.AlignCenter)
        self.label_total_manual.setStyleSheet(
            f"background-color: {C_GREEN}; color: white;"
            "border-radius: 12px; padding: 10px 50px;"
            "min-width: 130px; font-weight: 700; font-size: 15pt;"
        )
        fila_total.addWidget(self.label_total_manual)

        btn_limpiar = QPushButton("🗑  Limpiar Todo")
        btn_limpiar.setFixedWidth(138)
        btn_limpiar.setFixedHeight(40)
        btn_limpiar.setStyleSheet(BTN_GRIS)
        btn_limpiar.clicked.connect(self.limpiar_manual)
        fila_total.addWidget(btn_limpiar)

        layout.addLayout(fila_total)

        # Warning truzas
        self.lbl_warning_truza = QLabel("")
        self.lbl_warning_truza.setStyleSheet(
            "color: #92400E; font-weight: 600; font-size: 9pt;"
            "background-color: #FEF3C7; border: 1px solid #FCD34D;"
            "border-radius: 8px; padding: 7px 14px;"
        )
        self.lbl_warning_truza.setAlignment(Qt.AlignCenter)
        self.lbl_warning_truza.hide()
        layout.addWidget(self.lbl_warning_truza)

        # Botones de acción
        fila_acciones = QHBoxLayout()
        fila_acciones.setAlignment(Qt.AlignCenter)
        fila_acciones.setSpacing(12)

        btn_imagen = QPushButton("📋  Obtener detalles")
        btn_imagen.setFixedWidth(168)
        btn_imagen.setFixedHeight(40)
        btn_imagen.setStyleSheet(BTN_AZUL)
        btn_imagen.setToolTip("Genera la ficha como imagen y la copia al portapapeles")
        btn_imagen.clicked.connect(self.accion_copiar_imagen)

        btn_pdf = QPushButton("📄  Descargar en PDF")
        btn_pdf.setFixedWidth(168)
        btn_pdf.setFixedHeight(40)
        btn_pdf.setStyleSheet(BTN_ROJO)
        btn_pdf.setToolTip("Exporta la ficha como PDF a la carpeta Descargas")
        btn_pdf.clicked.connect(self.accion_descargar_pdf)

        fila_acciones.addWidget(btn_imagen)
        fila_acciones.addWidget(btn_pdf)
        layout.addLayout(fila_acciones)

        self.sub_notebook.addTab(pestana, " MODO MANUAL ")

    # ── Pestaña Automática ─────────────────────────────────────────
    def setup_pestana_automatica(self):
        pestana = QWidget()
        pestana.setStyleSheet(f"background-color: {C_BG};")
        outer = QVBoxLayout(pestana)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        card = _make_card(radius=16)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        outer.addWidget(card)

        btn_carpeta = QPushButton("📁  Seleccionar Carpeta")
        btn_carpeta.setFixedHeight(40)
        btn_carpeta.setFixedWidth(210)
        btn_carpeta.setStyleSheet(BTN_AZUL)
        btn_carpeta.clicked.connect(self.seleccionar_carpeta_y_calcular)
        layout.addWidget(btn_carpeta, 0, Qt.AlignHCenter)

        self.label_carpeta = QLabel("Ninguna carpeta seleccionada")
        self.label_carpeta.setStyleSheet(f"color: {C_TEXT_SEC}; font-size: 9pt;")
        self.label_carpeta.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_carpeta)

        group_resumen = QGroupBox(" Resumen ")
        group_resumen.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout_resumen = QVBoxLayout(group_resumen)
        self.label_resultado_rapido = QLabel("Esperando archivos...")
        self.label_resultado_rapido.setFont(QFont("Consolas", 9))
        self.label_resultado_rapido.setStyleSheet(f"color: {C_TEXT};")
        layout_resumen.addWidget(self.label_resultado_rapido)
        layout.addWidget(group_resumen)

        self.label_total_grande = QLabel("Total: S/. 0.00")
        self.label_total_grande.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.label_total_grande.setStyleSheet(
            f"color: {C_GREEN}; font-weight: 700; padding: 6px;"
        )
        self.label_total_grande.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_total_grande)

        self.btn_toggle = QPushButton("▶  Mostrar Cálculo Detallado")
        self.btn_toggle.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                color: {C_BLUE}; border: none; background: transparent;
                font-size: 10pt; font-weight: 500;
            }}
            QPushButton:hover {{ color: {C_BLUE_HV}; }}
        """)
        self.btn_toggle.clicked.connect(self.toggle_detalle)
        layout.addWidget(self.btn_toggle, 0, Qt.AlignHCenter)

        self.area_desglose = QScrollArea()
        self.area_desglose.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout  = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.area_desglose.setWidget(self.scroll_content)
        self.area_desglose.hide()
        layout.addWidget(self.area_desglose)

        self.sub_notebook.addTab(pestana, " MODO AUTOMÁTICO ")

    # ── Lógica Manual ──────────────────────────────────────────────
    def calcular_manual(self):
        TABLA_PRECIOS = get_tabla_precios()
        grand_total   = 0.0
        tipos         = ["CORTA", "LARGA", "TRUZA", "CERO"]
        acum_cantidades = {t: 0   for t in tipos}
        acum_precios    = {t: 0.0 for t in tipos}

        for rango, de_tipos in self.entradas_manuales.items():
            for tipo, entry in de_tipos.items():
                valor = entry.text().strip()
                subtotal_item = 0.0
                if valor:
                    try:
                        cant = int(valor)
                        if cant < 0:
                            raise ValueError
                        precio_unitario = TABLA_PRECIOS.get(rango, {}).get(tipo, 0.0)
                        subtotal_item   = cant * precio_unitario
                        acum_cantidades[tipo] += cant
                        acum_precios[tipo]    += subtotal_item
                        grand_total           += subtotal_item
                        entry.setStyleSheet(ENTRY_GRID)
                    except ValueError:
                        entry.setStyleSheet(ENTRY_ERROR)
                else:
                    entry.setStyleSheet(ENTRY_GRID)

                if subtotal_item > 0:
                    self.subtotales_manuales[rango][tipo].setText(
                        f"S/.{subtotal_item:.2f}"
                    )
                else:
                    self.subtotales_manuales[rango][tipo].setText("")

        for tipo in tipos:
            self.totales_col_cant[tipo].setText(
                str(acum_cantidades[tipo]) if acum_cantidades[tipo] > 0 else "0"
            )
            self.totales_col_precio[tipo].setText(
                f"S/. {acum_precios[tipo]:.2f}" if acum_precios[tipo] > 0 else "S/. 0.00"
            )

        self.label_total_manual.setText(
            f"S/. {grand_total:.2f}" if grand_total > 0 else "S/. 0.00"
        )

        camisetas_total = (acum_cantidades['CORTA'] + acum_cantidades['LARGA']
                           + acum_cantidades['CERO'])
        if acum_cantidades['TRUZA'] > camisetas_total:
            self.lbl_warning_truza.setText(
                "⚠️  La cantidad de TRUZAS es mayor que la de CAMISETAS."
            )
            self.lbl_warning_truza.show()
        else:
            self.lbl_warning_truza.hide()

    def limpiar_manual(self):
        for rango in self.entradas_manuales:
            for tipo in self.entradas_manuales[rango]:
                self.entradas_manuales[rango][tipo].clear()
                self.entradas_manuales[rango][tipo].setStyleSheet(ENTRY_GRID)
        self.calcular_manual()

    # ── Acciones portapapeles / PDF ────────────────────────────────
    def accion_copiar_imagen(self):
        imagen, err = generar_imagen_ficha(self.entradas_manuales)
        if imagen is None:
            QMessageBox.warning(self, "Sin datos", err)
            return
        QApplication.clipboard().setPixmap(QPixmap.fromImage(imagen))
        self._asi_toast("Ficha Copiada", "✅ La ficha fue copiada al portapapeles.")

    def accion_descargar_pdf(self):
        descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.isdir(descargas):
            descargas = os.path.expanduser("~")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"ficha_ceratias_{timestamp}.pdf"
        ruta_destino   = os.path.join(descargas, nombre_archivo)

        exito, err = generar_pdf_ficha(self.entradas_manuales, ruta_destino)
        if not exito:
            QMessageBox.warning(self, "Error al exportar",
                                f"No se pudo generar el PDF:\n{err}")
            return
        self._asi_toast("PDF Exportado",
                        f"✅ Ficha exportada.\n\nArchivo: {nombre_archivo}\n{descargas}")

    # ── Lógica Automática ──────────────────────────────────────────
    def seleccionar_carpeta_y_calcular(self):
        ruta_carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not ruta_carpeta:
            return
        self.label_carpeta.setText(f"Carpeta: {ruta_carpeta}")
        resumen, procesados, ignorados, detalle_conteo, status = \
            calcular_precio_total(ruta_carpeta)

        if resumen is None:
            QMessageBox.critical(self, "Error de Consistencia", procesados)
            return
        if "Advertencia" in status:
            QMessageBox.warning(self, "Advertencia de Archivos",
                                f"{status}\n\nEl sistema continuará procesando el resto.")

        texto_rapido  = f"👕 Camisetas vinculadas (CUELLO): {resumen['camisetas']} u.\n"
        texto_rapido += f"🩳 Truzas detectadas: {resumen['truzas']} u.\n"
        texto_rapido += f"📋 Perfil activo: {gestor.perfil_activo}\n"
        texto_rapido += "─" * 40 + "\n"
        for clave, cant in detalle_conteo.items():
            texto_rapido += f"• {clave}: {cant} unidades\n"
        self.label_resultado_rapido.setText(texto_rapido)
        self.label_total_grande.setText(f"Total: S/. {resumen['total']:.2f}")

        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for item in procesados:
            f_item = QFrame()
            f_item.setStyleSheet(
                f"background-color: {C_SURFACE}; border-bottom: 1px solid {C_BORDER};"
                "border-radius: 8px; margin: 2px 0;"
            )
            lay_item = QHBoxLayout(f_item)
            lbl_img = QLabel()
            if item['file'].lower().endswith('.jpg'):
                pix = QPixmap(item['path'])
                if not pix.isNull():
                    lbl_img.setPixmap(
                        pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )
                else:
                    lbl_img.setText("[Sin Vista]")
            else:
                lbl_img.setText("[PDF]")
            lay_item.addWidget(lbl_img)
            info_txt = (f"<b>{item['file']}</b><br>"
                        f"Talla: {item['rango']} | {item['tipo']}<br>"
                        f"<span style='color:{C_GREEN};'>S/. {item['subtotal']:.2f}</span>")
            lbl_info = QLabel(info_txt)
            lbl_info.setFont(QFont("Segoe UI", 9))
            lay_item.addWidget(lbl_info)
            lay_item.addStretch()
            self.scroll_layout.addWidget(f_item)

        if ignorados:
            lbl_ign_title = QLabel("\n⚠️  No procesados (sin patrón de talla/tipo)")
            lbl_ign_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl_ign_title.setStyleSheet(f"color: {C_RED};")
            self.scroll_layout.addWidget(lbl_ign_title)
            for f in ignorados:
                lbl_f = QLabel(f"❌  {f}")
                lbl_f.setFont(QFont("Segoe UI", 8))
                lbl_f.setStyleSheet(f"color: {C_TEXT_SEC};")
                self.scroll_layout.addWidget(lbl_f)

    def toggle_detalle(self):
        visible = self.area_desglose.isVisible()
        self.area_desglose.setVisible(not visible)
        self.btn_toggle.setText(
            "▼  Ocultar Cálculo Detallado" if not visible else "▶  Mostrar Cálculo Detallado"
        )

    # ── Pestaña Asistente ──────────────────────────────────────────
    def setup_pestana_asistente(self):
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {C_BG};")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        card = _make_card(radius=16)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)
        outer.addWidget(card)

        lbl_titulo = QLabel("ceratias Asistente — Panel de Control")
        lbl_titulo.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet(
            f"color: {C_BLUE}; padding: 6px 0 8px 0;"
            f"border-bottom: 2px solid {C_BORDER};"
            "font-weight: 700;"
        )
        layout.addWidget(lbl_titulo)

        if not _WATCHDOG_OK or not _PIL_OK or not _TOAST_OK:
            faltantes = []
            if not _WATCHDOG_OK: faltantes.append("watchdog")
            if not _PIL_OK:      faltantes.append("Pillow / numpy")
            if not _TOAST_OK:    faltantes.append("winotify")
            lbl_warn = QLabel(
                f"⚠️  Dependencias faltantes: {', '.join(faltantes)}\n"
                "Instálalas con pip para activar los detectores."
            )
            lbl_warn.setStyleSheet(
                "background-color: #FEF3C7; border: 1px solid #FCD34D;"
                "border-radius: 9px; padding: 10px 14px; color: #92400E;"
                "font-weight: 500;"
            )
            lbl_warn.setWordWrap(True)
            layout.addWidget(lbl_warn)

        # Rutas monitoreadas
        grp_rutas = QGroupBox(" Rutas Monitoreadas ")
        grp_rutas.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lay_grp = QVBoxLayout(grp_rutas)

        self.asi_list_rutas = QListWidget()
        self.asi_list_rutas.setFixedHeight(100)
        self.asi_list_rutas.setFont(QFont("Consolas", 9))
        lay_grp.addWidget(self.asi_list_rutas)

        fila_add = QHBoxLayout()
        self.asi_input_ruta = QLineEdit()
        self.asi_input_ruta.setPlaceholderText("Pegar ruta de carpeta aquí...")
        self.asi_input_ruta.setFont(QFont("Segoe UI", 9))
        btn_add = QPushButton("➕  Añadir")
        btn_add.setFixedWidth(100)
        btn_add.setFixedHeight(32)
        btn_add.setStyleSheet(BTN_AZUL)
        btn_del = QPushButton("🗑  Quitar")
        btn_del.setFixedWidth(100)
        btn_del.setFixedHeight(32)
        btn_del.setStyleSheet(BTN_GRIS)
        btn_add.clicked.connect(self._asi_agregar_ruta)
        btn_del.clicked.connect(self._asi_eliminar_ruta)
        fila_add.addWidget(self.asi_input_ruta)
        fila_add.addWidget(btn_add)
        fila_add.addWidget(btn_del)
        lay_grp.addLayout(fila_add)
        layout.addWidget(grp_rutas)

        # Módulos de monitoreo
        grp_ctrl = QGroupBox(" Módulos de Monitoreo ")
        grp_ctrl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lay_ctrl = QVBoxLayout(grp_ctrl)
        lay_ctrl.setSpacing(12)

        self.asi_btn_org, self.asi_lbl_org = self._asi_crear_fila(
            lay_ctrl, "🗂   AUTOGENERAR CARPETAS", self._asi_toggle_org)
        self.asi_btn_rgb, self.asi_lbl_rgb = self._asi_crear_fila(
            lay_ctrl, "🎨  DETECTOR RGB", self._asi_toggle_rgb)
        self.asi_btn_tinta, self.asi_lbl_tinta = self._asi_crear_fila(
            lay_ctrl, "💧  DETECTOR CARGA DE TINTA", self._asi_toggle_tinta)
        layout.addWidget(grp_ctrl)
        layout.addStretch()

        self.sub_notebook_2.addTab(panel, " ceratias Asistente ")

        config = cargar_config_asistente()
        self.asi_rutas       = config.get("rutas", [])
        self.asi_estados_ini = config.get("estados", {"org": False, "rgb": False, "tinta": False})
        for r in self.asi_rutas:
            self.asi_list_rutas.addItem(r)

    def _asi_crear_fila(self, layout_padre, nombre, funcion):
        fila = QHBoxLayout()
        fila.setSpacing(10)

        lbl_nom = QLabel(nombre)
        lbl_nom.setFont(QFont("Segoe UI", 10))
        lbl_nom.setFixedWidth(260)
        lbl_nom.setStyleSheet(f"color: {C_TEXT}; font-weight: 500;")

        lbl_est = QLabel("●  OFF")
        lbl_est.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_est.setFixedWidth(64)
        lbl_est.setStyleSheet(f"color: {C_TEXT_SEC}; font-weight: 700;")

        btn = QPushButton("INICIAR")
        btn.setCheckable(True)
        btn.setFixedWidth(110)
        btn.setFixedHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_GREEN};
                color: white;
                font-weight: 700;
                border-radius: 9px;
                border: none;
                font-size: 9.5pt;
            }}
            QPushButton:hover   {{ background-color: {C_GREEN_HV}; }}
            QPushButton:checked {{ background-color: {C_RED}; }}
            QPushButton:checked:hover {{ background-color: {C_RED_HV}; }}
        """)
        btn.clicked.connect(lambda chk, b=btn, l=lbl_est: funcion(chk, b, l))

        fila.addWidget(lbl_nom)
        fila.addStretch()
        fila.addWidget(lbl_est)
        fila.addWidget(btn)
        layout_padre.addLayout(fila)
        return btn, lbl_est

    def _asi_set_status(self, activo, btn, lbl):
        if activo:
            btn.setText("DETENER")
            lbl.setText("●  ON")
            lbl.setStyleSheet(f"color: {C_GREEN}; font-weight: 700;")
        else:
            btn.setText("INICIAR")
            lbl.setText("●  OFF")
            lbl.setStyleSheet(f"color: {C_TEXT_SEC}; font-weight: 700;")

    def _asi_detener(self, obs):
        if obs:
            obs.stop()
            obs.join()
        return None

    @Slot(str, str)
    def _asi_toast(self, titulo, mensaje):
        if not _TOAST_OK:
            return
        try:
            ruta_icono = os.path.join(BASE_DIR, "eym.png")
            toast = Notification(app_id="EYM Asistente", title=titulo, msg=mensaje,
                                 icon=ruta_icono if os.path.exists(ruta_icono) else "")
            toast.show()
        except Exception as e:
            print(f"Toast error: {e}")

    @Slot(str)
    def _asi_alerta_rgb(self, ruta):
        QMessageBox.warning(self, "¡Atención! — Archivo RGB",
                            f"Se detectó un archivo en MODO RGB:\n{os.path.basename(ruta)}")

    @Slot(str, str)
    def _asi_alerta_400(self, orig, mask):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("CARGA 400% Detectada")
        msg.setText(f"¡Carga total de tinta encontrada!\nArchivo: {os.path.basename(orig)}")
        btn_ver = msg.addButton("Ver Mapa", QMessageBox.ActionRole)
        msg.addButton("Cerrar", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_ver:
            os.startfile(mask)

    def _asi_toggle_org(self, chk, btn, lbl):
        self.asi_obs_org = self._asi_detener(self.asi_obs_org)
        if chk and self.asi_rutas and _WATCHDOG_OK:
            self.asi_obs_org = Observer()
            for r in self.asi_rutas:
                if os.path.exists(r):
                    self.asi_obs_org.schedule(
                        OrganizadorHandler(self.asi_signals), r, recursive=False
                    )
            self.asi_obs_org.start()
        self._asi_set_status(chk, btn, lbl)
        self._asi_guardar()

    def _asi_toggle_rgb(self, chk, btn, lbl):
        self.asi_obs_rgb = self._asi_detener(self.asi_obs_rgb)
        if chk and self.asi_rutas and _WATCHDOG_OK:
            self.asi_obs_rgb = Observer()
            for r in self.asi_rutas:
                if os.path.exists(r):
                    self.asi_obs_rgb.schedule(
                        RGBHandler(self.asi_signals), r, recursive=True
                    )
            self.asi_obs_rgb.start()
        self._asi_set_status(chk, btn, lbl)
        self._asi_guardar()

    def _asi_toggle_tinta(self, chk, btn, lbl):
        self.asi_obs_tinta = self._asi_detener(self.asi_obs_tinta)
        if chk and self.asi_rutas and _WATCHDOG_OK and _PIL_OK:
            self.asi_obs_tinta = Observer()
            for r in self.asi_rutas:
                if os.path.exists(r):
                    self.asi_obs_tinta.schedule(
                        TintaHandler(self.asi_signals), r, recursive=True
                    )
            self.asi_obs_tinta.start()
        self._asi_set_status(chk, btn, lbl)
        self._asi_guardar()

    def _asi_restaurar_estado(self):
        if not hasattr(self, 'asi_estados_ini'):
            return
        if self.asi_estados_ini.get("org"):   self.asi_btn_org.click()
        if self.asi_estados_ini.get("rgb"):   self.asi_btn_rgb.click()
        if self.asi_estados_ini.get("tinta"): self.asi_btn_tinta.click()

    def _asi_guardar(self):
        guardar_config_asistente(self.asi_rutas, {
            "org":   self.asi_btn_org.isChecked(),
            "rgb":   self.asi_btn_rgb.isChecked(),
            "tinta": self.asi_btn_tinta.isChecked(),
        })

    def _asi_agregar_ruta(self):
        r = self.asi_input_ruta.text().strip()
        if r and os.path.exists(r) and r not in self.asi_rutas:
            self.asi_rutas.append(r)
            self.asi_list_rutas.addItem(r)
            self.asi_input_ruta.clear()
            self._asi_guardar()
        elif r and not os.path.exists(r):
            QMessageBox.warning(self, "Ruta inválida", f"La ruta no existe:\n{r}")

    def _asi_eliminar_ruta(self):
        item = self.asi_list_rutas.currentItem()
        if item:
            self.asi_rutas.remove(item.text())
            self.asi_list_rutas.takeItem(self.asi_list_rutas.row(item))
            self._asi_guardar()

    # ── Menú actions ───────────────────────────────────────────────
    def abrir_seleccionar_perfil(self):
        dlg = SeleccionarPerfilDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self._actualizar_titulo_perfil()
            self.calcular_manual()

    def abrir_gestor_perfiles(self):
        GestorPerfilesDialog(self).exec()
        self._actualizar_titulo_perfil()
        self.calcular_manual()

    def abrir_acerca_de(self):
        AcercaDeDialog(self).exec()

    def abrir_cuenta(self):
        CuentaDialog(self.user_data, self).exec()

    def closeEvent(self, event):
        self.asi_obs_org   = self._asi_detener(self.asi_obs_org)
        self.asi_obs_rgb   = self._asi_detener(self.asi_obs_rgb)
        self.asi_obs_tinta = self._asi_detener(self.asi_obs_tinta)
        event.accept()


# ------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
