"""
CSI Specification Generator for Section 23 51 10
Generates DOCX specifications for US Draft Co. systems
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime

class CSISpecificationGenerator:
    """
    Generates CSI MasterFormat Section 23 51 10 specifications
    """
    
    def __init__(self):
        """Initialize specification generator"""
        self.section_number = "23 51 10"
        self.section_title = "BREECHINGS, CHIMNEYS, AND STACKS"
        
    def generate_specification(self, project_info, products_selected, system_data):
        """
        Generate complete CSI specification document
        
        Args:
            project_info: Dictionary with project details
            products_selected: Dictionary of selected products
            system_data: Dictionary with system calculations
            
        Returns:
            docx Document object
        """
        doc = Document()
        
        # Set up document
        self._setup_document_styles(doc)
        
        # Add header
        self._add_header(doc, project_info)
        
        # PART 1: GENERAL
        self._add_part_1_general(doc, project_info)
        
        # PART 2: PRODUCTS
        self._add_part_2_products(doc, products_selected, system_data)
        
        # PART 3: EXECUTION
        self._add_part_3_execution(doc, products_selected)
        
        return doc
    
    def _setup_document_styles(self, doc):
        """Set up document styles"""
        # Configure normal style
        style = doc.styles['Normal']
        style.font.name = 'Arial'
        style.font.size = Pt(11)
        
    def _add_header(self, doc, project_info):
        """Add specification header"""
        # Section number and title
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"SECTION {self.section_number}")
        run.bold = True
        run.font.size = Pt(14)
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(self.section_title)
        run.bold = True
        run.font.size = Pt(14)
        
        doc.add_paragraph()  # Blank line
        
        # Project info
        p = doc.add_paragraph(f"Project: {project_info.get('project_name', 'Unnamed Project')}")
        p = doc.add_paragraph(f"Location: {project_info.get('location', 'Not specified')}")
        p = doc.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        doc.add_paragraph()  # Blank line
    
    def _add_part_1_general(self, doc, project_info):
        """Add PART 1 - GENERAL"""
        # Part heading
        p = doc.add_paragraph("PART 1 - GENERAL")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        
        doc.add_paragraph()
        
        # 1.1 SUMMARY
        self._add_section_heading(doc, "1.1", "SUMMARY")
        
        doc.add_paragraph("A. Section Includes:")
        items = [
            "Mechanical draft systems for fuel-fired appliances",
            "Vent control systems (VCS)",
            "Overdraft control systems (ODCS)",
            "Pressure air systems (PAS) for combustion air",
            "Electronic controls and monitoring equipment",
            "System accessories and components"
        ]
        for item in items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.2 REFERENCES
        self._add_section_heading(doc, "1.2", "REFERENCES")
        
        doc.add_paragraph("A. Applicable Standards:")
        standards = [
            "NFPA 54 - National Fuel Gas Code",
            "NFPA 211 - Standard for Chimneys, Fireplaces, Vents, and Solid Fuel-Burning Appliances",
            "UL 441 - Standard for Gas Vents",
            "UL 1738 - Standard for Venting Systems for Gas-Burning Appliances, Categories II, III, and IV",
            "ASHRAE 90.1 - Energy Standard for Buildings",
            "IMC - International Mechanical Code",
            "IBC - International Building Code"
        ]
        for std in standards:
            p = doc.add_paragraph(std, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.3 SUBMITTALS
        self._add_section_heading(doc, "1.3", "SUBMITTALS")
        
        doc.add_paragraph("A. Product Data:")
        submittals = [
            "Manufacturer's technical data sheets for all components",
            "Fan performance curves showing operating points",
            "Control sequences and wiring diagrams",
            "Installation, operation, and maintenance manuals"
        ]
        for item in submittals:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Shop Drawings:")
        shop_items = [
            "System layout showing all components",
            "Vent sizing calculations",
            "Electrical single-line diagrams"
        ]
        for item in shop_items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.4 QUALITY ASSURANCE
        self._add_section_heading(doc, "1.4", "QUALITY ASSURANCE")
        
        doc.add_paragraph("A. Manufacturer Qualifications:")
        p = doc.add_paragraph("Provide products from US Draft Co., a division of R.M. Manifold Group, Inc., or approved equal with minimum 20 years experience in mechanical draft systems.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Installer Qualifications:")
        p = doc.add_paragraph("Installer shall be trained and certified by equipment manufacturer.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.5 WARRANTY
        self._add_section_heading(doc, "1.5", "WARRANTY")
        
        doc.add_paragraph("A. Provide manufacturer's standard warranty:")
        p = doc.add_paragraph("Minimum 2-year warranty on parts and workmanship from date of substantial completion.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_page_break()
    
    def _add_part_2_products(self, doc, products, system_data):
        """Add PART 2 - PRODUCTS"""
        # Part heading
        p = doc.add_paragraph("PART 2 - PRODUCTS")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        
        doc.add_paragraph()
        
        # 2.1 MANUFACTURERS
        self._add_section_heading(doc, "2.1", "MANUFACTURERS")
        
        doc.add_paragraph("A. Basis of Design:")
        p = doc.add_paragraph("US Draft Co., a division of R.M. Manifold Group, Inc.")
        p.paragraph_format.left_indent = Inches(0.5)
        p = doc.add_paragraph("100 S Sylvania Ave")
        p.paragraph_format.left_indent = Inches(0.75)
        p = doc.add_paragraph("Fort Worth, TX 76111")
        p.paragraph_format.left_indent = Inches(0.75)
        p = doc.add_paragraph("Phone: 817-393-4029")
        p.paragraph_format.left_indent = Inches(0.75)
        p = doc.add_paragraph("Website: www.usdraft.com")
        p.paragraph_format.left_indent = Inches(0.75)
        
        doc.add_paragraph()
        
        # 2.2 DRAFT INDUCER (if applicable)
        if products.get('draft_inducer'):
            self._add_section_heading(doc, "2.2", "DRAFT INDUCER")
            self._add_draft_inducer_spec(doc, products['draft_inducer'], system_data)
        
        # 2.3 CONTROLLER
        if products.get('controller'):
            section_num = "2.3" if products.get('draft_inducer') else "2.2"
            self._add_section_heading(doc, section_num, "ELECTRONIC CONTROLLER")
            self._add_controller_spec(doc, products['controller'])
        
        # 2.4 OVERDRAFT CONTROL (if applicable)
        if products.get('odcs'):
            section_num = "2.4"
            self._add_section_heading(doc, section_num, "OVERDRAFT CONTROL SYSTEM")
            self._add_odcs_spec(doc, products['odcs'])
        
        # 2.5 SUPPLY AIR FAN (if applicable)
        if products.get('supply_fan'):
            section_num = "2.5"
            self._add_section_heading(doc, section_num, "COMBUSTION AIR SUPPLY FAN")
            self._add_supply_fan_spec(doc, products['supply_fan'])
        
        doc.add_page_break()
    
    def _add_part_3_execution(self, doc, products):
        """Add PART 3 - EXECUTION"""
        # Part heading
        p = doc.add_paragraph("PART 3 - EXECUTION")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        
        doc.add_paragraph()
        
        # 3.1 EXAMINATION
        self._add_section_heading(doc, "3.1", "EXAMINATION")
        
        doc.add_paragraph("A. Verify existing conditions before beginning installation:")
        items = [
            "Vent piping is complete and properly sized",
            "Electrical service is available at equipment locations",
            "Mounting surfaces are adequate to support equipment",
            "Access for installation and service is adequate"
        ]
        for item in items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.2 INSTALLATION
        self._add_section_heading(doc, "3.2", "INSTALLATION")
        
        doc.add_paragraph("A. General:")
        p = doc.add_paragraph("Install equipment in accordance with manufacturer's written instructions and approved shop drawings.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Draft Inducer Installation:")
        if products.get('draft_inducer'):
            series = products['draft_inducer'].get('series', '')
            if series == 'CBX':
                p = doc.add_paragraph("Mount termination fan at top of vent stack. Ensure weatherproof installation with proper flashing.")
            elif series == 'TRV':
                p = doc.add_paragraph("Install true inline fan in vent pipe run. Provide adequate support for fan weight.")
            elif series == 'T9F':
                p = doc.add_paragraph("Install 90-degree inline fan at change of direction. Support fan independently of vent piping.")
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Controller Installation:")
        p = doc.add_paragraph("Mount controller in mechanical room at eye level for easy viewing. Provide minimum 3 feet clearance for service access.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Wiring:")
        wiring = [
            "Provide dedicated 120V/1Ph/60Hz electrical service to controller",
            "Install conduit and wiring in accordance with NEC",
            "Provide low-voltage wiring from controller to fans and sensors",
            "Label all wiring and connections"
        ]
        for item in wiring:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.3 STARTUP AND COMMISSIONING
        self._add_section_heading(doc, "3.3", "STARTUP AND COMMISSIONING")
        
        doc.add_paragraph("A. Factory Startup Service:")
        p = doc.add_paragraph("Provide manufacturer's authorized technician for initial startup and commissioning of system.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Testing:")
        tests = [
            "Verify all safeties and interlocks function properly",
            "Measure and record draft at appliance outlet under all firing conditions",
            "Verify combustion air delivery (if PAS installed)",
            "Confirm automatic modulation under varying loads",
            "Test emergency shutdown procedures"
        ]
        for item in tests:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.4 TRAINING
        self._add_section_heading(doc, "3.4", "TRAINING")
        
        p = doc.add_paragraph("Provide 4-hour training session for owner's maintenance personnel covering system operation, routine maintenance, and troubleshooting.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        p = doc.add_paragraph("END OF SECTION")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
    
    def _add_section_heading(self, doc, number, title):
        """Add a section heading"""
        p = doc.add_paragraph(f"{number} {title}")
        p.runs[0].bold = True
        p.runs[0].underline = True
        doc.add_paragraph()
    
    def _add_draft_inducer_spec(self, doc, inducer_info, system_data):
        """Add draft inducer specification details"""
        doc.add_paragraph("A. General:")
        p = doc.add_paragraph(f"Provide {inducer_info['series_name']} draft inducer sized for {system_data['total_cfm']:.0f} CFM at {system_data['static_pressure']:.3f} inches w.c.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Model:")
        p = doc.add_paragraph(f"{inducer_info['model']} or approved equal")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Construction:")
        materials = []
        if system_data.get('is_condensing'):
            materials.append("316L stainless steel construction for condensing applications")
        else:
            materials.append("Aluminum or 316L stainless steel construction")
        materials.extend([
            "Cast aluminum motor housing",
            "Permanently lubricated ball bearings",
            "Dynamically balanced impeller",
            "Weatherproof construction (for outdoor installations)"
        ])
        for item in materials:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Performance:")
        p = doc.add_paragraph(f"Fan shall deliver {system_data['total_cfm']:.0f} CFM at {system_data['static_pressure']:.3f} inches w.c. static pressure as shown on manufacturer's certified performance curve.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_controller_spec(self, doc, controller_info):
        """Add controller specification details"""
        doc.add_paragraph("A. Model:")
        p = doc.add_paragraph(f"{controller_info['model']}")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Features:")
        features = [
            f"{controller_info['display']} display",
            "EC-Flow™ technology for precise pressure control",
            "Modulating speed control (0-100%)",
            "Built-in diagnostics and alarms",
            "Automatic fault detection",
            "Data logging capability",
            "BACnet/Modbus communication (optional)"
        ]
        for item in features:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Control Modes:")
        modes = []
        if controller_info['features']['vcs']:
            modes.append("VCS - Vent Control System for exhaust management")
        if controller_info['features']['odcs']:
            modes.append("ODCS - Overdraft Control System")
        if controller_info['features']['pas']:
            modes.append("PAS - Pressure Air System for combustion air")
        for mode in modes:
            p = doc.add_paragraph(mode, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Electrical:")
        p = doc.add_paragraph("120V/1Ph/60Hz, 15A dedicated circuit")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_odcs_spec(self, doc, odcs_info):
        """Add ODCS specification details"""
        doc.add_paragraph("A. System:")
        p = doc.add_paragraph(f"Connector Draft System (CDS3) with modulating dampers for precise draft control")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Features:")
        features = [
            "Single Blade Damper (SBD) with butterfly actuator",
            "2-second actuator response time",
            "Bi-directional pressure transducer",
            "EC-Flow™ modulating control",
            "Integrated with system controller",
            "Standard 1/2\" flanges and v-band connections",
            "'G' model with Viton seal for backflow prevention (if required)"
        ]
        for item in features:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_supply_fan_spec(self, doc, supply_fan_info):
        """Add supply air fan specification"""
        doc.add_paragraph("A. Model:")
        p = doc.add_paragraph(f"{supply_fan_info['series']} Series - {supply_fan_info['name']}")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Features:")
        features = [
            "Sized for combustion air requirements",
            "Modulating speed control via system controller",
            "Weatherproof construction",
            "Low noise operation",
            "Coordinated with exhaust system via PAS control"
        ]
        for item in features:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
