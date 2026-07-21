import boto3
import base64
import os
import re
import logging
from botocore.exceptions import ClientError
from PIL import Image
import io

logger = logging.getLogger(__name__)


class AwsRekognitionService:
    def __init__(self):
        aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')

        if not aws_key or not aws_secret or aws_key == 'YOUR_AWS_ACCESS_KEY_ID':
            logger.error("AWS_ACCESS_KEY_ID o AWS_SECRET_ACCESS_KEY no están configurados correctamente en variables de entorno.")

        self.client = boto3.client(
            'rekognition',
            region_name=aws_region,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret
        )
        self.s3_client = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'sacarf-images')
        self.collection_id = os.getenv('REKOGNITION_COLLECTION_ID', 'sacarf_faces')

    def decode_base64_image(self, base64_str):
        if not base64_str:
            raise ValueError("La cadena base64 no puede estar vacía")
        try:
            if ',' in base64_str:
                base64_str = re.sub(r'^data:image/\w+;base64,', '', base64_str)
            return base64.b64decode(base64_str)
        except Exception:
            raise ValueError("Formato de imagen inválido")

    def crear_collection(self):
        try:
            self.client.create_collection(CollectionId=self.collection_id)
            return True
        except self.client.exceptions.ResourceAlreadyExistsException:
            return True
        except ClientError as e:
            logger.error("Error creando collection: %s", e)
            return False

    def _handle_aws_error(self, e, accion):
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error'].get('Message', str(e))

        if error_code == 'UnrecognizedClientException':
            return {'success': False, 'error': 'Credenciales AWS inválidas. Verifica AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY.'}
        if error_code == 'AccessDeniedException':
            return {'success': False, 'error': 'Las credenciales AWS no tienen permisos para Rekognition.'}
        if error_code == 'InvalidParameterException':
            return {'success': False, 'error': 'La imagen no es válida. Asegúrate de que se vea un rostro claro.'}
        if error_code == 'ResourceNotFoundException':
            if accion == 'buscar':
                return {'success': False, 'error': f'La colección "{self.collection_id}" no existe. Registra tu rostro primero.'}
            return {'success': False, 'error': f'La colección "{self.collection_id}" no existe en Rekognition.'}
        if error_code == 'ThrottlingException':
            return {'success': False, 'error': 'Demasiadas solicitudes a Rekognition. Intenta de nuevo en unos segundos.'}
        if error_code == 'ProvisionedThroughputExceededException':
            return {'success': False, 'error': 'Límite de solicitudes alcanzado. Intenta más tarde.'}
        if error_code == 'InternalServerError':
            return {'success': False, 'error': 'Error interno de AWS Rekognition. Intenta de nuevo más tarde.'}

        logger.error("Error AWS Rekognition (%s): [%s] %s", accion, error_code, error_msg)
        return {'success': False, 'error': f'Error de AWS Rekognition ({error_code}): {error_msg}'}

    def indexar_rostro(self, image_bytes, external_id):
        try:
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_id,
                MaxFaces=1,
                QualityFilter='AUTO',
                DetectionAttributes=['DEFAULT']
            )
            face_records = response.get('FaceRecords', [])
            if face_records:
                return {
                    'success': True,
                    'face_id': face_records[0]['Face']['FaceId'],
                    'confidence': face_records[0]['Face']['Confidence']
                }
            return {'success': False, 'error': 'No se detectó ningún rostro en la imagen. Intenta con otra foto con mejor iluminación.'}
        except ClientError as e:
            return self._handle_aws_error(e, 'indexar')
        except Exception as e:
            logger.exception("Error inesperado indexando rostro")
            return {'success': False, 'error': f'Error al indexar rostro: {str(e)}'}

    def buscar_rostro(self, image_bytes, threshold=85.0):
        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=1,
                FaceMatchThreshold=threshold
            )
            face_matches = response.get('FaceMatches', [])
            if face_matches:
                match = face_matches[0]
                return {
                    'success': True,
                    'face_id': match['Face']['FaceId'],
                    'confidence': match['Similarity'],
                    'external_id': match['Face']['ExternalImageId']
                }
            return {'success': False, 'error': 'No se encontró coincidencia con ningún rostro registrado. Asegúrate de que tu rostro esté bien iluminado y visible.'}
        except ClientError as e:
            return self._handle_aws_error(e, 'buscar')
        except Exception as e:
            logger.exception("Error inesperado buscando rostro")
            return {'success': False, 'error': f'Error al buscar rostro: {str(e)}'}

    def subir_imagen_s3(self, image_bytes, filename):
        try:
            self.s3_client.upload_fileobj(
                io.BytesIO(image_bytes),
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
        except ClientError as e:
            logger.error("Error subiendo imagen a S3: %s", e)
            return None
        except Exception as e:
            logger.error("Error subiendo imagen a S3: %s", e)
            return None