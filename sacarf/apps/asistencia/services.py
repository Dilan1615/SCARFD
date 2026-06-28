import boto3
import base64
import os
import re
from django.conf import settings
from PIL import Image
import io


# Clase de servicio para interactuar con AWS Rekognition y S3
class AwsRekognitionService:
    def __init__(self):
        self.client = boto3.client(
            'rekognition',
            region_name=os.getenv('AWS_REGION', 'us-east-1'), # Se obtiene la región de AWS desde las variables de entorno, con un valor por defecto de 'us-east-1'
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), # Se obtiene la clave de acceso de AWS desde las variables de entorno
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY') # Se obtiene la clave secreta de AWS desde las variables de entorno
        )
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1'), # Se obtiene la región de AWS desde las variables de entorno, con un valor por defecto de 'us-east-1'
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), # Se obtiene la clave de acceso de AWS desde las variables de entorno
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY') # Se obtiene la clave secreta de AWS desde las variables de entorno
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'sacarf-images') # Se obtiene el nombre del bucket de S3 desde las variables de entorno, con un valor por defecto de 'sacarf-images'
        self.collection_id = os.getenv('REKOGNITION_COLLECTION_ID', 'sacarf_faces') # Se define el ID de la colección de rostros en Rekognition, que se utilizará para almacenar y buscar rostros

    def decode_base64_image(self, base64_str):
        """Decodifica una cadena base64 a bytes"""
        if not base64_str:
            raise ValueError("La cadena base64 no puede estar vacía")
        try:
            if ',' in base64_str:
                base64_str = re.sub(r'^data:image/\w+;base64,', '', base64_str)
            return base64.b64decode(base64_str)
        except Exception:
            raise ValueError("Formato de imagen inválido")

    def crear_collection(self):
        """Crea la colección de faces en AWS Rekognition si no existe"""
        try:
            self.client.create_collection(CollectionId=self.collection_id)
            return True
        except self.client.exceptions.ResourceAlreadyExistsException:
            return True
        except Exception as e:
            print(f"Error creando collection: {e}")
            return False

    def indexar_rostro(self, image_bytes, external_id):
        """Indexa un rostro en la colección"""
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
                    'face_id': face_records[0]['Face']['FaceId'],
                    'confidence': face_records[0]['Face']['Confidence']
                }
            return None
        except Exception as e:
            print(f"Error indexando rostro: {e}")
            return None

    def buscar_rostro(self, image_bytes, threshold=85.0):
        """Busca un rostro en la colección"""
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
                    'face_id': match['Face']['FaceId'],
                    'confidence': match['Similarity'],
                    'external_id': match['Face']['ExternalImageId']
                }
            return None
        except Exception as e:
            print(f"Error buscando rostro: {e}")
            return None

    def subir_imagen_s3(self, image_bytes, filename):
        """Sube una imagen a S3 y retorna la URL"""
        try:
            self.s3_client.upload_fileobj(
                io.BytesIO(image_bytes),
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
        except Exception as e:
            print(f"Error subiendo imagen a S3: {e}")
            return None