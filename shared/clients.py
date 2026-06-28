import os
import requests
from urllib.parse import urljoin


def _get_gateway_url():
    return os.environ.get('GATEWAY_URL', 'http://gateway:80')


def _get_service_token():
    """Token interno para comunicación entre servicios (opcional)"""
    return os.environ.get('INTERNAL_API_TOKEN', '')


def _headers():
    headers = {'Content-Type': 'application/json'}
    token = _get_service_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


class UsuarioServiceClient:

    @staticmethod
    def _base_url():
        return urljoin(_get_gateway_url(), '/api/usuario/')

    @staticmethod
    def get_usuario(user_id):
        try:
            resp = requests.get(
                urljoin(UsuarioServiceClient._base_url(), f'usuarios/{user_id}/'),
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def get_usuarios_by_role(rol):
        try:
            resp = requests.get(
                UsuarioServiceClient._base_url() + 'usuarios/',
                params={'rol': rol},
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get('results', resp.json())
            return []
        except requests.RequestException:
            return []


class AcademicoServiceClient:

    @staticmethod
    def _base_url():
        return urljoin(_get_gateway_url(), '/api/academico/')

    @staticmethod
    def get_horario(horario_id):
        try:
            resp = requests.get(
                urljoin(AcademicoServiceClient._base_url(), f'horarios/{horario_id}/'),
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def get_materia(materia_id):
        try:
            resp = requests.get(
                urljoin(AcademicoServiceClient._base_url(), f'materias/{materia_id}/'),
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def get_horarios_by_materia(materia_id):
        try:
            resp = requests.get(
                AcademicoServiceClient._base_url() + 'horarios/',
                params={'materia': materia_id},
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get('results', resp.json())
            return []
        except requests.RequestException:
            return []

    @staticmethod
    def get_ciclo(ciclo_id):
        try:
            resp = requests.get(
                urljoin(AcademicoServiceClient._base_url(), f'ciclos/{ciclo_id}/'),
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def get_materias_by_docente(docente_id):
        try:
            resp = requests.get(
                AcademicoServiceClient._base_url() + 'materias/',
                params={'docente': docente_id},
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get('results', resp.json())
            return []
        except requests.RequestException:
            return []


class AsistenciaServiceClient:

    @staticmethod
    def _base_url():
        return urljoin(_get_gateway_url(), '/api/asistencia/')

    @staticmethod
    def get_asistencias_por_estudiante_materia(estudiante_id, horario_ids):
        try:
            resp = requests.get(
                AsistenciaServiceClient._base_url() + 'asistencias/',
                params={
                    'estudiante_id': estudiante_id,
                    'horario_id__in': ','.join(str(h) for h in horario_ids)
                },
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get('results', resp.json())
            return []
        except requests.RequestException:
            return []

    @staticmethod
    def get_asistencia_hoy(estudiante_id, horario_id):
        try:
            resp = requests.get(
                AsistenciaServiceClient._base_url() + 'asistencias/por_estudiante/',
                params={'estudiante_id': estudiante_id},
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                for a in resp.json():
                    if a.get('horario_id') == horario_id:
                        return a
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def tiene_registro_facial(estudiante_id):
        try:
            resp = requests.get(
                AsistenciaServiceClient._base_url() + 'registro-facial/',
                params={'estudiante_id': estudiante_id},
                headers=_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                results = resp.json().get('results', resp.json())
                return len(results) > 0
            return False
        except requests.RequestException:
            return False