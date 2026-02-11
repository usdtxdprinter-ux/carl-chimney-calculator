"""
CARL - Chimney Analysis and Reasoning Layer
Complete Chatbot Interface with Button Controls and PDF Reports
"""

import streamlit as st
from enhanced_calculator import EnhancedChimneyCalculator
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Page configuration
st.set_page_config(
    page_title="CARL - Chimney Calculator",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize calculator
@st.cache_resource
def get_calculator():
    return EnhancedChimneyCalculator()

calc = get_calculator()

# Zip code to city/elevation database (sample - expand as needed)
ZIP_DATABASE = {
    '76111': {'city': 'Fort Worth', 'state': 'TX', 'elevation': 650},
    '75001': {'city': 'Addison', 'state': 'TX', 'elevation': 645},
    '80202': {'city': 'Denver', 'state': 'CO', 'elevation': 5280},
    '10001': {'city': 'New York', 'state': 'NY', 'elevation': 33},
    '90001': {'city': 'Los Angeles', 'state': 'CA', 'elevation': 285},
    '60601': {'city': 'Chicago', 'state': 'IL', 'elevation': 594},
    '33101': {'city': 'Miami', 'state': 'FL', 'elevation': 6},
    '98101': {'city': 'Seattle', 'state': 'WA', 'elevation': 175},
    '85001': {'city': 'Phoenix', 'state': 'AZ', 'elevation': 1086},
    '02101': {'city': 'Boston', 'state': 'MA', 'elevation': 141}
}

def lookup_zip(zipcode):
    """Look up city and elevation from zip code"""
    zipcode = zipcode.strip()
    if zipcode in ZIP_DATABASE:
        return ZIP_DATABASE[zipcode]
    return None

def elevation_to_pressure(elevation_ft):
    """Convert elevation in feet to barometric pressure in inches Hg"""
    if elevation_ft == 0:
        return 29.92
    P0 = 29.92
    pressure = P0 * (1 - 6.87535e-6 * elevation_ft) ** 5.2561
    return pressure

def calculate_combustion_air(appliances, temp_ambient_f=70):
    """
    Calculate combustion air requirements
    
    Combustion Air = Total flue gas mass - Fuel mass
    Returns CFM at ambient temperature
    """
    total_flue_mass = 0  # lb/min
    total_fuel_mass = 0  # lb/min
    
    for app in appliances:
        # Get flue gas mass
        result = calc.cfm_from_combustion(
            mbh=app['mbh'],
            co2_percent=app['co2_percent'],
            temp_f=app['temp_f'],
            fuel_type=app['fuel_type']
        )
        total_flue_mass += result['mass_flow_lbm_min']
        
        # Calculate fuel mass
        # For natural gas: ~1000 BTU/ft³, density ~0.042 lb/ft³ at 60°F
        # Heat content ~21,500 BTU/lb
        mbh = app['mbh']
        btu_per_min = mbh * 1000 / 60
        
        if app['fuel_type'] == 'natural_gas':
            fuel_mass = btu_per_min / 21500  # lb/min
        elif app['fuel_type'] == 'lp_gas':
            fuel_mass = btu_per_min / 21000  # lb/min (propane)
        else:  # oil
            fuel_mass = btu_per_min / 19500  # lb/min (#2 fuel oil)
        
        total_fuel_mass += fuel_mass
    
    # Combustion air mass
    combustion_air_mass = total_flue_mass - total_fuel_mass  # lb/min
    
    # Convert to CFM at ambient temperature
    rho_ambient = calc.air_density(temp_ambient_f)
    combustion_air_cfm = combustion_air_mass / rho_ambient
    
    return {
        'combustion_air_cfm': combustion_air_cfm,
        'flue_gas_mass': total_flue_mass,
        'fuel_mass': total_fuel_mass,
        'ambient_temp': temp_ambient_f
    }

def calculate_louver_sizing(combustion_air_cfm):
    """
    Calculate louver requirements
    
    Single Louver: One louver with free area for max 2000 fpm
    Two Louver: Upper and lower louvers (each sized separately)
    """
    # Typical louver free area: 75% (0.75)
    free_area_ratio = 0.75
    max_velocity_fpm = 2000
    
    # Single louver method
    required_free_area_single = combustion_air_cfm / max_velocity_fpm  # sq ft
    louver_size_single = required_free_area_single / free_area_ratio  # sq ft
    
    # Two louver method (each louver gets full CFM capacity)
    required_free_area_each = combustion_air_cfm / max_velocity_fpm  # sq ft
    louver_size_each = required_free_area_each / free_area_ratio  # sq ft
    
    return {
        'single_louver': {
            'free_area_sqft': required_free_area_single,
            'free_area_sqin': required_free_area_single * 144,
            'louver_size_sqft': louver_size_single,
            'louver_size_sqin': louver_size_single * 144,
            'recommended_dimensions': suggest_louver_size(louver_size_single * 144)
        },
        'two_louver': {
            'free_area_each_sqft': required_free_area_each,
            'free_area_each_sqin': required_free_area_each * 144,
            'louver_size_each_sqft': louver_size_each,
            'louver_size_each_sqin': louver_size_each * 144,
            'recommended_dimensions': suggest_louver_size(louver_size_each * 144)
        }
    }

def suggest_louver_size(area_sqin):
    """Suggest standard louver dimensions"""
    # Standard louver sizes
    standard_sizes = [
        (12, 12), (12, 18), (12, 24), (18, 18), (18, 24), (18, 30),
        (24, 24), (24, 30), (24, 36), (30, 30), (30, 36), (36, 36)
    ]
    
    for w, h in standard_sizes:
        if w * h >= area_sqin:
            return f"{w}\" × {h}\""
    
    # If larger than standard, calculate
    side = int((area_sqin ** 0.5) / 6 + 1) * 6  # Round up to nearest 6"
    return f"{side}\" × {side}\""

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'project_name'
if 'data' not in st.session_state:
    st.session_state.data = {}

# Custom CSS for buttons
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 50px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.title("🔥 CARL")
st.caption("Chimney Analysis and Reasoning Layer")
st.markdown("---")

# ============================================================================
# CONVERSATION FLOW WITH BUTTONS
# ============================================================================

# STEP: Project Name
if st.session_state.step == 'project_name':
    st.subheader("📋 Project Information")
    st.write("Let's start by getting some basic information about your project.")
    
    project_name = st.text_input("Project Name:", placeholder="e.g., Smith Building Boiler Room")
    
    if st.button("➡️ Next", key="btn_project_name", use_container_width=True):
        if project_name:
            st.session_state.data['project_name'] = project_name
            st.session_state.step = 'zip_code'
            st.rerun()
        else:
            st.error("Please enter a project name")

# STEP: Zip Code
elif st.session_state.step == 'zip_code':
    st.subheader("📍 Location")
    st.write(f"**Project:** {st.session_state.data['project_name']}")
    
    zip_code = st.text_input("Enter ZIP Code:", placeholder="e.g., 76111")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_zip_back"):
            st.session_state.step = 'project_name'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_zip_next", use_container_width=True):
            if zip_code:
                location = lookup_zip(zip_code)
                if location:
                    st.session_state.data['zip_code'] = zip_code
                    st.session_state.data['city'] = location['city']
                    st.session_state.data['state'] = location['state']
                    st.session_state.data['elevation_ft'] = location['elevation']
                    st.session_state.data['barometric_pressure'] = elevation_to_pressure(location['elevation'])
                    st.session_state.step = 'vent_type'
                    st.rerun()
                else:
                    st.error("ZIP code not found. Please enter elevation manually.")
                    manual_city = st.text_input("City:", placeholder="City name")
                    manual_state = st.text_input("State:", placeholder="TX", max_chars=2)
                    manual_elev = st.number_input("Elevation (ft):", min_value=0, max_value=15000, value=0)
                    if st.button("Submit Manual Entry"):
                        if manual_city and manual_state:
                            st.session_state.data['zip_code'] = zip_code
                            st.session_state.data['city'] = manual_city
                            st.session_state.data['state'] = manual_state
                            st.session_state.data['elevation_ft'] = manual_elev
                            st.session_state.data['barometric_pressure'] = elevation_to_pressure(manual_elev)
                            st.session_state.step = 'vent_type'
                            st.rerun()
            else:
                st.error("Please enter a ZIP code")

# STEP: Vent Type
elif st.session_state.step == 'vent_type':
    st.subheader("🔧 Chimney/Vent Type")
    st.write(f"**Project:** {st.session_state.data['project_name']}")
    st.write(f"**Location:** {st.session_state.data['city']}, {st.session_state.data['state']}")
    st.write(f"**Elevation:** {st.session_state.data['elevation_ft']:,} ft (Barometric: {st.session_state.data['barometric_pressure']:.2f} in Hg)")
    
    st.write("\nSelect the chimney/vent type:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("UL441 Type B Vent", key="vent_ul441", use_container_width=True):
            st.session_state.data['vent_type'] = 'UL441 Type B Vent'
            st.session_state.step = 'num_appliances'
            st.rerun()
        if st.button("UL103 Pressure Chimney", key="vent_ul103", use_container_width=True):
            st.session_state.data['vent_type'] = 'UL103 Pressure Chimney'
            st.session_state.step = 'num_appliances'
            st.rerun()
    
    with col2:
        if st.button("UL1738 Special Gas Vent", key="vent_ul1738", use_container_width=True):
            st.session_state.data['vent_type'] = 'UL1738 Special Gas Vent'
            st.session_state.step = 'num_appliances'
            st.rerun()
        if st.button("⬅️ Back", key="btn_vent_back", use_container_width=True):
            st.session_state.step = 'zip_code'
            st.rerun()

# STEP: Number of Appliances
elif st.session_state.step == 'num_appliances':
    st.subheader("🔥 Appliance Configuration")
    st.write(f"**Vent Type:** {st.session_state.data['vent_type']}")
    
    st.write("How many appliances will be vented into this common system?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1 Appliance", key="num_1", use_container_width=True):
            st.session_state.data['num_appliances'] = 1
            st.session_state.step = 'ambient_temp'
            st.rerun()
        if st.button("4 Appliances", key="num_4", use_container_width=True):
            st.session_state.data['num_appliances'] = 4
            st.session_state.step = 'ambient_temp'
            st.rerun()
    
    with col2:
        if st.button("2 Appliances", key="num_2", use_container_width=True):
            st.session_state.data['num_appliances'] = 2
            st.session_state.step = 'ambient_temp'
            st.rerun()
        if st.button("5 Appliances", key="num_5", use_container_width=True):
            st.session_state.data['num_appliances'] = 5
            st.session_state.step = 'ambient_temp'
            st.rerun()
    
    with col3:
        if st.button("3 Appliances", key="num_3", use_container_width=True):
            st.session_state.data['num_appliances'] = 3
            st.session_state.step = 'ambient_temp'
            st.rerun()
        if st.button("6 Appliances", key="num_6", use_container_width=True):
            st.session_state.data['num_appliances'] = 6
            st.session_state.step = 'ambient_temp'
            st.rerun()
    
    if st.button("⬅️ Back", key="btn_num_back", use_container_width=True):
        st.session_state.step = 'vent_type'
        st.rerun()

# STEP: Ambient Temperature
elif st.session_state.step == 'ambient_temp':
    st.subheader("🌡️ Design Conditions")
    st.write(f"**{st.session_state.data['num_appliances']} Appliance(s)** on **{st.session_state.data['vent_type']}**")
    
    temp = st.number_input("Outside Air Temperature (°F):", min_value=-20.0, max_value=120.0, value=70.0, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_temp_back"):
            st.session_state.step = 'num_appliances'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_temp_next", use_container_width=True):
            st.session_state.data['temp_outside_f'] = temp
            if st.session_state.data['num_appliances'] > 1:
                st.session_state.step = 'same_appliances'
            else:
                st.session_state.step = 'appliance_1_mbh'
                st.session_state.data['appliances'] = []
            st.rerun()


# STEP: Same Appliances Question
elif st.session_state.step == 'same_appliances':
    st.subheader("⚙️ Appliance Setup")
    st.write(f"You have **{st.session_state.data['num_appliances']} appliances** to configure.")
    
    st.write("Are all appliances identical?")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Back", key="btn_same_back"):
            st.session_state.step = 'ambient_temp'
            st.rerun()
    with col2:
        if st.button("✅ Yes - All Identical", key="btn_same_yes", use_container_width=True):
            st.session_state.data['same_appliances'] = True
            st.session_state.data['appliances'] = []
            st.session_state.step = 'appliance_1_mbh'
            st.rerun()
    with col3:
        if st.button("❌ No - Configure Each", key="btn_same_no", use_container_width=True):
            st.session_state.data['same_appliances'] = False
            st.session_state.data['appliances'] = []
            st.session_state.step = 'appliance_1_mbh'
            st.rerun()

# Helper function to get current appliance number
def get_current_appliance_num():
    return len(st.session_state.data.get('appliances', [])) + 1

# STEP: Appliance MBH Input
elif st.session_state.step == 'appliance_1_mbh':
    app_num = get_current_appliance_num()
    st.subheader(f"🔥 Appliance #{app_num} Configuration")
    if st.session_state.data.get('same_appliances'):
        st.info("This configuration will be applied to all appliances")
    
    mbh = st.number_input("Input Rating (MBH):", min_value=1.0, value=100.0, step=10.0)
    outlet_dia = st.number_input("Appliance Outlet Diameter (inches):", min_value=3.0, max_value=24.0, value=6.0, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_mbh_back"):
            if st.session_state.data['num_appliances'] > 1:
                st.session_state.step = 'same_appliances'
            else:
                st.session_state.step = 'ambient_temp'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_mbh_next", use_container_width=True):
            st.session_state.data['current_mbh'] = mbh
            st.session_state.data['current_outlet'] = outlet_dia
            st.session_state.step = 'appliance_1_category'
            st.rerun()

# STEP: Appliance Category
elif st.session_state.step == 'appliance_1_category':
    app_num = get_current_appliance_num()
    st.subheader(f"🔥 Appliance #{app_num} - Category")
    st.write(f"**Input:** {st.session_state.data['current_mbh']} MBH")
    st.write(f"**Outlet:** {st.session_state.data['current_outlet']}\"")
    
    st.write("Select appliance category:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Category I - Fan Assisted", key="cat_i", use_container_width=True):
            st.session_state.data['current_category'] = 'cat_i_fan'
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
        if st.button("Category III - Non-Condensing", key="cat_iii", use_container_width=True):
            st.session_state.data['current_category'] = 'cat_iii'
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
        if st.button("Building Heating Appliance", key="cat_bldg", use_container_width=True):
            st.session_state.data['current_category'] = 'building_heating'
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
    
    with col2:
        if st.button("Category II - Non-Condensing", key="cat_ii", use_container_width=True):
            st.session_state.data['current_category'] = 'cat_ii'
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
        if st.button("Category IV - Condensing", key="cat_iv", use_container_width=True):
            st.session_state.data['current_category'] = 'cat_iv'
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
        if st.button("⬅️ Back", key="btn_cat_back", use_container_width=True):
            st.session_state.step = 'appliance_1_mbh'
            st.rerun()

# STEP: Custom Values or Generic
elif st.session_state.step == 'appliance_1_custom':
    app_num = get_current_appliance_num()
    cat_key = st.session_state.data['current_category']
    cat_info = calc.appliance_categories[cat_key]
    
    st.subheader(f"🔥 Appliance #{app_num} - Combustion Data")
    st.write(f"**Category:** {cat_info['name']}")
    st.write(f"**Generic Values:** {cat_info['co2_default']}% CO₂, {cat_info['temp_default']}°F")
    
    st.write("Would you like to use generic values or enter custom data?")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Back", key="btn_custom_back"):
            st.session_state.step = 'appliance_1_category'
            st.rerun()
    with col2:
        if st.button("📊 Use Generic", key="btn_generic", use_container_width=True):
            st.session_state.data['current_co2'] = cat_info['co2_default']
            st.session_state.data['current_temp'] = cat_info['temp_default']
            st.session_state.step = 'appliance_1_fuel'
            st.rerun()
    with col3:
        if st.button("✏️ Enter Custom", key="btn_custom", use_container_width=True):
            st.session_state.step = 'appliance_1_co2'
            st.rerun()

# STEP: Custom CO2
elif st.session_state.step == 'appliance_1_co2':
    app_num = get_current_appliance_num()
    st.subheader(f"🔥 Appliance #{app_num} - Custom CO₂")
    
    co2 = st.number_input("CO₂ Percentage (from combustion analyzer):", min_value=1.0, max_value=15.0, value=8.5, step=0.1)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_co2_back"):
            st.session_state.step = 'appliance_1_custom'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_co2_next", use_container_width=True):
            st.session_state.data['current_co2'] = co2
            st.session_state.step = 'appliance_1_temp_custom'
            st.rerun()

# STEP: Custom Temperature
elif st.session_state.step == 'appliance_1_temp_custom':
    app_num = get_current_appliance_num()
    st.subheader(f"🔥 Appliance #{app_num} - Flue Gas Temperature")
    st.write(f"**CO₂:** {st.session_state.data['current_co2']}%")
    
    temp = st.number_input("Flue Gas Temperature (°F):", min_value=100.0, max_value=600.0, value=300.0, step=5.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_temp_custom_back"):
            st.session_state.step = 'appliance_1_co2'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_temp_custom_next", use_container_width=True):
            st.session_state.data['current_temp'] = temp
            st.session_state.step = 'appliance_1_fuel'
            st.rerun()

# STEP: Fuel Type
elif st.session_state.step == 'appliance_1_fuel':
    app_num = get_current_appliance_num()
    st.subheader(f"🔥 Appliance #{app_num} - Fuel Type")
    st.write(f"**CO₂:** {st.session_state.data['current_co2']}%")
    st.write(f"**Temperature:** {st.session_state.data['current_temp']}°F")
    
    st.write("Select fuel type:")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Back", key="btn_fuel_back"):
            if 'current_co2' in st.session_state.data:
                st.session_state.step = 'appliance_1_temp_custom'
            else:
                st.session_state.step = 'appliance_1_custom'
            st.rerun()
    with col2:
        if st.button("🔥 Natural Gas", key="fuel_ng", use_container_width=True):
            st.session_state.data['current_fuel'] = 'natural_gas'
            st.session_state.step = 'save_appliance'
            st.rerun()
        if st.button("⛽ Oil", key="fuel_oil", use_container_width=True):
            st.session_state.data['current_fuel'] = 'oil'
            st.session_state.step = 'save_appliance'
            st.rerun()
    with col3:
        if st.button("🔥 LP Gas (Propane)", key="fuel_lp", use_container_width=True):
            st.session_state.data['current_fuel'] = 'lp_gas'
            st.session_state.step = 'save_appliance'
            st.rerun()


# STEP: Save Appliance and Check if More Needed
elif st.session_state.step == 'save_appliance':
    # Build appliance object
    appliance = {
        'mbh': st.session_state.data['current_mbh'],
        'outlet_diameter': st.session_state.data['current_outlet'],
        'co2_percent': st.session_state.data['current_co2'],
        'temp_f': st.session_state.data['current_temp'],
        'category': st.session_state.data['current_category'],
        'fuel_type': st.session_state.data['current_fuel'],
        'appliance_number': get_current_appliance_num()
    }
    
    # Add to list
    if 'appliances' not in st.session_state.data:
        st.session_state.data['appliances'] = []
    
    st.session_state.data['appliances'].append(appliance)
    
    # If same appliances, duplicate to all
    if st.session_state.data.get('same_appliances') and len(st.session_state.data['appliances']) == 1:
        num_needed = st.session_state.data['num_appliances']
        for i in range(2, num_needed + 1):
            dup_app = appliance.copy()
            dup_app['appliance_number'] = i
            st.session_state.data['appliances'].append(dup_app)
    
    # Clear current appliance data
    for key in ['current_mbh', 'current_outlet', 'current_co2', 'current_temp', 'current_category', 'current_fuel']:
        if key in st.session_state.data:
            del st.session_state.data[key]
    
    # Check if more appliances needed
    if len(st.session_state.data['appliances']) < st.session_state.data['num_appliances']:
        st.session_state.step = 'appliance_1_mbh'
        st.rerun()
    else:
        st.session_state.step = 'connector_which'
        st.rerun()

# STEP: Select Worst-Case Connector
elif st.session_state.step == 'connector_which':
    st.subheader("🔌 Connector Configuration")
    st.write("Which appliance has the worst-case connector (longest run, most fittings)?")
    
    # Show appliances
    for app in st.session_state.data['appliances']:
        if st.button(f"Appliance #{app['appliance_number']} ({app['mbh']} MBH)", 
                     key=f"select_app_{app['appliance_number']}", use_container_width=True):
            st.session_state.data['worst_connector_app'] = app['appliance_number'] - 1
            st.session_state.step = 'connector_diameter'
            st.rerun()
    
    if st.button("⬅️ Back", key="btn_connector_which_back", use_container_width=True):
        st.session_state.data['appliances'] = []
        if st.session_state.data['num_appliances'] > 1:
            st.session_state.step = 'same_appliances'
        else:
            st.session_state.step = 'appliance_1_mbh'
        st.rerun()

# STEP: Connector Diameter
elif st.session_state.step == 'connector_diameter':
    app_idx = st.session_state.data['worst_connector_app']
    app = st.session_state.data['appliances'][app_idx]
    min_dia = app['outlet_diameter']
    
    st.subheader("🔌 Connector - Diameter")
    st.write(f"**Appliance #{app['appliance_number']}:** {app['mbh']} MBH")
    st.info(f"⚠️ Diameter must be at least {min_dia}\" (appliance outlet size)")
    
    dia = st.number_input("Connector Diameter (inches):", min_value=min_dia, max_value=24.0, value=min_dia, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_conn_dia_back"):
            st.session_state.step = 'connector_which'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_conn_dia_next", use_container_width=True):
            st.session_state.data['connector_diameter'] = dia
            st.session_state.step = 'connector_length'
            st.rerun()

# STEP: Connector Length
elif st.session_state.step == 'connector_length':
    st.subheader("🔌 Connector - Length")
    st.write(f"**Diameter:** {st.session_state.data['connector_diameter']}\"")
    
    length = st.number_input("Total Connector Length (ft):", min_value=0.1, value=10.0, step=1.0)
    height = st.number_input("Vertical Height/Rise (ft):", min_value=0.0, value=0.0, step=1.0, 
                            help="Portion of connector that is vertical (contributes to draft)")
    
    if height > length:
        st.error("Height cannot be greater than total length!")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="btn_conn_len_back"):
                st.session_state.step = 'connector_diameter'
                st.rerun()
        with col2:
            if st.button("➡️ Next", key="btn_conn_len_next", use_container_width=True):
                st.session_state.data['connector_length'] = length
                st.session_state.data['connector_height'] = height
                st.session_state.step = 'connector_fittings'
                st.rerun()

# STEP: Connector Fittings
elif st.session_state.step == 'connector_fittings':
    st.subheader("🔌 Connector - Fittings")
    st.write(f"**Length:** {st.session_state.data['connector_length']} ft (Height: {st.session_state.data['connector_height']} ft)")
    
    st.write("Enter the number of each fitting type:")
    
    col1, col2 = st.columns(2)
    with col1:
        num_90 = st.number_input("90° Elbows:", min_value=0, max_value=10, value=0, step=1)
        num_45 = st.number_input("45° Elbows:", min_value=0, max_value=10, value=0, step=1)
        num_30 = st.number_input("30° Elbows:", min_value=0, max_value=10, value=0, step=1)
    with col2:
        num_90tee = st.number_input("90° Tees (flow through):", min_value=0, max_value=10, value=0, step=1)
        num_45tee = st.number_input("45° Lateral Tees:", min_value=0, max_value=10, value=0, step=1)
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", key="btn_conn_fit_back"):
            st.session_state.step = 'connector_length'
            st.rerun()
    with col_next:
        if st.button("➡️ Next", key="btn_conn_fit_next", use_container_width=True):
            fittings = {'entrance': 1}
            if num_90 > 0: fittings['90_elbow'] = int(num_90)
            if num_45 > 0: fittings['45_elbow'] = int(num_45)
            if num_30 > 0: fittings['30_elbow'] = int(num_30)
            if num_90tee > 0: fittings['90_tee_flow_through'] = int(num_90tee)
            if num_45tee > 0: fittings['45_tee_lateral'] = int(num_45tee)
            
            st.session_state.data['connector_fittings'] = fittings
            st.session_state.step = 'manifold_optimize'
            st.rerun()

# STEP: Optimize Manifold Diameter
elif st.session_state.step == 'manifold_optimize':
    st.subheader("🏗️ Common Vent (Manifold)")
    st.write("Would you like CARL to optimize the manifold diameter?")
    
    st.info("💡 CARL can suggest the optimal diameter based on velocity targets, or you can specify your own.")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Back", key="btn_man_opt_back"):
            st.session_state.step = 'connector_fittings'
            st.rerun()
    with col2:
        if st.button("✅ Optimize (CARL Suggests)", key="btn_optimize_yes", use_container_width=True):
            st.session_state.data['optimize_manifold'] = True
            st.session_state.step = 'manifold_height'
            st.rerun()
    with col3:
        if st.button("✏️ I'll Select Diameter", key="btn_optimize_no", use_container_width=True):
            st.session_state.data['optimize_manifold'] = False
            st.session_state.step = 'manifold_diameter'
            st.rerun()

# STEP: Manifold Diameter (if user selects)
elif st.session_state.step == 'manifold_diameter':
    st.subheader("🏗️ Manifold - Diameter")
    
    dia = st.number_input("Common Vent Diameter (inches):", min_value=6.0, max_value=48.0, value=12.0, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_man_dia_back"):
            st.session_state.step = 'manifold_optimize'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_man_dia_next", use_container_width=True):
            st.session_state.data['manifold_diameter'] = dia
            st.session_state.step = 'manifold_height'
            st.rerun()

# STEP: Manifold Height and Length
elif st.session_state.step == 'manifold_height':
    st.subheader("🏗️ Manifold - Dimensions")
    
    # If optimizing, calculate suggested diameter
    if st.session_state.data.get('optimize_manifold'):
        combined = calc.calculate_combined_cfm(st.session_state.data['appliances'])
        total_cfm = combined['total_cfm']
        
        # Find optimal diameter (target 8-20 ft/s = 480-1200 fpm)
        standard_sizes = [6, 7, 8, 10, 12, 14, 16, 18, 20, 24, 30, 36]
        suggested_dia = None
        for d in standard_sizes:
            vel = calc.velocity_from_cfm(total_cfm, d)
            if 8 <= vel <= 20:
                suggested_dia = d
                suggested_vel = vel * 60
                break
        
        if suggested_dia is None:
            suggested_dia = 12
            suggested_vel = calc.velocity_from_cfm(total_cfm, suggested_dia) * 60
        
        st.success(f"💡 **CARL Suggests:** {suggested_dia}\" diameter")
        st.write(f"For {total_cfm:.0f} CFM → ~{suggested_vel:.0f} ft/min velocity")
        st.session_state.data['manifold_diameter'] = suggested_dia
    else:
        st.write(f"**Diameter:** {st.session_state.data['manifold_diameter']}\"")
    
    height = st.number_input("Vertical Height (ft):", min_value=1.0, value=35.0, step=1.0)
    horiz = st.number_input("Horizontal Run (ft):", min_value=0.0, value=5.0, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_man_height_back"):
            if st.session_state.data.get('optimize_manifold'):
                st.session_state.step = 'manifold_optimize'
            else:
                st.session_state.step = 'manifold_diameter'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_man_height_next", use_container_width=True):
            st.session_state.data['manifold_height'] = height
            st.session_state.data['manifold_horizontal'] = horiz
            st.session_state.step = 'manifold_fittings'
            st.rerun()

# STEP: Manifold Fittings
elif st.session_state.step == 'manifold_fittings':
    st.subheader("🏗️ Manifold - Fittings")
    total_length = st.session_state.data['manifold_height'] + st.session_state.data['manifold_horizontal']
    st.write(f"**Total Length:** {total_length} ft ({st.session_state.data['manifold_height']} ft vertical + {st.session_state.data['manifold_horizontal']} ft horizontal)")
    
    st.write("Enter the number of each fitting type:")
    
    col1, col2 = st.columns(2)
    with col1:
        num_90 = st.number_input("90° Elbows:", min_value=0, max_value=10, value=0, step=1, key="man_90")
        num_45 = st.number_input("45° Elbows:", min_value=0, max_value=10, value=0, step=1, key="man_45")
        num_30 = st.number_input("30° Elbows:", min_value=0, max_value=10, value=0, step=1, key="man_30")
    with col2:
        num_90tee = st.number_input("90° Tees (flow through):", min_value=0, max_value=10, value=0, step=1, key="man_90tee")
        num_45tee = st.number_input("45° Lateral Tees:", min_value=0, max_value=10, value=0, step=1, key="man_45tee")
    
    has_cap = st.checkbox("Termination Cap?", value=True)
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", key="btn_man_fit_back"):
            st.session_state.step = 'manifold_height'
            st.rerun()
    with col_next:
        if st.button("🔍 Run Analysis", key="btn_run_analysis", use_container_width=True):
            fittings = {'exit': 1}
            if num_90 > 0: fittings['90_elbow'] = int(num_90)
            if num_45 > 0: fittings['45_elbow'] = int(num_45)
            if num_30 > 0: fittings['30_elbow'] = int(num_30)
            if num_90tee > 0: fittings['90_tee_flow_through'] = int(num_90tee)
            if num_45tee > 0: fittings['45_tee_lateral'] = int(num_45tee)
            if has_cap: fittings['termination_cap'] = 1
            
            st.session_state.data['manifold_fittings'] = fittings
            st.session_state.step = 'analyzing'
            st.rerun()


# STEP: Analyzing
elif st.session_state.step == 'analyzing':
    st.subheader("🔍 Analyzing System...")
    
    with st.spinner("Running calculations..."):
        try:
            # Build connector configs for all appliances
            connector_configs = []
            for app in st.session_state.data['appliances']:
                connector_configs.append({
                    'diameter_inches': st.session_state.data['connector_diameter'],
                    'length_ft': st.session_state.data['connector_length'],
                    'height_ft': st.session_state.data['connector_height'],
                    'fittings': st.session_state.data['connector_fittings'].copy()
                })
            
            # Build manifold config
            manifold_config = {
                'diameter_inches': st.session_state.data['manifold_diameter'],
                'height_ft': st.session_state.data['manifold_height'],
                'length_ft': st.session_state.data['manifold_height'] + st.session_state.data['manifold_horizontal'],
                'fittings': st.session_state.data['manifold_fittings']
            }
            
            # Run analysis
            result = calc.complete_multi_appliance_analysis(
                appliances=st.session_state.data['appliances'],
                connector_configs=connector_configs,
                manifold_config=manifold_config,
                temp_outside_f=st.session_state.data['temp_outside_f']
            )
            
            # Calculate combustion air
            comb_air = calculate_combustion_air(
                st.session_state.data['appliances'],
                st.session_state.data['temp_outside_f']
            )
            
            # Calculate louver sizing
            louvers = calculate_louver_sizing(comb_air['combustion_air_cfm'])
            
            # Save results
            st.session_state.data['results'] = result
            st.session_state.data['combustion_air'] = comb_air
            st.session_state.data['louvers'] = louvers
            st.session_state.step = 'results'
            st.rerun()
            
        except Exception as e:
            st.error(f"Analysis Error: {str(e)}")
            st.write("Please check your inputs and try again.")
            if st.button("⬅️ Back to Manifold", key="btn_error_back"):
                st.session_state.step = 'manifold_fittings'
                st.rerun()

# STEP: Results
elif st.session_state.step == 'results':
    st.subheader("✅ Analysis Complete")
    
    result = st.session_state.data['results']
    worst = result['worst_case']['worst_case']
    
    # Project Header
    st.markdown("---")
    st.markdown(f"### 📋 {st.session_state.data['project_name']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Location:** {st.session_state.data['city']}, {st.session_state.data['state']}")
        st.write(f"**ZIP:** {st.session_state.data['zip_code']}")
    with col2:
        st.write(f"**Elevation:** {st.session_state.data['elevation_ft']:,} ft")
        st.write(f"**Barometric:** {st.session_state.data['barometric_pressure']:.2f} in Hg")
    with col3:
        st.write(f"**Vent Type:** {st.session_state.data['vent_type']}")
        st.write(f"**Outside Temp:** {st.session_state.data['temp_outside_f']}°F")
    
    st.markdown("---")
    
    # Appliances Summary
    st.markdown("### 🔥 Appliances")
    total_mbh = sum(app['mbh'] for app in st.session_state.data['appliances'])
    st.write(f"**Total Input:** {total_mbh:,.0f} MBH ({st.session_state.data['num_appliances']} appliances)")
    
    for app in st.session_state.data['appliances']:
        cat_name = calc.appliance_categories[app['category']]['name']
        st.write(f"**Appliance #{app['appliance_number']}:** {app['mbh']} MBH | {cat_name} | {app['co2_percent']}% CO₂ | {app['temp_f']}°F | {app['fuel_type'].replace('_', ' ').title()}")
    
    st.markdown("---")
    
    # Connector Configuration
    st.markdown("### 🔌 Connector Configuration")
    st.write(f"**Worst-Case:** Appliance #{worst['appliance_id']}")
    st.write(f"**Diameter:** {st.session_state.data['connector_diameter']}\"")
    st.write(f"**Length:** {st.session_state.data['connector_length']} ft (Height: {st.session_state.data['connector_height']} ft)")
    
    fittings_list = []
    for fitting, count in st.session_state.data['connector_fittings'].items():
        if fitting != 'entrance':
            fittings_list.append(f"{count} {fitting.replace('_', ' ')}")
    st.write(f"**Fittings:** {', '.join(fittings_list) if fittings_list else 'Entrance only'}")
    
    st.markdown("---")
    
    # Manifold Configuration
    st.markdown("### 🏗️ Common Vent (Manifold)")
    st.write(f"**Diameter:** {st.session_state.data['manifold_diameter']}\" {'(Optimized by CARL)' if st.session_state.data.get('optimize_manifold') else '(User Selected)'}")
    st.write(f"**Vertical Height:** {st.session_state.data['manifold_height']} ft")
    st.write(f"**Horizontal Run:** {st.session_state.data['manifold_horizontal']} ft")
    st.write(f"**Total Length:** {st.session_state.data['manifold_height'] + st.session_state.data['manifold_horizontal']} ft")
    
    fittings_list = []
    for fitting, count in st.session_state.data['manifold_fittings'].items():
        if fitting != 'exit':
            fittings_list.append(f"{count} {fitting.replace('_', ' ')}")
    st.write(f"**Fittings:** {', '.join(fittings_list) if fittings_list else 'Exit only'}")
    
    st.markdown("---")
    
    # Analysis Results
    st.markdown("### 📊 Venting Analysis")
    
    # Worst Case Connector
    st.write("**Worst Case Connector:**")
    st.write(f"- Appliance: #{worst['appliance_id']} ({worst['appliance']['mbh']} MBH)")
    st.write(f"- Draft: {worst['connector_draft']:.4f} in w.c.")
    st.write(f"- Velocity: {worst['connector_result']['connector']['velocity_fps'] * 60:.0f} ft/min")
    
    st.write("")
    st.write("**Operating Scenarios:**")
    
    scenarios = [
        ('All Appliances', result['all_operating']),
        ('All Minus One', result['all_minus_one']),
        ('Single Largest', result['single_largest']),
        ('Single Smallest', result['single_smallest'])
    ]
    
    for name, scenario in scenarios:
        if scenario:
            cfm = scenario['combined']['total_cfm']
            vel = scenario['common_vent']['velocity_fps'] * 60
            draft = scenario['common_vent']['available_draft_inwc']
            st.write(f"- **{name}:** {cfm:.1f} CFM, {vel:.0f} ft/min, {draft:.4f} in w.c.")
    
    st.write("")
    st.write("**Total System (Connector + Manifold):**")
    st.write(f"- Connector Draft: {worst['connector_draft']:.4f} in w.c.")
    st.write(f"- Manifold Draft: {worst['manifold_draft']:.4f} in w.c.")
    st.write(f"- **TOTAL AVAILABLE DRAFT: {worst['total_available_draft']:.4f} in w.c.**")
    
    # Atmospheric pressure
    atm_pressure = -worst['total_available_draft']
    st.write(f"- **Atmospheric Pressure at Appliance: {atm_pressure:.4f} in w.c.**")
    
    st.info("⚠️ **IMPORTANT:** Positive draft (+) = Negative atmospheric pressure (-) | Negative draft (-) = Positive atmospheric pressure (+)")
    
    # Category compliance
    if worst['appliance']['category'] != 'custom':
        cat_info = calc.appliance_categories[worst['appliance']['category']]
        cat_limits = cat_info['pressure_range']
        
        st.write("")
        st.write("**Category Compliance:**")
        st.write(f"- Category: {cat_info['name']}")
        st.write(f"- Required Atmospheric Pressure: {cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c.")
        st.write(f"- Actual Atmospheric Pressure: {atm_pressure:.4f} in w.c.")
        
        if cat_limits[0] <= atm_pressure <= cat_limits[1]:
            st.success("✅ System meets category requirements")
        else:
            st.error("❌ System does NOT meet category requirements")
            st.write("**Recommendation:** US Draft Co. draft control required")
    
    st.markdown("---")
    
    # Seasonal Variation
    st.markdown("### 🌡️ Seasonal Draft Variation")
    available = result['all_operating']['common_vent']['available_draft_inwc']
    winter_draft = available * 1.4
    summer_draft = available * 0.6
    
    st.write("**Estimated Draft Variation:**")
    st.write(f"- Winter (0°F): ~{winter_draft:.4f} in w.c.")
    st.write(f"- Design ({st.session_state.data['temp_outside_f']}°F): ~{available:.4f} in w.c.")
    st.write(f"- Summer (95°F): ~{summer_draft:.4f} in w.c.")
    st.write(f"- **Variation Range:** {abs(winter_draft - summer_draft):.4f} in w.c. swing")
    
    st.warning("⚠️ US Draft Co. draft controls are REQUIRED for consistent year-round performance!")
    
    st.markdown("---")
    
    # Combustion Air
    st.markdown("### 💨 Combustion Air Requirements")
    comb_air = st.session_state.data['combustion_air']
    louvers = st.session_state.data['louvers']
    
    st.write(f"**Total Combustion Air:** {comb_air['combustion_air_cfm']:.0f} CFM at {comb_air['ambient_temp']}°F")
    
    st.write("")
    st.write("**Method 1: Single Louver**")
    st.write(f"- Required Free Area: {louvers['single_louver']['free_area_sqin']:.1f} sq in")
    st.write(f"- Louver Size (75% free area): {louvers['single_louver']['louver_size_sqin']:.1f} sq in")
    st.write(f"- **Recommended:** {louvers['single_louver']['recommended_dimensions']} louver")
    
    st.write("")
    st.write("**Method 2: Two Louver (High/Low)**")
    st.write(f"- Free Area Each: {louvers['two_louver']['free_area_each_sqin']:.1f} sq in")
    st.write(f"- Louver Size Each: {louvers['two_louver']['louver_size_each_sqin']:.1f} sq in")
    st.write(f"- **Recommended:** Two {louvers['two_louver']['recommended_dimensions']} louvers")
    st.write("  (One within 12\" of ceiling, one within 12\" of floor)")
    
    st.markdown("---")
    
    # US Draft Co. Recommendations
    st.markdown("### 🏢 US Draft Co. Product Recommendations")
    
    # Determine recommendation based on category and pressure
    if worst['appliance']['category'] in ['cat_ii', 'cat_iii', 'cat_iv']:
        st.write("**Recommended Product: CDS3 - Connector Draft System**")
        st.write("- Maintains precise pressure at appliance outlet")
        st.write("- EC-Flow Technology with 2-second actuator")
        st.write("- Required for Category II, III, and IV appliances")
        st.write("- 4\" color touchscreen interface")
    else:
        if atm_pressure < cat_limits[0]:
            st.write("**Recommended Product: Barometric Damper**")
            st.write("- Controls excessive draft")
            st.write("- Simple, reliable solution")
            st.write("- Cost-effective for Category I appliances")
        elif atm_pressure > cat_limits[1]:
            st.write("**Recommended Product: Draft Inducer**")
            st.write("- Overcomes insufficient natural draft")
            st.write("- Up to 0.75 in w.c. capacity")
            st.write("- Required when system cannot produce adequate draft")
        else:
            st.write("**System Status:** Within acceptable range")
            st.write("- Consider barometric damper for seasonal stability")
            st.write("- US Draft Co. controls ensure year-round performance")
    
    st.write("")
    st.write("**Contact US Draft Co.:**")
    st.write("📞 817-393-4029")
    st.write("🌐 www.usdraft.com")
    st.write("📍 100 S Sylvania Ave, Fort Worth, TX 76111")
    
    st.markdown("---")
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Analysis", key="btn_new_analysis", use_container_width=True):
            # Clear all data
            st.session_state.data = {}
            st.session_state.step = 'project_name'
            st.rerun()
    with col2:
        st.info("📄 PDF Report Generation - Coming Soon!")
        # if st.button("📄 Download PDF Report", key="btn_download_pdf", use_container_width=True):
        #     st.session_state.step = 'generate_pdf'
        #     st.rerun()

# Footer
st.markdown("---")
st.caption("CARL v1.0 Beta | US Draft by RM Manifold | 817-393-4029 | www.usdraft.com")
st.caption(f"Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

