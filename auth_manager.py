"""
auth_manager.py
Autenticación Firebase usando SOLO la API REST pública.
No requiere serviceAccountKey.json ni firebase-admin SDK.
Solo necesita la API Key pública del proyecto.
"""

import os
import json
import uuid
import hashlib
import requests
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

FIREBASE_API_KEY  = "AIzaSyBQ-1E2utlJBX2QTOOSkDQIJe4iLuI-LMY"
FIREBASE_PROJECT  = "ceratias"   # tu projectId

# URLs de Firebase REST
AUTH_URL       = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
CHANGE_PWD_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"
REFRESH_URL    = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
FIRESTORE_URL  = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT}/databases/(default)/documents"

# Sesión local cifrada
APP_DATA_DIR  = Path(os.environ.get("APPDATA", Path.home())) / ".ceratias"
SESSION_FILE  = APP_DATA_DIR / "session.dat"
KEY_FILE      = APP_DATA_DIR / "session.key"


# ─── CIFRADO LOCAL ─────────────────────────────────────────────────────────────

def _get_or_create_key() -> bytes:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    try:
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(str(KEY_FILE), 2)
    except Exception:
        pass
    return key

def _fernet() -> Fernet:
    return Fernet(_get_or_create_key())

def _save_session(data: dict):
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    encrypted = _fernet().encrypt(json.dumps(data, default=str).encode())
    SESSION_FILE.write_bytes(encrypted)

def _load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        decrypted = _fernet().decrypt(SESSION_FILE.read_bytes())
        return json.loads(decrypted)
    except Exception:
        SESSION_FILE.unlink(missing_ok=True)
        return None

def _clear_session():
    SESSION_FILE.unlink(missing_ok=True)


# ─── ID ÚNICO DE DISPOSITIVO ───────────────────────────────────────────────────

def _device_id() -> str:
    try:
        import subprocess
        result = subprocess.check_output("wmic csproduct get UUID", shell=True).decode()
        raw = result.strip().split()[-1]
    except Exception:
        raw = str(uuid.getnode())
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ─── FIRESTORE REST ────────────────────────────────────────────────────────────

def _parse_firestore_value(value: dict):
    """Convierte un valor Firestore REST al tipo Python correspondiente."""
    if "stringValue"    in value: return value["stringValue"]
    if "integerValue"   in value: return int(value["integerValue"])
    if "booleanValue"   in value: return value["booleanValue"]
    if "doubleValue"    in value: return float(value["doubleValue"])
    if "timestampValue" in value:
        ts = value["timestampValue"].replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    if "nullValue"      in value: return None
    if "mapValue"       in value:
        fields = value["mapValue"].get("fields", {})
        return {k: _parse_firestore_value(v) for k, v in fields.items()}
    if "arrayValue"     in value:
        items = value["arrayValue"].get("values", [])
        return [_parse_firestore_value(i) for i in items]
    return None

def _parse_firestore_doc(doc: dict) -> dict:
    fields = doc.get("fields", {})
    return {k: _parse_firestore_value(v) for k, v in fields.items()}

def _to_firestore_value(value) -> dict:
    if value is None:                return {"nullValue": None}
    if isinstance(value, bool):      return {"booleanValue": value}
    if isinstance(value, int):       return {"integerValue": str(value)}
    if isinstance(value, float):     return {"doubleValue": value}
    if isinstance(value, str):       return {"stringValue": value}
    if isinstance(value, datetime):
        return {"timestampValue": value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    return {"stringValue": str(value)}

def _firestore_get(collection: str, doc_id: str, id_token: str) -> dict | None:
    url  = f"{FIRESTORE_URL}/{collection}/{doc_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {id_token}"}, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return _parse_firestore_doc(resp.json())

def _firestore_patch(collection: str, doc_id: str, fields: dict, id_token: str):
    """Actualiza solo los campos indicados sin tocar el resto del documento."""
    url         = f"{FIRESTORE_URL}/{collection}/{doc_id}"
    mask_params = "&".join(f"updateMask.fieldPaths={k}" for k in fields)
    body        = {"fields": {k: _to_firestore_value(v) for k, v in fields.items()}}
    resp        = requests.patch(
        f"{url}?{mask_params}", json=body,
        headers={"Authorization": f"Bearer {id_token}"},
        timeout=10
    )
    resp.raise_for_status()

def _firestore_delete_fields(collection: str, doc_id: str, field_names: list, id_token: str):
    """Elimina campos específicos enviando null + updateMask."""
    _firestore_patch(collection, doc_id, {f: None for f in field_names}, id_token)


# ─── RESULTADO DE AUTH ─────────────────────────────────────────────────────────

class AuthResult:
    def __init__(self, success: bool, user_data: dict = None, error: str = ""):
        self.success   = success
        self.user_data = user_data or {}
        self.error     = error

    def __bool__(self):
        return self.success


# ─── AUTH MANAGER ─────────────────────────────────────────────────────────────

class AuthManager:
    def __init__(self):
        self._uid: str | None      = None
        self._id_token: str | None = None

    # ── LOGIN ──────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> AuthResult:
        # 1. Autenticar con Firebase Auth REST
        try:
            resp = requests.post(AUTH_URL, json={
                "email": email, "password": password, "returnSecureToken": True
            }, timeout=10)
            resp.raise_for_status()
            auth_data = resp.json()
        except requests.HTTPError:
            return AuthResult(False, error="Correo o contraseña incorrectos.")
        except requests.RequestException:
            return AuthResult(False, error="Sin conexión a Internet.")

        self._uid           = auth_data["localId"]
        self._id_token      = auth_data["idToken"]
        refresh_token       = auth_data.get("refreshToken", "")

        # 2. Leer documento del usuario en Firestore
        try:
            user = _firestore_get("usuarios", self._uid, self._id_token)
        except Exception as e:
            return AuthResult(False, error=f"Error al leer datos del usuario: {e}")

        if user is None:
            return AuthResult(False, error="Usuario no encontrado en la base de datos.")

        # 3. Verificar licencia
        licencia_ok, motivo = self._check_licencia(user)
        if not licencia_ok:
            return AuthResult(False, error=motivo)

        # 4. Verificar sesión duplicada
        device        = _device_id()
        stored_token  = user.get("session_token", "")
        stored_device = user.get("session_device", "")

        if stored_token and stored_device and stored_device != device:
            return AuthResult(
                False,
                error=(
                    "⚠️ Ya existe una sesión activa en otro dispositivo.\n"
                    "Cierra sesión allí o contacta al administrador."
                )
            )

        # 5. Registrar sesión en Firestore
        new_token = str(uuid.uuid4())
        _firestore_patch("usuarios", self._uid, {
            "session_token":     new_token,
            "session_device":    device,
            "session_last_seen": datetime.now(timezone.utc),
        }, self._id_token)

        # 6. Guardar sesión cifrada localmente (incluye refresh_token)
        _save_session({
            "uid":           self._uid,
            "email":         email,
            "id_token":      self._id_token,
            "refresh_token": refresh_token,
            "session_token": new_token,
            "device_id":     device,
        })

        return AuthResult(True, user_data={
            "uid":               self._uid,
            "nombre":            user.get("nombre", ""),
            "mensaje":           user.get("mensaje", ""),
            "fecha_vencimiento": user.get("fecha_vencimiento"),
            "estado":            user.get("estado"),
        })

    # ── RESTAURAR SESIÓN ───────────────────────────────────────────────────────

    def restore_session(self) -> AuthResult:
        session = _load_session()
        if not session:
            return AuthResult(False, error="No hay sesión guardada.")

        if session.get("device_id") != _device_id():
            _clear_session()
            return AuthResult(False, error="La sesión no pertenece a este dispositivo.")

        self._uid      = session["uid"]
        self._id_token = session["id_token"]

        # Refrescar idToken (expira en 1h, refresh_token dura semanas)
        if not self._refresh_token(session):
            _clear_session()
            return AuthResult(False, error="Sesión expirada. Inicia sesión nuevamente.")

        # Verificar en Firestore
        try:
            user = _firestore_get("usuarios", self._uid, self._id_token)
        except Exception:
            return AuthResult(False, error="Sin conexión para verificar sesión.")

        if user is None:
            _clear_session()
            return AuthResult(False, error="Usuario eliminado.")

        # Verificar token anti-duplicado
        if user.get("session_token") != session.get("session_token"):
            _clear_session()
            return AuthResult(False, error="Sesión invalidada desde otro dispositivo.")

        # Verificar licencia
        licencia_ok, motivo = self._check_licencia(user)
        if not licencia_ok:
            self.logout()
            return AuthResult(False, error=motivo)

        # Actualizar last_seen
        _firestore_patch("usuarios", self._uid, {
            "session_last_seen": datetime.now(timezone.utc)
        }, self._id_token)

        return AuthResult(True, user_data={
            "uid":               self._uid,
            "nombre":            user.get("nombre", ""),
            "mensaje":           user.get("mensaje", ""),
            "fecha_vencimiento": user.get("fecha_vencimiento"),
            "estado":            user.get("estado"),
        })

    # ── CERRAR SESIÓN ──────────────────────────────────────────────────────────

    def logout(self):
        if self._uid and self._id_token:
            try:
                _firestore_delete_fields(
                    "usuarios", self._uid,
                    ["session_token", "session_device"],
                    self._id_token
                )
            except Exception:
                pass
        _clear_session()
        self._uid      = None
        self._id_token = None

    # ── CAMBIAR CONTRASEÑA ─────────────────────────────────────────────────────

    def change_password(self, new_password: str) -> AuthResult:
        if not self._id_token:
            return AuthResult(False, error="No hay sesión activa.")
        try:
            resp = requests.post(CHANGE_PWD_URL, json={
                "idToken": self._id_token, "password": new_password,
                "returnSecureToken": True,
            }, timeout=10)
            resp.raise_for_status()
            data           = resp.json()
            self._id_token = data["idToken"]
            session        = _load_session()
            if session:
                session["id_token"]      = self._id_token
                session["refresh_token"] = data.get("refreshToken", session.get("refresh_token", ""))
                _save_session(session)
            return AuthResult(True)
        except requests.HTTPError as e:
            return AuthResult(False, error=f"Error al cambiar contraseña: {e}")

    # ── REFRESCAR TOKEN ────────────────────────────────────────────────────────

    def _refresh_token(self, session: dict) -> bool:
        """Renueva el idToken usando el refreshToken. Devuelve True si ok."""
        refresh_token = session.get("refresh_token", "")
        if not refresh_token:
            return True  # sin refresh_token intentar con el token actual
        try:
            resp = requests.post(REFRESH_URL, json={
                "grant_type": "refresh_token", "refresh_token": refresh_token
            }, timeout=10)
            resp.raise_for_status()
            data                     = resp.json()
            self._id_token           = data["id_token"]
            session["id_token"]      = self._id_token
            session["refresh_token"] = data["refresh_token"]
            _save_session(session)
            return True
        except Exception:
            return False

    # ── VERIFICAR LICENCIA ─────────────────────────────────────────────────────

    @staticmethod
    def _check_licencia(user: dict) -> tuple[bool, str]:
        estado = user.get("estado", "")
        if estado != "activo":
            return False, f"Tu licencia está '{estado}'. Contacta al administrador."
        fecha_vcto = user.get("fecha_vencimiento")
        if fecha_vcto and isinstance(fecha_vcto, datetime):
            ahora = datetime.now(timezone.utc)
            if fecha_vcto.tzinfo is None:
                fecha_vcto = fecha_vcto.replace(tzinfo=timezone.utc)
            if ahora > fecha_vcto:
                return False, "Tu licencia ha vencido. Contacta al administrador para renovar."
        return True, ""
