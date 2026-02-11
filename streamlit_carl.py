"""
CARL - Chimney Analysis and Reasoning Layer
Streamlit Web Application for Beta Testing
PUBLIC VERSION
"""

import streamlit as st
from enhanced_calculator import EnhancedChimneyCalculator
import json

# Page configuration
st.set_page_config(
    page_title="CARL - Chimney Analysis & Reasoning Layer",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize calculator
@st.cache_resource
def get_calculator():
    return EnhancedChimneyCalculator()

calc = get_calculator()

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .warning-box {
        padding: 15px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .success-box {
        padding: 15px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .danger-box {
        padding: 15px;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
    .info-box {
        padding: 15px;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'appliances' not in st.session_state:
    st.session_state.appliances = []
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'results' not in st.session_state:
    st.session_state.results = None

# Header
st.title("🔥 CARL - Chimney Analysis and Reasoning Layer")
st.markdown("### Multi-Appliance Venting System Analyzer")

# Beta notice
st.info("🧪 **BETA VERSION** - This tool is under active development. For production use, please contact US Draft Co. at 817-393-4029")

# Disclaimer
with st.expander("⚠️ IMPORTANT: Calculation Limitations & Disclaimers", expanded=False):
    st.markdown("""
    <div class="warning-box">
    <h4>Steady-State Calculation Limitations</h4>
    <p>These calculations are based on <strong>STEADY-STATE</strong> conditions at design temperatures (70°F outside). 
    Actual draft will vary significantly with:</p>
    <ul>
        <li><strong>Outdoor temperature</strong> - Seasonal variations (winter may have 40-60% higher draft, summer 30-50% lower)</li>
        <li><strong>Wind conditions</strong> - Can swing draft ±0.05 to ±0.10 in w.c. instantly</li>
        <li><strong>Barometric pressure</strong> - Changes daily with weather</li>
        <li><strong>Building pressure</strong> - HVAC systems, exhaust fans affect draft</li>
        <li><strong>Operating scenarios</strong> - Different appliance combinations</li>
    </ul>
    <p><strong>US Draft Co. draft controls are REQUIRED to maintain consistent performance 
    throughout all operating conditions and seasons.</strong></p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### 📋 Navigation")
    st.markdown(f"**Current Step:** {st.session_state.step}")
    
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.appliances = []
        st.session_state.step = 1
        st.session_state.results = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📞 Contact")
    st.markdown("""
    **US Draft by RM Manifold**  
    100 S Sylvania Ave  
    Fort Worth, TX 76111  
    📞 817-393-4029  
    🌐 [www.usdraft.com](https://www.usdraft.com)
    """)

# Main content
if st.session_state.step == 1:
    st.markdown("## Step 1: Appliance Configuration")
    
    num_appliances = st.number_input(
        "How many appliances? (1-6)", 
        min_value=1, 
        max_value=6, 
        value=1,
        help="Enter the total number of appliances that will be vented through the common vent"
    )
    
    st.markdown("---")
    
    appliances = []
    
    for i in range(num_appliances):
        st.markdown(f"### Appliance #{i+1}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mbh = st.number_input(
                f"Input Rating (MBH)", 
                min_value=1.0, 
                value=100.0,
                key=f"mbh_{i}",
                help="Appliance input in thousands of BTU per hour"
            )
            
            data_source = st.radio(
                "Combustion Data Source",
                ["Generic Category Values", "Custom Analyzer Data"],
                key=f"data_source_{i}"
            )
        
        with col2:
            fuel_type = st.selectbox(
                "Fuel Type",
                ["Natural Gas", "LP Gas (Propane)", "Oil"],
                key=f"fuel_{i}"
            )
            fuel_map = {
                "Natural Gas": "natural_gas",
                "LP Gas (Propane)": "lp_gas",
                "Oil": "oil"
            }
            
            if data_source == "Generic Category Values":
                category = st.selectbox(
                    "Appliance Category",
                    [
                        "Category I - Fan Assisted",
                        "Category II - Non-Condensing",
                        "Category III - Non-Condensing",
                        "Category IV - Condensing"
                    ],
                    key=f"category_{i}"
                )
                
                cat_map = {
                    "Category I - Fan Assisted": "cat_i_fan",
                    "Category II - Non-Condensing": "cat_ii",
                    "Category III - Non-Condensing": "cat_iii",
                    "Category IV - Condensing": "cat_iv"
                }
                cat_key = cat_map[category]
                cat_info = calc.appliance_categories[cat_key]
                
                co2 = cat_info['co2_default']
                temp = cat_info['temp_default']
                
                st.info(f"CO₂: {co2}% | Temperature: {temp}°F | Pressure: {cat_info['pressure_range'][0]} to {cat_info['pressure_range'][1]} in w.c.")
            else:
                col_a, col_b = st.columns(2)
                with col_a:
                    co2 = st.number_input(
                        "CO₂ Percentage",
                        min_value=1.0,
                        max_value=15.0,
                        value=8.5,
                        key=f"co2_{i}"
                    )
                with col_b:
                    temp = st.number_input(
                        "Flue Gas Temperature (°F)",
                        min_value=100.0,
                        max_value=600.0,
                        value=285.0,
                        key=f"temp_{i}"
                    )
                cat_key = 'custom'
        
        outlet_diameter = st.number_input(
            f"Appliance Outlet Diameter (inches)",
            min_value=3.0,
            max_value=24.0,
            value=12.0,
            step=1.0,
            key=f"outlet_{i}",
            help="Diameter of the appliance flue outlet"
        )
        
        appliances.append({
            'mbh': mbh,
            'co2_percent': co2,
            'temp_f': temp,
            'category': cat_key,
            'fuel_type': fuel_map[fuel_type],
            'outlet_diameter': outlet_diameter,
            'appliance_number': i + 1
        })
        
        st.markdown("---")
    
    if st.button("➡️ Next: Configure Connectors", use_container_width=True, type="primary"):
        st.session_state.appliances = appliances
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.markdown("## Step 2: Worst-Case Connector Configuration")
    
    st.info("Configure the worst-case appliance connector (longest run, most fittings)")
    
    worst_case_idx = st.selectbox(
        "Select worst-case appliance",
        range(len(st.session_state.appliances)),
        format_func=lambda x: f"Appliance #{x+1} ({st.session_state.appliances[x]['mbh']} MBH)"
    )
    
    st.markdown(f"### Connector for Appliance #{worst_case_idx + 1}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate suggested diameter
        worst_app = st.session_state.appliances[worst_case_idx]
        combustion = calc.cfm_from_combustion(
            mbh=worst_app['mbh'],
            co2_percent=worst_app['co2_percent'],
            temp_f=worst_app['temp_f'],
            fuel_type=worst_app['fuel_type']
        )
        
        standard_sizes = [3, 4, 5, 6, 7, 8, 10, 12]
        suggested_diameter = None
        for d in standard_sizes:
            vel = calc.velocity_from_cfm(combustion['cfm'], d)
            if 5 <= vel <= 25:
                suggested_diameter = d
                break
        if suggested_diameter is None:
            suggested_diameter = 6
        
        st.info(f"💡 Suggested: {suggested_diameter}\" diameter for {combustion['cfm']:.1f} CFM")
        
        connector_diameter = st.number_input(
            "Connector Diameter (inches)",
            min_value=3.0,
            max_value=24.0,
            value=float(suggested_diameter),
            step=1.0
        )
        
        connector_length = st.number_input(
            "Total Connector Length (ft)",
            min_value=0.0,
            value=10.0,
            step=1.0
        )
    
    with col2:
        st.markdown("**Fittings in Connector:**")
        num_90_elbow = st.number_input("90° Elbows", min_value=0, value=2, step=1)
        num_45_elbow = st.number_input("45° Elbows", min_value=0, value=0, step=1)
        num_tee = st.number_input("Tees", min_value=0, value=0, step=1)
    
    fittings = {'entrance': 1}
    if num_90_elbow > 0:
        fittings['90_elbow'] = num_90_elbow
    if num_45_elbow > 0:
        fittings['45_elbow'] = num_45_elbow
    if num_tee > 0:
        fittings['90_tee_flow_through'] = num_tee
    
    # Store connector config for all appliances (simplified - same for all)
    st.session_state.connector_configs = []
    for i in range(len(st.session_state.appliances)):
        st.session_state.connector_configs.append({
            'diameter_inches': connector_diameter,
            'length_ft': connector_length,
            'height_ft': 0,
            'fittings': fittings.copy()
        })
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("➡️ Next: Configure Common Vent", use_container_width=True, type="primary"):
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    st.markdown("## Step 3: Common Vent (Manifold) Configuration")
    
    # Calculate total CFM
    combined = calc.calculate_combined_cfm(st.session_state.appliances)
    total_cfm = combined['total_cfm']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Suggest diameter
        standard_sizes = [6, 7, 8, 10, 12, 14, 16, 18, 20, 24, 30, 36]
        suggested_diameter = None
        for d in standard_sizes:
            vel = calc.velocity_from_cfm(total_cfm, d)
            if 8 <= vel <= 20:
                suggested_diameter = d
                break
        if suggested_diameter is None:
            suggested_diameter = 12
        
        st.info(f"💡 Suggested: {suggested_diameter}\" diameter for {total_cfm:.1f} CFM total")
        
        manifold_diameter = st.number_input(
            "Common Vent Diameter (inches)",
            min_value=6.0,
            max_value=48.0,
            value=float(suggested_diameter),
            step=1.0
        )
        
        vertical_height = st.number_input(
            "Vertical Height (ft)",
            min_value=1.0,
            value=35.0,
            step=1.0
        )
        
        horizontal_run = st.number_input(
            "Horizontal Run (ft)",
            min_value=0.0,
            value=5.0,
            step=1.0
        )
    
    with col2:
        st.markdown("**Fittings in Common Vent:**")
        num_90_elbow_m = st.number_input("90° Elbows", min_value=0, value=0, step=1, key="manifold_90")
        num_45_elbow_m = st.number_input("45° Elbows", min_value=0, value=0, step=1, key="manifold_45")
        has_cap = st.checkbox("Termination Cap", value=True)
        
        st.markdown("**Conditions:**")
        temp_outside = st.number_input(
            "Outside Air Temperature (°F)",
            min_value=-20.0,
            max_value=120.0,
            value=70.0,
            step=5.0
        )
    
    fittings_m = {'exit': 1}
    if num_90_elbow_m > 0:
        fittings_m['90_elbow'] = num_90_elbow_m
    if num_45_elbow_m > 0:
        fittings_m['45_elbow'] = num_45_elbow_m
    if has_cap:
        fittings_m['termination_cap'] = 1
    
    st.session_state.manifold_config = {
        'diameter_inches': manifold_diameter,
        'height_ft': vertical_height,
        'length_ft': vertical_height + horizontal_run,
        'fittings': fittings_m
    }
    
    st.session_state.temp_outside = temp_outside
    
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("🔍 Run Analysis", use_container_width=True, type="primary"):
            # Run the analysis
            result = calc.complete_multi_appliance_analysis(
                appliances=st.session_state.appliances,
                connector_configs=st.session_state.connector_configs,
                manifold_config=st.session_state.manifold_config,
                temp_outside_f=st.session_state.temp_outside
            )
            st.session_state.results = result
            st.session_state.step = 4
            st.rerun()

elif st.session_state.step == 4:
    st.markdown("## 📊 Analysis Results")
    
    result = st.session_state.results
    worst = result['worst_case']['worst_case']
    
    # Worst case connector
    st.markdown("### Worst Case Appliance Connector")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Appliance", f"#{worst['appliance_id']} ({worst['appliance']['mbh']} MBH)")
    with col2:
        st.metric("Draft", f"{worst['connector_draft']:.4f} in w.c.")
    with col3:
        st.metric("Velocity", f"{worst['connector_result']['connector']['velocity_fps'] * 60:.0f} ft/min")
    
    # Operating scenarios
    st.markdown("### Operating Scenarios")
    
    scenarios_data = []
    for name, scenario in [
        ('All Appliances', result['all_operating']),
        ('All Minus One', result['all_minus_one']),
        ('Single Largest', result['single_largest']),
        ('Single Smallest', result['single_smallest'])
    ]:
        if scenario:
            scenarios_data.append({
                'Scenario': name,
                'CFM': f"{scenario['combined']['total_cfm']:.1f}",
                'Velocity (ft/min)': f"{scenario['common_vent']['velocity_fps'] * 60:.0f}",
                'Draft (in wc)': f"{scenario['common_vent']['available_draft_inwc']:.4f}"
            })
    
    st.dataframe(scenarios_data, use_container_width=True, hide_index=True)
    
    # Total system
    st.markdown("### Total System (Connector + Manifold)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Connector Draft", f"{worst['connector_draft']:.4f} in w.c.")
    with col2:
        st.metric("Manifold Draft", f"{worst['manifold_draft']:.4f} in w.c.")
    with col3:
        draft_val = worst['total_available_draft']
        st.metric(
            "TOTAL AVAILABLE DRAFT", 
            f"{draft_val:.4f} in w.c.",
            delta=None,
            delta_color="off" if draft_val > 0.02 else "inverse"
        )
    
    # Atmospheric pressure
    atm_pressure = -worst['total_available_draft']
    atm_sign = "negative" if atm_pressure < 0 else "positive"
    
    st.info(f"**Pressure vs. Atmosphere:** {atm_pressure:.4f} in w.c. ({atm_sign})  \n"
            f"*Note: Positive available draft = Negative to atmosphere*")
    
    # Category compliance
    if worst['appliance']['category'] != 'custom':
        pressure_check = calc.check_appliance_pressure_limits(
            worst['appliance'],
            worst['total_available_draft']
        )
        
        if pressure_check['compliant']:
            st.markdown(f"""
            <div class="success-box">
            <strong>✓ {pressure_check['message']}</strong><br>
            Category: {pressure_check['category']}<br>
            Required: {pressure_check['required_range'][0]} to {pressure_check['required_range'][1]} in w.c.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="danger-box">
            <strong>✗ {pressure_check['message']}</strong><br>
            Category: {pressure_check['category']}<br>
            Required: {pressure_check['required_range'][0]} to {pressure_check['required_range'][1]} in w.c.<br>
            <strong>⚠ {pressure_check['recommendation']}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    # Seasonal variation estimate
    st.markdown("### 🌡️ Estimated Seasonal Draft Variation")
    
    available = result['all_operating']['common_vent']['available_draft_inwc']
    winter_draft = available * 1.4
    summer_draft = available * 0.6
    
    st.markdown(f"""
    <div class="warning-box">
    <strong>Based on steady-state calculation at {st.session_state.temp_outside}°F:</strong><br>
    <ul>
        <li>Winter (0°F outside): ~{winter_draft:.4f} in w.c. (high draft)</li>
        <li>Design ({st.session_state.temp_outside}°F outside): ~{available:.4f} in w.c. (calculated)</li>
        <li>Summer (95°F outside): ~{summer_draft:.4f} in w.c. (low draft)</li>
        <li><strong>Variation range: {abs(winter_draft - summer_draft):.4f} in w.c. swing!</strong></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # US Draft Co. Recommendations
    st.markdown("---")
    st.markdown("## 🛠️ US Draft Co. Draft Control Recommendations")
    
    worst_category = worst['appliance'].get('category', 'custom')
    
    if worst_category == 'cat_i_fan':
        st.markdown("### Category I - Fan Assisted")
        if available > 0.10:
            st.markdown("""
            <div class="info-box">
            <h4>RECOMMENDED: Barometric Damper</h4>
            <ul>
                <li>Traditional solution for Cat I over-draft</li>
                <li>Mechanical regulation of excess draft</li>
                <li>Prevents over-firing in cold weather</li>
                <li>Cost-effective for Cat I applications</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        elif available < 0:
            st.markdown(f"""
            <div class="info-box">
            <h4>RECOMMENDED: US Draft Co. Draft Inducer</h4>
            <ul>
                <li>Provides mechanical draft to overcome {abs(available):.4f} in w.c. deficit</li>
                <li>Ensures consistent operation regardless of weather</li>
                <li>Reliable performance for Cat I applications</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-box">
            <h4>RECOMMENDED: Barometric Damper</h4>
            <ul>
                <li>Regulates natural draft variations</li>
                <li>Protects against seasonal over-draft</li>
                <li>Standard solution for Cat I appliances</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    elif worst_category in ['cat_ii', 'cat_iii', 'cat_iv']:
        cat_name = calc.appliance_categories[worst_category]['name']
        st.markdown(f"### {cat_name}")
        st.markdown(f"""
        <div class="success-box">
        <h4>REQUIRED: US Draft Co. CDS3 Connector Draft System</h4>
        <ul>
            <li>Maintains PERFECT DRAFT at the appliance outlet</li>
            <li>EC-Flow Technology - industry leading precision</li>
            <li>Bi-directional pressure control (positive or negative)</li>
            <li>2-second actuator responds to pressure changes</li>
            <li>4" color touchscreen - displays pressure & setpoint</li>
            <li>Protects against flue gas recirculation</li>
            <li>Meets National & International Fuel Gas Codes</li>
        </ul>
        <p><strong>⚠️ CRITICAL:</strong> Barometric dampers are NOT suitable for Category II, III, or IV appliances!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    ---
    ### 📞 Contact US Draft Co.
    **US Draft by RM Manifold**  
    100 S Sylvania Ave, Fort Worth, TX 76111  
    Phone: **817-393-4029**  
    Web: [www.usdraft.com](https://www.usdraft.com)
    """)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.appliances = []
            st.session_state.step = 1
            st.session_state.results = None
            st.rerun()
    with col2:
        # Download results as JSON
        results_json = {
            'appliances': st.session_state.appliances,
            'connector': st.session_state.connector_configs[0],
            'manifold': st.session_state.manifold_config,
            'temperature': st.session_state.temp_outside,
            'total_available_draft': worst['total_available_draft'],
            'scenarios': scenarios_data
        }
        st.download_button(
            label="📥 Download Results (JSON)",
            data=json.dumps(results_json, indent=2),
            file_name="carl_analysis.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<p><strong>CARL v1.0 Beta</strong> - Chimney Analysis and Reasoning Layer<br>
© 2025 US Draft by RM Manifold | Fort Worth, TX<br>
<em>For professional venting system design and analysis</em></p>
</div>
""", unsafe_allow_html=True)
