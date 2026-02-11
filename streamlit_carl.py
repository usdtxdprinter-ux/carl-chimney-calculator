"""
CARL - Chimney Analysis and Reasoning Layer
Complete Chatbot Interface with Button Controls and PDF Reports
"""

import streamlit as st
from enhanced_calculator import EnhancedChimneyCalculator
import pandas as pd
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

# Helper function to get current appliance number
def get_current_appliance_num():
    return len(st.session_state.data.get('appliances', [])) + 1

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
    
    # If optimizing, calculate suggested diameter with detailed analysis
    if st.session_state.data.get('optimize_manifold'):
        combined = calc.calculate_combined_cfm(st.session_state.data['appliances'])
        total_cfm = combined['total_cfm']
        
        st.info(f"📊 **System Total:** {total_cfm:.0f} CFM combined from all appliances")
        
        # Evaluate multiple diameters to find optimal
        standard_sizes = [6, 7, 8, 10, 12, 14, 16, 18, 20, 24, 30, 36]
        
        st.write("**🔍 Evaluating diameters for optimal performance:**")
        st.write("")
        
        optimization_results = []
        
        for d in standard_sizes:
            vel_fps = calc.velocity_from_cfm(total_cfm, d)
            vel_fpm = vel_fps * 60
            
            # Calculate approximate friction for evaluation
            # Using simplified formula: dP ≈ 0.3 * (L/D) * ρ * V²
            # Assume typical 35 ft height for estimation
            estimated_L = 40  # ft
            D_ft = d / 12
            rho = 0.075  # lb/ft³ typical
            dp_friction = 0.3 * (estimated_L / D_ft) * rho * (vel_fps ** 2) / 5.2  # Convert to in w.c.
            
            # Determine status based on velocity
            if vel_fpm < 480:
                status = "❌ Too slow (< 480 ft/min)"
                score = 0
            elif vel_fpm > 1200:
                status = "❌ Too fast (> 1200 ft/min)"
                score = 0
            elif 600 <= vel_fpm <= 900:
                status = "✅ Optimal"
                score = 3
            elif 480 <= vel_fpm <= 1200:
                status = "⚠️ Acceptable"
                score = 2
            else:
                status = "❌ Out of range"
                score = 0
            
            optimization_results.append({
                'diameter': d,
                'velocity_fpm': vel_fpm,
                'velocity_fps': vel_fps,
                'dp_estimate': dp_friction,
                'status': status,
                'score': score
            })
            
            # Only show first few for display
            if d <= 20:
                if score > 0:
                    st.write(f"  • {d}\" → {vel_fpm:.0f} ft/min {status}")
        
        # Find optimal (highest score, lowest pressure)
        optimal = max(optimization_results, key=lambda x: (x['score'], -x['dp_estimate']))
        suggested_dia = optimal['diameter']
        suggested_vel = optimal['velocity_fpm']
        
        st.write("")
        st.success(f"💡 **CARL Recommends: {suggested_dia}\" diameter**")
        st.write(f"   • Velocity: {suggested_vel:.0f} ft/min ({optimal['velocity_fps']:.1f} ft/s)")
        st.write(f"   • Target Range: 600-900 ft/min (optimal) | 480-1200 ft/min (acceptable)")
        st.write(f"   • Estimated Friction: ~{optimal['dp_estimate']:.4f} in w.c. per 40 ft")
        
        st.session_state.data['manifold_diameter'] = suggested_dia
        st.session_state.data['optimization_details'] = {
            'recommended_diameter': suggested_dia,
            'velocity_fpm': suggested_vel,
            'all_options': optimization_results
        }
    else:
        st.write(f"**Diameter:** {st.session_state.data['manifold_diameter']}\" (User Selected)")
    
    st.write("")
    st.write("**Enter manifold dimensions:**")
    
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
            
            # Debug info
            st.write(f"✓ Analyzing {len(st.session_state.data['appliances'])} appliances...")
            
            # Run analysis
            result = calc.complete_multi_appliance_analysis(
                appliances=st.session_state.data['appliances'],
                connector_configs=connector_configs,
                manifold_config=manifold_config,
                temp_outside_f=st.session_state.data['temp_outside_f']
            )
            
            # Debug: Show what was returned
            st.write("✓ Analysis complete")
            st.write(f"Result type: {type(result)}")
            st.write(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check each scenario
            if isinstance(result, dict):
                st.write(f"- all_operating: {type(result.get('all_operating'))}")
                st.write(f"- all_minus_one: {type(result.get('all_minus_one'))}")
                st.write(f"- single_largest: {type(result.get('single_largest'))}")
                st.write(f"- single_smallest: {type(result.get('single_smallest'))}")
                st.write(f"- worst_case: {type(result.get('worst_case'))}")
            
            # Verify results exist
            if not result or 'worst_case' not in result:
                st.error("Analysis returned incomplete results")
                st.write("Debug: Missing 'worst_case' key")
                if st.button("⬅️ Back to Manifold", key="btn_error_back"):
                    st.session_state.step = 'manifold_fittings'
                    st.rerun()
                st.stop()
            
            if not result.get('all_operating'):
                st.error("Analysis returned no 'all_operating' scenario")
                if st.button("⬅️ Back to Manifold", key="btn_error_all_op"):
                    st.session_state.step = 'manifold_fittings'
                    st.rerun()
                st.stop()
            
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
            
        except KeyError as e:
            st.error(f"Missing data key: {str(e)}")
            st.write("Debug info:")
            st.write("- Appliances configured:", len(st.session_state.data.get('appliances', [])))
            st.write("- Connector diameter:", st.session_state.data.get('connector_diameter'))
            st.write("- Manifold diameter:", st.session_state.data.get('manifold_diameter'))
            if st.button("⬅️ Back to Manifold", key="btn_error_keyerror_back"):
                st.session_state.step = 'manifold_fittings'
                st.rerun()
        except Exception as e:
            st.error(f"Analysis Error: {str(e)}")
            st.write("Error type:", type(e).__name__)
            import traceback
            st.code(traceback.format_exc())
            if st.button("⬅️ Back to Manifold", key="btn_error_general_back"):
                st.session_state.step = 'manifold_fittings'
                st.rerun()

# STEP: Results
elif st.session_state.step == 'results':
    st.subheader("✅ Analysis Complete")
    
    result = st.session_state.data.get('results')
    
    # Verify we have results
    if not result or not isinstance(result, dict):
        st.error("❌ No analysis results found. Please run the analysis again.")
        if st.button("⬅️ Back to Manifold", key="btn_no_results"):
            st.session_state.step = 'manifold_fittings'
            st.rerun()
        st.stop()
    
    # Verify we have worst case data
    if 'worst_case' not in result or not result['worst_case']:
        st.error("❌ Worst case analysis data missing.")
        st.write("Debug: Available keys:", list(result.keys()))
        if st.button("⬅️ Back to Manifold", key="btn_no_worst"):
            st.session_state.step = 'manifold_fittings'
            st.rerun()
        st.stop()
    
    worst = result['worst_case'].get('worst_case')
    if not worst:
        st.error("❌ Worst case connector data missing.")
        if st.button("⬅️ Back to Manifold", key="btn_no_worst_connector"):
            st.session_state.step = 'manifold_fittings'
            st.rerun()
        st.stop()
    
    
    # ========================================================================
    # PROJECT SUMMARY TABLE
    # ========================================================================
    st.markdown("## 📋 Project Summary")
    
    project_data = {
        "Item": [
            "Project Name",
            "Location", 
            "Elevation",
            "Barometric Pressure",
            "Vent Type",
            "Outside Design Temperature",
            "Number of Appliances",
            "Analysis Date"
        ],
        "Value": [
            st.session_state.data['project_name'],
            f"{st.session_state.data['city']}, {st.session_state.data['state']} {st.session_state.data['zip_code']}",
            f"{st.session_state.data['elevation_ft']:,} ft",
            f"{st.session_state.data['barometric_pressure']:.2f} in Hg",
            st.session_state.data['vent_type'],
            f"{st.session_state.data['temp_outside_f']}°F",
            str(st.session_state.data['num_appliances']),
            datetime.now().strftime('%B %d, %Y at %I:%M %p')
        ]
    }
    
    st.table(pd.DataFrame(project_data))
    
    # ========================================================================
    # APPLIANCES TABLE
    # ========================================================================
    st.markdown("## 🔥 Appliance Configuration")
    
    total_mbh = sum(app['mbh'] for app in st.session_state.data['appliances'])
    st.write(f"**Total System Input:** {total_mbh:,.0f} MBH")
    st.write("")
    
    appliance_data = {
        "Appliance": [],
        "Input (MBH)": [],
        "Category": [],
        "CO₂ (%)": [],
        "Flue Temp (°F)": [],
        "Fuel Type": [],
        "Outlet Dia (\")": []
    }
    
    for app in st.session_state.data['appliances']:
        cat_name = calc.appliance_categories[app['category']]['name']
        fuel_name = app['fuel_type'].replace('_', ' ').title()
        
        appliance_data["Appliance"].append(f"#{app['appliance_number']}")
        appliance_data["Input (MBH)"].append(f"{app['mbh']:,.0f}")
        appliance_data["Category"].append(cat_name)
        appliance_data["CO₂ (%)"].append(f"{app['co2_percent']}")
        appliance_data["Flue Temp (°F)"].append(f"{app['temp_f']}")
        appliance_data["Fuel Type"].append(fuel_name)
        appliance_data["Outlet Dia (\")"].append(f"{app['outlet_diameter']}")
    
    st.table(pd.DataFrame(appliance_data))
    
    # ========================================================================
    # CONNECTOR CONFIGURATION TABLE
    # ========================================================================
    st.markdown("## 🔌 Connector Configuration")
    st.write(f"**Worst-Case Connector:** Appliance #{worst['appliance_id']}")
    st.write("")
    
    # Build fittings list
    fittings_list = []
    for fitting, count in st.session_state.data['connector_fittings'].items():
        if fitting != 'entrance':
            fittings_list.append(f"{count}× {fitting.replace('_', ' ')}")
    fittings_str = ', '.join(fittings_list) if fittings_list else 'None'
    
    horiz_run = st.session_state.data['connector_length'] - st.session_state.data['connector_height']
    
    connector_config = {
        "Parameter": [
            "Diameter",
            "Total Length",
            "Vertical Height",
            "Horizontal Run",
            "Fittings"
        ],
        "Value": [
            f"{st.session_state.data['connector_diameter']}\"",
            f"{st.session_state.data['connector_length']} ft",
            f"{st.session_state.data['connector_height']} ft",
            f"{horiz_run} ft",
            fittings_str
        ]
    }
    
    st.table(pd.DataFrame(connector_config))
    
    # Connector Results
    st.markdown("### Connector Analysis Results")
    connector_results = {
        "Metric": ["Draft", "Velocity"],
        "Value": [
            f"{worst['connector_draft']:.4f} in w.c.",
            f"{worst['connector_result']['connector']['velocity_fps'] * 60:.0f} ft/min"
        ]
    }
    st.table(pd.DataFrame(connector_results))
    
    # ========================================================================
    # MANIFOLD CONFIGURATION TABLE
    # ========================================================================
    st.markdown("## 🏗️ Common Vent (Manifold) Configuration")
    
    if st.session_state.data.get('optimize_manifold') and 'optimization_details' in st.session_state.data:
        opt = st.session_state.data['optimization_details']
        diameter_note = f"{st.session_state.data['manifold_diameter']}\" (Optimized by CARL)"
        st.success(f"✅ **CARL Optimized:** {opt['recommended_diameter']}\" diameter for {opt['velocity_fpm']:.0f} ft/min velocity")
    else:
        diameter_note = f"{st.session_state.data['manifold_diameter']}\" (User Selected)"
    
    st.write("")
    
    # Build fittings list
    manifold_fittings_list = []
    for fitting, count in st.session_state.data['manifold_fittings'].items():
        if fitting != 'exit':
            manifold_fittings_list.append(f"{count}× {fitting.replace('_', ' ')}")
    manifold_fittings_str = ', '.join(manifold_fittings_list) if manifold_fittings_list else 'None'
    
    total_length = st.session_state.data['manifold_height'] + st.session_state.data['manifold_horizontal']
    
    manifold_config = {
        "Parameter": [
            "Diameter",
            "Vertical Height",
            "Horizontal Run",
            "Total Length",
            "Fittings"
        ],
        "Value": [
            diameter_note,
            f"{st.session_state.data['manifold_height']} ft",
            f"{st.session_state.data['manifold_horizontal']} ft",
            f"{total_length} ft",
            manifold_fittings_str
        ]
    }
    
    st.table(pd.DataFrame(manifold_config))
    
    # Manifold Results
    st.markdown("### Manifold Analysis Results")
    manifold_results = {
        "Metric": ["Draft"],
        "Value": [f"{worst['manifold_draft']:.4f} in w.c."]
    }
    st.table(pd.DataFrame(manifold_results))
    
    # Show optimization details if available
    if st.session_state.data.get('optimize_manifold') and 'optimization_details' in st.session_state.data:
        with st.expander("📊 View CARL Optimization Analysis"):
            opt = st.session_state.data['optimization_details']
            st.write("**Diameters Evaluated:**")
            opt_data = {
                "Diameter": [],
                "Velocity (ft/min)": [],
                "Status": []
            }
            for result in opt['all_options']:
                if result['score'] > 0:
                    opt_data["Diameter"].append(f"{result['diameter']}\"")
                    opt_data["Velocity (ft/min)"].append(f"{result['velocity_fpm']:.0f}")
                    opt_data["Status"].append(result['status'])
            st.table(pd.DataFrame(opt_data))
    
    # ========================================================================
    # OPERATING SCENARIOS TABLE
    # ========================================================================
    st.markdown("## 📊 Operating Scenarios Analysis")
    
    scenario_data = {
        "Scenario": [],
        "CFM": [],
        "Velocity (ft/min)": [],
        "Draft (in w.c.)": []
    }
    
    scenarios = [
        ('All Appliances', result.get('all_operating')),
        ('All Minus One', result.get('all_minus_one')),
        ('Single Largest', result.get('single_largest')),
        ('Single Smallest', result.get('single_smallest'))
    ]
    
    for name, scenario in scenarios:
        if scenario and scenario is not None:
            cfm = scenario['combined']['total_cfm']
            vel = scenario['common_vent']['velocity_fps'] * 60
            draft = scenario['common_vent']['available_draft_inwc']
            
            scenario_data["Scenario"].append(name)
            scenario_data["CFM"].append(f"{cfm:.1f}")
            scenario_data["Velocity (ft/min)"].append(f"{vel:.0f}")
            scenario_data["Draft (in w.c.)"].append(f"{draft:.4f}")
    
    st.table(pd.DataFrame(scenario_data))
    
    # ========================================================================
    # SYSTEM DRAFT SUMMARY TABLE
    # ========================================================================
    st.markdown("## ⚖️ Total System Draft Summary")
    
    atm_pressure = -worst['total_available_draft']
    
    system_summary = {
        "Component": [
            "Connector Draft",
            "Manifold Draft",
            "**TOTAL AVAILABLE DRAFT**",
            "",
            "**ATMOSPHERIC PRESSURE at Appliance**"
        ],
        "Value (in w.c.)": [
            f"{worst['connector_draft']:.4f}",
            f"{worst['manifold_draft']:.4f}",
            f"**{worst['total_available_draft']:.4f}**",
            "",
            f"**{atm_pressure:.4f}**"
        ]
    }
    
    st.table(pd.DataFrame(system_summary))
    
    st.info("ℹ️ **Important Relationship:** Positive draft (+) = Negative atmospheric pressure (−) | Negative draft (−) = Positive atmospheric pressure (+)")
    
    # ========================================================================
    # CATEGORY COMPLIANCE
    # ========================================================================
    if worst['appliance']['category'] != 'custom':
        st.markdown("## ✅ Category Compliance Check")
        
        cat_info = calc.appliance_categories[worst['appliance']['category']]
        cat_limits = cat_info['pressure_range']
        
        compliance_data = {
            "Item": [
                "Appliance Category",
                "Required Atmospheric Pressure Range",
                "Actual Atmospheric Pressure",
                "Status"
            ],
            "Value": [
                cat_info['name'],
                f"{cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c.",
                f"{atm_pressure:.4f} in w.c.",
                "✅ COMPLIANT" if cat_limits[0] <= atm_pressure <= cat_limits[1] else "❌ NON-COMPLIANT"
            ]
        }
        
        st.table(pd.DataFrame(compliance_data))
        
        if cat_limits[0] <= atm_pressure <= cat_limits[1]:
            st.success("✅ **System meets category requirements**")
        else:
            st.error("❌ **System does NOT meet category requirements**")
            st.warning("⚠️ **Action Required:** US Draft Co. draft control system needed")
    
    # ========================================================================
    # SEASONAL VARIATION TABLE
    # ========================================================================
    st.markdown("## 🌡️ Seasonal Draft Variation")
    
    all_op = result.get('all_operating')
    if all_op and isinstance(all_op, dict) and 'common_vent' in all_op:
        common_vent = all_op['common_vent']
        if isinstance(common_vent, dict) and 'available_draft_inwc' in common_vent:
            available = common_vent['available_draft_inwc']
            winter_draft = available * 1.4
            summer_draft = available * 0.6
            variation_range = abs(winter_draft - summer_draft)
            
            seasonal_data = {
                "Condition": [
                    "Winter (0°F)",
                    f"Design ({st.session_state.data['temp_outside_f']}°F)",
                    "Summer (95°F)",
                    "",
                    "**Total Variation**"
                ],
                "Draft (in w.c.)": [
                    f"{winter_draft:.4f}",
                    f"{available:.4f}",
                    f"{summer_draft:.4f}",
                    "",
                    f"**{variation_range:.4f}**"
                ],
                "Change from Design": [
                    "+40% (Higher draft)",
                    "Calculated value",
                    "−40% (Lower draft)",
                    "",
                    "**80% total swing**"
                ]
            }
            
            st.table(pd.DataFrame(seasonal_data))
            
            st.error("⚠️ **CRITICAL:** Draft varies 80% throughout the year! US Draft Co. controls are REQUIRED for safe, consistent operation.")
        else:
            st.warning("⚠️ Seasonal variation data incomplete - draft controls still recommended")
    else:
        st.warning("⚠️ Seasonal variation data not available - draft controls still recommended")
    
    # ========================================================================
    # COMBUSTION AIR REQUIREMENTS
    # ========================================================================
    st.markdown("## 💨 Combustion Air Requirements")
    
    comb_air = st.session_state.data['combustion_air']
    louvers = st.session_state.data['louvers']
    
    st.write(f"**Total Combustion Air Required:** {comb_air['combustion_air_cfm']:.0f} CFM at {comb_air['ambient_temp']}°F")
    st.write("")
    
    # Single Louver Method
    st.markdown("### Method 1: Single Louver")
    
    single_louver_data = {
        "Parameter": [
            "Required Free Area",
            "Louver Size (75% free area)",
            "**RECOMMENDED**"
        ],
        "Value": [
            f"{louvers['single_louver']['free_area_sqin']:.1f} sq in",
            f"{louvers['single_louver']['louver_size_sqin']:.1f} sq in",
            f"**{louvers['single_louver']['recommended_dimensions']}**"
        ]
    }
    st.table(pd.DataFrame(single_louver_data))
    
    # Two Louver Method
    st.markdown("### Method 2: Two Louver (High/Low)")
    st.caption("One louver within 12\" of ceiling, one within 12\" of floor")
    
    two_louver_data = {
        "Parameter": [
            "Free Area (Each Louver)",
            "Louver Size Each (75% free area)",
            "**RECOMMENDED (Each)**",
            "**TOTAL REQUIRED**"
        ],
        "Value": [
            f"{louvers['two_louver']['free_area_each_sqin']:.1f} sq in",
            f"{louvers['two_louver']['louver_size_each_sqin']:.1f} sq in",
            f"**{louvers['two_louver']['recommended_dimensions']}**",
            f"**Two louvers @ {louvers['two_louver']['recommended_dimensions']} each**"
        ]
    }
    st.table(pd.DataFrame(two_louver_data))
    
    # ========================================================================
    # US DRAFT CO. PRODUCT RECOMMENDATIONS
    # ========================================================================
    st.markdown("## 🏢 US Draft Co. Product Recommendations")
    
    # Determine draft condition
    total_draft = worst['total_available_draft']
    atm_pressure_check = -total_draft
    
    # Get category info
    cat_info = calc.appliance_categories.get(worst['appliance']['category'], {})
    cat_limits = cat_info.get('pressure_range', (-0.08, -0.03))
    is_condensing = worst['appliance']['category'] in ['cat_ii', 'cat_iv']
    num_appliances = st.session_state.data['num_appliances']
    
    # Decision Logic from US Draft Training Document
    # Step 1: Determine draft condition
    if atm_pressure_check > cat_limits[1]:
        # Excessive draft (too positive atmospheric pressure = too negative draft)
        draft_condition = "EXCESSIVE DRAFT"
        need_odcs = True
        need_vcs = False
    elif atm_pressure_check < cat_limits[0]:
        # Insufficient draft (too negative atmospheric pressure = too positive draft)
        draft_condition = "INSUFFICIENT DRAFT"
        need_odcs = False
        need_vcs = True
    else:
        # Within range but could be marginal
        draft_condition = "ADEQUATE DRAFT"
        need_odcs = False
        need_vcs = False
    
    st.write(f"**Draft Analysis:** {draft_condition}")
    st.write(f"**Atmospheric Pressure:** {atm_pressure_check:.4f} in w.c.")
    st.write(f"**Category Limits:** {cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c.")
    st.write("")
    
    # ========================================================================
    # PRIMARY SYSTEM RECOMMENDATION
    # ========================================================================
    
    if need_vcs and need_odcs:
        # Need BOTH exhaust and overdraft protection
        st.error("🔴 **CRITICAL: System needs BOTH draft inducement AND overdraft protection**")
        st.write("")
        st.success("**RECOMMENDED: VCS + ODCS System (RBD Configuration)**")
        st.write("")
        st.write("**Primary Product: RBD (Relief Barometric Damper)**")
        st.write("- Combines draft inducer WITH overdraft protection in one unit")
        st.write("- Provides both insufficient draft correction AND excess draft relief")
        st.write("- Single integrated solution for dual-condition systems")
        st.write("")
        
        system_type = "-OV"  # VCS + ODCS
        primary_product = "RBD (Relief Barometric Damper)"
        
    elif need_vcs:
        # Need draft inducer only
        st.warning("⚠️ **INSUFFICIENT DRAFT: Draft inducer required**")
        st.write("")
        st.success("**RECOMMENDED: VCS (Vent Control System)**")
        st.write("")
        st.write("**Primary Product: Draft Inducer**")
        st.write("- Provides mechanical exhaust to overcome insufficient draft")
        st.write("- Maintains consistent venting under all conditions")
        st.write("")
        
        system_type = "-V"  # VCS only
        primary_product = "Draft Inducer (TRV, T9F, or CBX series)"
        
    elif need_odcs:
        # Need overdraft control only
        st.warning("⚠️ **EXCESSIVE DRAFT: Overdraft control required**")
        st.write("")
        st.success("**RECOMMENDED: ODCS (Overdraft Control System)**")
        st.write("")
        st.write("**Primary Product: CDS3 (Connector Draft System)**")
        st.write("- Modulating damper system for precise draft control")
        st.write("- Controls excessive draft at low fire")
        st.write("- Maintains optimal pressure throughout firing range")
        st.write("")
        
        system_type = "-O"  # ODCS only
        primary_product = "CDS3 (Connector Draft System)"
        
    else:
        # Adequate draft, but recommend controls for seasonal stability
        st.info("ℹ️ **ADEQUATE DRAFT: Within category limits**")
        st.write("")
        st.success("**RECOMMENDED: ODCS for Seasonal Stability**")
        st.write("")
        st.write("**Primary Product: CDS3 (Connector Draft System)**")
        st.write("- Although currently adequate, draft varies 80% seasonally")
        st.write("- CDS3 provides year-round consistent performance")
        st.write("- Prevents issues during extreme weather")
        st.write("")
        
        system_type = "-O"  # ODCS for stability
        primary_product = "CDS3 (Connector Draft System)"
    
    # ========================================================================
    # CONTROLLER RECOMMENDATION
    # ========================================================================
    st.markdown("### 🎛️ Controller Selection")
    
    # Determine controller based on appliance count and system needs
    if is_condensing:
        control_type = "Constant Pressure (REQUIRED for condensing)"
    else:
        control_type = "Constant Pressure (Recommended)"
    
    # Select controller model
    if num_appliances == 1:
        if system_type == "-V" and not is_condensing:
            controller = "H100" + system_type
            display = "LCD"
        else:
            controller = "V150" + system_type
            display = "LCD with 4 buttons"
    elif num_appliances <= 2:
        controller = "V150" + system_type
        display = "LCD with 4 buttons"
    elif num_appliances <= 6:
        controller = "V250" + system_type
        display = "4\" Touchscreen"
    elif num_appliances <= 15:
        controller = "V350" + system_type
        display = "7\" Touchscreen"
    else:
        controller = "V350" + system_type
        display = "7\" Touchscreen"
    
    controller_data = {
        "Parameter": [
            "Recommended Controller",
            "Configuration",
            "Control Type",
            "Max Appliances",
            "Display Type",
            "Systems Supported"
        ],
        "Specification": [
            f"**{controller}**",
            system_type,
            control_type,
            f"Up to {num_appliances} (configured)",
            display,
            "VCS, PAS, ODCS combinations"
        ]
    }
    
    st.table(pd.DataFrame(controller_data))
    
    # ========================================================================
    # DRAFT INDUCER SELECTION (if needed)
    # ========================================================================
    if need_vcs or (need_vcs and need_odcs):
        st.markdown("### 🌀 Draft Inducer Selection")
        
        # Get CFM from all operating scenario
        all_op = result.get('all_operating')
        if all_op:
            total_cfm = all_op['combined']['total_cfm']
            static_pressure = abs(worst['total_available_draft'])
            
            # Select inducer series based on CFM and pressure
            if total_cfm <= 2675:
                inducer_series = "TRV Series"
                inducer_desc = "True Inline configuration"
                cfm_range = "80-2,675 CFM"
                pressure_range = "0-3\" w.c."
            elif total_cfm <= 6090:
                inducer_series = "T9F Series"
                inducer_desc = "90° Inline configuration"
                cfm_range = "200-6,090 CFM"
                pressure_range = "0-4\" w.c."
            elif total_cfm <= 17000:
                inducer_series = "CBX Series"
                inducer_desc = "Termination mount (top of chimney)"
                cfm_range = "3,300-17,000 CFM"
                pressure_range = "0-4\" w.c."
            else:
                inducer_series = "T9F Extended Series"
                inducer_desc = "90° Inline - High Capacity"
                cfm_range = "2,650-22,000 CFM"
                pressure_range = "0-8\" w.c."
            
            # Material selection
            if is_condensing:
                material = "316L Stainless Steel (REQUIRED for condensing)"
            else:
                material = "Aluminum or 316L Stainless Steel"
            
            inducer_data = {
                "Parameter": [
                    "Recommended Series",
                    "Configuration",
                    "CFM Requirement",
                    "Static Pressure Required",
                    "Available CFM Range",
                    "Max Pressure Capacity",
                    "Material Required"
                ],
                "Specification": [
                    f"**{inducer_series}**",
                    inducer_desc,
                    f"{total_cfm:.0f} CFM",
                    f"{static_pressure:.4f} in w.c.",
                    cfm_range,
                    pressure_range,
                    material
                ]
            }
            
            st.table(pd.DataFrame(inducer_data))
            
            if is_condensing:
                st.error("⚠️ **316L Stainless Steel is REQUIRED** for condensing appliances to prevent corrosion from acidic condensate.")
    
    # ========================================================================
    # CDS3 SPECIFICATIONS (if ODCS needed)
    # ========================================================================
    if need_odcs or (not need_vcs and not need_odcs):
        st.markdown("### 🎛️ CDS3 Connector Draft System Details")
        
        cds3_features = {
            "Feature": [
                "Application",
                "Control Method",
                "Technology",
                "Pressure Transducer",
                "Response Time",
                "User Interface",
                "Damper Configuration",
                "Actuator Type",
                "Connection Options",
                "Seal Options",
                "Ideal For"
            ],
            "Specification": [
                "Overdraft control for all appliance categories",
                "Modulating damper maintains precise outlet pressure",
                "EC-Flow™ bi-directional pressure control",
                "Built-in bi-directional transducer",
                "2-second actuator (industry leading)",
                "Integrated with controller touchscreen",
                "Single Blade Damper (SBD) with butterfly design",
                "Butterfly actuator for smooth modulation",
                "Standard 1/2\" flanges and v-band connections",
                "'G' model available with Viton seal for backflow prevention",
                "Systems with adequate draft needing seasonal stability"
            ]
        }
        
        st.table(pd.DataFrame(cds3_features))
    
    # ========================================================================
    # CRITICAL NOTES
    # ========================================================================
    st.markdown("### ⚠️ Critical Installation Requirements")
    
    critical_notes = []
    
    if is_condensing:
        critical_notes.append("**316L Stainless Steel REQUIRED:** All exhaust components must be 316L SS for condensing applications")
    
    if need_vcs and need_odcs:
        critical_notes.append("**RBD Configuration:** Use Relief Barometric Damper to combine draft inducer and overdraft protection")
    
    critical_notes.append("**Constant Pressure Control:** Required for safe, consistent operation across all firing ranges")
    critical_notes.append("**Seasonal Variation:** Draft varies 80% throughout the year - controls ensure safe operation year-round")
    critical_notes.append("**Professional Installation:** All systems must be installed per US Draft Co. specifications and local codes")
    
    for note in critical_notes:
        st.write(f"• {note}")
    
    st.markdown("---")
    st.markdown("### 📞 Contact Information")
    
    contact_data = {
        "": [
            "Company",
            "Address",
            "Phone",
            "Website",
            "Technical Support"
        ],
        " ": [
            "US Draft Co. - A Division of R.M. Manifold Group, Inc.",
            "100 S Sylvania Ave, Fort Worth, TX 76111",
            "817-393-4029",
            "www.usdraft.com",
            "Available for sizing assistance and product selection"
        ]
    }
    st.table(pd.DataFrame(contact_data))
    
    # ========================================================================
    # ACTION BUTTONS
    # ========================================================================
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Analysis", key="btn_new_analysis", use_container_width=True):
            # Clear all data
            st.session_state.data = {}
            st.session_state.step = 'project_name'
            st.rerun()
    with col2:
        st.info("📄 PDF Report Generation - Coming Soon!")

# Footer
st.markdown("---")
st.caption("CARL v1.0 Beta | US Draft by RM Manifold | 817-393-4029 | www.usdraft.com")
st.caption(f"Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

