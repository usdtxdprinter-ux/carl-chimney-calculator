"""
Enhanced Chimney Calculator with Multi-Appliance Support
Supports up to 6 appliances with Category I-IV classifications
"""

from chimney_calculator import ChimneyCalculator

class EnhancedChimneyCalculator(ChimneyCalculator):
    """Extended calculator with multi-appliance and category support"""
    
    def __init__(self):
        super().__init__()
        
        # Appliance category definitions (ANSI Z21.47/CSA 2.3 categories)
        self.appliance_categories = {
            'cat_i_fan': {
                'name': 'Category I - Fan Assisted',
                'co2_default': 6.8,
                'temp_default': 320,
                'pressure_range': (-0.08, -0.03),  # (min, max) in w.c.
                'description': 'Fan-assisted with non-positive vent pressure'
            },
            'cat_ii': {
                'name': 'Category II - Non-Condensing',
                'co2_default': 8.5,
                'temp_default': 285,
                'pressure_range': (-0.08, -0.03),
                'description': 'Non-condensing with non-positive vent pressure'
            },
            'cat_iii': {
                'name': 'Category III - Non-Condensing',
                'co2_default': 8.0,
                'temp_default': 320,
                'pressure_range': (0.00, 0.08),
                'description': 'Non-condensing with positive vent pressure'
            },
            'cat_iv': {
                'name': 'Category IV - Condensing',
                'co2_default': 8.5,
                'temp_default': 275,
                'pressure_range': (-0.05, 0.25),
                'description': 'Condensing with positive vent pressure'
            }
        }
    
    def calculate_combined_cfm(self, appliances):
        """
        Calculate combined CFM for multiple appliances with adiabatic mixing
        
        When mixing flue gases at different temperatures, the combined temperature
        is calculated using energy balance (mass-weighted enthalpy).
        
        Args:
            appliances: List of appliance dicts with 'mbh', 'co2_percent', 'temp_f', 'fuel_type'
            
        Returns:
            Dictionary with combined CFM and individual results
        """
        total_cfm = 0
        total_mass_flow_lbm_min = 0
        appliance_results = []
        
        # Calculate individual appliance flows
        for i, app in enumerate(appliances):
            result = self.cfm_from_combustion(
                mbh=app['mbh'],
                co2_percent=app['co2_percent'],
                temp_f=app['temp_f'],
                fuel_type=app.get('fuel_type', 'natural_gas')
            )
            
            total_cfm += result['cfm']
            total_mass_flow_lbm_min += result['mass_flow_lbm_min']
            
            appliance_results.append({
                'appliance_id': i + 1,
                'mbh': app['mbh'],
                'cfm': result['cfm'],
                'mass_flow_lbm_min': result['mass_flow_lbm_min'],
                'temp_f': app['temp_f'],
                'temp_r': app['temp_f'] + 459.67,  # Store Rankine for mixing
                'category': app.get('category', 'custom')
            })
        
        # Adiabatic mixing: mass-weighted temperature (assumes constant Cp)
        # T_mixed = (m1*T1 + m2*T2 + ...) / (m1 + m2 + ...)
        if total_mass_flow_lbm_min > 0:
            weighted_temp_r = sum(
                app['mass_flow_lbm_min'] * app['temp_r'] 
                for app in appliance_results
            ) / total_mass_flow_lbm_min
            
            mixed_temp_f = weighted_temp_r - 459.67
        else:
            mixed_temp_f = appliances[0]['temp_f']
        
        # Recalculate combined CFM at mixed temperature
        # CFM_mixed = (m_total / ρ_mixed)
        # where ρ_mixed is density at the mixed temperature
        rho_mixed = self.air_density(mixed_temp_f)
        cfm_at_mixed_temp = total_mass_flow_lbm_min / rho_mixed
        
        return {
            'total_cfm': cfm_at_mixed_temp,
            'total_mass_flow_lbm_min': total_mass_flow_lbm_min,
            'weighted_avg_temp_f': mixed_temp_f,
            'num_appliances': len(appliances),
            'appliance_results': appliance_results,
            'mixing_info': {
                'individual_temps_f': [app['temp_f'] for app in appliance_results],
                'mixed_temp_f': mixed_temp_f,
                'density_at_mixed_temp': rho_mixed
            }
        }
    
    def analyze_connector(self, appliance, connector_config, temp_outside_f):
        """
        Analyze individual appliance connector
        
        Args:
            appliance: Dict with appliance parameters
            connector_config: Dict with connector length, diameter, fittings
            temp_outside_f: Outside temperature
            
        Returns:
            Analysis results for the connector
        """
        # Calculate CFM for single appliance
        combustion = self.cfm_from_combustion(
            mbh=appliance['mbh'],
            co2_percent=appliance['co2_percent'],
            temp_f=appliance['temp_f'],
            fuel_type=appliance.get('fuel_type', 'natural_gas')
        )
        
        # Analyze connector
        result = self.analyze_system(
            cfm=combustion['cfm'],
            diameter_inches=connector_config['diameter_inches'],
            height_ft=connector_config.get('height_ft', 0),  # Connector usually horizontal
            length_ft=connector_config['length_ft'],
            temp_flue_gas_f=appliance['temp_f'],
            temp_outside_f=temp_outside_f,
            fittings_dict=connector_config['fittings']
        )
        
        return {
            'connector': result,
            'cfm': combustion['cfm'],
            'appliance': appliance
        }
    
    def analyze_manifold_system(self, appliances, manifold_config, temp_outside_f, 
                                operating_scenario='all'):
        """
        Analyze manifolded venting system with multiple appliances
        
        Args:
            appliances: List of appliance dicts
            manifold_config: Dict with manifold/common vent configuration
            temp_outside_f: Outside temperature
            operating_scenario: 'all', 'all_minus_one', 'single_largest', or 'single_smallest'
            
        Returns:
            Complete system analysis
        """
        # Determine which appliances are operating
        if operating_scenario == 'all':
            operating = appliances
        elif operating_scenario == 'all_minus_one':
            # Remove largest appliance (one appliance down from full load)
            sorted_apps = sorted(appliances, key=lambda x: x['mbh'], reverse=True)
            operating = sorted_apps[1:]  # Remove largest, keep rest
        elif operating_scenario == 'single_largest':
            # Only largest appliance
            operating = [max(appliances, key=lambda x: x['mbh'])]
        elif operating_scenario == 'single_smallest':
            # Only smallest appliance
            operating = [min(appliances, key=lambda x: x['mbh'])]
        else:
            operating = appliances
        
        # Calculate combined CFM
        combined = self.calculate_combined_cfm(operating)
        
        # Analyze common vent
        common_result = self.analyze_system(
            cfm=combined['total_cfm'],
            diameter_inches=manifold_config['diameter_inches'],
            height_ft=manifold_config['height_ft'],
            length_ft=manifold_config['length_ft'],
            temp_flue_gas_f=combined['weighted_avg_temp_f'],
            temp_outside_f=temp_outside_f,
            fittings_dict=manifold_config['fittings']
        )
        
        return {
            'scenario': operating_scenario,
            'num_operating': len(operating),
            'combined': combined,
            'common_vent': common_result,
            'operating_appliances': operating
        }
    
    def analyze_worst_case_appliance(self, appliances, connector_configs, 
                                    manifold_config, temp_outside_f):
        """
        Complete analysis for worst-case appliance
        Connector + Manifold = Total available draft
        
        Args:
            appliances: List of all appliances
            connector_configs: Dict mapping appliance index to connector config
            manifold_config: Common vent configuration
            temp_outside_f: Outside temperature
            
        Returns:
            Complete worst-case analysis
        """
        worst_case_results = []
        
        for i, app in enumerate(appliances):
            # Analyze this appliance's connector
            connector_result = self.analyze_connector(
                appliance=app,
                connector_config=connector_configs[i],
                temp_outside_f=temp_outside_f
            )
            
            # Analyze manifold with all appliances
            manifold_all = self.analyze_manifold_system(
                appliances=appliances,
                manifold_config=manifold_config,
                temp_outside_f=temp_outside_f,
                operating_scenario='all'
            )
            
            # Total available draft = connector + manifold
            total_available_draft = (
                connector_result['connector']['available_draft_inwc'] +
                manifold_all['common_vent']['available_draft_inwc']
            )
            
            worst_case_results.append({
                'appliance_id': i + 1,
                'appliance': app,
                'connector_draft': connector_result['connector']['available_draft_inwc'],
                'manifold_draft': manifold_all['common_vent']['available_draft_inwc'],
                'total_available_draft': total_available_draft,
                'connector_result': connector_result,
                'manifold_result': manifold_all
            })
        
        # Find actual worst case (lowest total available draft)
        worst_case = min(worst_case_results, key=lambda x: x['total_available_draft'])
        
        return {
            'worst_case': worst_case,
            'all_appliances': worst_case_results
        }
    
    def complete_multi_appliance_analysis(self, appliances, connector_configs,
                                         manifold_config, temp_outside_f):
        """
        Run complete analysis for all operating scenarios
        
        Returns:
            Full analysis with all scenarios
        """
        # Scenario 1: All appliances operating
        all_operating = self.analyze_manifold_system(
            appliances=appliances,
            manifold_config=manifold_config,
            temp_outside_f=temp_outside_f,
            operating_scenario='all'
        )
        
        # Scenario 2: All minus one (if more than 1 appliance)
        all_minus_one = None
        if len(appliances) > 1:
            all_minus_one = self.analyze_manifold_system(
                appliances=appliances,
                manifold_config=manifold_config,
                temp_outside_f=temp_outside_f,
                operating_scenario='all_minus_one'
            )
        
        # Scenario 3: Single largest appliance
        single_largest = self.analyze_manifold_system(
            appliances=appliances,
            manifold_config=manifold_config,
            temp_outside_f=temp_outside_f,
            operating_scenario='single_largest'
        )
        
        # Scenario 4: Single smallest appliance (if more than 1 appliance)
        single_smallest = None
        if len(appliances) > 1:
            single_smallest = self.analyze_manifold_system(
                appliances=appliances,
                manifold_config=manifold_config,
                temp_outside_f=temp_outside_f,
                operating_scenario='single_smallest'
            )
        
        # Worst case appliance analysis
        worst_case = self.analyze_worst_case_appliance(
            appliances=appliances,
            connector_configs=connector_configs,
            manifold_config=manifold_config,
            temp_outside_f=temp_outside_f
        )
        
        return {
            'all_operating': all_operating,
            'all_minus_one': all_minus_one,
            'single_largest': single_largest,
            'single_smallest': single_smallest,
            'worst_case': worst_case,
            'num_appliances': len(appliances)
        }
    
    def check_appliance_pressure_limits(self, appliance, available_draft):
        """
        Check if available draft is within appliance category limits
        
        Args:
            appliance: Appliance dict with 'category' key
            available_draft: Available draft in in w.c.
            
        Returns:
            Dict with compliance status
        """
        if 'category' not in appliance or appliance['category'] not in self.appliance_categories:
            return {
                'compliant': None,
                'message': 'No category specified or unknown category'
            }
        
        category = self.appliance_categories[appliance['category']]
        min_pressure, max_pressure = category['pressure_range']
        
        if min_pressure <= available_draft <= max_pressure:
            return {
                'compliant': True,
                'available_draft': available_draft,
                'required_range': (min_pressure, max_pressure),
                'category': category['name'],
                'message': f"✓ Within {category['name']} limits"
            }
        else:
            if available_draft < min_pressure:
                issue = 'too_negative'
                recommendation = 'Consider draft control device'
            else:
                issue = 'too_positive'
                recommendation = 'Consider draft inducer or larger diameter'
            
            return {
                'compliant': False,
                'available_draft': available_draft,
                'required_range': (min_pressure, max_pressure),
                'category': category['name'],
                'issue': issue,
                'message': f"✗ Outside {category['name']} limits",
                'recommendation': recommendation
            }
    
    def optimize_for_draft_inducer(self, system_result, max_inducer_capacity=0.75):
        """
        Check if system can be optimized with draft inducer
        
        Args:
            system_result: System analysis result
            max_inducer_capacity: Maximum draft inducer capacity (in w.c.)
            
        Returns:
            Optimization recommendations
        """
        available = system_result['common_vent']['available_draft_inwc']
        
        if available >= 0:
            return {
                'needs_inducer': False,
                'available_draft': available,
                'message': 'System has positive draft - no inducer needed'
            }
        
        deficit = abs(available)
        
        if deficit <= max_inducer_capacity:
            return {
                'needs_inducer': True,
                'available_draft': available,
                'deficit': deficit,
                'inducer_capacity_needed': deficit,
                'can_use_inducer': True,
                'message': f'Draft inducer can compensate for {deficit:.3f} in w.c. deficit',
                'recommendation': f'US Draft Co. draft inducer rated for {deficit:.3f} in w.c. minimum'
            }
        else:
            return {
                'needs_inducer': True,
                'available_draft': available,
                'deficit': deficit,
                'inducer_capacity_needed': deficit,
                'can_use_inducer': False,
                'message': f'Deficit {deficit:.3f} in w.c. exceeds maximum inducer capacity {max_inducer_capacity} in w.c.',
                'recommendation': 'Increase diameter, reduce length, or minimize fittings'
            }
    
    def recommend_draft_control(self, system_result):
        """
        Recommend draft control if system is too negative
        
        Args:
            system_result: System analysis result
            
        Returns:
            Draft control recommendations
        """
        available = system_result['common_vent']['available_draft_inwc']
        
        if available >= -0.10:
            return {
                'needs_control': False,
                'available_draft': available,
                'message': 'Draft within acceptable range'
            }
        
        return {
            'needs_control': True,
            'available_draft': available,
            'excess_draft': abs(available),
            'message': f'Excessive draft: {abs(available):.3f} in w.c.',
            'recommendation': 'US Draft Co. over-draft control system recommended',
            'device_type': 'Barometric damper or draft regulator'
        }


if __name__ == "__main__":
    # Test the enhanced calculator
    calc = EnhancedChimneyCalculator()
    
    print("=" * 70)
    print("ENHANCED CHIMNEY CALCULATOR - MULTI-APPLIANCE TEST")
    print("=" * 70)
    
    # Example: 3 appliances on common vent
    appliances = [
        {
            'mbh': 100,
            'co2_percent': 8.5,
            'temp_f': 285,
            'category': 'cat_ii',
            'fuel_type': 'natural_gas'
        },
        {
            'mbh': 150,
            'co2_percent': 8.5,
            'temp_f': 285,
            'category': 'cat_ii',
            'fuel_type': 'natural_gas'
        },
        {
            'mbh': 200,
            'co2_percent': 8.5,
            'temp_f': 285,
            'category': 'cat_ii',
            'fuel_type': 'natural_gas'
        }
    ]
    
    # Connector configurations
    connector_configs = [
        {
            'diameter_inches': 4,
            'length_ft': 10,
            'height_ft': 0,
            'fittings': {'90_elbow': 2, 'entrance': 1}
        },
        {
            'diameter_inches': 5,
            'length_ft': 8,
            'height_ft': 0,
            'fittings': {'90_elbow': 1, 'entrance': 1}
        },
        {
            'diameter_inches': 6,
            'length_ft': 12,
            'height_ft': 0,
            'fittings': {'90_elbow': 2, 'entrance': 1}
        }
    ]
    
    # Common vent configuration
    manifold_config = {
        'diameter_inches': 10,
        'height_ft': 30,
        'length_ft': 35,
        'fittings': {
            'termination_cap': 1,
            'exit': 1
        }
    }
    
    # Run complete analysis
    result = calc.complete_multi_appliance_analysis(
        appliances=appliances,
        connector_configs=connector_configs,
        manifold_config=manifold_config,
        temp_outside_f=70
    )
    
    print(f"\nNumber of appliances: {result['num_appliances']}")
    print(f"\nAll operating CFM: {result['all_operating']['combined']['total_cfm']:.1f}")
    print(f"All operating draft: {result['all_operating']['common_vent']['available_draft_inwc']:.4f} in w.c.")
    
    if result['all_minus_one']:
        print(f"\nAll-1 operating CFM: {result['all_minus_one']['combined']['total_cfm']:.1f}")
        print(f"All-1 operating draft: {result['all_minus_one']['common_vent']['available_draft_inwc']:.4f} in w.c.")
    
    print(f"\nSingle largest CFM: {result['single_largest']['combined']['total_cfm']:.1f}")
    print(f"Single largest draft: {result['single_largest']['common_vent']['available_draft_inwc']:.4f} in w.c.")
    
    if result['single_smallest']:
        print(f"\nSingle smallest CFM: {result['single_smallest']['combined']['total_cfm']:.1f}")
        print(f"Single smallest draft: {result['single_smallest']['common_vent']['available_draft_inwc']:.4f} in w.c.")
    
    worst = result['worst_case']['worst_case']
    print(f"\nWorst case appliance: #{worst['appliance_id']}")
    print(f"  Connector draft: {worst['connector_draft']:.4f} in w.c.")
    print(f"  Manifold draft: {worst['manifold_draft']:.4f} in w.c.")
    print(f"  Total available: {worst['total_available_draft']:.4f} in w.c.")
    
    print("\n" + "=" * 70)
