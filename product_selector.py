"""
Product Selection and Specification Module
Helps users select the right US Draft Co. products and generates reports
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Try to import fan curves data
try:
    from fan_curves_data import FAN_CURVES
    print("✅ Successfully imported FAN_CURVES")
except ImportError as e:
    print(f"❌ ERROR: Could not import fan_curves_data: {e}")
    print(f"   Current directory: {Path.cwd()}")
    print(f"   Files in directory: {list(Path('.').glob('*.py'))}")
    FAN_CURVES = {}  # Empty dict as fallback

class ProductSelector:
    """
    Intelligent product selection based on system requirements
    """
    
    def __init__(self):
        """Initialize with fan curve data"""
        self.fan_curves = self._load_fan_curves()
        
    def _load_fan_curves(self):
        """Load fan curve data from embedded Python dictionary"""
        curves = {}
        
        if not FAN_CURVES:
            print("⚠️ WARNING: FAN_CURVES dictionary is empty!")
            print("   This means fan_curves_data.py was not imported properly")
            return curves
        
        # Convert embedded dictionary data to pandas DataFrames
        try:
            for model_name, data in FAN_CURVES.items():
                df = pd.DataFrame({
                    'CFM': data['CFM'],
                    'PRESSURE': data['PRESSURE']
                })
                curves[model_name] = df
            
            print(f"✅ Loaded {len(curves)} fan curves from embedded data")
        except Exception as e:
            print(f"❌ ERROR converting fan curves to DataFrames: {e}")
        
        return curves
    
    def get_system_recommendation(self, appliances, calc_results, user_preferences=None):
        """
        Intelligent system recommendation with guard rails
        
        Args:
            appliances: List of appliance dictionaries with category info
            calc_results: Calculation results with pressure data
            user_preferences: Dict with user's control preferences
            
        Returns:
            Dict with intelligent product recommendations and warnings
        """
        recommendation = {
            'draft_inducer_needed': True,
            'controller_type': None,
            'odcs_needed': False,
            'cds3_needed': False,
            'odcs_with_rbd': False,
            'barometric_dampers': False,
            'warnings': [],
            'notes': []
        }
        
        # Analyze appliance categories
        categories = [app.get('category', 'I').upper().replace('CAT_', '').replace('CATEGORY_', '') 
                     for app in appliances]
        all_cat_i = all(cat == 'I' for cat in categories)
        all_cat_iv = all(cat == 'IV' for cat in categories)
        has_cat_iv = any(cat == 'IV' for cat in categories)
        
        # Get unique categories
        unique_categories = set(categories)
        has_mixed_categories = len(unique_categories) > 1
        
        # GUARD RAIL: Mixed appliance categories ALWAYS need draft inducer
        if has_mixed_categories:
            recommendation['draft_inducer_needed'] = True
            recommendation['notes'].append(
                f"Mixed appliance categories detected ({', '.join(sorted(unique_categories))}). "
                "Draft inducer REQUIRED for proper venting of different appliance types."
            )
            
            # Check if turndown exists for mixed categories - need ODCS
            has_turndown = any(app.get('turndown_ratio', 1) > 1 for app in appliances)
            if has_turndown:
                recommendation['odcs_needed'] = True
                recommendation['notes'].append(
                    "Modulating appliances with turndown detected. VCS handles high fire operation. "
                    "ODCS recommended to control excessive draft at low fire."
                )
            
            # Mixed categories is complex - continue with normal controller selection
            # Don't return early - need to select controller
            # Continue to controller selection below
        else:
            # Single category - apply category-specific guard rails
            
            # Get pressure data
            worst_case = calc_results.get('worst_case', {}).get('worst_case', {})
            total_draft = worst_case.get('total_available_draft', 0)  # Negative value
            manifold_pressure = abs(total_draft)  # Positive value for comparison
            
            # GUARD RAIL 1: Category IV systems - Check if natural draft sufficient
            if all_cat_iv:
                # For Category IV, check manifold pressure requirement
                
                if manifold_pressure < 0.11:
                    # Very low pressure requirement - CDS3 for overdraft control
                    # Still recommend CDS3 to prevent code violations and maintain safe operation
                    recommendation['draft_inducer_needed'] = False
                    recommendation['odcs_needed'] = False
                    recommendation['cds3_needed'] = True
                    recommendation['controller_type'] = 'CDS3_ONLY'
                    
                    # Check if there are building heating appliances (>200 MBH indicates heating)
                    has_heating = any(app.get('mbh', 0) > 200 for app in appliances)
                    if has_heating:
                        recommendation['odcs_with_rbd'] = True
                        recommendation['notes'].append(
                            f"Category IV system with low pressure requirement ({manifold_pressure:.4f} in w.c.). "
                            "CDS3 chimney draft stabilization recommended for code compliance and safety. "
                            "ODCS with RBD available for building heating applications."
                        )
                    else:
                        recommendation['notes'].append(
                            f"Category IV system with low pressure requirement ({manifold_pressure:.4f} in w.c.). "
                            "CDS3 chimney draft stabilization recommended for code compliance and safe operation."
                        )
                    return recommendation
                else:
                    # Need mechanical draft for Cat IV
                    recommendation['draft_inducer_needed'] = True
                    recommendation['notes'].append(
                        "All Category IV appliances: Connector pressure loss is negligible due to positive pressure system. "
                        "Only manifold pressure used for fan selection."
                    )
            
            # GUARD RAIL 2: Low manifold pressure (< 0.11 in w.c.) for non-Category IV
            # Still need draft control - recommend ODCS or CDS3
            elif manifold_pressure < 0.11:
                recommendation['draft_inducer_needed'] = False
                recommendation['odcs_needed'] = True
                recommendation['controller_type'] = 'ODCS'
                recommendation['notes'].append(
                    f"Manifold pressure ({manifold_pressure:.4f} in w.c.) is under 0.11 in w.c. - "
                    "ODCS overdraft control system recommended for code compliance and safe operation."
                )
                return recommendation
        
        # GUARD RAIL 3: All Category I - ALWAYS need VCS + Barometric dampers
        # Cat I appliances ALWAYS need draft assistance and spillage protection
        if all_cat_i:
            recommendation['draft_inducer_needed'] = True
            recommendation['barometric_dampers'] = True
            recommendation['notes'].append(
                "All Category I appliances: VCS draft inducer REQUIRED for code compliance. "
                "KW Barometric Dampers recommended on all appliances for draft regulation and spillage prevention."
            )
        
        # GUARD RAIL 4: Check for turndown overdraft situation
        # High fire = More CFM = More pressure loss = Need VCS (insufficient draft)
        # Low fire = Less CFM = Less pressure loss = Overdraft (excessive draft)
        # Only recommend ODCS if low fire pressure is actually out of appliance's acceptable range
        # Category I: Barometric dampers handle low fire overdraft automatically
        # Other categories: Check if ODCS needed for low fire overdraft control
        # Skip if mixed categories already handled turndown
        has_turndown = any(app.get('turndown_ratio', 1) > 1 for app in appliances)
        
        if has_turndown and recommendation['draft_inducer_needed'] and not all_cat_i and not has_mixed_categories:
            # Check if low fire data exists and if it's out of range
            worst_low = calc_results.get('worst_case_low_fire', {})
            
            if worst_low:
                low_fire_data = worst_low.get('low_fire', {})
                low_fire_atm = -low_fire_data.get('total_available_draft', 0)
                
                # Get category limits for worst case appliance
                worst_case = calc_results.get('worst_case', {}).get('worst_case', {})
                appliance_category = worst_case.get('appliance', {}).get('category', 'cat_i')
                
                # Category pressure ranges (atmospheric pressure at appliance)
                category_limits = {
                    'cat_i': (-0.08, -0.02),
                    'cat_ii': (-0.08, -0.03),
                    'cat_iii': (0.02, 0.06),
                    'cat_iv': (0.02, 0.06)
                }
                
                limits = category_limits.get(appliance_category, (-0.08, -0.02))
                
                # Check if low fire atmospheric pressure is below lower limit (too much draft)
                if low_fire_atm < limits[0]:
                    # Low fire creates overdraft beyond category limits - need ODCS
                    recommendation['odcs_needed'] = True
                    recommendation['notes'].append(
                        f"Modulating appliances with turndown detected. VCS handles high fire operation "
                        f"(high mass flow, high pressure loss). Low fire atmospheric pressure "
                        f"({low_fire_atm:.4f} in w.c.) exceeds category limit ({limits[0]:.2f} in w.c.) - "
                        f"ODCS recommended to control excessive draft at low fire."
                    )
                else:
                    # Low fire is within range - no ODCS needed
                    recommendation['notes'].append(
                        f"Modulating appliances with turndown detected. VCS handles high fire operation. "
                        f"Low fire atmospheric pressure ({low_fire_atm:.4f} in w.c.) is within category limits - "
                        f"no overdraft control needed."
                    )
            else:
                # No low fire data available - conservative approach, recommend ODCS
                recommendation['odcs_needed'] = True
                recommendation['notes'].append(
                    "Modulating appliances with turndown detected. VCS handles high fire operation "
                    "(high mass flow, high pressure loss). ODCS recommended to control potential "
                    "excessive draft at low fire (low mass flow creates overdraft)."
                )
        elif has_turndown and recommendation['draft_inducer_needed'] and all_cat_i:
            # Category I modulating appliances - barometric dampers handle low fire overdraft
            recommendation['notes'].append(
                "Modulating appliances with turndown detected. VCS handles high fire operation "
                "(high mass flow, high pressure loss). Barometric dampers automatically regulate "
                "excessive draft at low fire."
            )
        
        # Determine controller type based on system configuration
        user_prefs = user_preferences or {}
        wants_vcs = user_prefs.get('vcs', True)
        wants_odcs = user_prefs.get('odcs', False)
        wants_pas = user_prefs.get('pas', False)
        wants_touchscreen = user_prefs.get('touchscreen', False)
        
        # Count active systems
        system_count = sum([wants_vcs, wants_odcs, wants_pas])
        
        # GUARD RAIL 5: Smart controller defaults based on system count
        # 2 systems (VCS+PAS or VCS+ODCS) → Default to V250
        # 3 systems → Default to V300 or V350
        num_appliances = len(appliances)
        
        if wants_touchscreen:
            if system_count == 2:
                # Two systems: VCS+PAS or VCS+ODCS → V250
                recommendation['controller_type'] = 'V250'
                config = []
                if wants_vcs:
                    config.append('VCS')
                if wants_odcs:
                    config.append('ODCS')
                if wants_pas:
                    config.append('PAS')
                
                config_str = '+'.join(config)
                recommendation['notes'].append(
                    f"Configuration: {config_str} with touchscreen - V250 recommended "
                    f"for 2-system applications."
                )
            elif system_count == 3:
                # Three systems → V300 or V350 based on appliance count
                if num_appliances <= 4:
                    recommendation['controller_type'] = 'V300'
                    recommendation['notes'].append(
                        f"Configuration: VCS+ODCS+PAS with touchscreen - V300 recommended "
                        f"for 3-system applications with {num_appliances} appliances."
                    )
                else:
                    recommendation['controller_type'] = 'V350'
                    recommendation['notes'].append(
                        f"Configuration: VCS+ODCS+PAS with touchscreen - V350 recommended "
                        f"for 3-system applications with {num_appliances} appliances."
                    )
            else:
                # Single system or 4+ systems
                if num_appliances <= 6:
                    recommendation['controller_type'] = 'V250'
                else:
                    recommendation['controller_type'] = 'V350'
        else:
            # LCD controller
            recommendation['controller_type'] = 'V150'
        
        return recommendation
    
    def adjust_pressure_for_categories(self, static_pressure, appliances, calc_results):
        """
        Adjust static pressure based on appliance categories
        
        For all Category IV systems, connector pressure loss should be ignored
        since these are positive pressure systems
        
        Args:
            static_pressure: Original static pressure calculation
            appliances: List of appliance dictionaries
            calc_results: Full calculation results
            
        Returns:
            Adjusted static pressure and notes
        """
        categories = [app.get('category', 'I').upper().replace('CAT_', '').replace('CATEGORY_', '') 
                     for app in appliances]
        all_cat_iv = all(cat == 'IV' for cat in categories)
        
        notes = []
        adjusted_pressure = static_pressure
        
        if all_cat_iv:
            # For all Cat IV, ignore connector loss
            worst_case = calc_results.get('worst_case', {}).get('worst_case', {})
            connector_result = worst_case.get('connector_result', {})
            connector = connector_result.get('connector', {})
            connector_loss = abs(connector.get('pressure_loss_inwc', 0))
            
            # Subtract connector loss from total requirement
            adjusted_pressure = static_pressure - connector_loss
            
            notes.append(
                f"Category IV system: Connector pressure loss ({connector_loss:.3f} in w.c.) "
                f"removed from fan selection criteria. Adjusted pressure: {adjusted_pressure:.3f} in w.c."
            )
        
        return adjusted_pressure, notes
    
    def select_draft_inducer_series(self, cfm, static_pressure, user_preference=None, mean_temp_f=300):
        """
        Select appropriate draft inducer series based on requirements
        
        Args:
            cfm: Required CFM
            static_pressure: Required static pressure (in w.c.) at mean_temp_f
            user_preference: 'CBX', 'TRV', or 'T9F' (optional)
            mean_temp_f: Mean flue gas temperature for density correction
            
        Returns:
            Dictionary with series selection and specific model
        """
        # Fan curves are at 70°F standard air
        # Need to correct system pressure to equivalent 70°F pressure
        # SP_70 = SP_actual × (ρ_70 / ρ_actual)
        
        # Calculate density ratio for correction
        rho_70 = self._air_density(70)  # lb/ft³ at 70°F
        rho_actual = self._air_density(mean_temp_f)  # lb/ft³ at actual temp
        density_ratio = rho_70 / rho_actual
        
        # Correct static pressure to 70°F equivalent
        static_pressure_70f = static_pressure * density_ratio
        
        # Define series capabilities
        series_info = {
            'TRV': {
                'name': 'TRV Series - True Inline',
                'cfm_range': (80, 2675),
                'pressure_range': (0, 3.0),
                'models': ['TRV002', 'TRV004', 'TRV011', 'TRV018', 'TRV025', 
                          'TRV035', 'TRV050', 'TRV075', 'TRV090'],
                'description': 'True inline configuration, compact design'
            },
            'T9F': {
                'name': 'T9F Series - 90° Inline',
                'cfm_range': (200, 6090),
                'pressure_range': (0, 4.0),
                'models': ['T9F004', 'T9F008', 'T9F015', 'T9F025', 'T9F035',
                          'T9F050', 'T9F075', 'T9F100', 'T9F150'],
                'description': '90° inline configuration for space savings'
            },
            'CBX': {
                'name': 'CBX Series - Termination Mount',
                'cfm_range': (215, 17000),  # CBX007 starts at 215 CFM
                'pressure_range': (0, 4.0),
                'models': ['CBX007', 'CBX013', 'CBX022', 'CBX025', 'CBX035',
                          'CBX050', 'CBX075'],
                'description': 'Mounts at top of chimney/vent'
            }
        }
        
        # If user specified preference, check if it works
        if user_preference:
            if user_preference in series_info:
                info = series_info[user_preference]
                if (info['cfm_range'][0] <= cfm <= info['cfm_range'][1] and
                    static_pressure_70f <= info['pressure_range'][1]):
                    # Find best model in preferred series
                    model = self._find_best_model(cfm, static_pressure_70f, info['models'])
                    if model:
                        return {
                            'series': user_preference,
                            'series_name': info['name'],
                            'model': model,
                            'description': info['description'],
                            'user_selected': True,
                            'corrected_pressure_70f': static_pressure_70f,
                            'actual_pressure': static_pressure,
                            'temp_correction_ratio': density_ratio
                        }
        
        # Auto-select based on requirements
        suitable_series = []
        
        for series, info in series_info.items():
            if (info['cfm_range'][0] <= cfm <= info['cfm_range'][1] and
                static_pressure_70f <= info['pressure_range'][1]):
                model = self._find_best_model(cfm, static_pressure_70f, info['models'])
                if model:
                    suitable_series.append({
                        'series': series,
                        'series_name': info['name'],
                        'model': model,
                        'description': info['description'],
                        'cfm_range': info['cfm_range'],
                        'pressure_range': info['pressure_range'],
                        'corrected_pressure_70f': static_pressure_70f,
                        'actual_pressure': static_pressure,
                        'temp_correction_ratio': density_ratio
                    })
        
        if not suitable_series:
            return None
        
        # Prefer smallest series that meets requirements
        # Priority: TRV (most compact) > T9F > CBX
        priority = {'TRV': 3, 'T9F': 2, 'CBX': 1}
        suitable_series.sort(key=lambda x: priority.get(x['series'], 0), reverse=True)
        
        result = suitable_series[0]
        result['user_selected'] = False
        result['alternatives'] = suitable_series[1:] if len(suitable_series) > 1 else []
        
        return result
    
    def get_barometric_damper_spec(self, appliances):
        """
        Get barometric damper specifications for Category I appliances
        
        Args:
            appliances: List of appliances
            
        Returns:
            List of barometric damper recommendations
        """
        dampers = []
        
        for i, app in enumerate(appliances, 1):
            category = app.get('category', 'I').upper().replace('CAT_', '').replace('CATEGORY_', '')
            
            if category == 'I':
                outlet_dia = app.get('outlet_diameter', 0)
                
                # Recommend KW barometric damper sized to appliance outlet
                dampers.append({
                    'appliance_num': i,
                    'product': 'KW Barometric Damper',
                    'size': f"{outlet_dia}\"",
                    'description': f'Field-adjustable barometric draft regulator for {outlet_dia}" outlet',
                    'purpose': 'Maintains constant overfire draft and prevents spillage'
                })
        
        return dampers
    
    def _air_density(self, temp_f):
        """
        Calculate air density at given temperature
        
        Args:
            temp_f: Temperature in Fahrenheit
            
        Returns:
            Air density in lbm/ft³
        """
        temp_r = temp_f + 459.67  # Convert to Rankine
        # Using ideal gas law: ρ = P/(R*T)
        # Standard atmospheric pressure (14.7 psia = 2116.2 lbf/ft²)
        P = 2116.2  # lbf/ft²
        R = 53.35   # ft·lbf/(lbm·°R) for air
        rho = P / (R * temp_r)
        return rho
    
    def _find_best_model(self, cfm, static_pressure, model_list):
        """
        Find the best fan model from a list that meets requirements
        
        Args:
            cfm: Required CFM
            static_pressure: Required static pressure (in w.c.)
            model_list: List of model names to check
            
        Returns:
            Model name or None
        """
        suitable_models = []
        
        for model in model_list:
            if model in self.fan_curves:
                curve_data = self.fan_curves[model]
                
                # Check if this model can deliver required CFM at required pressure
                if self._can_deliver(curve_data, cfm, static_pressure):
                    # Calculate how much excess capacity (larger = more oversized)
                    max_cfm = curve_data['CFM'].max()
                    oversize_factor = max_cfm / cfm
                    
                    suitable_models.append({
                        'model': model,
                        'max_cfm': max_cfm,
                        'oversize_factor': oversize_factor
                    })
        
        if not suitable_models:
            return None
        
        # Select model with smallest acceptable oversize (most efficient)
        suitable_models.sort(key=lambda x: x['oversize_factor'])
        return suitable_models[0]['model']
    
    def _can_deliver(self, curve_data, required_cfm, required_pressure):
        """
        Check if fan curve can deliver required CFM at required pressure
        
        Args:
            curve_data: DataFrame with CFM and PRESSURE columns
            required_cfm: Required airflow
            required_pressure: Required static pressure
            
        Returns:
            True if fan can deliver, False otherwise
        """
        try:
            cfm_values = curve_data['CFM'].values
            pressure_values = curve_data['PRESSURE'].values
            
            # Fan must be able to deliver at least required CFM
            if required_cfm > cfm_values.max():
                return False
            
            # Interpolate to find pressure at required CFM
            available_pressure = np.interp(required_cfm, cfm_values[::-1], pressure_values[::-1])
            
            # Fan must deliver at least required pressure
            return available_pressure >= required_pressure
            
        except Exception as e:
            print(f"Error checking fan capacity: {e}")
            return False
    
    def select_supply_fan(self, combustion_air_cfm, user_preference=None):
        """
        Select appropriate supply air fan for combustion air
        
        Args:
            combustion_air_cfm: Required combustion air in CFM
            user_preference: 'PRIO' or 'TAF' (optional)
            
        Returns:
            Dictionary with fan selection
        """
        # Define supply fan capabilities
        fan_info = {
            'PRIO': {
                'name': 'PRIO Series - Premium Indoor/Outdoor',
                'cfm_range': (0, 3000),
                'description': 'Premium design, indoor/outdoor rated'
            },
            'TAF': {
                'name': 'TAF Series - Termination Air Fan',
                'cfm_range': (0, 6000),
                'description': 'High capacity termination mount'
            }
        }
        
        suitable_fans = []
        
        for fan, info in fan_info.items():
            if combustion_air_cfm <= info['cfm_range'][1]:
                suitable_fans.append({
                    'series': fan,
                    'name': info['name'],
                    'description': info['description'],
                    'cfm_capacity': info['cfm_range'][1]
                })
        
        # If user has preference and it works, use it
        if user_preference and user_preference in [f['series'] for f in suitable_fans]:
            result = [f for f in suitable_fans if f['series'] == user_preference][0]
            result['user_selected'] = True
            return result
        
        # Default to PRIO if it can handle it, otherwise TAF
        if suitable_fans:
            result = suitable_fans[0]
            result['user_selected'] = False
            return result
        
        return None
    
    def select_controller(self, num_appliances, needs_vcs, needs_odcs, needs_pas, 
                         wants_touchscreen):
        """
        Select appropriate controller based on system needs
        
        Args:
            num_appliances: Number of appliances
            needs_vcs: Boolean - needs vent control system
            needs_odcs: Boolean - needs overdraft control
            needs_pas: Boolean - needs pressure air system (supply air)
            wants_touchscreen: Boolean - user wants touchscreen
            
        Returns:
            Dictionary with controller selection
        """
        # Build configuration suffix
        config_parts = []
        if needs_vcs:
            config_parts.append('V')
        if needs_pas:
            config_parts.append('P')
        if needs_odcs:
            config_parts.append('O')
        
        # Sort for consistency (alphabetical: O, P, V)
        config_parts.sort()
        config_suffix = ''.join(config_parts) if config_parts else 'V'
        
        # Select controller based on touchscreen preference and appliance count
        # V250: 1-6 appliances, 4" touchscreen
        # V300: 1-4 appliances, 7" touchscreen  
        # V350: 1-15 appliances, 7" touchscreen
        # V150: 1-2 appliances, LCD with 4 buttons
        # H100: 1 appliance, LCD
        
        if wants_touchscreen:
            # User wants touchscreen - select V250/V300/V350
            if num_appliances <= 4:
                # Could use V250, V300, or V350
                # Prefer V300 for 1-4 (better display)
                controller = f"V300-{config_suffix}"
                display = "7\" Touchscreen"
                base_model = "V300"
            elif num_appliances <= 6:
                # V250 or V350
                controller = f"V250-{config_suffix}"
                display = "4\" Touchscreen"
                base_model = "V250"
            elif num_appliances <= 15:
                # V350 only
                controller = f"V350-{config_suffix}"
                display = "7\" Touchscreen"
                base_model = "V350"
            else:
                # >15 appliances: V350
                controller = f"V350-{config_suffix}"
                display = "7\" Touchscreen"
                base_model = "V350"
            has_touchscreen = True
        else:
            # User wants LCD - select V150 or H100
            if num_appliances == 1:
                # H100 or V150
                controller = f"H100-{config_suffix}"
                display = "LCD"
                base_model = "H100"
            elif num_appliances <= 2:
                # V150
                controller = f"V150-{config_suffix}"
                display = "LCD with 4 buttons"
                base_model = "V150"
            else:
                # 3+ appliances but wants LCD - not recommended, upgrade to V250
                controller = f"V250-{config_suffix}"
                display = "4\" Touchscreen (required for 3+ appliances)"
                base_model = "V250"
                has_touchscreen = True  # Forced touchscreen
        
        return {
            'model': controller,
            'base_model': base_model,
            'display': display,
            'has_touchscreen': has_touchscreen if 'has_touchscreen' in locals() else False,
            'configuration': config_suffix,
            'max_appliances': num_appliances,
            'features': {
                'vcs': needs_vcs,
                'odcs': needs_odcs,
                'pas': needs_pas
            }
        }
    
    def plot_fan_and_system_curves(self, fan_model, system_cfm, system_pressure,
                                   title="Fan Performance Curve"):
        """
        Plot fan curve with system operating point
        
        Args:
            fan_model: Fan model name (e.g., 'TRV025')
            system_cfm: System required CFM
            system_pressure: System required pressure (in w.c.)
            title: Plot title
            
        Returns:
            matplotlib figure object
        """
        if fan_model not in self.fan_curves:
            return None
        
        curve_data = self.fan_curves[fan_model]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot fan curve
        ax.plot(curve_data['CFM'], curve_data['PRESSURE'], 
               'b-', linewidth=2, label=f'{fan_model} Performance')
        ax.fill_between(curve_data['CFM'], 0, curve_data['PRESSURE'], alpha=0.1)
        
        # Plot system operating point
        ax.plot(system_cfm, system_pressure, 'ro', markersize=10, 
               label=f'System Point ({system_cfm:.0f} CFM, {system_pressure:.3f}" w.c.)')
        
        # Create simple system curve (parabolic)
        # System curve: SP = k * Q^2, where k = SP / Q^2
        k = system_pressure / (system_cfm ** 2) if system_cfm > 0 else 0
        cfm_range = np.linspace(0, curve_data['CFM'].max(), 100)
        system_curve = k * (cfm_range ** 2)
        ax.plot(cfm_range, system_curve, 'r--', linewidth=1.5, 
               alpha=0.7, label='System Resistance Curve')
        
        # Formatting
        ax.set_xlabel('Airflow (CFM)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Static Pressure (inches w.c.)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Set reasonable axis limits
        ax.set_xlim(0, curve_data['CFM'].max() * 1.1)
        ax.set_ylim(0, curve_data['PRESSURE'].max() * 1.1)
        
        plt.tight_layout()
        return fig
    
    def get_datasheet_path(self, product_code):
        """
        Get path to product datasheet PDF
        
        Args:
            product_code: Product identifier (e.g., 'TRV', 'V250', 'CDS3')
            
        Returns:
            Path to PDF or None
        """
        # Map product codes to datasheet files
        datasheet_map = {
            'TRV': 'TRV_Data_Sheet_0125_1.pdf',
            'T9F': 'T9F_Data_Sheet_0125_1.pdf',
            'CBX': 'CBX_Data_Sheet_0126_1.pdf',
            'V150': 'V150_Data_Sheet_0125_1.pdf',
            'V250': 'V250_Data_Sheet_0125_1.pdf',
            'V300': 'V300_Data_Sheet_0125_1.pdf',
            'V350': 'V350_Data_Sheet_0125_1.pdf',
            'H100': 'H100_Data_Sheet_0125_1.pdf',
            'CDS3': 'CDS3_Brochure_0525_1.pdf',
            'PRIO': 'PRIO_Data_Sheet_0522_1.pdf',
            'TAF': 'TAF_Data_Sheet_0125_1.pdf',
            'RB': 'RB_Data_Sheet_0125_1.pdf'
        }
        
        if product_code in datasheet_map:
            path = self.project_dir / datasheet_map[product_code]
            if path.exists():
                return path
        
        return None
