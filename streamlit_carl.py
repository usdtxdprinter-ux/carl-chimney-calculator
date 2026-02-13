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

# Initialize postal code lookup
from postal_code_lookup import PostalCodeLookup

@st.cache_resource
def get_postal_lookup():
    return PostalCodeLookup()

postal_lookup = get_postal_lookup()

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
# Display logo and title
import os
logo_path = os.path.join(os.path.dirname(__file__), 'us_draft_logo.png')
if os.path.exists(logo_path):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo_path, use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>CARL - Chimney Analysis & Reasoning Layer</h1>", unsafe_allow_html=True)
else:
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
    
    # User information
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("Your Name:*", placeholder="e.g., John Smith")
    with col2:
        user_email = st.text_input("Email Address:*", placeholder="e.g., john@company.com")
    
    # Project name
    project_name = st.text_input("Project Name:*", placeholder="e.g., USR Boiler Room")
    
    if st.button("➡️ Next", key="btn_project_name", use_container_width=True):
        if project_name and user_name and user_email:
            # Basic email validation
            if '@' in user_email and '.' in user_email:
                st.session_state.data['project_name'] = project_name
                st.session_state.data['user_name'] = user_name
                st.session_state.data['user_email'] = user_email
                st.session_state.step = 'zip_code'
                st.rerun()
            else:
                st.error("Please enter a valid email address")
        else:
            st.error("Please fill in all required fields (*)")

# STEP: Zip Code
elif st.session_state.step == 'zip_code':
    st.subheader("📍 Location")
    st.write(f"**Project:** {st.session_state.data['project_name']}")
    
    zip_code = st.text_input("Enter ZIP/Postal Code:", placeholder="e.g., 76111 or M5H 2N2")
    
    # Try lookup if code entered
    location = None
    if zip_code:
        location = postal_lookup.lookup(zip_code)
    
    # Show manual entry if code not found or if user hasn't entered code yet
    if zip_code and not location:
        st.warning(f"Postal code '{zip_code}' not recognized. Please enter location manually.")
        manual_city = st.text_input("City:*", placeholder="e.g., Fort Worth")
        manual_state = st.text_input("State/Province:*", placeholder="e.g., TX or ON", max_chars=2).upper()
        manual_elev = st.number_input("Elevation (ft):*", min_value=0, max_value=15000, value=650, step=50)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="btn_zip_back"):
                st.session_state.step = 'project_name'
                st.rerun()
        with col2:
            if st.button("➡️ Next", key="btn_zip_next", use_container_width=True):
                if manual_city and manual_state and len(manual_state) == 2:
                    st.session_state.data['zip_code'] = zip_code
                    st.session_state.data['city'] = manual_city
                    st.session_state.data['state'] = manual_state
                    st.session_state.data['elevation'] = manual_elev
                    st.session_state.data['barometric_pressure'] = elevation_to_pressure(manual_elev)
                    st.session_state.step = 'vent_type'
                    st.rerun()
                else:
                    st.error("Please fill in all location fields")
    
    else:
        # Normal flow - either no code entered yet, or code was found
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="btn_zip_back"):
                st.session_state.step = 'project_name'
                st.rerun()
        with col2:
            if st.button("➡️ Next", key="btn_zip_next", use_container_width=True):
                if not zip_code:
                    st.error("Please enter a ZIP/Postal code")
                elif location:
                    # Show info message if estimated
                    if location.get('estimated'):
                        st.info(f"ℹ️ Location estimated based on postal code prefix: {location['city']}, {location['state']}")
                    
                    st.session_state.data['zip_code'] = zip_code
                    st.session_state.data['city'] = location['city']
                    st.session_state.data['state'] = location['state']
                    st.session_state.data['elevation'] = location['elevation']
                    st.session_state.data['barometric_pressure'] = elevation_to_pressure(location['elevation'])
                    st.session_state.step = 'vent_type'
                    st.rerun()

# STEP: Vent Type
elif st.session_state.step == 'vent_type':
    st.subheader("🔧 Chimney/Vent Type")
    st.write(f"**Project:** {st.session_state.data['project_name']}")
    st.write(f"**Location:** {st.session_state.data['city']}, {st.session_state.data['state']}")
    st.write(f"**Elevation:** {st.session_state.data['elevation']:,} ft (Barometric: {st.session_state.data['barometric_pressure']:.2f} in Hg)")
    
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
            st.session_state.step = 'appliance_1_turndown'
            st.rerun()
        if st.button("⛽ Oil", key="fuel_oil", use_container_width=True):
            st.session_state.data['current_fuel'] = 'oil'
            st.session_state.step = 'appliance_1_turndown'
            st.rerun()
    with col3:
        if st.button("🔥 LP Gas (Propane)", key="fuel_lp", use_container_width=True):
            st.session_state.data['current_fuel'] = 'lp_gas'
            st.session_state.step = 'appliance_1_turndown'
            st.rerun()

# STEP: Appliance Turndown Ratio
elif st.session_state.step == 'appliance_1_turndown':
    app_num = get_current_appliance_num()
    st.subheader(f"🔄 Appliance #{app_num} - Turndown Ratio")
    
    st.write(f"**Input:** {st.session_state.data['current_mbh']} MBH")
    st.write(f"**Fuel:** {st.session_state.data['current_fuel'].replace('_', ' ').title()}")
    
    st.info("💡 **Turndown ratio** is the ratio of maximum firing rate to minimum firing rate. For example, a 10:1 turndown means the appliance can modulate from 100% down to 10% (1/10th) of its rated input.")
    
    st.write("**Common Turndown Ratios:**")
    st.write("• On/Off appliances: 1:1 (no turndown)")
    st.write("• Two-stage: 2:1")
    st.write("• Modulating condensing boilers: 5:1 to 10:1")
    st.write("• High-efficiency modulating: 10:1 to 20:1")
    st.write("• Ultra-high efficiency: 25:1+")
    
    st.markdown("---")
    
    turndown_ratio = st.number_input(
        "Turndown Ratio (e.g., 10 for 10:1):",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        help="Enter turndown ratio. 1 = on/off, 5 = 5:1, 10 = 10:1, etc."
    )
    
    # Calculate low fire input
    low_fire_mbh = st.session_state.data['current_mbh'] / turndown_ratio
    
    st.write("")
    st.success(f"**High Fire:** {st.session_state.data['current_mbh']:.0f} MBH (100%)")
    st.success(f"**Low Fire:** {low_fire_mbh:.1f} MBH ({100/turndown_ratio:.1f}%)")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="btn_turndown_back"):
            st.session_state.step = 'appliance_1_fuel'
            st.rerun()
    with col2:
        if st.button("➡️ Next", key="btn_turndown_next", use_container_width=True):
            st.session_state.data['current_turndown'] = turndown_ratio
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
        'turndown_ratio': st.session_state.data.get('current_turndown', 1),
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
    for key in ['current_mbh', 'current_outlet', 'current_co2', 'current_temp', 'current_category', 'current_fuel', 'current_turndown']:
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
    
    st.info("💡 **Total Length** = Vertical rise + Horizontal run. For example: 8 ft vertical + 5 ft horizontal = 13 ft total length")
    
    length = st.number_input("Total Connector Length (ft):", min_value=0.1, value=10.0, step=1.0,
                            help="Sum of all vertical and horizontal sections")
    height = st.number_input("Vertical Height/Rise (ft):", min_value=0.0, value=0.0, step=1.0, 
                            help="Portion of connector that is vertical (contributes to draft)")
    
    # Calculate horizontal for display
    horizontal = length - height
    
    if height > length:
        st.error("❌ Vertical height cannot be greater than total length!")
    else:
        st.write(f"**Breakdown:** {height:.1f} ft vertical + {horizontal:.1f} ft horizontal = {length:.1f} ft total")
        
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
    st.write(f"**Vent Type:** {st.session_state.data['vent_type']}")
    st.write(f"**Length:** {st.session_state.data['connector_length']} ft (Height: {st.session_state.data['connector_height']} ft)")
    
    st.write("**Enter the number of each fitting type:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Elbows:**")
        num_15 = st.number_input("15° Elbows:", min_value=0, max_value=20, value=0, step=1, key="conn_15")
        num_30 = st.number_input("30° Elbows:", min_value=0, max_value=20, value=0, step=1, key="conn_30")
        num_45 = st.number_input("45° Elbows:", min_value=0, max_value=20, value=0, step=1, key="conn_45")
        num_90 = st.number_input("90° Elbows:", min_value=0, max_value=20, value=0, step=1, key="conn_90")
    
    with col2:
        st.write("**Tees:**")
        num_straight_tee = st.number_input("Straight Tees (flow through):", min_value=0, max_value=10, value=0, step=1, key="conn_straight_tee")
        num_90tee = st.number_input("90° Tees (change direction):", min_value=0, max_value=10, value=0, step=1, key="conn_90tee")
        num_lateral = st.number_input("Lateral Tees (45°):", min_value=0, max_value=10, value=0, step=1, key="conn_lateral")
    
    with col3:
        st.write("**Custom Losses:**")
        additional_k = st.number_input("Additional K Resistance:", min_value=0.0, max_value=10.0, value=0.0, step=0.1, 
                                      help="Additional dimensionless K-factor for unlisted fittings or devices", key="conn_add_k")
        additional_pressure = st.number_input("Additional Pressure Loss (in w.c.):", min_value=0.0, max_value=1.0, value=0.0, step=0.001, format="%.4f",
                                             help="Additional pressure loss in inches water column", key="conn_add_p")
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", key="btn_conn_fit_back"):
            st.session_state.step = 'connector_length'
            st.rerun()
    with col_next:
        if st.button("➡️ Next", key="btn_conn_fit_next", use_container_width=True):
            fittings = {'entrance': 1}
            if num_15 > 0: fittings['15_elbow'] = int(num_15)
            if num_30 > 0: fittings['30_elbow'] = int(num_30)
            if num_45 > 0: fittings['45_elbow'] = int(num_45)
            if num_90 > 0: fittings['90_elbow'] = int(num_90)
            if num_straight_tee > 0: fittings['straight_tee'] = int(num_straight_tee)
            if num_90tee > 0: fittings['90_tee_branch'] = int(num_90tee)
            if num_lateral > 0: fittings['lateral_tee'] = int(num_lateral)
            
            st.session_state.data['connector_fittings'] = fittings
            st.session_state.data['connector_additional_k'] = additional_k
            st.session_state.data['connector_additional_pressure'] = additional_pressure
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
    st.write(f"**Vent Type:** {st.session_state.data['vent_type']}")
    total_length = st.session_state.data['manifold_height'] + st.session_state.data['manifold_horizontal']
    st.write(f"**Total Length:** {total_length} ft ({st.session_state.data['manifold_height']} ft vertical + {st.session_state.data['manifold_horizontal']} ft horizontal)")
    
    st.write("**Enter the number of each fitting type:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Elbows:**")
        num_15 = st.number_input("15° Elbows:", min_value=0, max_value=20, value=0, step=1, key="man_15")
        num_30 = st.number_input("30° Elbows:", min_value=0, max_value=20, value=0, step=1, key="man_30")
        num_45 = st.number_input("45° Elbows:", min_value=0, max_value=20, value=0, step=1, key="man_45")
        num_90 = st.number_input("90° Elbows:", min_value=0, max_value=20, value=0, step=1, key="man_90")
    
    with col2:
        st.write("**Tees:**")
        num_straight_tee = st.number_input("Straight Tees (flow through):", min_value=0, max_value=10, value=0, step=1, key="man_straight_tee")
        num_90tee = st.number_input("90° Tees (change direction):", min_value=0, max_value=10, value=0, step=1, key="man_90tee")
        num_lateral = st.number_input("Lateral Tees (45°):", min_value=0, max_value=10, value=0, step=1, key="man_lateral")
        num_tee_cap = st.number_input("Tee Caps (dead end branches):", min_value=0, max_value=10, value=0, step=1, key="man_tee_cap",
                                      help="Cap on unused tee branch")
    
    with col3:
        st.write("**Termination & Custom:**")
        has_term_cap = st.checkbox("Termination Cap at top?", value=True, key="man_term_cap",
                                   help="Cap at top of chimney/vent")
        st.write("")
        additional_k = st.number_input("Additional K Resistance:", min_value=0.0, max_value=10.0, value=0.0, step=0.1,
                                      help="Additional dimensionless K-factor", key="man_add_k")
        additional_pressure = st.number_input("Additional Pressure Loss (in w.c.):", min_value=0.0, max_value=1.0, value=0.0, step=0.001, format="%.4f",
                                             help="Additional pressure loss", key="man_add_p")
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", key="btn_man_fit_back"):
            st.session_state.step = 'manifold_height'
            st.rerun()
    with col_next:
        if st.button("🔍 Run Analysis", key="btn_run_analysis", use_container_width=True):
            fittings = {'exit': 1}
            if num_15 > 0: fittings['15_elbow'] = int(num_15)
            if num_30 > 0: fittings['30_elbow'] = int(num_30)
            if num_45 > 0: fittings['45_elbow'] = int(num_45)
            if num_90 > 0: fittings['90_elbow'] = int(num_90)
            if num_straight_tee > 0: fittings['straight_tee'] = int(num_straight_tee)
            if num_90tee > 0: fittings['90_tee_branch'] = int(num_90tee)
            if num_lateral > 0: fittings['lateral_tee'] = int(num_lateral)
            if num_tee_cap > 0: fittings['tee_cap'] = int(num_tee_cap)
            if has_term_cap: fittings['termination_cap'] = 1
            
            st.session_state.data['manifold_fittings'] = fittings
            st.session_state.data['manifold_additional_k'] = additional_k
            st.session_state.data['manifold_additional_pressure'] = additional_pressure
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
            f"{st.session_state.data['elevation']:,} ft",
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
        "Outlet Dia (\")": [],
        "Turndown": []
    }
    
    for app in st.session_state.data['appliances']:
        cat_name = calc.appliance_categories[app['category']]['name']
        fuel_name = app['fuel_type'].replace('_', ' ').title()
        turndown = app.get('turndown_ratio', 1)
        
        appliance_data["Appliance"].append(f"#{app['appliance_number']}")
        appliance_data["Input (MBH)"].append(f"{app['mbh']:,.0f}")
        appliance_data["Category"].append(cat_name)
        appliance_data["CO₂ (%)"].append(f"{app['co2_percent']}")
        appliance_data["Flue Temp (°F)"].append(f"{app['temp_f']}")
        appliance_data["Fuel Type"].append(fuel_name)
        appliance_data["Outlet Dia (\")"].append(f"{app['outlet_diameter']}")
        appliance_data["Turndown"].append(f"{turndown}:1" if turndown > 1 else "On/Off")
    
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
    
    has_data = False
    for name, scenario in scenarios:
        if scenario and isinstance(scenario, dict) and 'combined' in scenario and 'common_vent' in scenario:
            try:
                cfm = scenario['combined']['total_cfm']
                vel = scenario['common_vent']['velocity_fps'] * 60
                draft = scenario['common_vent']['available_draft_inwc']
                
                scenario_data["Scenario"].append(name)
                scenario_data["CFM"].append(f"{cfm:.1f}")
                scenario_data["Velocity (ft/min)"].append(f"{vel:.0f}")
                scenario_data["Draft (in w.c.)"].append(f"{draft:.4f}")
                has_data = True
            except (KeyError, TypeError) as e:
                continue
    
    if has_data:
        st.table(pd.DataFrame(scenario_data))
    else:
        # Fallback: Show worst case data only
        st.warning("⚠️ Multiple scenario analysis not available. Showing worst case analysis only.")
        worst_case_data = {
            "Scenario": ["Worst Case"],
            "CFM": [f"{worst.get('appliance', {}).get('mbh', 0) * 0.8:.1f}"],  # Approximate CFM
            "Velocity (ft/min)": ["See manifold section"],
            "Draft (in w.c.)": [f"{worst.get('total_available_draft', 0):.4f}"]
        }
        st.table(pd.DataFrame(worst_case_data))
    
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
    # LOW FIRE (TURNDOWN) ANALYSIS
    # ========================================================================
    worst_case_analysis = result.get('worst_case', {})
    worst_low = worst_case_analysis.get('worst_case_low_fire')
    
    if worst_low:
        st.markdown("## 🔥 Low Fire (Turndown) Analysis")
        
        st.info("⚠️ **Critical:** Modulating appliances must maintain adequate draft at minimum firing rate. Low fire conditions have reduced flow and temperature, which can significantly affect available draft.")
        
        low_fire_data = worst_low['low_fire']
        turndown = low_fire_data['turndown_ratio']
        firing_pct = low_fire_data['firing_rate_percent']
        
        st.write(f"**Worst Case Appliance:** #{worst_low['appliance_id']}")
        st.write(f"**Turndown Ratio:** {turndown}:1")
        st.write(f"**Low Fire:** {firing_pct:.1f}% of rated input ({low_fire_data['appliance']['mbh']:.1f} MBH)")
        
        st.markdown("---")
        
        # Create comparison table: High Fire vs Low Fire
        comparison_data = {
            "Condition": ["High Fire (100%)", f"Low Fire ({firing_pct:.1f}%)"],
            "Input (MBH)": [
                f"{worst['appliance']['mbh']:.0f}",
                f"{low_fire_data['appliance']['mbh']:.1f}"
            ],
            "Connector Draft": [
                f"{worst['connector_draft']:.4f}",
                f"{low_fire_data['connector_draft']:.4f}"
            ],
            "Manifold Draft": [
                f"{worst['manifold_draft']:.4f}",
                f"{low_fire_data['manifold_draft']:.4f}"
            ],
            "TOTAL DRAFT": [
                f"**{worst['total_available_draft']:.4f}**",
                f"**{low_fire_data['total_available_draft']:.4f}**"
            ],
            "Atm Pressure": [
                f"{-worst['total_available_draft']:.4f}",
                f"{-low_fire_data['total_available_draft']:.4f}"
            ]
        }
        
        st.table(pd.DataFrame(comparison_data))
        
        # Check compliance at low fire
        if worst['appliance']['category'] != 'custom':
            cat_info = calc.appliance_categories[worst['appliance']['category']]
            cat_limits = cat_info['pressure_range']
            atm_low = -low_fire_data['total_available_draft']
            
            if cat_limits[0] <= atm_low <= cat_limits[1]:
                st.success(f"✅ **Low fire compliant:** {atm_low:.4f} in w.c. is within {cat_limits[0]:.2f} to {cat_limits[1]:.2f} range")
            else:
                st.error(f"❌ **Low fire NON-COMPLIANT:** {atm_low:.4f} in w.c. is outside {cat_limits[0]:.2f} to {cat_limits[1]:.2f} range")
                
                # Determine if needs VCS, ODCS, or both
                atm_high = -worst['total_available_draft']
                
                if atm_high > cat_limits[1] and atm_low > cat_limits[1]:
                    st.warning("⚠️ **Solution:** VCS (Draft Inducer) needed at both high and low fire")
                elif atm_high < cat_limits[0] and atm_low < cat_limits[0]:
                    st.warning("⚠️ **Solution:** ODCS (Overdraft Control) needed at both high and low fire")
                elif atm_high < cat_limits[0] and atm_low > cat_limits[1]:
                    st.error("🚨 **CRITICAL:** Excessive draft at high fire, insufficient at low fire")
                    st.warning("⚠️ **Solution:** VCS + ODCS (Combined system) or RBD (Relief Barometric Damper) required")
                elif atm_high > cat_limits[1] and atm_low < cat_limits[0]:
                    st.error("🚨 **CRITICAL:** Insufficient draft at high fire, excessive at low fire (unusual condition)")
                    st.warning("⚠️ **Review:** Check vent sizing and configuration")
        
        st.markdown("---")
    
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
    available_draft = None
    
    # Try to get draft from all_operating scenario
    if all_op and isinstance(all_op, dict) and 'common_vent' in all_op:
        common_vent = all_op['common_vent']
        if isinstance(common_vent, dict) and 'available_draft_inwc' in common_vent:
            available_draft = common_vent['available_draft_inwc']
    
    # Fallback to worst case if all_operating not available
    if available_draft is None:
        available_draft = worst.get('total_available_draft', -0.10)
        st.info("ℹ️ Using worst case draft for seasonal variation analysis")
    
    # Calculate seasonal variation
    winter_draft = available_draft * 1.4
    summer_draft = available_draft * 0.6
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
            f"{available_draft:.4f}",
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
    # 
    # CRITICAL UNDERSTANDING:
    # - Atmospheric pressure POSITIVE = Not enough draft = Need INDUCER (VCS)
    # - Atmospheric pressure NEGATIVE = Too much draft = Need DAMPER (ODCS)
    # 
    # Category limits are for atmospheric pressure:
    # Example Cat II: -0.08 to -0.03 in w.c. (negative = natural draft pulling)
    
    if atm_pressure_check > cat_limits[1]:
        # Atmospheric pressure TOO POSITIVE (above upper limit)
        # Means: Not enough draft pulling on appliance
        # Solution: Need draft inducer to pull harder
        draft_condition = "INSUFFICIENT DRAFT"
        need_odcs = False
        need_vcs = True
    elif atm_pressure_check < cat_limits[0]:
        # Atmospheric pressure TOO NEGATIVE (below lower limit)  
        # Means: Too much draft pulling on appliance
        # Solution: Need overdraft control to reduce pull
        draft_condition = "EXCESSIVE DRAFT"
        need_odcs = True
        need_vcs = False
    else:
        # Within range but could be marginal
        draft_condition = "ADEQUATE DRAFT"
        need_odcs = False
        need_vcs = False
    
    st.write(f"**Draft Analysis:** {draft_condition}")
    st.write(f"**Atmospheric Pressure at Appliance:** {atm_pressure_check:.4f} in w.c.")
    st.write(f"**Category {cat_info.get('name', 'Unknown')} Limits:** {cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c.")
    st.write("")
    
    # Show interpretation
    with st.expander("ℹ️ Understanding Draft vs Atmospheric Pressure"):
        st.write("**Key Concept:**")
        st.write("- **Negative** atmospheric pressure (e.g., -0.05) = Draft is **pulling** on appliance = Good for natural draft")
        st.write("- **Positive** atmospheric pressure (e.g., +0.05) = **Pushing** on appliance = Not enough draft")
        st.write("")
        st.write("**What This Means:**")
        if atm_pressure_check > cat_limits[1]:
            st.write(f"- Your system: {atm_pressure_check:.4f} in w.c. (too positive)")
            st.write(f"- Upper limit: {cat_limits[1]:.2f} in w.c.")
            st.write(f"- **Problem:** Not enough draft pulling on appliance")
            st.write(f"- **Solution:** Draft inducer needed to create more pull")
        elif atm_pressure_check < cat_limits[0]:
            st.write(f"- Your system: {atm_pressure_check:.4f} in w.c. (too negative)")
            st.write(f"- Lower limit: {cat_limits[0]:.2f} in w.c.")
            st.write(f"- **Problem:** Too much draft pulling on appliance")
            st.write(f"- **Solution:** Overdraft control needed to reduce pull")
        else:
            st.write(f"- Your system: {atm_pressure_check:.4f} in w.c.")
            st.write(f"- Limits: {cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c.")
            st.write(f"- **Status:** Within acceptable range")
            st.write(f"- **Recommendation:** Controls recommended for seasonal stability")
    
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
        if st.button("🛒 Select Products & Generate Reports", key="btn_select_products", use_container_width=True):
            st.session_state.step = 'product_selection_start'
            st.rerun()
    with col2:
        if st.button("🔄 New Analysis", key="btn_new_analysis", use_container_width=True):
            # Clear all data
            st.session_state.data = {}
            st.session_state.step = 'project_name'
            st.rerun()

# ============================================================================
# PRODUCT SELECTION & REPORT GENERATION STEPS
# ============================================================================

# STEP: Product Selection Start
elif st.session_state.step == 'product_selection_start':
    st.subheader("🛒 Product Selection & Report Generation")
    
    st.success("✅ System analysis complete!")
    
    st.write("**CARL can help you:**")
    st.write("• Select the right US Draft Co. products for your system")
    st.write("• Generate fan performance curves")
    st.write("• Create a comprehensive sizing report")
    st.write("• Generate CSI Section 23 51 10 specification")
    st.write("• Provide product datasheets")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Results", key="btn_back_to_results"):
            st.session_state.step = 'results'
            st.rerun()
    with col2:
        if st.button("➡️ Start Product Selection", key="btn_start_product_sel", use_container_width=True):
            # Initialize product selection data
            st.session_state.data['products'] = {}
            st.session_state.step = 'draft_inducer_type'
            st.rerun()

# STEP: Draft Inducer Type Selection
elif st.session_state.step == 'draft_inducer_type':
    from product_selector import ProductSelector
    
    selector = ProductSelector()
    
    # Get system requirements
    result = st.session_state.data.get('results')
    worst = result['worst_case'].get('worst_case')
    all_op = result.get('all_operating')
    
    total_cfm = all_op['combined']['total_cfm'] if all_op else 0
    
    # Check if all appliances are Category IV
    appliances = st.session_state.data.get('appliances', [])
    categories = [app.get('category', 'I').upper().replace('CAT_', '').replace('CATEGORY_', '') 
                 for app in appliances]
    all_cat_iv = all(cat == 'IV' for cat in categories)
    
    # Get intelligent system recommendation
    recommendation = selector.get_system_recommendation(appliances, result)
    
    # CRITICAL: We NEVER recommend natural draft only - always need draft control equipment
    # All systems need either VCS, ODCS, or CDS3
    
    # Check if CDS3-only system (Cat IV low pressure)
    if recommendation.get('cds3_needed'):
        st.subheader("✅ CDS3 Chimney Draft Stabilization System")
        st.success("Category IV system with low pressure - CDS3 recommended for code compliance and safe operation.")
        
        # Display recommendation notes
        for note in recommendation['notes']:
            st.info(f"ℹ️ {note}")
        
        st.write("**Required Equipment:**")
        st.write(f"• **CDS3 System** - {len(appliances)} unit(s) (one per appliance connector)")
        st.write("  - Self-contained draft control for Category IV appliances")
        st.write("  - No separate controller needed")
        st.write("  - Prevents code violations and ensures safe operation")
        
        st.session_state.data['products']['cds3'] = True
        st.session_state.data['products']['odcs'] = False
        st.session_state.data['products']['draft_inducer'] = None
        st.session_state.data['products']['controller'] = None
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="btn_back_cds3"):
                st.session_state.step = 'confirm_appliances'
                st.rerun()
        with col2:
            if st.button("➡️ Continue to Specification", key="btn_continue_cds3", use_container_width=True):
                st.session_state.step = 'confirm_products'
                st.rerun()
        
        st.stop()
    else:
        # Need powered draft - continue with selection
        
        # Calculate static pressure
        static_pressure = abs(worst['total_available_draft'])
        
        # GUARD RAIL: For Category IV, ignore connector pressure loss
        if all_cat_iv:
            connector_result = worst.get('connector_result', {})
            connector = connector_result.get('connector', {})
            connector_loss = abs(connector.get('pressure_loss_inwc', 0))
            
            # Remove connector loss from fan selection requirement
            # Note: This can result in negative value if connector loss > total
            adjusted_pressure = static_pressure - connector_loss
            
            st.info(f"ℹ️ **Category IV System:** Connector pressure loss ({connector_loss:.4f} in w.c.) "
                    f"excluded from fan selection. Manifold pressure only: {adjusted_pressure:.4f} in w.c.")
            
            # If adjusted pressure is negative or very low, natural draft is sufficient
            if adjusted_pressure <= 0.11:
                st.subheader("✅ Natural Draft System Recommended")
                
                if adjusted_pressure <= 0:
                    st.success(f"Manifold pressure ({adjusted_pressure:.4f} in w.c.) shows positive atmospheric pressure. "
                             "Natural draft with overdraft control is sufficient.")
                else:
                    st.success(f"Manifold pressure ({adjusted_pressure:.4f} in w.c.) is very low. "
                             "Natural draft with overdraft control is sufficient.")
                
                st.markdown("---")
                
                st.write("### 📦 Recommended Equipment")
                
                num_appliances = len(appliances)
                
                st.write("#### CDS3 Chimney Draft Stabilization System")
                st.write(f"**Quantity Required:** {num_appliances} unit(s) - one per appliance connector")
                st.write("")
                
                st.info("""
                **ℹ️ About the CDS3:**
                
                The CDS3 is a **self-contained draft control system** - no separate controller needed!
                
                **Designed specifically for Category IV condensing appliances.**
                
                **Each CDS3 unit includes:**
                - Motorized damper with 24VAC actuator (2-second stroke, spring return)
                - Bidirectional pressure transducer (±2.0" w.c., 0.001" resolution)
                - Built-in PID controller with auto-tuning
                
                **How it works:**
                - Installs in each appliance connector (breeching)
                - Continuously monitors draft pressure
                - Automatically modulates damper to maintain optimal draft (-0.10 to -0.01 in w.c.)
                - Prevents excessive draft that wastes energy
                - Maintains stable combustion conditions
                
                **No additional controller or interface needed** - each CDS3 operates independently!
                """)
                
                st.session_state.data['products']['cds3'] = True
                st.session_state.data['products']['odcs'] = False
                st.session_state.data['products']['draft_inducer'] = None
                st.session_state.data['products']['controller'] = None  # No controller needed!
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⬅️ Back", key="btn_back_cat4_natural"):
                        st.session_state.step = 'confirm_appliances'
                        st.rerun()
                with col2:
                    if st.button("➡️ Continue to Specification", key="btn_continue_cat4_natural", use_container_width=True):
                        st.session_state.step = 'confirm_products'
                        st.rerun()
                
                # Stop here - don't show fan selection
                st.stop()
            
            # If we get here, need powered draft with adjusted pressure
            static_pressure = adjusted_pressure
        
        # Get mean flue gas temperature for correction
        # Try to get from combined results, otherwise calculate from appliances
        if all_op and 'combined' in all_op and 'weighted_avg_temp_f' in all_op['combined']:
            mean_temp_f = all_op['combined']['weighted_avg_temp_f']
        elif all_op and 'common_vent' in all_op:
            # Try to get from common vent data
            mean_temp_f = all_op['common_vent'].get('mean_temp_f', 300)
        else:
            # Calculate from worst case appliance or use default
            mean_temp_f = worst['appliance'].get('temp_f', 300)

        
        st.subheader("🌀 Draft Inducer Selection")
        
        st.write(f"**System Requirements:**")
        st.write(f"• Airflow: {total_cfm:.0f} CFM")
        st.write(f"• Static Pressure: {static_pressure:.3f} in w.c. at {mean_temp_f:.0f}°F")
        
        st.info("💡 **Note:** Fan curves are at 70°F. System pressure will be adjusted for actual flue gas temperature.")
        
        st.markdown("---")
        st.write("**Select draft inducer configuration:**")
        st.write("")
        
        # Debug: Show what we're looking for
        try:
            with st.expander("🔍 Debug Info - Fan Selection Criteria"):
                st.write(f"**Fan curves loaded:** {len(selector.fan_curves)}")
                if len(selector.fan_curves) == 0:
                    st.error("❌ NO FAN CURVES LOADED! Check fan_curves_data.py is in repository.")
                    st.write("This means the import failed. Check Streamlit Cloud logs.")
                else:
                    st.success(f"✅ {len(selector.fan_curves)} fan models available")
                
                st.write(f"**Required CFM:** {total_cfm:.0f}")
                st.write(f"**Static Pressure (actual @ {mean_temp_f:.0f}°F):** {static_pressure:.4f} in w.c.")
                
                # Calculate corrected pressure here for display
                rho_70 = selector._air_density(70)
                rho_actual = selector._air_density(mean_temp_f)
                density_ratio = rho_70 / rho_actual
                corrected_pressure = static_pressure * density_ratio
                
                st.write(f"**Static Pressure (corrected to 70°F):** {corrected_pressure:.4f} in w.c.")
                st.write(f"**Temperature correction ratio:** {density_ratio:.3f}")
                st.write("")
                st.write("**Fan Series Ranges:**")
                st.write("• CBX: 215-17,000 CFM, 0-4.0 in w.c.")
                st.write("• TRV: 80-2,675 CFM, 0-3.0 in w.c.")
                st.write("• T9F: 200-6,090 CFM, 0-4.0 in w.c.")
        except Exception as e:
            st.error(f"Debug section error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
        
        # Check which series can work
        cbx_selection = selector.select_draft_inducer_series(total_cfm, static_pressure, 'CBX', mean_temp_f)
        trv_selection = selector.select_draft_inducer_series(total_cfm, static_pressure, 'TRV', mean_temp_f)
        t9f_selection = selector.select_draft_inducer_series(total_cfm, static_pressure, 'T9F', mean_temp_f)
        
        # Debug results
        with st.expander("🔍 Debug Info - Selection Results"):
            st.write(f"**CBX Result:** {'✅ ' + cbx_selection['model'] if cbx_selection else '❌ None'}")
            st.write(f"**TRV Result:** {'✅ ' + trv_selection['model'] if trv_selection else '❌ None'}")
            st.write(f"**T9F Result:** {'✅ ' + t9f_selection['model'] if t9f_selection else '❌ None'}")
        
        # Get CARL recommendation
        auto_selection = selector.select_draft_inducer_series(total_cfm, static_pressure, None, mean_temp_f)
        
        # Create 3 columns for the 3 fan types
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**CBX Series**")
            st.write("Termination Mount")
            st.write("(Top of chimney)")
            is_recommended = auto_selection and auto_selection['series'] == 'CBX'
            if cbx_selection:
                label = f"{'⭐ ' if is_recommended else ''}Select CBX"
                if st.button(label, key="btn_inducer_CBX", use_container_width=True):
                    st.session_state.data['products']['draft_inducer'] = cbx_selection
                    st.session_state.data['draft_inducer_preference'] = 'CBX'
                    st.session_state.step = 'controller_touchscreen'
                    st.rerun()
            else:
                st.button("❌ Not Available", key="btn_cbx_na", disabled=True, use_container_width=True)
        
        with col2:
            st.write("**TRV Series**")
            st.write("True Inline")
            st.write("(Compact, straight)")
            is_recommended = auto_selection and auto_selection['series'] == 'TRV'
            if trv_selection:
                label = f"{'⭐ ' if is_recommended else ''}Select TRV"
                if st.button(label, key="btn_inducer_TRV", use_container_width=True):
                    st.session_state.data['products']['draft_inducer'] = trv_selection
                    st.session_state.data['draft_inducer_preference'] = 'TRV'
                    st.session_state.step = 'controller_touchscreen'
                    st.rerun()
            else:
                st.button("❌ Not Available", key="btn_trv_na", disabled=True, use_container_width=True)
        
        with col3:
            st.write("**T9F Series**")
            st.write("90° Inline")
            st.write("(Space saving)")
            is_recommended = auto_selection and auto_selection['series'] == 'T9F'
            if t9f_selection:
                label = f"{'⭐ ' if is_recommended else ''}Select T9F"
                if st.button(label, key="btn_inducer_T9F", use_container_width=True):
                    st.session_state.data['products']['draft_inducer'] = t9f_selection
                    st.session_state.data['draft_inducer_preference'] = 'T9F'
                    st.session_state.step = 'controller_touchscreen'
                    st.rerun()
            else:
                st.button("❌ Not Available", key="btn_t9f_na", disabled=True, use_container_width=True)
        
        st.markdown("---")
        
        # Show CARL recommendation
        if auto_selection:
            st.success(f"⭐ **CARL Recommends:** {auto_selection['series_name']} - {auto_selection['model']}")
            st.write(f"**Why:** {auto_selection['description']}")
        
        st.markdown("---")
        
        if st.button("⬅️ Back", key="btn_inducer_back"):
            st.session_state.step = 'product_selection_start'
            st.rerun()

# STEP: Controller Touchscreen Preference
elif st.session_state.step == 'controller_touchscreen':
    # Check if CDS3-only system (no controller needed)
    if st.session_state.data.get('products', {}).get('draft_inducer') is None and \
       st.session_state.data.get('products', {}).get('cds3') is True:
        # CDS3-only system - skip controller selection
        st.session_state.data['products']['controller'] = None
        st.session_state.step = 'confirm_products'
        st.rerun()
    
    st.subheader("🎛️ Controller Selection")
    
    num_appliances = st.session_state.data['num_appliances']
    
    st.write(f"**System:** {num_appliances} appliance(s)")
    st.write("")
    st.write("**Do you want a touchscreen controller?**")
    
    st.info("💡 Touchscreen controllers (V250/V300/V350) provide easier operation and better visibility. LCD controllers (V150/H100) are more economical.")
    
    # Show which controllers are available based on appliance count
    st.write("**Available Controllers:**")
    
    available_controllers = []
    
    # V250: 1-6 appliances
    if num_appliances <= 6:
        available_controllers.append(('V250', '1-6 appliances', '4\" Touchscreen', True))
    
    # V300: 1-4 appliances
    if num_appliances <= 4:
        available_controllers.append(('V300', '1-4 appliances', '7\" Touchscreen', True))
    
    # V350: 1-15 appliances
    if num_appliances <= 15:
        available_controllers.append(('V350', '1-15 appliances', '7\" Touchscreen', True))
    
    # V150: 1-2 appliances (LCD)
    if num_appliances <= 2:
        available_controllers.append(('V150', '1-2 appliances', 'LCD with 4 buttons', False))
    
    # H100: 1 appliance (LCD)
    if num_appliances == 1:
        available_controllers.append(('H100', '1 appliance', 'LCD', False))
    
    # Display available options
    for controller, app_range, display, is_touch in available_controllers:
        icon = "📱" if is_touch else "📟"
        st.write(f"{icon} **{controller}** - {app_range} - {display}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Back", key="btn_touch_back"):
            if st.session_state.data['products'].get('draft_inducer'):
                st.session_state.step = 'draft_inducer_type'
            else:
                st.session_state.step = 'product_selection_start'
            st.rerun()
    
    with col2:
        if st.button("📱 Yes - Touchscreen\n(V250/V300/V350)", key="btn_touch_yes", use_container_width=True):
            st.session_state.data['wants_touchscreen'] = True
            st.session_state.step = 'supply_air_option'
            st.rerun()
    
    with col3:
        if st.button("📟 No - LCD Display\n(V150/H100)", key="btn_touch_no", use_container_width=True):
            st.session_state.data['wants_touchscreen'] = False
            st.session_state.step = 'supply_air_option'
            st.rerun()

# STEP: Supply Air Option
elif st.session_state.step == 'supply_air_option':
    st.subheader("💨 Combustion Air System")
    
    comb_air = st.session_state.data.get('combustion_air', {})
    combustion_air_cfm = comb_air.get('combustion_air_cfm', 0)
    
    st.write(f"**Combustion Air Required:** {combustion_air_cfm:.0f} CFM")
    st.write("")
    st.write("**Would you like to add a mechanical supply air fan (PAS)?**")
    
    st.info("💡 PAS (Pressure Air System) provides positive combustion air delivery. Alternative is natural ventilation through louvers.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Back", key="btn_supply_back"):
            st.session_state.step = 'controller_touchscreen'
            st.rerun()
    
    with col2:
        if st.button("✅ Yes - Add PAS", key="btn_supply_yes", use_container_width=True):
            st.session_state.data['wants_pas'] = True
            st.session_state.step = 'supply_fan_type'
            st.rerun()
    
    with col3:
        if st.button("❌ No - Use Louvers", key="btn_supply_no", use_container_width=True):
            st.session_state.data['wants_pas'] = False
            st.session_state.data['products']['supply_fan'] = None
            st.session_state.step = 'confirm_products'
            st.rerun()

# STEP: Supply Fan Type
elif st.session_state.step == 'supply_fan_type':
    from product_selector import ProductSelector
    
    selector = ProductSelector()
    
    comb_air = st.session_state.data.get('combustion_air', {})
    combustion_air_cfm = comb_air.get('combustion_air_cfm', 0)
    
    st.subheader("🌬️ Supply Air Fan Selection")
    
    st.write(f"**Required:** {combustion_air_cfm:.0f} CFM")
    st.write("")
    st.write("**Select supply air fan series:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Back", key="btn_fan_type_back"):
            st.session_state.step = 'supply_air_option'
            st.rerun()
    
    with col2:
        if st.button("🏢 PRIO Series\nPremium Indoor/Outdoor", key="btn_prio", use_container_width=True):
            prio = selector.select_supply_fan(combustion_air_cfm, 'PRIO')
            st.session_state.data['products']['supply_fan'] = prio
            st.session_state.step = 'confirm_products'
            st.rerun()
    
    with col3:
        if st.button("🏭 TAF Series\nHigh Capacity", key="btn_taf", use_container_width=True):
            taf = selector.select_supply_fan(combustion_air_cfm, 'TAF')
            st.session_state.data['products']['supply_fan'] = taf
            st.session_state.step = 'confirm_products'
            st.rerun()

# STEP: Confirm Products
elif st.session_state.step == 'confirm_products':
    from product_selector import ProductSelector
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    selector = ProductSelector()
    
    st.subheader("✅ Product Selection Summary")
    
    # Determine what systems are needed
    result = st.session_state.data.get('results')
    worst = result['worst_case'].get('worst_case')
    atm_pressure = -worst['total_available_draft']
    cat_info = calc.appliance_categories.get(worst['appliance']['category'], {})
    cat_limits = cat_info.get('pressure_range', (-0.08, -0.03))
    
    need_vcs = atm_pressure > cat_limits[1]
    need_odcs = atm_pressure < cat_limits[0] or (not need_vcs and atm_pressure > -0.01)  # Also recommend for stability
    needs_pas = st.session_state.data.get('wants_pas', False)
    
    # Check if CDS3-only system (no controller needed)
    if st.session_state.data.get('products', {}).get('cds3') is True:
        # CDS3-only - skip controller selection
        st.session_state.data['products']['controller'] = None
    else:
        # Select controller for other systems
        controller = selector.select_controller(
            num_appliances=st.session_state.data['num_appliances'],
            needs_vcs=need_vcs,
            needs_odcs=need_odcs,
            needs_pas=needs_pas,
            wants_touchscreen=st.session_state.data.get('wants_touchscreen', False)
        )
        st.session_state.data['products']['controller'] = controller
    
    # Add ODCS if needed
    if need_odcs:
        st.session_state.data['products']['odcs'] = {
            'model': 'CDS3',
            'name': 'Connector Draft System',
            'description': 'Modulating damper for precise draft control'
        }
    
    # Display selected products
    st.markdown("### 📦 Selected Products:")
    
    # Controller
    if st.session_state.data['products'].get('controller'):
        controller = st.session_state.data['products']['controller']
        st.write(f"**Controller:** {controller['model']}")
        st.write(f"  - Display: {controller['display']}")
        st.write(f"  - Configuration: {controller['configuration']}")
    elif st.session_state.data['products'].get('cds3'):
        st.write(f"**Controller:** None (CDS3 is self-contained)")
    else:
        st.write(f"**Controller:** TBD")
    
    # Draft Inducer
    if st.session_state.data['products'].get('draft_inducer'):
        inducer = st.session_state.data['products']['draft_inducer']
        st.write(f"**Draft Inducer:** {inducer['model']} ({inducer['series_name']})")
        st.write(f"  - {inducer['description']}")
    
    # ODCS
    if st.session_state.data['products'].get('odcs'):
        st.write(f"**Overdraft Control:** CDS3 - Connector Draft System")
    
    # Supply Fan
    if st.session_state.data['products'].get('supply_fan'):
        supply = st.session_state.data['products']['supply_fan']
        st.write(f"**Supply Air Fan:** {supply['series']} - {supply['name']}")
    
    st.markdown("---")
    
    # Plot fan curve if draft inducer selected
    if st.session_state.data['products'].get('draft_inducer'):
        inducer = st.session_state.data['products']['draft_inducer']
        all_op = result.get('all_operating')
        total_cfm = all_op['combined']['total_cfm'] if all_op else 0
        static_pressure_actual = abs(worst['total_available_draft'])
        
        # Get the corrected pressure used for fan selection
        static_pressure_70f = inducer.get('corrected_pressure_70f', static_pressure_actual)
        mean_temp_f = all_op['combined']['weighted_avg_temp_f'] if all_op else 300
        
        st.markdown("### 📊 Fan Performance Curve")
        
        # Show both actual and corrected pressures
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("System Pressure (Actual)", f"{static_pressure_actual:.3f} in w.c.", 
                     f"at {mean_temp_f:.0f}°F")
        with col_b:
            st.metric("System Pressure (70°F Equivalent)", f"{static_pressure_70f:.3f} in w.c.",
                     "used for fan selection")
        
        st.write("")
        
        fig = selector.plot_fan_and_system_curves(
            fan_model=inducer['model'],
            system_cfm=total_cfm,
            system_pressure=static_pressure_70f,  # Use corrected pressure
            title=f"{inducer['model']} Performance Curve with System Operating Point"
        )
        
        if fig:
            st.pyplot(fig)
            plt.close(fig)
            
            # Save figure for later use
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            st.session_state.data['fan_curve_image'] = buf.getvalue()
        else:
            st.warning(f"⚠️ Fan curve data not available for {inducer['model']}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Modify Selection", key="btn_modify"):
            st.session_state.step = 'draft_inducer_type'
            st.rerun()
    with col2:
        if st.button("📄 Generate Reports", key="btn_generate", use_container_width=True):
            st.session_state.step = 'generating_reports'
            st.rerun()
    with col3:
        if st.button("🔄 New Analysis", key="btn_new_from_confirm"):
            st.session_state.data = {}
            st.session_state.step = 'project_name'
            st.rerun()

# STEP: Generating Reports
elif st.session_state.step == 'generating_reports':
    st.subheader("📝 Generating Reports...")
    
    with st.spinner("Creating comprehensive documentation..."):
        import time
        time.sleep(1)  # Brief pause for UX
        
        st.session_state.step = 'reports_complete'
        st.rerun()

# STEP: Reports Complete
elif st.session_state.step == 'reports_complete':
    from product_selector import ProductSelector
    from csi_spec_generator import CSISpecificationGenerator
    from docx import Document
    from docx.shared import Inches
    import io
    
    st.subheader("✅ Reports Generated!")
    
    st.success("All documentation has been generated successfully!")
    
    # Generate CSI Specification
    spec_gen = CSISpecificationGenerator()
    
    # Prepare data for spec
    project_info = {
        'project_name': st.session_state.data['project_name'],
        'location': f"{st.session_state.data['city']}, {st.session_state.data['state']} {st.session_state.data['zip_code']}"
    }
    
    result = st.session_state.data.get('results')
    worst = result['worst_case'].get('worst_case')
    all_op = result.get('all_operating')
    
    system_data = {
        'cfm': all_op['combined']['total_cfm'] if all_op else 0,
        'static_pressure': abs(worst['total_available_draft']),
        'appliance_category': worst['appliance']['category'],
        'appliances': st.session_state.data.get('appliances', [])
    }
    
    # Generate specification
    spec_doc = spec_gen.generate_specification(
        project_info=project_info,
        products_selected=st.session_state.data['products'],
        system_data=system_data
    )
    
    # Save spec to bytes
    spec_buffer = io.BytesIO()
    spec_doc.save(spec_buffer)
    spec_buffer.seek(0)
    
    st.markdown("### 📥 Download Reports:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSI Specification
        st.download_button(
            label="📋 CSI Specification (DOCX)",
            data=spec_buffer.getvalue(),
            file_name=f"{st.session_state.data['project_name']}_CSI_23_51_10.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_csi"
        )
        
        # Fan curve image (if available)
        if st.session_state.data.get('fan_curve_image'):
            st.download_button(
                label="📊 Fan Performance Curve (PNG)",
                data=st.session_state.data['fan_curve_image'],
                file_name=f"{st.session_state.data['project_name']}_Fan_Curve.png",
                mime="image/png",
                key="download_curve"
            )
    
    with col2:
        # PDF Sizing Report
        from pdf_report_generator import PDFReportGenerator
        
        pdf_gen = PDFReportGenerator()
        
        # Get fan curve image if available
        fan_curve_bytes = st.session_state.data.get('fan_curve_image')
        
        # Prepare data for PDF
        pdf_buffer = pdf_gen.generate_report(
            project_data=st.session_state.data,
            calc_results=result,
            products=st.session_state.data['products'],
            fan_curve_img=fan_curve_bytes
        )
        
        st.download_button(
            label="📄 Sizing Report (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"{st.session_state.data['project_name']}_Sizing_Report.pdf",
            mime="application/pdf",
            key="download_pdf"
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Products", key="btn_back_products"):
            st.session_state.step = 'confirm_products'
            st.rerun()
    with col2:
        if st.button("🔄 New Analysis", key="btn_new_from_reports", use_container_width=True):
            st.session_state.data = {}
            st.session_state.step = 'project_name'
            st.rerun()

# Footer
st.markdown("---")
st.caption("CARL v1.0 Beta | US Draft by RM Manifold | 817-393-4029 | www.usdraft.com")
st.caption(f"Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

