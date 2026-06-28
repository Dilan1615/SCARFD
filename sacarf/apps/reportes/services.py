import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from django.db.models import Count, Q

from shared.models import Usuario, AsistenciaModel, HorarioModel, MateriaModel


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
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _get_materia_nombre(horario_id):
        try:
            horario = HorarioModel.objects.select_related('materia').get(id=horario_id)
            return horario.materia.nombre
        except HorarioModel.DoesNotExist:
            return 'N/A'

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

        return data
