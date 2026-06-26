from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch
from datetime import datetime

from .models import Carrera, Ciclo, Materia, Horario, Matricula
from .serializers import (
    CarreraSerializer, CicloSerializer, MateriaSerializer,
    HorarioSerializer, MatriculaSerializer, MisMateriasSerializer
)
from apps.usuario.permissions import IsAdminForMutation
from apps.asistencia.models import Asistencia, RegistroFacial


class CarreraViewSet(viewsets.ModelViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    permission_classes = [IsAdminForMutation]
    search_fields = ['nombre', 'codigo']
    filterset_fields = ['modalidad']


class CicloViewSet(viewsets.ModelViewSet):
    queryset = Ciclo.objects.all()
    serializer_class = CicloSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['carrera', 'estado']


class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [IsAdminForMutation]
    search_fields = ['nombre', 'codigo']
    filterset_fields = ['carrera', 'ciclo', 'docente']


class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['materia', 'dia_semana']


class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['estudiante', 'carrera', 'ciclo', 'estado']

    def get_queryset(self):
        return Matricula.objects.select_related('estudiante', 'carrera', 'ciclo')

    @action(detail=False, methods=['get'])
    def mis_materias(self, request):
        """Devuelve las materias con horarios de hoy del estudiante autenticado"""
        if request.user.rol != 'ESTUDIANTE':
            return Response({'error': 'Solo estudiantes pueden ver sus materias'},
                          status=status.HTTP_403_FORBIDDEN)

        matriculas = Matricula.objects.filter(
            estudiante=request.user,
            estado='ACTIVA'
        ).select_related('carrera', 'ciclo')

        if not matriculas.exists():
            return Response({'error': 'No tienes una matrícula activa'},
                          status=status.HTTP_404_NOT_FOUND)

        dias_map = {
            0: 'LUNES', 1: 'MARTES', 2: 'MIERCOLES',
            3: 'JUEVES', 4: 'VIERNES', 5: 'SABADO', 6: 'DOMINGO'
        }
        dia_hoy = dias_map.get(datetime.now().weekday(), '')
        fecha_hoy = datetime.now().date()

        resultado = []
        for mat in matriculas:
            materias = mat.ciclo.materias.select_related('docente').prefetch_related(
                Prefetch('horarios', queryset=Horario.objects.filter(dia_semana=dia_hoy))
            )

            materias_data = []
            for materia in materias:
                horarios_hoy = materia.horarios.all()
                if not horarios_hoy:
                    continue

                horarios_data = []
                for horario in horarios_hoy:
                    ya_registro = Asistencia.objects.filter(
                        estudiante=request.user,
                        horario=horario,
                        fecha=fecha_hoy
                    ).first()

                    horarios_data.append({
                        'id': horario.id,
                        'dia_semana': horario.dia_semana,
                        'dia_display': horario.get_dia_semana_display(),
                        'hora_inicio': horario.hora_inicio,
                        'hora_fin': horario.hora_fin,
                        'minutos_tolerancia': horario.minutos_tolerancia,
                        'aula': horario.aula,
                        'ya_registro': ya_registro is not None,
                        'asistencia_id': ya_registro.id if ya_registro else None,
                        'estado_asistencia': ya_registro.estado if ya_registro else None,
                    })

                materias_data.append({
                    'id': materia.id,
                    'codigo': materia.codigo,
                    'nombre': materia.nombre,
                    'docente_nombre': f"{materia.docente.first_name} {materia.docente.last_name}" if materia.docente else None,
                    'horarios_hoy': horarios_data,
                })

            resultado.append({
                'matricula_id': mat.id,
                'carrera': mat.carrera.nombre,
                'ciclo': f"Ciclo {mat.ciclo.num}",
                'materias': materias_data,
            })

        tiene_rostro = RegistroFacial.objects.filter(
            estudiante=request.user, estado='ACTIVO'
        ).exists()

        serializer = MisMateriasSerializer(resultado, many=True)
        return Response({
            'tiene_registro_facial': tiene_rostro,
            'matriculas': serializer.data
        })
