# CARL - Chimney Analysis and Reasoning Layer
## Complete File Manifest

### 🎯 CORE APPLICATION FILES (Required)

**Main Application:**
- `streamlit_carl.py` (111KB) - Main Streamlit application with chatbot interface
  * All user interaction screens
  * Step-by-step appliance configuration
  * Results display and product selection
  * Report generation

**Calculation Engine:**
- `chimney_calculator.py` (32KB) - Core thermodynamic calculations
  * Draft calculations
  * Pressure loss calculations  
  * Updated K-values from spreadsheet
  * Vent type coefficients (UL441, UL103, UL1738)

**Product Selection:**
- `product_selector.py` (33KB) - Intelligent product recommendation
  * All guard rails implemented
  * Mixed category detection
  * Turndown overdraft logic
  * Controller selection (V150/V250/V300/V350)
  * CDS3 vs ODCS logic

**Fan Performance Data:**
- `fan_curves_data.py` (3.9KB) - Embedded fan curve data
  * TRV, T9F, CBX series data
  * 25 fan models included

**Postal Code Lookup:**
- `postal_code_lookup.py` (12KB) - US & Canadian postal codes
  * All 50 US states
  * All Canadian provinces
  * Elevation estimation

### 📄 REPORT GENERATION FILES (Required)

**PDF Reports:**
- `pdf_report_generator.py` (31KB) - Enhanced PDF sizing reports
  * Professional US Draft Co. branding
  * Color-coded sections
  * Fan curve images
  * All system inputs displayed
  * Contact information capture

**CSI Specifications:**
- `csi_spec_generator.py` (16KB) - Construction spec documents
  * Part 1, 2, 3 format
  * CDS3 detailed specifications
  * ODCS specifications
  * Draft inducer specs
  * Controller specs

### 📊 DATA FILES (Optional but Recommended)

**Fan Curve Source Data:**
- `DEF_Fan_Curves.xlsx` - Draft inducer fan curves
- `Draft_Inducers_Fan_Curves.xlsx` - Additional fan data

**Product Data Sheets:**
- Multiple PDF datasheets in `/mnt/project/` directory
  * CBX series
  * TRV series
  * T9F series
  * Controller specs
  * CDS3 documentation

### 🗑️ DEPRECATED/BACKUP FILES (Not Required)

These can be ignored:
- `app.py` - Old version
- `carl_chatbot.py` - Old version
- `chimney_chatbot.py` - Old version
- `csi_spec_generator_new.py` - Superseded
- `enhanced_calculator.py` - Old version
- `streamlit_app.py` - Old version
- `streamlit_carl_backup.py` - Backup only

---

## 🚀 Deployment Checklist

### Minimum Required Files:
1. ✅ streamlit_carl.py
2. ✅ chimney_calculator.py
3. ✅ product_selector.py
4. ✅ fan_curves_data.py
5. ✅ postal_code_lookup.py
6. ✅ pdf_report_generator.py
7. ✅ csi_spec_generator.py

### Optional Enhancement Files:
- Excel files (for reference/updates)
- PDF datasheets (for detailed specs)

### Dependencies (requirements.txt):
```
streamlit>=1.31.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
python-docx>=1.1.0
reportlab>=4.0.0
matplotlib>=3.7.0
```

---

## 📋 File Relationships

```
streamlit_carl.py
├── chimney_calculator.py (calculations)
├── product_selector.py (recommendations)
│   └── fan_curves_data.py (fan data)
├── postal_code_lookup.py (location data)
├── pdf_report_generator.py (PDF output)
└── csi_spec_generator.py (DOCX output)
```

---

## ✨ Current Features

### Guard Rails Implemented:
1. ✅ Mixed categories → Draft inducer required
2. ✅ All Cat IV + low pressure → CDS3 only
3. ✅ All Cat IV + high pressure → Ignore connector loss
4. ✅ All Cat I → Barometric dampers
5. ✅ Turndown + pressure check → ODCS if needed
6. ✅ 2 systems + touchscreen → V250
7. ✅ 3 systems + touchscreen → V300/V350

### K-Values Updated:
- ✅ UL441 Type B Vent
- ✅ UL103 Pressure Chimney
- ✅ UL1738 Special Gas Vent
- ✅ All values from K-Values.xlsx

### Reports Include:
- ✅ PDF sizing reports (enhanced design)
- ✅ CSI specifications (CDS3 detailed)
- ✅ Fan curve images
- ✅ User contact capture
- ✅ All system inputs

