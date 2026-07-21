import os
import io
from datetime import datetime
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from django.db.models import Count, Q

from shared.models import Usuario, AsistenciaModel, HorarioModel, MateriaModel, CicloModel

from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell

class ReporteService:

    @staticmethod
    def generar_reporte_pdf(data, titulo, subtitulo=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        elements.append(Paragraph(titulo, titulo_style))

        if subtitulo:
            subtitulo_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                alignment=1,
                spaceAfter=12
            )
            elements.append(Paragraph(subtitulo, subtitulo_style))

        elements.append(Spacer(1, 12))

        fecha_style = ParagraphStyle(
            'FechaStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            spaceAfter=12
        )
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))

        elements.append(Spacer(1, 12))

        if data:
            headers = list(data[0].keys()) if data else []
            table_data = [headers]
            for row in data:
                table_data.append([str(row.get(h, '')) for h in headers])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_reporte_excel(data, titulo):
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells('A1:F1')
        ws['A1'] = titulo
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = center_alignment

        if data:
            headers = list(data[0].keys())
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=2, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment

            for row_idx, row_data in enumerate(data, 3):
                for col_idx, header in enumerate(headers, 1):
                    ws.cell(row=row_idx, column=col_idx, value=str(row_data.get(header, '')))

            for col in ws.columns:
                max_length = 0
                column_index = None
                for cell in col:
                    if isinstance(cell, MergedCell):
                        continue
                    if column_index is None:
                        column_index = cell.column
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                if column_index is not None:
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[get_column_letter(column_index)].width = adjusted_width

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def guardar_archivo(buffer, nombre, extension):
        carpeta = os.path.join(settings.MEDIA_ROOT, 'reportes')
        os.makedirs(carpeta, exist_ok=True)
        filepath = os.path.join(carpeta, f"{nombre}.{extension}")
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        return f"reportes/{nombre}.{extension}"

    @staticmethod
    def _get_materia_nombre(horario_id):
        try:
            horario = HorarioModel.objects.select_related('materia').get(id=horario_id)
            return horario.materia.nombre
        except HorarioModel.DoesNotExist:
            return 'N/A'

    @staticmethod
    def _construir_reporte_grupal(horarios_qs, params):
        """Genera filas Estudiante/Materia/Presentes/Tardes/Ausentes/Total/Asistencia
        para un conjunto de horarios. Usado por POR_CICLO y GENERAL."""
        horarios = {h.id: h for h in horarios_qs.select_related('materia')}
        horario_ids = list(horarios.keys())
        if not horario_ids:
            return []

        asistencias = AsistenciaModel.objects.filter(horario_id__in=horario_ids)
        if params.get('fecha_desde'):
            asistencias = asistencias.filter(fecha__gte=params['fecha_desde'])
        if params.get('fecha_hasta'):
            asistencias = asistencias.filter(fecha__lte=params['fecha_hasta'])

        grupos = {}
        for a in asistencias:
            horario = horarios.get(a.horario_id)
            materia_id = horario.materia_id if horario else None
            materia_nombre = horario.materia.nombre if horario else 'N/A'
            key = (a.estudiante_id, materia_id)
            if key not in grupos:
                grupos[key] = {'materia_nombre': materia_nombre, 'estados': []}
            grupos[key]['estados'].append(a.estado)

        data = []
        for (estudiante_id, materia_id), info in grupos.items():
            try:
                estudiante = Usuario.objects.get(id=estudiante_id, rol='ESTUDIANTE')
            except Usuario.DoesNotExist:
                continue

            estados = info['estados']
            total = len(estados)
            presentes = estados.count('PRESENTE')
            tardes = estados.count('TARDE')
            ausentes = estados.count('AUSENTE')

            data.append({
                'Estudiante': f"{estudiante.first_name} {estudiante.last_name}",
                'Materia': info['materia_nombre'],
                'Presentes': presentes,
                'Tardes': tardes,
                'Ausentes': ausentes,
                'Total': total,
                'Asistencia': f"{(presentes/total*100):.1f}%" if total > 0 else "0%"
            })
        return data
    
    @staticmethod
    def obtener_datos_asistencia(tipo, params):
        data = []

        if tipo == 'POR_ESTUDIANTE':
            estudiante_id = params.get('estudiante_id')
            if estudiante_id:
                try:
                    estudiante = Usuario.objects.get(id=estudiante_id, rol='ESTUDIANTE')
                except Usuario.DoesNotExist:
                    return []

                asistencias = AsistenciaModel.objects.filter(estudiante_id=estudiante_id)

                if params.get('fecha_desde'):
                    asistencias = asistencias.filter(fecha__gte=params['fecha_desde'])
                if params.get('fecha_hasta'):
                    asistencias = asistencias.filter(fecha__lte=params['fecha_hasta'])

                _cache_materias = {}
                for asist in asistencias:
                    if asist.horario_id not in _cache_materias:
                        _cache_materias[asist.horario_id] = ReporteService._get_materia_nombre(asist.horario_id)

                    estados_display = {
                        'PRESENTE': 'Presente',
                        'TARDE': 'Tarde',
                        'AUSENTE': 'Ausente',
                        'JUSTIFICADO': 'Justificado',
                    }

                    data.append({
                        'Fecha': asist.fecha.strftime('%d/%m/%Y'),
                        'Hora': asist.hora_registro.strftime('%H:%M'),
                        'Estado': estados_display.get(asist.estado, asist.estado),
                        'Materia': _cache_materias.get(asist.horario_id, 'N/A'),
                        'Confianza': f"{asist.confianza:.1f}%"
                    })

        elif tipo == 'POR_MATERIA':
            materia_id = params.get('materia_id')
            if materia_id:
                try:
                    materia = MateriaModel.objects.get(id=materia_id)
                except MateriaModel.DoesNotExist:
                    return []

                horarios = HorarioModel.objects.filter(materia=materia)
                horario_ids = [h.id for h in horarios]
                asistencias = AsistenciaModel.objects.filter(horario_id__in=horario_ids)

                if params.get('fecha_desde'):
                    asistencias = asistencias.filter(fecha__gte=params['fecha_desde'])
                if params.get('fecha_hasta'):
                    asistencias = asistencias.filter(fecha__lte=params['fecha_hasta'])

                estudiante_ids = asistencias.values_list('estudiante_id', flat=True).distinct()

                for eid in estudiante_ids:
                    try:
                        estudiante = Usuario.objects.get(id=eid, rol='ESTUDIANTE')
                    except Usuario.DoesNotExist:
                        continue

                    asistencias_est = asistencias.filter(estudiante_id=eid)
                    total = asistencias_est.count()
                    presentes = asistencias_est.filter(estado='PRESENTE').count()
                    tardes = asistencias_est.filter(estado='TARDE').count()
                    ausentes = asistencias_est.filter(estado='AUSENTE').count()

                    data.append({
                        'Estudiante': f"{estudiante.first_name} {estudiante.last_name}",
                        'Presentes': presentes,
                        'Tardes': tardes,
                        'Ausentes': ausentes,
                        'Total': total,
                        'Asistencia': f"{(presentes/total*100):.1f}%" if total > 0 else "0%"
                    })
            elif tipo == 'POR_CICLO':
                ciclo_id = params.get('ciclo_id')
            if ciclo_id:
                materias = MateriaModel.objects.filter(ciclo_id=ciclo_id)
                horarios_qs = HorarioModel.objects.filter(materia__in=materias)
                data = ReporteService._construir_reporte_grupal(horarios_qs, params)

            elif tipo == 'GENERAL':
                horarios_qs = HorarioModel.objects.all()
                data = ReporteService._construir_reporte_grupal(horarios_qs, params)

        return data