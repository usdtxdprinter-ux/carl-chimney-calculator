"""
CARL - Chimney Analysis and Reasoning Layer
Chatbot Interface for Natural Conversation
"""

import streamlit as st
from enhanced_calculator import EnhancedChimneyCalculator
import json

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

# Initialize session state for conversation
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'welcome'
if 'project_data' not in st.session_state:
    st.session_state.project_data = {
        'appliances': [],
        'elevation_ft': 0,
        'temp_outside_f': 70,
        'connector_configs': [],
        'manifold_config': None
    }

# Elevation to barometric pressure conversion
def elevation_to_pressure(elevation_ft):
    """Convert elevation in feet to barometric pressure in inches Hg"""
    # Standard formula: P = P0 * (1 - 6.87535e-6 * h)^5.2561
    # Where P0 = 29.92 in Hg at sea level, h = elevation in feet
    if elevation_ft == 0:
        return 29.92
    P0 = 29.92
    pressure = P0 * (1 - 6.87535e-6 * elevation_ft) ** 5.2561
    return pressure

# Helper function to add message
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# Helper to get current appliance being configured
def get_current_appliance_index():
    return len(st.session_state.project_data['appliances'])

# Main title
st.title("🔥 CARL")
st.caption("Chimney Analysis and Reasoning Layer")

# Chat container
chat_container = st.container()

with chat_container:
    # Display all previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Input area at bottom
user_input = st.chat_input("Type your response here...")

# Welcome message
if st.session_state.current_step == 'welcome' and len(st.session_state.messages) == 0:
    welcome_msg = """Hello! I'm CARL, your chimney analysis assistant. I'll help you analyze your venting system.

I'll guide you through:
- Configuring your appliances
- Setting up connectors
- Designing the common vent
- Analyzing the complete system

Let's start! How many appliances will be vented into this common system? (Enter 1-6)"""
    
    add_message("assistant", welcome_msg)
    st.rerun()

# Process user input
if user_input:
    # Add user message to chat
    add_message("user", user_input)
    
    # Process based on current step
    if st.session_state.current_step == 'welcome':
        try:
            num_appliances = int(user_input)
            if 1 <= num_appliances <= 6:
                st.session_state.project_data['num_appliances'] = num_appliances
                st.session_state.current_step = 'elevation'
                response = f"Great! We'll configure {num_appliances} appliance{'s' if num_appliances > 1 else ''}.\n\nFirst, what is the elevation of your installation in feet above sea level? (This affects barometric pressure)\n\nExamples:\n- Sea level: 0 ft\n- Denver: 5,280 ft\n- Most locations: 0-2,000 ft"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a number between 1 and 6.")
        except:
            add_message("assistant", "Please enter a valid number (1-6).")
    
    elif st.session_state.current_step == 'elevation':
        try:
            elevation = float(user_input)
            if -500 <= elevation <= 15000:
                st.session_state.project_data['elevation_ft'] = elevation
                barometric = elevation_to_pressure(elevation)
                st.session_state.current_step = 'outside_temp'
                response = f"Elevation set to {elevation:,.0f} ft (Barometric pressure: {barometric:.2f} in Hg)\n\nWhat is the outside air temperature for your design calculation? (in °F)\n\nTypical values:\n- Winter design: 0-20°F\n- Standard: 70°F\n- Summer: 90-95°F"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a realistic elevation (-500 to 15,000 ft).")
        except:
            add_message("assistant", "Please enter a valid elevation in feet.")
    
    elif st.session_state.current_step == 'outside_temp':
        try:
            temp = float(user_input)
            if -20 <= temp <= 120:
                st.session_state.project_data['temp_outside_f'] = temp
                st.session_state.current_step = 'appliance_mbh'
                response = f"Outside temperature set to {temp}°F.\n\nNow let's configure Appliance #1.\n\nWhat is the input rating in MBH (thousands of BTU/hr)?"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a realistic temperature (-20 to 120°F).")
        except:
            add_message("assistant", "Please enter a valid temperature.")
    
    elif st.session_state.current_step == 'appliance_mbh':
        try:
            mbh = float(user_input)
            if mbh > 0:
                appliance_num = get_current_appliance_index() + 1
                st.session_state.temp_mbh = mbh
                st.session_state.current_step = 'appliance_outlet'
                response = f"Appliance #{appliance_num}: {mbh} MBH\n\nWhat is the appliance outlet diameter in inches?\n\n(The connector diameter cannot be smaller than this)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a positive MBH value.")
        except:
            add_message("assistant", "Please enter a valid MBH number.")
    
    elif st.session_state.current_step == 'appliance_outlet':
        try:
            outlet_dia = float(user_input)
            if 3 <= outlet_dia <= 24:
                appliance_num = get_current_appliance_index() + 1
                st.session_state.temp_outlet = outlet_dia
                st.session_state.current_step = 'appliance_category'
                response = f"Appliance #{appliance_num} outlet: {outlet_dia}\"\n\nWhat category is this appliance?\n\n1) Category I - Fan Assisted\n2) Category II - Non-Condensing\n3) Category III - Non-Condensing  \n4) Category IV - Condensing\n5) Custom (I'll enter CO2% and temperature)\n\nEnter 1, 2, 3, 4, or 5:"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a diameter between 3 and 24 inches.")
        except:
            add_message("assistant", "Please enter a valid diameter.")
    
    elif st.session_state.current_step == 'appliance_category':
        category_map = {
            '1': ('cat_i_fan', 'Category I - Fan Assisted'),
            '2': ('cat_ii', 'Category II - Non-Condensing'),
            '3': ('cat_iii', 'Category III - Non-Condensing'),
            '4': ('cat_iv', 'Category IV - Condensing'),
            '5': ('custom', 'Custom')
        }
        
        if user_input in category_map:
            cat_key, cat_name = category_map[user_input]
            st.session_state.temp_category = cat_key
            
            if cat_key == 'custom':
                st.session_state.current_step = 'appliance_co2'
                response = f"Custom appliance selected.\n\nWhat is the CO2 percentage from the combustion analyzer?\n\n(Typical range: 6-12%)"
                add_message("assistant", response)
            else:
                # Show defaults but allow adjustment
                cat_info = calc.appliance_categories[cat_key]
                st.session_state.temp_co2_default = cat_info['co2_default']
                st.session_state.temp_temp_default = cat_info['temp_default']
                st.session_state.current_step = 'appliance_adjust'
                response = f"{cat_name} selected.\n\nDefault values:\n- CO2: {cat_info['co2_default']}%\n- Flue Gas Temperature: {cat_info['temp_default']}°F\n\nWould you like to adjust these values?\n\n1) Use defaults (recommended)\n2) Adjust CO2 and temperature\n\nEnter 1 or 2:"
                add_message("assistant", response)
        else:
            add_message("assistant", "Please enter 1, 2, 3, 4, or 5.")
    
    elif st.session_state.current_step == 'appliance_adjust':
        if user_input == '1':
            # Use defaults
            st.session_state.temp_co2 = st.session_state.temp_co2_default
            st.session_state.temp_temp = st.session_state.temp_temp_default
            del st.session_state.temp_co2_default
            del st.session_state.temp_temp_default
            st.session_state.current_step = 'appliance_fuel'
            response = f"Using default values: {st.session_state.temp_co2}% CO2, {st.session_state.temp_temp}°F\n\nWhat fuel type?\n\n1) Natural Gas\n2) LP Gas (Propane)\n3) Oil\n\nEnter 1, 2, or 3:"
            add_message("assistant", response)
        elif user_input == '2':
            # Allow adjustment
            del st.session_state.temp_co2_default
            del st.session_state.temp_temp_default
            st.session_state.current_step = 'appliance_co2'
            response = f"Let's adjust the values.\n\nWhat is the CO2 percentage from your combustion analyzer?\n\n(Typical range: 6-12%)"
            add_message("assistant", response)
        else:
            add_message("assistant", "Please enter 1 to use defaults or 2 to adjust values.")
    
    elif st.session_state.current_step == 'appliance_co2':
        try:
            co2 = float(user_input)
            if 1 <= co2 <= 15:
                st.session_state.temp_co2 = co2
                st.session_state.current_step = 'appliance_temp'
                response = f"CO2 set to {co2}%\n\nWhat is the flue gas temperature in °F?\n\n(Typical range: 250-400°F)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a CO2% between 1 and 15.")
        except:
            add_message("assistant", "Please enter a valid CO2 percentage.")
    
    elif st.session_state.current_step == 'appliance_temp':
        try:
            temp = float(user_input)
            if 100 <= temp <= 600:
                st.session_state.temp_temp = temp
                st.session_state.current_step = 'appliance_fuel'
                response = f"Flue gas temperature set to {temp}°F\n\nWhat fuel type?\n\n1) Natural Gas\n2) LP Gas (Propane)\n3) Oil\n\nEnter 1, 2, or 3:"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a temperature between 100 and 600°F.")
        except:
            add_message("assistant", "Please enter a valid temperature.")
    
    elif st.session_state.current_step == 'appliance_fuel':
        fuel_map = {
            '1': ('natural_gas', 'Natural Gas'),
            '2': ('lp_gas', 'LP Gas'),
            '3': ('oil', 'Oil')
        }
        
        if user_input in fuel_map:
            fuel_key, fuel_name = fuel_map[user_input]
            
            # Save appliance
            appliance_num = get_current_appliance_index() + 1
            appliance = {
                'mbh': st.session_state.temp_mbh,
                'co2_percent': st.session_state.temp_co2,
                'temp_f': st.session_state.temp_temp,
                'category': st.session_state.temp_category,
                'fuel_type': fuel_key,
                'outlet_diameter': st.session_state.temp_outlet,
                'appliance_number': appliance_num
            }
            st.session_state.project_data['appliances'].append(appliance)
            
            # Clear temp data
            for key in ['temp_mbh', 'temp_co2', 'temp_temp', 'temp_category', 'temp_outlet']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Check if more appliances needed
            if appliance_num < st.session_state.project_data['num_appliances']:
                st.session_state.current_step = 'appliance_mbh'
                response = f"✓ Appliance #{appliance_num} configured: {appliance['mbh']} MBH, {fuel_name}\n\nNow let's configure Appliance #{appliance_num + 1}.\n\nWhat is the input rating in MBH?"
                add_message("assistant", response)
            else:
                st.session_state.current_step = 'connector_which'
                response = f"✓ All {appliance_num} appliances configured!\n\nNow let's configure the connectors (individual appliance to common vent).\n\nWhich appliance has the worst-case connector (longest run, most fittings)?\n\nEnter the appliance number (1-{appliance_num}):"
                add_message("assistant", response)
        else:
            add_message("assistant", "Please enter 1, 2, or 3.")
    
    elif st.session_state.current_step == 'connector_which':
        try:
            app_num = int(user_input)
            if 1 <= app_num <= len(st.session_state.project_data['appliances']):
                st.session_state.worst_connector_appliance = app_num - 1
                worst_app = st.session_state.project_data['appliances'][app_num - 1]
                min_dia = worst_app['outlet_diameter']
                st.session_state.current_step = 'connector_diameter'
                response = f"Configuring connector for Appliance #{app_num} ({worst_app['mbh']} MBH)\n\nWhat is the connector diameter in inches?\n\n⚠️ Cannot be less than appliance outlet: {min_dia}\""
                add_message("assistant", response)
            else:
                add_message("assistant", f"Please enter a number between 1 and {len(st.session_state.project_data['appliances'])}.")
        except:
            add_message("assistant", "Please enter a valid appliance number.")
    
    elif st.session_state.current_step == 'connector_diameter':
        try:
            dia = float(user_input)
            worst_app = st.session_state.project_data['appliances'][st.session_state.worst_connector_appliance]
            min_dia = worst_app['outlet_diameter']
            
            if dia >= min_dia and dia <= 24:
                st.session_state.temp_connector_dia = dia
                st.session_state.current_step = 'connector_length'
                response = f"Connector diameter: {dia}\"\n\nWhat is the total connector length in feet?"
                add_message("assistant", response)
            elif dia < min_dia:
                add_message("assistant", f"⚠️ Connector diameter ({dia}\") cannot be less than appliance outlet ({min_dia}\").\n\nPlease enter a diameter of at least {min_dia}\".")
            else:
                add_message("assistant", "Please enter a diameter between {min_dia} and 24 inches.")
        except:
            add_message("assistant", "Please enter a valid diameter.")
    
    elif st.session_state.current_step == 'connector_length':
        try:
            length = float(user_input)
            if length > 0:
                st.session_state.temp_connector_length = length
                st.session_state.current_step = 'connector_height'
                response = f"Connector length: {length} ft\n\nWhat is the vertical height (rise) of the connector in feet?\n\n(This contributes to theoretical draft. Enter 0 if horizontal only)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a positive length.")
        except:
            add_message("assistant", "Please enter a valid length in feet.")
    
    elif st.session_state.current_step == 'connector_height':
        try:
            height = float(user_input)
            if height >= 0 and height <= st.session_state.temp_connector_length:
                st.session_state.temp_connector_height = height
                st.session_state.current_step = 'connector_90'
                response = f"Connector height: {height} ft\n\nHow many 90° elbows? (Enter a whole number)"
                add_message("assistant", response)
            elif height > st.session_state.temp_connector_length:
                add_message("assistant", f"Height ({height} ft) cannot be greater than total length ({st.session_state.temp_connector_length} ft).")
            else:
                add_message("assistant", "Please enter 0 or a positive height.")
        except:
            add_message("assistant", "Please enter a valid height in feet.")
    
    elif st.session_state.current_step == 'connector_90':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_connector_90 = num
                st.session_state.current_step = 'connector_45'
                response = f"90° elbows: {num}\n\nHow many 45° elbows? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'connector_45':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_connector_45 = num
                st.session_state.current_step = 'connector_30'
                response = f"45° elbows: {num}\n\nHow many 30° elbows? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'connector_30':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_connector_30 = num
                st.session_state.current_step = 'connector_90tee'
                response = f"30° elbows: {num}\n\nHow many 90° Tees (flow through)? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'connector_90tee':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_connector_90tee = num
                st.session_state.current_step = 'connector_45tee'
                response = f"90° Tees: {num}\n\nHow many 45° Lateral Tees? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'connector_45tee':
        try:
            num = int(user_input)
            if num >= 0:
                # Build fittings dict
                fittings = {'entrance': 1}
                if st.session_state.temp_connector_90 > 0:
                    fittings['90_elbow'] = st.session_state.temp_connector_90
                if st.session_state.temp_connector_45 > 0:
                    fittings['45_elbow'] = st.session_state.temp_connector_45
                if st.session_state.temp_connector_30 > 0:
                    fittings['30_elbow'] = st.session_state.temp_connector_30
                if st.session_state.temp_connector_90tee > 0:
                    fittings['90_tee_flow_through'] = st.session_state.temp_connector_90tee
                if num > 0:
                    fittings['45_tee_lateral'] = num
                
                # Save connector configs for all appliances (simplified)
                st.session_state.project_data['connector_configs'] = []
                for i in range(len(st.session_state.project_data['appliances'])):
                    st.session_state.project_data['connector_configs'].append({
                        'diameter_inches': st.session_state.temp_connector_dia,
                        'length_ft': st.session_state.temp_connector_length,
                        'height_ft': st.session_state.temp_connector_height,
                        'fittings': fittings.copy()
                    })
                
                # Clear temp data
                for key in list(st.session_state.keys()):
                    if key.startswith('temp_connector'):
                        del st.session_state[key]
                
                st.session_state.current_step = 'manifold_diameter'
                response = f"✓ Connector configuration complete!\n\nNow let's configure the common vent (manifold).\n\nWhat is the common vent diameter in inches?"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_diameter':
        try:
            dia = float(user_input)
            if 6 <= dia <= 48:
                st.session_state.temp_manifold_dia = dia
                st.session_state.current_step = 'manifold_height'
                response = f"Common vent diameter: {dia}\"\n\nWhat is the vertical height in feet?"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a diameter between 6 and 48 inches.")
        except:
            add_message("assistant", "Please enter a valid diameter.")
    
    elif st.session_state.current_step == 'manifold_height':
        try:
            height = float(user_input)
            if height > 0:
                st.session_state.temp_manifold_height = height
                st.session_state.current_step = 'manifold_horizontal'
                response = f"Vertical height: {height} ft\n\nWhat is the horizontal run in feet? (Enter 0 if none)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter a positive height.")
        except:
            add_message("assistant", "Please enter a valid height.")
    
    elif st.session_state.current_step == 'manifold_horizontal':
        try:
            horiz = float(user_input)
            if horiz >= 0:
                st.session_state.temp_manifold_horiz = horiz
                st.session_state.current_step = 'manifold_90'
                response = f"Horizontal run: {horiz} ft\n\nHow many 90° elbows in the common vent? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a valid length.")
    
    elif st.session_state.current_step == 'manifold_90':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_manifold_90 = num
                st.session_state.current_step = 'manifold_45'
                response = f"90° elbows: {num}\n\nHow many 45° elbows? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_45':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_manifold_45 = num
                st.session_state.current_step = 'manifold_30'
                response = f"45° elbows: {num}\n\nHow many 30° elbows? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_30':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_manifold_30 = num
                st.session_state.current_step = 'manifold_90tee'
                response = f"30° elbows: {num}\n\nHow many 90° Tees (flow through)? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_90tee':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_manifold_90tee = num
                st.session_state.current_step = 'manifold_45tee'
                response = f"90° Tees: {num}\n\nHow many 45° Lateral Tees? (Enter a whole number)"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_45tee':
        try:
            num = int(user_input)
            if num >= 0:
                st.session_state.temp_manifold_45tee = num
                st.session_state.current_step = 'manifold_cap'
                response = f"45° Lateral Tees: {num}\n\nDoes the vent have a termination cap?\n\n1) Yes\n2) No\n\nEnter 1 or 2:"
                add_message("assistant", response)
            else:
                add_message("assistant", "Please enter 0 or a positive number.")
        except:
            add_message("assistant", "Please enter a whole number.")
    
    elif st.session_state.current_step == 'manifold_cap':
        if user_input in ['1', '2']:
            has_cap = (user_input == '1')
            
            # Build fittings dict
            fittings = {'exit': 1}
            if st.session_state.temp_manifold_90 > 0:
                fittings['90_elbow'] = st.session_state.temp_manifold_90
            if st.session_state.temp_manifold_45 > 0:
                fittings['45_elbow'] = st.session_state.temp_manifold_45
            if st.session_state.temp_manifold_30 > 0:
                fittings['30_elbow'] = st.session_state.temp_manifold_30
            if st.session_state.temp_manifold_90tee > 0:
                fittings['90_tee_flow_through'] = st.session_state.temp_manifold_90tee
            if st.session_state.temp_manifold_45tee > 0:
                fittings['45_tee_lateral'] = st.session_state.temp_manifold_45tee
            if has_cap:
                fittings['termination_cap'] = 1
            
            # Save manifold config
            st.session_state.project_data['manifold_config'] = {
                'diameter_inches': st.session_state.temp_manifold_dia,
                'height_ft': st.session_state.temp_manifold_height,
                'length_ft': st.session_state.temp_manifold_height + st.session_state.temp_manifold_horiz,
                'fittings': fittings
            }
            
            # Clear temp data
            for key in list(st.session_state.keys()):
                if key.startswith('temp_manifold'):
                    del st.session_state[key]
            
            # Run analysis!
            st.session_state.current_step = 'analyzing'
            response = "✓ System configuration complete!\n\n🔍 Analyzing your venting system...\n\nThis will take just a moment."
            add_message("assistant", response)
            
            # Perform calculation
            try:
                result = calc.complete_multi_appliance_analysis(
                    appliances=st.session_state.project_data['appliances'],
                    connector_configs=st.session_state.project_data['connector_configs'],
                    manifold_config=st.session_state.project_data['manifold_config'],
                    temp_outside_f=st.session_state.project_data['temp_outside_f']
                )
                st.session_state.results = result
                st.session_state.current_step = 'results'
                
                # Format results
                worst = result['worst_case']['worst_case']
                
                results_msg = f"""
✅ **ANALYSIS COMPLETE**

**WORST CASE CONNECTOR**
Appliance #{worst['appliance_id']} ({worst['appliance']['mbh']} MBH)
- Draft: {worst['connector_draft']:.4f} in w.c.
- Velocity: {worst['connector_result']['connector']['velocity_fps'] * 60:.0f} ft/min

**OPERATING SCENARIOS**
"""
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
                        results_msg += f"\n{name}: {cfm:.1f} CFM, {vel:.0f} ft/min, {draft:.4f} in w.c."
                
                # Calculate atmospheric pressure (opposite sign of draft)
                atm_pressure = -worst['total_available_draft']
                
                results_msg += f"""

**TOTAL SYSTEM (Connector + Manifold)**
- Connector Draft: {worst['connector_draft']:.4f} in w.c.
- Manifold Draft: {worst['manifold_draft']:.4f} in w.c.
- **TOTAL AVAILABLE DRAFT: {worst['total_available_draft']:.4f} in w.c.**

**PRESSURE AT APPLIANCE OUTLET**
- Atmospheric Pressure: {atm_pressure:.4f} in w.c.

⚠️ **IMPORTANT:** 
Positive draft (+) = Negative atmospheric pressure (-)
Negative draft (-) = Positive atmospheric pressure (+)

Available draft shows system capability.
Atmospheric pressure shows what appliance experiences.
Category limits are specified as atmospheric pressure.
"""
                
                # Category compliance
                if worst['appliance']['category'] != 'custom':
                    pressure_check = calc.check_appliance_pressure_limits(
                        worst['appliance'],
                        worst['total_available_draft']
                    )
                    
                    cat_info = calc.appliance_categories[worst['appliance']['category']]
                    cat_limits = cat_info['pressure_range']
                    
                    results_msg += f"\n**CATEGORY COMPLIANCE CHECK**"
                    results_msg += f"\nAppliance Category: {cat_info['name']}"
                    results_msg += f"\nRequired atmospheric pressure: {cat_limits[0]:.2f} to {cat_limits[1]:.2f} in w.c."
                    results_msg += f"\nActual atmospheric pressure: {atm_pressure:.4f} in w.c."
                    results_msg += f"\nStatus: {pressure_check['message']}"
                    
                    if not pressure_check['compliant']:
                        results_msg += f"\n⚠️ {pressure_check['recommendation']}"
                
                # Seasonal variation
                available = result['all_operating']['common_vent']['available_draft_inwc']
                winter_draft = available * 1.4
                summer_draft = available * 0.6
                
                results_msg += f"""

⚠️ **SEASONAL VARIATION ESTIMATE**
- Winter (0°F): ~{winter_draft:.4f} in w.c.
- Design ({st.session_state.project_data['temp_outside_f']}°F): ~{available:.4f} in w.c.
- Summer (95°F): ~{summer_draft:.4f} in w.c.
- Variation: {abs(winter_draft - summer_draft):.4f} in w.c. swing

**US Draft Co. draft controls are REQUIRED for year-round reliability.**

Would you like to start a new analysis? (Type 'yes' to start over)
"""
                
                add_message("assistant", results_msg)
                
            except Exception as e:
                st.session_state.current_step = 'error'
                add_message("assistant", f"⚠️ Error during analysis: {str(e)}\n\nPlease start over. Type 'restart' to begin again.")
        else:
            add_message("assistant", "Please enter 1 for Yes or 2 for No.")
    
    elif st.session_state.current_step == 'results':
        if user_input.lower() in ['yes', 'restart', 'new', 'start over']:
            # Reset everything
            st.session_state.messages = []
            st.session_state.current_step = 'welcome'
            st.session_state.project_data = {
                'appliances': [],
                'elevation_ft': 0,
                'temp_outside_f': 70,
                'connector_configs': [],
                'manifold_config': None
            }
            if 'results' in st.session_state:
                del st.session_state['results']
        else:
            add_message("assistant", "Type 'yes' or 'restart' to start a new analysis.")
    
    st.rerun()

# Footer
st.markdown("---")
st.caption("CARL v1.0 Beta | US Draft by RM Manifold | 817-393-4029")
