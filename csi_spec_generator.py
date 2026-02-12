"""
CSI Specification Generator for Section 23 51 10
MECHANICAL DRAFT SYSTEMS FOR COMMERCIAL/RESIDENTIAL VENTING
Generates comprehensive DOCX specifications for US Draft Co. systems
Compliant with UL 705, UL 378, NFPA 54, NFPA 211, IMC, IFGC
"""

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime

class CSISpecificationGenerator:
    """Generates detailed CSI MasterFormat Section 23 51 10 specifications"""
    
    def __init__(self):
        self.section_number = "23 51 10"
        self.section_title = "MECHANICAL DRAFT SYSTEMS FOR COMMERCIAL/RESIDENTIAL VENTING"
        
    def generate_specification(self, project_info, products_selected, system_data):
        """Generate complete CSI specification document"""
        doc = Document()
        self._setup_document_styles(doc)
        self._add_header(doc, project_info)
        self._add_part_1_general(doc)
        self._add_part_2_products(doc, products_selected, system_data)
        self._add_part_3_execution(doc, products_selected, system_data)
        return doc
    
    def _setup_document_styles(self, doc):
        """Set up document styles"""
        style = doc.styles['Normal']
        style.font.name = 'Arial'
        style.font.size = Pt(11)
    
    def _add_header(self, doc, project_info):
        """Add specification header"""
        p = doc.add_paragraph()
        p.add_run(f"SECTION {self.section_number}").bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p = doc.add_paragraph()
        p.add_run(self.section_title).bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size = Pt(14)
        
        doc.add_paragraph()
        doc.add_paragraph(f"Project: {project_info.get('name', 'TBD')}")
        doc.add_paragraph(f"Location: {project_info.get('location', 'TBD')}")
        doc.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}")
        doc.add_paragraph()
        doc.add_paragraph("_" * 80)
        doc.add_paragraph()
    
    def _add_section_heading(self, doc, number, title):
        """Add section heading"""
        p = doc.add_paragraph()
        run = p.add_run(f"{number} {title}")
        run.bold = True
        run.underline = True
        run.font.size = Pt(11)
    
    def _add_part_1_general(self, doc):
        """Add PART 1 - GENERAL with comprehensive requirements"""
        p = doc.add_paragraph("PART 1 - GENERAL")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        doc.add_paragraph()
        
        # 1.1 SUMMARY
        self._add_section_heading(doc, "1.1", "SUMMARY")
        doc.add_paragraph("A. Section Includes:")
        for item in [
            "Powered draft equipment for commercial and residential venting systems",
            "Electronic control systems for draft management and safety interlocking",
            "Overdraft control systems (where required for natural draft appliances)",
            "Control wiring, sensors, transducers, and accessories",
            "Factory startup service, system commissioning, and operator training"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Related Sections:")
        for item in [
            "Section 23 00 00 - Heating, Ventilating, and Air Conditioning",
            "Section 23 33 00 - Air Duct Accessories",
            "Section 23 51 00 - Breechings, Chimneys, and Stacks",
            "Section 26 05 00 - Common Work Results for Electrical",
            "Section 26 24 00 - Switchboards and Panelboards"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.2 REFERENCES
        self._add_section_heading(doc, "1.2", "REFERENCES")
        doc.add_paragraph("A. Applicable Codes and Standards:")
        
        refs = [
            ("UL 705", "Power Ventilators - Standard for safety of powered draft equipment"),
            ("UL 378", "Draft Equipment - Standard for safety of draft control devices"),
            ("NFPA 54", "National Fuel Gas Code - Gas appliance venting and safety"),
            ("NFPA 211", "Standard for Chimneys, Fireplaces, Vents, and Solid Fuel-Burning Appliances"),
            ("IMC", "International Mechanical Code - Mechanical system requirements"),
            ("IFGC", "International Fuel Gas Code - Fuel gas appliance installation"),
            ("IBC", "International Building Code - Structural and fire safety"),
            ("ASHRAE 90.1", "Energy Standard for Buildings Except Low-Rise Residential"),
            ("NEC (NFPA 70)", "National Electrical Code - Electrical installation standards"),
            ("IEEE C62.41", "Recommended Practice on Surge Voltages - Surge protection")
        ]
        
        for code, desc in refs:
            p = doc.add_paragraph(f"{code}: {desc}", style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.3 ADMINISTRATIVE REQUIREMENTS
        self._add_section_heading(doc, "1.3", "ADMINISTRATIVE REQUIREMENTS")
        doc.add_paragraph("A. Coordination:")
        p = doc.add_paragraph("Coordinate installation of powered draft equipment with venting system, appliances, and electrical work. Review interface requirements with all trades.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Preinstallation Meeting:")
        p = doc.add_paragraph("Conduct preinstallation meeting with installing contractor, mechanical engineer, electrical contractor, and manufacturer's representative to review installation requirements, sequencing, control logic, and testing procedures.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.4 SUBMITTALS
        self._add_section_heading(doc, "1.4", "SUBMITTALS")
        
        doc.add_paragraph("A. Product Data:")
        for item in [
            "Manufacturer's catalog data sheets for all equipment including dimensions and weights",
            "Certified fan performance curves showing system operating point",
            "Motor nameplate data and electrical characteristics",
            "Control system wiring diagrams with terminal identification",
            "Differential pressure sensor calibration certificates",
            "UL 705 and UL 378 Listing certificates and labels"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Shop Drawings:")
        for item in [
            "Equipment layout showing dimensions, clearances, and mounting details",
            "Ductwork and vent connections with sizes, materials, and orientations",
            "Electrical single-line diagrams and point-to-point control schematics",
            "Sensor and transducer locations with installation details",
            "Sequence of operations narrative with safety interlocking logic"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Operation and Maintenance Data:")
        for item in [
            "Manufacturer's installation, operating, and maintenance instructions",
            "Preventive maintenance procedures and recommended schedules",
            "Troubleshooting guides and diagnostic flowcharts",
            "Replacement parts lists with manufacturer part numbers and sources",
            "Factory startup and commissioning reports with test data",
            "Warranty information, terms, and registration procedures"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.5 QUALITY ASSURANCE
        self._add_section_heading(doc, "1.5", "QUALITY ASSURANCE")
        
        doc.add_paragraph("A. Manufacturer Qualifications:")
        for item in [
            "Manufacturer with minimum 25 years documented experience in design and manufacture of powered draft equipment",
            "Manufacturer maintains UL 705 Listing for powered draft equipment and UL 378 Listing for draft control devices",
            "Manufacturer provides factory technical support, field service, and operator training",
            "Manufacturer maintains inventory of replacement parts for minimum 10 years after production"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Installer Qualifications:")
        for item in [
            "Installer certified by equipment manufacturer for installation, startup, and service",
            "Licensed mechanical contractor in jurisdiction of project",
            "Installer experienced with minimum three (3) similar installations in past five (5) years",
            "Electrical work performed by licensed electrician per local authority requirements"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Regulatory Requirements:")
        for item in [
            "Equipment shall be UL Listed and labeled per UL 705 and UL 378",
            "Installation shall comply with manufacturer's written instructions and applicable codes",
            "Electrical work shall comply with NEC and local amendments",
            "Obtain all required permits and schedule inspections with authority having jurisdiction"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 1.6 WARRANTY
        self._add_section_heading(doc, "1.6", "WARRANTY")
        
        doc.add_paragraph("A. Standard Warranty:")
        p = doc.add_paragraph("Manufacturer's standard warranty of two (2) years from date of substantial completion covering defects in materials and workmanship. Warranty shall cover parts and factory labor for repair or replacement.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Extended Warranty:")
        p = doc.add_paragraph("Extended warranty coverage available for motors and electronic controls up to five (5) years. Coordinate extended warranty requirements with Owner during submittal review.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_page_break()
    
    def _add_part_2_products(self, doc, products, system_data):
        """Add PART 2 - PRODUCTS with detailed specifications"""
        p = doc.add_paragraph("PART 2 - PRODUCTS")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        doc.add_paragraph()
        
        # 2.1 MANUFACTURERS
        self._add_section_heading(doc, "2.1", "MANUFACTURERS")
        
        doc.add_paragraph("A. Basis of Design Manufacturer:")
        p = doc.add_paragraph("US Draft Co., a division of R.M. Manifold Group, Inc.")
        p.paragraph_format.left_indent = Inches(0.5)
        p = doc.add_paragraph("100 S Sylvania Ave, Fort Worth, TX 76111")
        p.paragraph_format.left_indent = Inches(0.75)
        p = doc.add_paragraph("Phone: 817-393-4029 | Email: info@usdraft.com")
        p.paragraph_format.left_indent = Inches(0.75)
        p = doc.add_paragraph("Website: www.usdraft.com")
        p.paragraph_format.left_indent = Inches(0.75)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Substitutions:")
        p = doc.add_paragraph("Requests for substitutions must be submitted in accordance with Section 01 25 00 - Substitution Procedures. Proposed substitutes must be UL 705 and UL 378 Listed, provide equivalent performance characteristics, features, warranty, and be approved by Engineer prior to bidding.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # Add product sections
        section_num = 1
        
        if products.get('draft_inducer'):
            section_num += 1
            self._add_section_heading(doc, f"2.{section_num}", "POWERED DRAFT INDUCER")
            self._add_draft_inducer_spec(doc, products['draft_inducer'], system_data)
        
        if products.get('controller'):
            section_num += 1
            self._add_section_heading(doc, f"2.{section_num}", "ELECTRONIC CONTROL SYSTEM")
            self._add_controller_spec(doc, products['controller'], system_data)
        
        if products.get('odcs'):
            section_num += 1
            self._add_section_heading(doc, f"2.{section_num}", "OVERDRAFT CONTROL SYSTEM")
            self._add_odcs_spec(doc)
        
        doc.add_page_break()
    
    def _add_draft_inducer_spec(self, doc, inducer, system_data):
        """Add detailed draft inducer specification"""
        series = inducer.get('series', '')
        model = inducer.get('model', '')
        
        # Series-specific data
        series_data = {
            'TRV': {
                'name': 'TRV Series True Inline Draft Inducer',
                'config': 'True inline configuration, compact straight-through design',
                'ip_rating': 'IP54',
                'performance': '80-8,520 CFM, 0-7.0" w.c. static pressure',
                'current': '0.8-3.5A depending on model size'
            },
            'T9F': {
                'name': 'T9F Series 90-Degree Inline Draft Inducer',
                'config': '90-degree inline configuration with integrated elbow for space savings',
                'ip_rating': 'IP54',
                'performance': '200-17,250 CFM, 0-8.0" w.c. static pressure',
                'current': '1.2-6.0A depending on model size'
            },
            'CBX': {
                'name': 'CBX Series Termination Mount Chimney Exhaust Fan',
                'config': 'Termination mount design for installation at top of chimney/vent stack',
                'ip_rating': 'IP65 (outdoor rated)',
                'performance': '215-7,900 CFM, 0-5.0" w.c. static pressure',
                'current': '2.0-10.0A depending on model size'
            }
        }
        
        spec = series_data.get(series, series_data['TRV'])
        
        doc.add_paragraph("A. General:")
        p = doc.add_paragraph(f"Provide {spec['name']} as manufactured by US Draft Co. Equipment shall be UL 705 Listed Powered Draft Equipment for installation in commercial and residential fuel-fired appliance venting systems. {spec['config']}.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Model and Capacity:")
        
        cfm = system_data.get('cfm', 'TBD')
        pressure = system_data.get('static_pressure', 'TBD')
        
        for item in [
            f"Model Number: {model}",
            f"Design Airflow: {cfm} CFM at {pressure} inches w.c. static pressure",
            f"Operating Range: {spec['performance']}",
            "Fan performance curves certified at 70°F standard air, sea level"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Construction:")
        
        # Material selection based on appliance category
        cat = system_data.get('appliance_category', 'I')
        if cat in ['II', 'IV']:
            material = "316L stainless steel for condensing flue gas applications (Category II and IV appliances)"
        else:
            material = "Heavy gauge aluminized steel or 316L stainless steel per Engineer's selection"
        
        construction_items = [
            f"Housing: {material}",
            "Impeller: Dynamically balanced cast aluminum alloy with backward curved blades for high efficiency and low noise",
            "Motor: Electronically commutated (EC) permanent magnet motor with integral variable frequency drive",
            f"Motor Enclosure: {spec['ip_rating']} rated for protection from dust and moisture",
            "Motor Efficiency: IE4 Super Premium Efficiency classification per IEC 60034-30-1",
            "Bearings: Permanently lubricated sealed ball bearings rated for continuous duty, L10 life exceeding 40,000 hours",
            "Motor Insulation: Class F (155°C) with Class B (130°C) temperature rise",
            "Shaft Seal: Labyrinth seal to prevent flue gas ingress to motor cavity"
        ]
        
        if series == 'CBX':
            construction_items.append("Weather Protection: Integral rain cap, bird screen, and sealed electrical enclosure for outdoor installation")
        
        for item in construction_items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Performance Characteristics:")
        
        for item in [
            "Temperature Rating: Flue gas temperatures up to 550°F continuous duty, 650°F intermittent (30 minutes)",
            f"Electrical: 120V/1Ph/60Hz, {spec['current']}",
            "Speed Control: 0-10VDC analog input signal, modulates fan from 10-100% of rated capacity",
            "Control Response: EC-Flow™ constant airflow technology maintains setpoint CFM regardless of system resistance changes due to vent condensate, blockage, or wind conditions",
            "Noise Level: Sound power level per AMCA 301 available upon request",
            "Vibration: Balanced to ISO 1940 Grade G6.3 for smooth, quiet operation"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("E. Standard Features:")
        
        for item in [
            "Vibration isolation: Motor mounted on vibration-isolating rubber grommets to minimize structure-borne noise transmission",
            "Flow proving switch: Normally open dry contact output to prove fan operation, rated 5A @ 120VAC",
            "Service access: Removable panel for motor inspection and service without disturbing vent connections",
            "Corrosion protection: All fasteners stainless steel, outdoor-rated finish",
            "Motor overload protection: Internal thermal overload per UL 705 requirements",
            "Wiring connections: Strain-relieved terminal block with integral ground connection",
            "Mounting gaskets: High-temperature silicone gaskets for leak-free vent connections"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("F. Accessories Provided:")
        
        for item in [
            "Installation manual with wiring diagrams",
            "Mounting hardware and fasteners",
            "Control wiring connection diagram",
            "UL Listing label affixed to equipment"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_controller_spec(self, doc, controller, system_data):
        """Add detailed controller specification"""
        model = controller.get('base_model', 'V250')
        full_model = controller.get('model', model)
        
        # Model-specific data
        model_data = {
            'V150': {
                'name': 'V150 Electronic Vent Control System',
                'display': 'LCD display with 4-button interface',
                'capacity': '1-2 appliances',
                'features_short': 'Basic control with LCD display, suitable for simple applications'
            },
            'V250': {
                'name': 'V250 Electronic Vent Control System',
                'display': '4-inch color touchscreen with intuitive graphical interface',
                'capacity': '1-6 appliances with individual sequencing',
                'features_short': 'Advanced control with touchscreen, data logging, and optional communications'
            },
            'V350': {
                'name': 'V350 Electronic Vent Control System',
                'display': '7-inch color touchscreen with multi-language support',
                'capacity': '1-15 appliances with advanced load management',
                'features_short': 'Premium control system with web monitoring, extensive data logging, and building automation integration'
            }
        }
        
        spec = model_data.get(model, model_data['V250'])
        
        doc.add_paragraph("A. General:")
        p = doc.add_paragraph(f"Provide {spec['name']} as manufactured by US Draft Co. Controller shall be UL 378 Listed Draft Control Equipment for automatic control and safety interlocking of powered draft equipment. {spec['features_short']}.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Model and Configuration:")
        
        config = controller.get('configuration', '')
        config_items = [f"Model Number: {full_model}"]
        
        if 'V' in config:
            config_items.append("VCS (Vent Control System): Controls powered draft inducer with 0-10VDC modulating output")
        if 'O' in config:
            config_items.append("ODCS (Overdraft Control System): Controls motorized damper for natural draft regulation")
        if 'P' in config:
            config_items.append("PAS (Powered Air System): Controls combustion air supply fan")
        
        config_items.extend([
            f"Appliance Capacity: Controls up to {spec['capacity']}",
            f"User Interface: {spec['display']}"
        ])
        
        for item in config_items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Safety Interlocking (per NFPA 54):")
        
        for item in [
            "Appliance Proving: Differential pressure switch monitors appliance flue outlet to verify appliance operation per NFPA 54 Section 13.2 before enabling vent system",
            "Draft Proving: Verifies adequate vent draft pressure before enabling appliance gas valve interlock",
            "Flow Proving: Monitors draft inducer flow proving switch to verify fan operation",
            "Pre-Purge: Adjustable pre-purge timer (0-300 seconds) runs fan before appliance enable to clear vent of residual products of combustion",
            "Post-Purge: Adjustable post-purge timer (0-300 seconds) continues fan operation after appliance shutdown to clear vent system",
            "Low Draft Cutout: Disables appliance and initiates alarm if vent draft falls below adjustable setpoint, indicating blocked vent or fan failure",
            "High Draft Protection: Optional overdraft protection to prevent excessive draft conditions (V250/V350 only)",
            "Power Failure Restart: Adjustable restart delay (0-600 seconds) after power restoration prevents simultaneous restart of multiple appliances"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Control Features:")
        
        if model == 'V150':
            features = [
                "Manual/Auto/Off control modes with keypad lockout",
                "Adjustable draft setpoint with real-time draft display",
                "Appliance call input via 24VAC or dry contact",
                "Adjustable fan speed control (10-100%)",
                "Alarm relay output for remote monitoring",
                "Runtime hour meter and cycle counter"
            ]
        elif model == 'V250':
            features = [
                "EC-Flow™ closed-loop airflow control with flow measurement and display",
                "Individual appliance sequencing with configurable operating modes",
                "Draft measurement with 0.001 inches w.c. resolution",
                "Advanced data logging: Stores 10,000+ events with timestamp",
                "Trend graphing: Real-time and historical graphs of draft, airflow, and runtime",
                "Password-protected settings with multiple user levels",
                "Configurable alarm outputs with adjustable delay timers",
                "Optional Modbus RTU or BACnet MS/TP communication for building automation",
                "Optional email/SMS alarm notification capability"
            ]
        else:  # V350
            features = [
                "EC-Flow™ closed-loop airflow control with real-time CFM measurement",
                "Advanced multi-appliance load management with lead/lag rotation",
                "Dual differential pressure transducers for redundancy (0.001 inch w.c. resolution)",
                "Extensive data logging: 50,000+ events with microSD card storage",
                "Advanced trend graphing with data export capability",
                "Multi-level password protection with audit trail",
                "Configurable alarm matrix with priority levels and escalation",
                "Modbus RTU, BACnet MS/TP, or LonWorks communication protocols",
                "Web-based remote monitoring and control via Ethernet",
                "Email, SMS, and push notification alarm capability",
                "Fault diagnostics with guided troubleshooting procedures",
                "Seasonal energy optimization algorithms to minimize runtime and energy consumption"
            ]
        
        for item in features:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("E. Inputs and Outputs:")
        
        io_items = [
            "Appliance Call Inputs: 24VAC or dry contact, one per appliance",
            "Draft Pressure Sensor: Bidirectional differential pressure transducer, ±2.0 inches w.c. range",
            "Motor Speed Output: 0-10VDC analog output for draft inducer speed control",
            "Appliance Enable Outputs: SPDT relay contacts rated 10A @ 120VAC resistive",
            "Alarm Output: Form-C relay contacts for remote alarm system",
            "Flow Proving Input: Dry contact input from draft inducer flow switch"
        ]
        
        if model in ['V250', 'V350']:
            io_items.append("Communication Port: RS-485 for Modbus RTU or BACnet MS/TP")
        
        if model == 'V350':
            io_items.append("Ethernet Port: 10/100 Mbps for web-based monitoring and BACnet/IP")
        
        for item in io_items:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("F. Electrical:")
        
        for item in [
            "Power Input: 120VAC/1Ph/60Hz, dedicated 15A circuit required",
            "Surge Protection: Internal surge suppression per IEEE C62.41 Category A",
            "Control Power: Integral 24VAC transformer for control circuit",
            "Wire Terminations: Screw terminal blocks, accept 14-22 AWG wire",
            "Wiring: In accordance with NEC Article 725 for Class 2 control circuits"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("G. Enclosure:")
        
        p = doc.add_paragraph("NEMA 1 general-purpose enclosure suitable for indoor mounting in mechanical room environment. Enclosure finish: Gray powder coat RAL 7035. Provide NEMA 4X outdoor-rated enclosure where controller is exposed to weather or washdown conditions.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("H. Code Compliance:")
        
        for item in [
            "UL 378 Listed Draft Control Equipment",
            "NFPA 54 compliant safety interlocking",
            "IMC and IFGC approved for fuel gas applications",
            "ASHRAE 90.1 energy efficiency features (V250/V350)"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_odcs_spec(self, doc):
        """Add ODCS specification"""
        doc.add_paragraph("A. General:")
        p = doc.add_paragraph("Provide CDS3 Chimney Draft Stabilization System as manufactured by US Draft Co. System shall be UL 378 Listed for automatic control of excessive chimney draft on natural draft appliances.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. System Components:")
        
        for item in [
            "Motorized Damper: SBD Series stack barometric damper with modulating control",
            "Damper Actuator: 24VAC direct-coupled actuator, 90-degree rotation, 2-second stroke time, spring return to closed on power failure",
            "Pressure Sensor: Bidirectional differential pressure transducer, ±2.0 inches w.c. range, 0.001 inch resolution",
            "Controller: Microprocessor-based PID control with auto-tuning algorithm"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Operation:")
        p = doc.add_paragraph("System continuously monitors chimney draft and modulates damper position to maintain user-adjustable draft setpoint. PID control algorithm with auto-tuning provides stable control without hunting or oscillation.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
    
    def _add_part_3_execution(self, doc, products, system_data):
        """Add PART 3 - EXECUTION"""
        p = doc.add_paragraph("PART 3 - EXECUTION")
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        doc.add_paragraph()
        
        # 3.1 EXAMINATION
        self._add_section_heading(doc, "3.1", "EXAMINATION")
        doc.add_paragraph("A. Verify existing conditions before installation:")
        
        for item in [
            "Vent piping is complete, properly sized per design calculations, and pressure tested per IMC Section 803",
            "Appliances are installed, connected, and ready for startup",
            "Electrical service is available at equipment locations with proper voltage and capacity",
            "Mounting surfaces are structurally adequate to support equipment weight and loads",
            "Ambient temperature and humidity are within equipment operating range",
            "Clearances meet code requirements (IMC, IFGC, NFPA 54) and manufacturer recommendations"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.2 INSTALLATION
        self._add_section_heading(doc, "3.2", "INSTALLATION")
        
        doc.add_paragraph("A. General Requirements:")
        for item in [
            "Install equipment in accordance with manufacturer's written instructions, approved shop drawings, and applicable codes",
            "Maintain manufacturer's recommended clearances for service access and ventilation",
            "Provide structural support independent of vent piping system",
            "Install equipment level and plumb within ±1/4 inch",
            "Protect equipment from construction dust, moisture, and physical damage during installation"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        if products.get('draft_inducer'):
            doc.add_paragraph("B. Draft Inducer Installation:")
            series = products['draft_inducer'].get('series', '')
            
            if series == 'CBX':
                install_items = [
                    "Mount termination fan at top of vent stack using manufacturer's mounting template",
                    "Provide weatherproof installation with proper roof flashing, counterflashing, and approved sealant",
                    "Support fan weight independently with structural framing adequate for equipment weight plus wind loads per IBC",
                    "Install integral rain cap and bird screen in accordance with manufacturer's instructions",
                    "Seal all roof penetrations to prevent water infiltration per roofing manufacturer requirements",
                    "Route control wiring and power wiring in separate weatherproof conduits to controller location",
                    "Provide lightning protection where required by local codes"
                ]
            elif series == 'TRV':
                install_items = [
                    "Install true inline fan in horizontal or vertical vent pipe run at location shown on drawings",
                    "Support fan independently of vent piping using structural hangers, floor supports, or vibration-isolated platform",
                    "Provide vibration isolation between fan and structural supports using neoprene or spring isolators",
                    "Maintain straight duct lengths of minimum 3 diameters upstream and 5 diameters downstream of fan",
                    "Verify flow direction arrow on fan housing matches system flow direction",
                    "Seal vent connections with high-temperature silicone gaskets, torque fasteners per manufacturer specifications",
                    "Support vent piping adjacent to fan to prevent stress on fan housing"
                ]
            else:  # T9F
                install_items = [
                    "Install 90-degree inline fan at change of direction in vent system",
                    "Support fan weight independently of vent piping using structural steel or vibration-isolated platform",
                    "Provide vibration isolation pads between fan base and support structure",
                    "Orient fan for proper flow direction per directional arrow marking on housing",
                    "Support both inlet and outlet vent connections to prevent cantilever loads on fan",
                    "Ensure removable access panel is accessible for motor service without disturbing vent connections",
                    "Seal all joints with high-temperature gaskets"
                ]
            
            for item in install_items:
                p = doc.add_paragraph(item, style='List Number')
                p.paragraph_format.left_indent = Inches(0.5)
            
            doc.add_paragraph()
        
        doc.add_paragraph("C. Controller Installation:")
        for item in [
            "Mount controller on wall in mechanical room at 60 inches above finished floor (eye level for operator viewing)",
            "Provide minimum 36 inches clear space in front of controller for service access per NEC Article 110.26",
            "Install in location protected from water, excessive heat (>104°F), vibration, and direct sunlight",
            "Mount enclosure level and plumb using manufacturer's provided mounting template and fasteners",
            "Route control wiring in rigid or EMT conduit in accordance with NEC Article 725 for Class 2 circuits",
            "Maintain minimum 6 inch separation between power wiring and control wiring per NEC Article 725.136"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        doc.add_paragraph("D. Electrical Installation:")
        for item in [
            "Provide dedicated 120V/1Ph/60Hz, 15A branch circuit for draft inducer and controller per NEC Article 210",
            "Install Type 2 surge protective device at panelboard per IEEE C62.41 Category A, UL 1449 Listed",
            "Wire equipment in accordance with NEC and manufacturer's wiring diagrams, use copper conductors only",
            "Size conductors per NEC Article 310, minimum 14 AWG, rated 75°C minimum",
            "Provide proper equipment grounding per NEC Article 250, bond all metal enclosures",
            "Label all circuits at panelboard and equipment per NEC Article 110.22",
            "Provide disconnect switch within sight of equipment per NEC Article 430.102, lockable in OFF position",
            "Route low-voltage control wiring in separate conduit from power wiring",
            "Terminate all wiring connections with proper connectors, provide strain relief, secure unused conductors"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        doc.add_paragraph("E. Control Wiring and Sensors:")
        for item in [
            "Install differential pressure sensor at appliance flue outlet per manufacturer's recommendations",
            "Route pressure sensing tubing with continuous downward slope (1/4 inch per foot minimum) to prevent condensate traps",
            "Use 1/4-inch OD clear nylon or copper tubing for pressure sensing lines, avoid kinks",
            "Support tubing every 3 feet maximum using plastic or metal clips to prevent sagging",
            "Keep sensing tubing away from hot surfaces, maintain 6 inch minimum clearance",
            "Connect appliance interlock wiring per approved control diagrams and sequence of operations",
            "Test all circuits for continuity, shorts, and proper voltage levels before energizing equipment"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.3 STARTUP AND COMMISSIONING
        self._add_section_heading(doc, "3.3", "STARTUP SERVICE AND COMMISSIONING")
        
        doc.add_paragraph("A. Factory Startup Service:")
        p = doc.add_paragraph("Manufacturer's factory-trained service technician shall perform initial startup, functional testing, and commissioning of all equipment. Coordinate startup service date minimum two (2) weeks in advance. Startup service shall not be performed until installation is complete, appliances are operational, and electrical service is available.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Pre-Startup Checklist:")
        for item in [
            "Verify electrical power is available, correct voltage ±10%, and properly grounded",
            "Verify all control wiring is complete, properly terminated, and tested for continuity",
            "Verify draft inducer impeller rotates freely by hand with no binding or rubbing",
            "Verify all sensors and transducers are installed, connected, and calibrated",
            "Verify appliances are installed, connected, and ready for operation",
            "Verify vent system is complete, sealed, and leak-tested per IMC Section 803.2"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Startup and Testing Procedure:")
        for item in [
            "Energize controller, verify display functions and no fault indications",
            "Program controller settings per design requirements and sequence of operations",
            "Calibrate draft pressure sensor using precision manometer traceable to NIST standards",
            "Test all safety interlocks for proper operation (appliance proving, draft proving, flow proving)",
            "Start draft inducer, verify correct rotation direction and smooth operation",
            "Measure and record draft pressure at appliance outlet and compare to design calculations",
            "Measure and record draft inducer airflow using pitot tube traverse or calibrated flow station",
            "Verify appliance proving switches operate correctly and interlock functions as designed",
            "Test system operation under all appliance firing scenarios (single appliance, multiple appliances, all appliances)",
            "Adjust controller setpoints and PID parameters for optimal performance and stability",
            "Conduct 30-minute test run under full load to verify stable operation",
            "Complete manufacturer's startup report form and submit to Engineer for review"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("D. Performance Verification:")
        for item in [
            f"Draft Pressure: Measure at appliance outlet, verify meets design target ±0.01 inches w.c.",
            f"Airflow: Measure draft inducer CFM, verify within ±10% of design value",
            "Motor Current: Measure and verify within motor nameplate full load amps",
            "Low Draft Cutout: Test setpoint and verify appliance lockout occurs",
            "Alarm Outputs: Verify relay contacts operate and external alarm system responds",
            "Data Logging: Verify events are being logged with correct timestamp"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        
        # 3.4 TRAINING
        self._add_section_heading(doc, "3.4", "OPERATOR TRAINING")
        
        doc.add_paragraph("A. Training Requirements:")
        p = doc.add_paragraph("Provide minimum four (4) hours of hands-on training for Owner's operating and maintenance personnel at project site. Training shall be conducted by manufacturer's factory representative following successful system commissioning. Provide separate training session for Owner's night shift or weekend personnel if requested.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("B. Training Topics:")
        for item in [
            "System overview: Theory of operation, major components, and control logic",
            "Controller operation: Display navigation, setpoint adjustment, alarm acknowledgment",
            "Safety interlocks: Purpose and operation of proving switches and safety cutouts",
            "Routine maintenance: Inspection procedures, filter cleaning, sensor calibration verification",
            "Troubleshooting: Alarm interpretation, diagnostic procedures, common problems and solutions",
            "Emergency procedures: System shutdown, lockout/tagout, emergency contacts",
            "Parts replacement: Identification of wear items, part numbers, ordering procedures",
            "Record keeping: Maintenance log procedures, data retrieval, report generation"
        ]:
            p = doc.add_paragraph(item, style='List Number')
            p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph("C. Training Documentation:")
        p = doc.add_paragraph("Provide training completion certificates signed by instructor and all attendees. Submit attendance roster with names, titles, and contact information to Engineer within one (1) week of training completion.")
        p.paragraph_format.left_indent = Inches(0.5)
        
        doc.add_paragraph()
        doc.add_paragraph()
        p = doc.add_paragraph("END OF SECTION 23 51 10")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True

# End of file
