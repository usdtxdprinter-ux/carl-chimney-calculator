"""
PDF Report Generator for CARL Chimney Analysis
Creates comprehensive sizing reports with enhanced visual design
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import io

class NumberedCanvas(canvas.Canvas):
    """Canvas with page numbers and footer"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor('#666666'))
        # Page number
        self.drawRightString(7.5*inch, 0.5*inch, f"Page {self._pageNumber} of {page_count}")
        # Footer text
        self.drawString(1*inch, 0.5*inch, "US Draft Co. | www.usdraft.com | 817-393-4029")

class PDFReportGenerator:
    """Generates comprehensive PDF sizing reports with enhanced design"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        # US Draft Co. brand colors
        self.primary_blue = colors.HexColor('#003366')
        self.accent_blue = colors.HexColor('#0066CC')
        self.light_blue = colors.HexColor('#E6F2FF')
        self.gray = colors.HexColor('#666666')
        self.light_gray = colors.HexColor('#F5F5F5')
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        # Main title
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header with background
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.white,
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold',
            backColor=colors.HexColor('#003366'),
            borderPadding=8
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#0066CC'),
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Data label
        self.styles.add(ParagraphStyle(
            name='DataLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold'
        ))
        
        # Data value
        self.styles.add(ParagraphStyle(
            name='DataValue',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica'
        ))
    
    def generate_report(self, project_data, calc_results, products, fan_curve_img=None):
        """Generate complete PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        story = []
        
        # Title page
        story.extend(self._add_title_page(project_data))
        
        # Project information
        story.extend(self._add_project_info(project_data))
        
        # System inputs
        story.extend(self._add_system_inputs(project_data))
        
        # System summary
        story.extend(self._add_system_summary(calc_results, products))
        
        # Appliance configuration
        story.extend(self._add_appliance_config(project_data.get('appliances', [])))
        
        # Draft calculations
        story.extend(self._add_draft_calculations(calc_results))
        
        # Fan curve (if available)
        if fan_curve_img:
            story.extend(self._add_fan_curve(fan_curve_img, products))
        
        # Product specifications
        story.extend(self._add_product_specs(products))
        
        # Build PDF with custom canvas for page numbers
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer
    
    def _add_title_page(self, project_data):
        """Add enhanced title page with US Draft logo"""
        story = []
        
        # Add logo at top
        import os
        logo_path = os.path.join(os.path.dirname(__file__), 'us_draft_logo.png')
        if os.path.exists(logo_path):
            # Calculate proportional height for 4-inch width
            from reportlab.lib.utils import ImageReader
            img = ImageReader(logo_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            logo_width = 4 * inch
            logo_height = logo_width * aspect
            
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = 'CENTER'
            story.append(Spacer(1, 0.5*inch))
            story.append(logo)
            story.append(Spacer(1, 0.5*inch))
        else:
            story.append(Spacer(1, 1*inch))
        
        # Main title with line
        title = Paragraph("CHIMNEY DRAFT SYSTEM", self.styles['MainTitle'])
        story.append(title)
        story.append(Spacer(1, 0.05*inch))
        
        # Horizontal line
        line_table = Table([['']], colWidths=[5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 3, self.primary_blue),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.05*inch))
        
        title2 = Paragraph("SIZING REPORT", self.styles['MainTitle'])
        story.append(title2)
        story.append(Spacer(1, 0.4*inch))
        
        # Project name in box
        project_name = project_data.get('project_name', 'Untitled Project')
        proj_table = Table([[project_name]], colWidths=[5*inch])
        proj_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.light_blue),
            ('BOX', (0, 0), (-1, -1), 2, self.accent_blue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.primary_blue),
        ]))
        story.append(proj_table)
        story.append(Spacer(1, 0.4*inch))
        
        # User info if provided
        user_name = project_data.get('user_name', '')
        user_email = project_data.get('user_email', '')
        if user_name or user_email:
            user_data = []
            if user_name:
                user_data.append(['Prepared for:', user_name])
            if user_email:
                user_data.append(['Contact:', user_email])
            
            user_table = Table(user_data, colWidths=[1.5*inch, 3.5*inch])
            user_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.gray),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(user_table)
            story.append(Spacer(1, 0.5*inch))
        
        # Company info
        story.append(Spacer(1, 0.3*inch))
        p = Paragraph("<b>US Draft Co.</b>", self.styles['Subtitle'])
        story.append(p)
        
        company_info = [
            "A Division of R.M. Manifold Group, Inc.",
            "100 S Sylvania Ave, Fort Worth, TX 76111",
            "Phone: 817-393-4029 | www.usdraft.com"
        ]
        
        for line in company_info:
            p = Paragraph(f'<font size="9" color="#666666">{line}</font>', self.styles['Normal'])
            p.alignment = TA_CENTER
            story.append(p)
        
        story.append(Spacer(1, 0.4*inch))
        
        # Date
        date_str = datetime.now().strftime('%B %d, %Y')
        p = Paragraph(f'<font size="10" color="#003366"><b>Report Date:</b> {date_str}</font>', self.styles['Normal'])
        p.alignment = TA_CENTER
        story.append(p)
        
        story.append(PageBreak())
        
        return story
    
    def _add_project_info(self, project_data):
        """Add project information section"""
        story = []
        
        # Section header
        header = Paragraph("  PROJECT INFORMATION", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Project details in styled table
        data = [
            ['Project Name:', project_data.get('project_name', 'N/A')],
            ['Location:', f"{project_data.get('city', '')}, {project_data.get('state', '')} {project_data.get('zip_code', '')}"],
        ]
        
        if project_data.get('user_name'):
            data.append(['Contact:', f"{project_data['user_name']}"])
        if project_data.get('user_email'):
            data.append(['Email:', project_data['user_email']])
        
        table = Table(data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (0, -1), 12),
            ('RIGHTPADDING', (0, 0), (0, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_system_inputs(self, project_data):
        """Add all system inputs"""
        story = []
        
        header = Paragraph("  SYSTEM INPUTS", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Environmental conditions
        story.append(Paragraph("Environmental Conditions", self.styles['SubHeader']))
        
        env_data = [
            ['Outside Air Temperature:', f"{project_data.get('temp_outside_f', 'N/A')}°F"],
            ['Barometric Pressure:', f"{project_data.get('barometric_pressure', 29.92):.2f} in Hg"],
            ['Elevation:', f"{project_data.get('elevation', 0):,.0f} ft"]
        ]
        
        env_table = Table(env_data, colWidths=[2.5*inch, 2*inch])
        env_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.light_blue),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(env_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Vent system configuration
        story.append(Paragraph("Vent System Configuration", self.styles['SubHeader']))
        
        vent_data = [
            ['Common Vent Diameter:', f"{project_data.get('manifold_diameter', 'N/A')} inches"],
            ['Common Vent Height:', f"{project_data.get('manifold_height', 'N/A')} ft"],
            ['Vent Material:', project_data.get('vent_type', 'Type B Double Wall')],
        ]
        
        if project_data.get('connector_length'):
            vent_data.append(['Connector Total Length:', f"{project_data.get('connector_length', 'N/A')} ft"])
        if project_data.get('connector_height'):
            vent_data.append(['Connector Vertical Rise:', f"{project_data.get('connector_height', 'N/A')} ft"])
        
        vent_table = Table(vent_data, colWidths=[2.5*inch, 2*inch])
        vent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.light_blue),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(vent_table)
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_system_summary(self, calc_results, products):
        """Add system summary with highlights"""
        story = []
        
        header = Paragraph("  SYSTEM SUMMARY", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Extract worst case data - handle nested structure
        worst_case_outer = calc_results.get('worst_case', {})
        if isinstance(worst_case_outer, dict) and 'worst_case' in worst_case_outer:
            worst = worst_case_outer['worst_case']
        else:
            worst = worst_case_outer
        
        all_op = calc_results.get('all_operating', {})
        
        # Key metrics in highlight boxes
        total_cfm = 0
        if all_op and isinstance(all_op, dict):
            total_cfm = all_op.get('combined', {}).get('total_cfm', 0)
        
        # If still zero, estimate from worst case appliance
        if total_cfm == 0 and worst:
            appliance = worst.get('appliance', {})
            mbh = appliance.get('mbh', 0)
            total_cfm = mbh * 0.8  # Rough estimate
        
        total_draft = worst.get('total_available_draft', 0)
        
        metrics = [
            ['Total Airflow', f"{int(round(total_cfm))} CFM"],
            ['Pressure Loss', f"{abs(total_draft):.4f} in w.c."],
            ['Worst Case', f"Appliance #{worst.get('appliance_id', 'N/A')}"]
        ]
        
        metric_table = Table(metrics, colWidths=[2.2*inch]*3)
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.accent_blue),
            ('BACKGROUND', (0, 1), (-1, 1), self.light_blue),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
            ('FONT', (0, 1), (-1, 1), 'Helvetica-Bold', 16),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), self.primary_blue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 1), (-1, 1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
            ('BOX', (0, 0), (-1, -1), 1, self.accent_blue),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.white),
        ]))
        
        story.append(metric_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Selected products
        story.append(Paragraph("Selected Products", self.styles['SubHeader']))
        
        product_data = []
        if products.get('draft_inducer'):
            di = products['draft_inducer']
            product_data.append(['Draft Inducer:', f"{di.get('series', '')} {di.get('model', '')}"])
        
        if products.get('controller'):
            ctrl = products['controller']
            product_data.append(['Controller:', ctrl.get('model', 'N/A')])
        
        if products.get('cds3'):
            num_units = len(products.get('appliances', []))
            product_data.append(['Draft Control:', f'CDS3 ({num_units} units)'])
        
        if products.get('odcs'):
            product_data.append(['Overdraft Control:', 'ODCS'])
        
        if products.get('supply_fan'):
            supply = products['supply_fan']
            product_data.append(['Supply Air:', f"{supply.get('series', '')} {supply.get('model', '')}"])
        
        if product_data:
            prod_table = Table(product_data, colWidths=[2*inch, 4.5*inch])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (0, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(prod_table)
        
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_appliance_config(self, appliances):
        """Add appliance configuration table"""
        story = []
        
        header = Paragraph("  APPLIANCE CONFIGURATION", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Build table data
        headers = ['#', 'Input\n(MBH)', 'Cat.', 'Temp\n(°F)', 'Fuel', 'Outlet\n(in)', 'Turndown']
        data = [headers]
        
        for i, app in enumerate(appliances, 1):
            turndown = app.get('turndown_ratio', 1)
            turndown_str = 'On/Off' if turndown == 1 else f"{turndown}:1"
            
            row = [
                str(i),
                f"{app.get('mbh', 0):,.0f}",
                app.get('category', 'I'),
                f"{app.get('temp_f', 0):.0f}",
                app.get('fuel_type', 'NG')[:2],  # Abbreviate
                f"{app.get('outlet_diameter', 0)}\"",
                turndown_str
            ]
            data.append(row)
        
        # Create table with enhanced styling
        col_widths = [0.4*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.9*inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1.5, self.primary_blue),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_gray])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_draft_calculations(self, calc_results):
        """Add draft calculation details"""
        story = []
        
        header = Paragraph("  DRAFT CALCULATIONS", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Extract worst case data - handle nested structure
        worst_case_outer = calc_results.get('worst_case', {})
        if isinstance(worst_case_outer, dict) and 'worst_case' in worst_case_outer:
            worst = worst_case_outer['worst_case']
        else:
            worst = worst_case_outer
        
        # Connector calculations
        story.append(Paragraph("Connector (Worst Case Appliance)", self.styles['SubHeader']))
        
        # Get connector data with safe defaults
        conn_result = worst.get('connector_result', {})
        if isinstance(conn_result, dict):
            conn = conn_result.get('connector', {})
        else:
            conn = {}
        
        conn_data = [
            ['Diameter:', f"{conn.get('diameter_inches', 0)}\""],
            ['Total Length:', f"{conn.get('total_length_ft', 0):.1f} ft"],
            ['Vertical Rise:', f"{conn.get('height_ft', 0):.1f} ft"],
            ['Velocity:', f"{conn.get('velocity_fpm', 0):.0f} ft/min"],
            ['Pressure Loss:', f"{abs(conn.get('pressure_loss_inwc', 0)):.4f} in w.c."],
            ['Available Draft:', f"{conn.get('available_draft_inwc', 0):.4f} in w.c."]
        ]
        
        conn_table = Table(conn_data, colWidths=[2*inch, 2*inch])
        conn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.light_blue),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(conn_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Manifold calculations - prefer all_operating, fallback to worst case manifold
        all_op = calc_results.get('all_operating', {})
        manifold = None
        
        if all_op and isinstance(all_op, dict) and 'common_vent' in all_op:
            manifold = all_op.get('common_vent', {})
            story.append(Paragraph("Common Vent (All Appliances Operating)", self.styles['SubHeader']))
        elif worst and isinstance(worst, dict):
            # Fallback to worst case manifold data
            manifold = worst.get('manifold_result', {}).get('manifold', {})
            story.append(Paragraph("Common Vent (Worst Case Analysis)", self.styles['SubHeader']))
        
        if manifold and isinstance(manifold, dict):
            man_data = [
                ['Diameter:', f"{manifold.get('diameter_inches', 0)}\""],
                ['Height:', f"{manifold.get('height_ft', 0):.1f} ft"],
                ['Total CFM:', f"{manifold.get('total_cfm', 0):.0f} CFM"],
                ['Velocity:', f"{manifold.get('velocity_fpm', 0):.0f} ft/min"],
                ['Pressure Loss:', f"{abs(manifold.get('pressure_loss_inwc', 0)):.4f} in w.c."],
                ['Available Draft:', f"{manifold.get('available_draft_inwc', 0):.4f} in w.c."]
            ]
            
            man_table = Table(man_data, colWidths=[2*inch, 2*inch])
            man_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_blue),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(man_table)
        
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_fan_curve(self, fan_curve_img, products):
        """Add fan performance curve"""
        story = []
        
        header = Paragraph("  FAN PERFORMANCE CURVE", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Add selected fan info
        if products.get('draft_inducer'):
            di = products['draft_inducer']
            p = Paragraph(
                f'<b>Selected Fan:</b> {di.get("series", "")} {di.get("model", "")}',
                self.styles['Normal']
            )
            story.append(p)
            story.append(Spacer(1, 0.1*inch))
        
        # Add image with border
        try:
            from io import BytesIO as BIO
            img_buffer = BIO(fan_curve_img)
            img = Image(img_buffer, width=6*inch, height=4.5*inch)
            
            # Wrap image in table for border
            img_table = Table([[img]], colWidths=[6*inch])
            img_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 2, self.accent_blue),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            
            story.append(img_table)
        except Exception as e:
            story.append(Paragraph(
                f"<i>Fan curve image could not be loaded</i>",
                self.styles['Normal']
            ))
        
        story.append(Spacer(1, 0.25*inch))
        
        return story
    
    def _add_product_specs(self, products):
        """Add product specifications"""
        story = []
        
        header = Paragraph("  PRODUCT SPECIFICATIONS", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 0.15*inch))
        
        # Draft Inducer
        if products.get('draft_inducer'):
            di = products['draft_inducer']
            story.append(Paragraph(f"{di.get('series_name', 'Draft Inducer')}", self.styles['SubHeader']))
            
            di_data = [
                ['Model:', di.get('model', 'N/A')],
                ['Series:', di.get('series', 'N/A')],
                ['Description:', di.get('description', 'N/A')]
            ]
            
            di_table = Table(di_data, colWidths=[1.5*inch, 5*inch])
            di_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(di_table)
            story.append(Spacer(1, 0.15*inch))
        
        # Controller
        if products.get('controller') and products.get('controller') is not None:
            ctrl = products['controller']
            story.append(Paragraph("Electronic Control System", self.styles['SubHeader']))
            
            ctrl_data = [
                ['Model:', ctrl.get('model', 'N/A')],
                ['Display:', ctrl.get('display', 'N/A')],
                ['Capacity:', f"Controls up to {ctrl.get('max_appliances', 1)} appliance(s)"]
            ]
            
            ctrl_table = Table(ctrl_data, colWidths=[1.5*inch, 5*inch])
            ctrl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(ctrl_table)
            story.append(Spacer(1, 0.15*inch))
        
        # CDS3 (Category IV only - self-contained, no controller)
        if products.get('cds3'):
            story.append(Paragraph("CDS3 Chimney Draft Stabilization System", self.styles['SubHeader']))
            
            num_appliances = len(products.get('appliances', []))
            
            cds3_data = [
                ['System:', 'CDS3 Self-Contained Draft Control'],
                ['Application:', 'Category IV condensing appliances only'],
                ['Quantity:', f"{num_appliances} unit(s) - one per appliance connector"],
                ['Control:', 'Built-in PID controller with auto-tuning (self-contained)'],
                ['Components:', 'Motorized damper, pressure transducer, integrated controller'],
                ['Draft Range:', '-0.10 to -0.01 in w.c. (adjustable)'],
                ['Note:', 'No separate controller needed - each CDS3 operates independently']
            ]
            
            cds3_table = Table(cds3_data, colWidths=[1.5*inch, 5*inch])
            cds3_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(cds3_table)
            story.append(Spacer(1, 0.15*inch))
        
        # ODCS (for non-Category IV, requires controller)
        if products.get('odcs'):
            story.append(Paragraph("ODCS Overdraft Control System", self.styles['SubHeader']))
            
            odcs_data = [
                ['System:', 'ODCS with motorized damper'],
                ['Application:', 'Natural draft systems requiring overdraft control'],
                ['Control:', 'Requires separate controller (V150/V250/V350)'],
                ['Components:', 'Motorized damper, pressure sensor'],
                ['Note:', 'Works with electronic control system for multi-appliance coordination']
            ]
            
            odcs_table = Table(odcs_data, colWidths=[1.5*inch, 5*inch])
            odcs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(odcs_table)
            story.append(Spacer(1, 0.15*inch))
        
        # Supply Air Fan (PRIO or TAF)
        if products.get('supply_fan'):
            supply = products['supply_fan']
            story.append(Paragraph("Supply Air Fan System", self.styles['SubHeader']))
            
            supply_data = [
                ['Model:', supply.get('model', 'N/A')],
                ['Series:', supply.get('series', 'N/A')],
                ['Description:', supply.get('description', 'Positive pressure supply air system')],
                ['Application:', 'Provides combustion air and building pressurization']
            ]
            
            supply_table = Table(supply_data, colWidths=[1.5*inch, 5*inch])
            supply_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_gray),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.primary_blue),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            story.append(supply_table)
            story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Footer disclaimer
        disclaimer = Paragraph(
            '<i><font size="8" color="#666666">This report is prepared for preliminary design purposes. '
            'Calculations are based on the ASHRAE Chimney Design Equation and applicable industry standards. '
            'Final installation shall comply with all applicable codes including UL 705, UL 378, '
            'NFPA 54, NFPA 211, IMC, and IFGC, and manufacturer\'s installation instructions.</font></i>',
            self.styles['Normal']
        )
        story.append(disclaimer)
        
        return story
