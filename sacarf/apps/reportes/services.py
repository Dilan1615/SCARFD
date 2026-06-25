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
from django.utils import timezone

from apps.asistencia.models import Asistencia, EstadoAsistencia
from apps.academico.models import Materia, Ciclo, Horario
from apps.usuario.models import Usuario

class ReporteService:
    
    @staticmethod
    def generar_reporte_pdf(data, titulo, subtitulo=None):
        """Genera un reporte en PDF con los datos proporcionados"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,  # Centrado
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
        
        # Fecha de generación
        fecha_style = ParagraphStyle(
            'FechaStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,  # Derecha
            spaceAfter=12
        )
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))
        
        elements.append(Spacer(1, 12))
        
        # Tabla de datos
        if data:
            # Preparar datos para la tabla
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
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generar_reporte_excel(data, titulo):
        """Genera un reporte en Excel con los datos proporcionados"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # Título
        ws.merge_cells('A1:F1')
        ws['A1'] = titulo
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = center_alignment
        
        # Datos
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
        
        # Ajustar anchos
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
    def obtener_datos_asistencia(tipo, params):
        """Obtiene los datos de asistencia según el tipo de reporte"""
        data = []
        
        if tipo == 'POR_ESTUDIANTE':
            estudiante_id = params.get('estudiante_id')
            if estudiante_id:
                estudiante = Usuario.objects.get(id=estudiante_id, rol='ESTUDIANTE')
                asistencias = Asistencia.objects.filter(estudiante=estudiante)
                
                # Filtrar por fechas
                if params.get('fecha_desde'):
                    asistencias = asistencias.filter(fecha__gte=params['fecha_desde'])
                if params.get('fecha_hasta'):
                    asistencias = asistencias.filter(fecha__lte=params['fecha_hasta'])
                
                for asist in asistencias:
                    data.append({
                        'Fecha': asist.fecha.strftime('%d/%m/%Y'),
                        'Hora': asist.hora_registro.strftime('%H:%M'),
                        'Estado': asist.get_estado_display(),
                        'Materia': asist.horario.materia.nombre,
                        'Confianza': f"{asist.confianza:.1f}%"
                    })
        
        elif tipo == 'POR_MATERIA':
            materia_id = params.get('materia_id')
            if materia_id:
                materia = Materia.objects.get(id=materia_id)
                horarios = Horario.objects.filter(materia=materia)
                asistencias = Asistencia.objects.filter(horario__in=horarios)
                
                if params.get('fecha_desde'):
                    asistencias = asistencias.filter(fecha__gte=params['fecha_desde'])
                if params.get('fecha_hasta'):
                    asistencias = asistencias.filter(fecha__lte=params['fecha_hasta'])
                
                # Estadísticas por estudiante
                estudiantes = Usuario.objects.filter(
                    rol='ESTUDIANTE',
                    asistencias__in=asistencias
                ).distinct()
                
                for estudiante in estudiantes:
                    asistencias_est = asistencias.filter(estudiante=estudiante)
                    total = asistencias_est.count()
                    presentes = asistencias_est.filter(estado=EstadoAsistencia.PRESENTE).count()
                    tardes = asistencias_est.filter(estado=EstadoAsistencia.TARDE).count()
                    ausentes = asistencias_est.filter(estado=EstadoAsistencia.AUSENTE).count()
                    
                    data.append({
                        'Estudiante': f"{estudiante.first_name} {estudiante.last_name}",
                        'Presentes': presentes,
                        'Tardes': tardes,
                        'Ausentes': ausentes,
                        'Total': total,
                        'Asistencia': f"{(presentes/total*100):.1f}%" if total > 0 else "0%"
                    })
        
        return data