"""
Chimney Design Calculation Engine
Handles all thermodynamic and pressure loss calculations for chimney systems
"""

import math

class ChimneyCalculator:
    """
    Core calculation engine for chimney draft and pressure loss analysis.
    Uses standard HVAC and thermodynamic principles.
    """
    
    def __init__(self):
        # Physical constants
        self.g = 32.174  # gravitational acceleration (ft/s²)
        self.R = 53.35   # gas constant for air (ft·lbf/(lbm·°R))
        self.standard_barometric_pressure = 29.92  # inches Hg at sea level
        
        # Combustion formula for natural gas
        # M = 0.705 × (0.159 + (10.72 / CO2%))
        # Where M = lb of combustion products per 1000 BTU fuel input
        # This is the actual ASHRAE formula for natural gas
        
        # For oil, using similar empirical formula
        # M = 0.68 × (0.188 + (11.2 / CO2%))
        
        # These will be calculated in the method, not as constants
        
        # Typical CO2 percentages (reference values)
        self.typical_co2 = {
            'natural_gas': {
                'stoichiometric': 11.7,  # Perfect combustion
                'typical_range': (8.0, 10.5),  # Normal operating range
                'recommended': 9.0  # Good efficiency target
            },
            'lp_gas': {
                'stoichiometric': 13.7,  # Perfect combustion for propane
                'typical_range': (9.5, 12.0),  # Normal operating range
                'recommended': 10.5  # Good efficiency target
            },
            'oil': {
                'stoichiometric': 15.0,  # Perfect combustion
                'typical_range': (10.0, 13.0),  # Normal operating range
                'recommended': 12.0  # Good efficiency target
            }
        }
        
        # Fitting loss coefficients (K-values) organized by vent type
        # Updated from K-Values.xlsx spreadsheet
        # Values are dimensionless loss coefficients for pressure drop calculation
        self.fitting_coefficients_by_vent_type = {
            'UL441 Type B Vent': {
                'entrance': 0.5,
                '15_elbow': 0.12,
                '30_elbow': 0.12,
                '45_elbow': 0.25,
                '90_elbow': 0.75,
                'straight_tee': 1.25,     # Flow straight through tee
                '90_tee_branch': 1.25,    # 90° turn at tee (using straight tee value)
                'lateral_tee': 0.40,      # 45° lateral branch at tee
                'exit': 1.0,
                'termination_cap': 0.50,  # Stack cap
                'tee_cap': 0.3,           # Cap on tee branch (dead end)
                'base_friction_factor': 0.40  # Vent material friction factor
            },
            'UL1738 Special Gas Vent': {
                'entrance': 0.5,
                '15_elbow': 0.12,
                '30_elbow': 0.12,
                '45_elbow': 0.15,
                '90_elbow': 0.30,
                'straight_tee': 1.25,
                '90_tee_branch': 1.25,
                'lateral_tee': 0.55,
                'exit': 1.0,
                'termination_cap': 0.50,
                'tee_cap': 0.35,
                'base_friction_factor': 0.27
            },
            'UL103 Pressure Chimney': {
                'entrance': 0.5,
                '15_elbow': 0.12,
                '30_elbow': 0.12,
                '45_elbow': 0.15,
                '90_elbow': 0.30,
                'straight_tee': 1.25,
                '90_tee_branch': 1.25,
                'lateral_tee': 0.40,
                'exit': 1.0,
                'termination_cap': 0.50,
                'tee_cap': 0.25,
                'base_friction_factor': 0.30
            }
        }
        
        # Default/Generic fitting coefficients (used if vent type not specified)
        # These are conservative values
        self.fittings = {
            "entrance": 0.5,
            "15_elbow": 0.15,
            "30_elbow": 0.25,
            "45_elbow": 0.4,
            "90_elbow": 0.9,
            "straight_tee": 0.6,
            "90_tee_branch": 1.3,
            "lateral_tee": 0.8,
            "termination_cap": 1.0,
            "tee_cap": 0.6,
            "exit": 1.0
        }
        
        # Base friction factor for generic calculation
        self.base_friction_factor = 0.3
        
        # Standard vent/chimney diameters (inches)
        self.standard_diameters = [3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 24, 30, 36]
        
    def air_density(self, temp_f):
        """
        Calculate air density at given temperature.
        
        Args:
            temp_f: Temperature in Fahrenheit
            
        Returns:
            Air density in lbm/ft³
        """
        temp_r = temp_f + 459.67  # Convert to Rankine
        # Using ideal gas law: ρ = P/(R*T)
        # Assuming standard atmospheric pressure (14.7 psia = 2116.2 lbf/ft²)
        P = 2116.2  # lbf/ft²
        rho = P / (self.R * temp_r)
        return rho
    
    def mass_flow_from_fuel_input(self, mbh, co2_percent, fuel_type='natural_gas'):
        """
        Calculate flue gas mass flow rate from fuel input and CO2 percentage.
        
        ASHRAE Formulas:
        
        Natural Gas:
            M = 0.705 × (0.159 + (10.72 / %CO2))
            
        LP Gas (Propane):
            M = 0.704 × (0.144 + (12.61 / %CO2))
            
        Oil (#2 Fuel Oil):
            M = 0.72 × (0.12 + (14.4 / %CO2))
        
        Where M = lb of combustion products per 1000 BTU fuel input
        
        Mass Flow (lb/hr) = M × MBH
        Mass Flow (lb/min) = M × MBH / 60
        
        Args:
            mbh: Fuel input in MBH (thousands of BTU/hr)
            co2_percent: CO2 percentage in flue gas (e.g., 9.0 for 9%)
            fuel_type: 'natural_gas', 'lp_gas', 'propane', or 'oil'
            
        Returns:
            Dictionary with:
                - mass_flow_lbm_hr: Mass flow rate (lb/hr)
                - mass_flow_lbm_min: Mass flow rate (lb/min)
                - M_factor: M value (lb per 1000 BTU)
                - fuel_type: Type of fuel
                - mbh: Input fuel rate
                - co2_percent: CO2 percentage used
                
        Example - Natural Gas:
            100 MBH at 9% CO2:
            M = 0.705 × (0.159 + 10.72/9) = 0.9518 lb/1000 BTU
            Mass Flow = 0.9518 × 100 = 95.18 lb/hr
            At 400°F: CFM = 1.586 lb/min / 0.0461 lb/ft³ = 34.4 CFM
            
        Example - LP Gas:
            100 MBH at 10% CO2:
            M = 0.704 × (0.144 + 12.61/10) = 0.9896 lb/1000 BTU
            Mass Flow = 98.96 lb/hr
            At 400°F: CFM = 35.7 CFM
            
        Example - Oil:
            100 MBH at 12% CO2:
            M = 0.72 × (0.12 + 14.4/12) = 0.9504 lb/1000 BTU
            Mass Flow = 95.04 lb/hr
            At 500°F: CFM = 38.3 CFM
        """
        fuel_type_lower = fuel_type.lower()
        
        if fuel_type_lower in ['natural_gas', 'gas', 'ng']:
            # Natural gas formula
            M = 0.705 * (0.159 + (10.72 / co2_percent))
            fuel_name = 'natural_gas'
        elif fuel_type_lower in ['lp_gas', 'lp', 'propane', 'lpg']:
            # LP gas (propane) formula
            M = 0.704 * (0.144 + (12.61 / co2_percent))
            fuel_name = 'lp_gas'
        elif fuel_type_lower in ['oil', 'fuel_oil', '#2_oil']:
            # Oil formula
            M = 0.72 * (0.12 + (14.4 / co2_percent))
            fuel_name = 'oil'
        else:
            raise ValueError(f"Unknown fuel type: {fuel_type}. Use 'natural_gas', 'lp_gas', or 'oil'")
        
        # Calculate mass flow rate
        # M is lb per 1000 BTU, MBH is thousands of BTU/hr
        # So: mass_lbm_hr = M × (MBH × 1000) / 1000 = M × MBH
        mass_flow_lbm_hr = M * mbh
        
        # Also provide lb/min for direct CFM calculation
        mass_flow_lbm_min = mass_flow_lbm_hr / 60
        
        return {
            'mass_flow_lbm_hr': mass_flow_lbm_hr,
            'mass_flow_lbm_min': mass_flow_lbm_min,
            'M_factor': M,
            'fuel_type': fuel_name,
            'mbh': mbh,
            'co2_percent': co2_percent
        }
    
    def cfm_from_mass_flow(self, mass_flow_lbm_min, temp_f):
        """
        Calculate volumetric flow rate (CFM) from mass flow rate.
        
        Formula: CFM = mass flow rate (lb/min) / density (lb/ft³)
        
        Args:
            mass_flow_lbm_min: Mass flow rate (lb/min)
            temp_f: Flue gas temperature (°F)
            
        Returns:
            Dictionary with:
                - cfm: Volumetric flow rate (ft³/min)
                - mass_flow_lbm_min: Input mass flow
                - density_lbm_ft3: Gas density at temperature
                - temp_f: Temperature used
        """
        # Get density at flue gas temperature
        rho = self.air_density(temp_f)
        
        # Calculate CFM
        # mass_flow_lbm_min / rho = ft³/min (CFM)
        cfm = mass_flow_lbm_min / rho
        
        return {
            'cfm': cfm,
            'mass_flow_lbm_min': mass_flow_lbm_min,
            'density_lbm_ft3': rho,
            'temp_f': temp_f
        }
    
    def cfm_from_combustion(self, mbh, co2_percent, temp_f, fuel_type='natural_gas'):
        """
        Calculate CFM directly from combustion parameters.
        
        Combines mass_flow_from_fuel_input and cfm_from_mass_flow.
        
        Args:
            mbh: Fuel input in MBH (thousands of BTU/hr)
            co2_percent: CO2 percentage in flue gas
            temp_f: Flue gas temperature (°F)
            fuel_type: 'natural_gas', 'lp_gas', or 'oil'
            
        Returns:
            Dictionary with complete combustion analysis
        """
        # Get mass flow
        mass_result = self.mass_flow_from_fuel_input(mbh, co2_percent, fuel_type)
        
        # Convert to CFM using lb/min
        cfm_result = self.cfm_from_mass_flow(mass_result['mass_flow_lbm_min'], temp_f)
        
        # Combine results
        return {
            'cfm': cfm_result['cfm'],
            'mass_flow_lbm_hr': mass_result['mass_flow_lbm_hr'],
            'mass_flow_lbm_min': mass_result['mass_flow_lbm_min'],
            'M_factor': mass_result['M_factor'],
            'mbh': mbh,
            'co2_percent': co2_percent,
            'temp_f': temp_f,
            'fuel_type': mass_result['fuel_type'],
            'density_lbm_ft3': cfm_result['density_lbm_ft3']
        }
    
    def theoretical_draft(self, height_ft, temp_flue_gas_f, temp_outside_f, barometric_pressure_inHg=None):
        """
        Calculate theoretical draft using ASHRAE formula.
        
        Formula: dT = 0.2554 * B * H * (1/To - 1/Tm)
        
        Where:
            dT = Theoretical draft (inches w.c.)
            B = Barometric pressure (inches Hg)
            H = Height (ft)
            To = Outside air temperature (°R)
            Tm = Mean flue gas temperature (°R)
        
        Args:
            height_ft: Vertical height of chimney (ft)
            temp_flue_gas_f: Mean flue gas temperature (°F)
            temp_outside_f: Outside air temperature (°F)
            barometric_pressure_inHg: Barometric pressure (inches Hg), defaults to 29.92 (sea level)
            
        Returns:
            Theoretical draft in inches w.c.
        """
        # Use standard barometric pressure if not specified
        if barometric_pressure_inHg is None:
            barometric_pressure_inHg = self.standard_barometric_pressure
        
        # Convert temperatures to Rankine
        temp_outside_r = temp_outside_f + 459.67
        temp_flue_gas_r = temp_flue_gas_f + 459.67
        
        # ASHRAE formula
        draft_inwc = 0.2554 * barometric_pressure_inHg * height_ft * (1/temp_outside_r - 1/temp_flue_gas_r)
        
        return draft_inwc
    
    def velocity_from_cfm(self, cfm, diameter_inches):
        """
        Calculate gas velocity from volumetric flow rate.
        
        Args:
            cfm: Volumetric flow rate (ft³/min)
            diameter_inches: Vent inside diameter (inches)
            
        Returns:
            Velocity in ft/s
        """
        area_ft2 = math.pi * (diameter_inches / 12) ** 2 / 4
        velocity_fpm = cfm / area_ft2
        velocity_fps = velocity_fpm / 60
        return velocity_fps
    
    def cfm_from_velocity(self, velocity_fps, diameter_inches):
        """
        Calculate volumetric flow rate from velocity.
        
        Args:
            velocity_fps: Gas velocity (ft/s)
            diameter_inches: Vent inside diameter (inches)
            
        Returns:
            Volumetric flow rate in CFM
        """
        area_ft2 = math.pi * (diameter_inches / 12) ** 2 / 4
        cfm = velocity_fps * 60 * area_ft2
        return cfm
    
    def pressure_loss(self, length_ft, diameter_inches, velocity_fpm, temp_f, fittings_dict=None, 
                      vent_type=None, additional_k=0, additional_pressure_loss=0):
        """
        Calculate total pressure loss using ASHRAE equation with vent-type-specific coefficients.
        
        ASHRAE Formula: dP = (f × (L/D) + SUM(k) + additional_k) × ρ × (V/1096.2)² + additional_pressure_loss
        
        Where:
            dP = Pressure loss (inches w.c.)
            f = Base friction factor (vent-type specific, default 0.3)
            L = Length (ft)
            D = Diameter (inches)
            k = Friction coefficients of fittings (vent-type specific)
            additional_k = User-specified additional resistance
            ρ = Density at mean flue gas temperature (lbm/ft³)
            V = Velocity (FPM)
            additional_pressure_loss = User-specified pressure loss (in w.c.)
        
        Args:
            length_ft: Total vent length (ft)
            diameter_inches: Vent inside diameter (inches)
            velocity_fpm: Gas velocity (feet per minute)
            temp_f: Gas temperature (°F)
            fittings_dict: Dictionary of fittings and quantities (optional)
            vent_type: Type of vent system (UL441, UL1738, UL103) - uses specific K-values
            additional_k: Additional user-specified K resistance factor (dimensionless)
            additional_pressure_loss: Additional user-specified pressure loss (in w.c.)
            
        Returns:
            Dictionary with pressure loss breakdown in inches w.c.
        """
        # Get density at flue gas temperature
        rho = self.air_density(temp_f)
        
        # Select fitting coefficients based on vent type
        if vent_type and vent_type in self.fitting_coefficients_by_vent_type:
            fitting_k_values = self.fitting_coefficients_by_vent_type[vent_type]
            base_friction = fitting_k_values.get('base_friction_factor', 0.3)
        else:
            fitting_k_values = self.fittings
            base_friction = self.base_friction_factor
        
        # Calculate friction term: f × (L/D)
        friction_term = base_friction * (length_ft / diameter_inches)
        
        # Calculate sum of fitting k-factors using vent-type-specific values
        sum_k = 0
        fitting_breakdown = {}
        
        if fittings_dict:
            for fitting_type, quantity in fittings_dict.items():
                if fitting_type in fitting_k_values:
                    k_value = fitting_k_values[fitting_type] * quantity
                    sum_k += k_value
                    fitting_breakdown[fitting_type] = {
                        'quantity': quantity,
                        'k_each': fitting_k_values[fitting_type],
                        'k_total': k_value
                    }
                elif fitting_type in self.fittings:
                    # Fallback to generic if not in vent-specific
                    k_value = self.fittings[fitting_type] * quantity
                    sum_k += k_value
                    fitting_breakdown[fitting_type] = {
                        'quantity': quantity,
                        'k_each': self.fittings[fitting_type],
                        'k_total': k_value
                    }
        
        # Add user-specified additional K resistance
        if additional_k > 0:
            sum_k += additional_k
            fitting_breakdown['additional_k_resistance'] = {
                'quantity': 1,
                'k_each': additional_k,
                'k_total': additional_k
            }
        
        # Calculate total pressure loss using ASHRAE equation
        # dP = (f × (L/D) + SUM(k)) × ρ × (V/1096.2)²
        velocity_term = (velocity_fpm / 1096.2) ** 2
        calculated_loss = (friction_term + sum_k) * rho * velocity_term
        
        # Add user-specified additional pressure loss
        total_loss = calculated_loss + additional_pressure_loss
        
        # Calculate friction and fitting portions separately for reporting
        friction_loss = friction_term * rho * velocity_term
        fitting_loss = sum_k * rho * velocity_term
        
        return {
            'friction': friction_loss,
            'fittings': fitting_loss,
            'calculated_loss': calculated_loss,
            'additional_pressure_loss': additional_pressure_loss,
            'total': total_loss,
            'friction_term': friction_term,
            'base_friction_factor': base_friction,
            'sum_k': sum_k,
            'additional_k': additional_k,
            'fitting_breakdown': fitting_breakdown,
            'density_lbm_ft3': rho,
            'velocity_fpm': velocity_fpm,
            'vent_type': vent_type or 'Generic'
        }
    
    def total_pressure_loss(self, system_config, velocity_fps, temp_f):
        """
        Calculate total system pressure loss using ASHRAE method.
        
        Args:
            system_config: Dictionary containing:
                - 'length_ft': Total vent length
                - 'diameter_inches': Vent diameter
                - 'fittings': Dictionary of fitting types and quantities
                                e.g., {'90_elbow': 2, '45_elbow': 1}
            velocity_fps: Gas velocity (ft/s)
            temp_f: Gas temperature (°F)
            
        Returns:
            Dictionary with breakdown of losses in inches w.c.
        """
        # Convert velocity from ft/s to ft/min for ASHRAE equation
        velocity_fpm = velocity_fps * 60
        
        # Use ASHRAE pressure loss equation
        losses = self.pressure_loss(
            length_ft=system_config['length_ft'],
            diameter_inches=system_config['diameter_inches'],
            velocity_fpm=velocity_fpm,
            temp_f=temp_f,
            fittings_dict=system_config.get('fittings', {})
        )
        
        return {
            'friction': losses['friction'],
            'total_fittings': losses['fittings'],
            'total': losses['total'],
            'fittings': losses['fitting_breakdown'],
            'details': losses  # Include full ASHRAE calculation details
        }
    
    
    def available_draft(self, theoretical_draft_inwc, total_loss_inwc):
        """
        Calculate available draft for appliance.
        
        Args:
            theoretical_draft_inwc: Theoretical stack draft (inches w.c.)
            total_loss_inwc: Total system pressure loss (inches w.c.)
            
        Returns:
            Available draft in inches w.c.
        """
        return theoretical_draft_inwc - total_loss_inwc
    
    def select_diameter(self, cfm, height_ft, temp_flue_gas_f, temp_outside_f, 
                       system_config, min_available_draft_inwc, barometric_pressure_inHg=None):
        """
        Select optimal diameter that meets minimum available draft requirement.
        
        Args:
            cfm: Required volumetric flow rate
            height_ft: Chimney height
            temp_flue_gas_f: Mean flue gas temperature
            temp_outside_f: Outside air temperature
            system_config: System configuration (without diameter specified)
            min_available_draft_inwc: Minimum required available draft
            barometric_pressure_inHg: Barometric pressure (inches Hg), optional
            
        Returns:
            Dictionary with selected diameter and performance data
        """
        theoretical = self.theoretical_draft(height_ft, temp_flue_gas_f, temp_outside_f, barometric_pressure_inHg)
        
        results = []
        
        for diameter in self.standard_diameters:
            # Calculate velocity for this diameter
            velocity = self.velocity_from_cfm(cfm, diameter)
            
            # Create config with this diameter
            config = system_config.copy()
            config['diameter_inches'] = diameter
            
            # Calculate losses
            losses = self.total_pressure_loss(config, velocity, temp_flue_gas_f)
            
            # Calculate available draft
            available = self.available_draft(theoretical, losses['total'])
            
            results.append({
                'diameter_inches': diameter,
                'velocity_fps': velocity,
                'theoretical_draft_inwc': theoretical,
                'pressure_loss_inwc': losses['total'],
                'available_draft_inwc': available,
                'meets_requirement': available >= min_available_draft_inwc,
                'loss_breakdown': losses
            })
        
        # Find smallest diameter that meets requirement
        suitable = [r for r in results if r['meets_requirement']]
        
        if suitable:
            selected = suitable[0]  # Smallest diameter
            selected['all_options'] = results
            return selected
        else:
            # No diameter meets requirement
            return {
                'diameter_inches': None,
                'error': 'No standard diameter meets the minimum draft requirement',
                'all_options': results
            }
    
    def analyze_system(self, cfm, diameter_inches, height_ft, length_ft,
                      temp_flue_gas_f, temp_outside_f, fittings_dict, barometric_pressure_inHg=None):
        """
        Complete analysis of a chimney system with specified parameters.
        
        Args:
            cfm: Volumetric flow rate
            diameter_inches: Vent diameter
            height_ft: Vertical height
            length_ft: Total vent length
            temp_flue_gas_f: Mean flue gas temperature
            temp_outside_f: Outside air temperature
            fittings_dict: Dictionary of fittings and quantities
            barometric_pressure_inHg: Barometric pressure (inches Hg), optional
            
        Returns:
            Complete system analysis dictionary
        """
        # Calculate theoretical draft
        theoretical = self.theoretical_draft(height_ft, temp_flue_gas_f, temp_outside_f, barometric_pressure_inHg)
        
        # Calculate velocity
        velocity = self.velocity_from_cfm(cfm, diameter_inches)
        
        # System configuration
        config = {
            'length_ft': length_ft,
            'diameter_inches': diameter_inches,
            'fittings': fittings_dict
        }
        
        # Calculate losses
        losses = self.total_pressure_loss(config, velocity, temp_flue_gas_f)
        
        # Calculate available draft
        available = self.available_draft(theoretical, losses['total'])
        
        return {
            'cfm': cfm,
            'diameter_inches': diameter_inches,
            'velocity_fps': velocity,
            'height_ft': height_ft,
            'length_ft': length_ft,
            'temp_flue_gas_f': temp_flue_gas_f,
            'temp_outside_f': temp_outside_f,
            'barometric_pressure_inHg': barometric_pressure_inHg or self.standard_barometric_pressure,
            'theoretical_draft_inwc': theoretical,
            'pressure_loss_inwc': losses['total'],
            'available_draft_inwc': available,
            'loss_breakdown': losses,
            'fittings': fittings_dict
        }


# Example usage and testing
if __name__ == "__main__":
    calc = ChimneyCalculator()
    
    print("=" * 60)
    print("CHIMNEY CALCULATION ENGINE - TEST MODE")
    print("=" * 60)
    
    # Example system
    print("\nExample System:")
    print("  - CFM: 500")
    print("  - Height: 20 ft")
    print("  - Total Length: 25 ft")
    print("  - Flue Gas Temp: 400°F")
    print("  - Ambient Temp: 70°F")
    print("  - Fittings: 2x 90° elbows, 1x termination cap")
    
    fittings = {
        '90_elbow': 2,
        'termination_cap': 1,
        'entrance': 1,
        'exit': 1
    }
    
    # Analyze with 6-inch diameter
    print("\n" + "-" * 60)
    print("Analysis with 6-inch diameter:")
    print("-" * 60)
    
    result = calc.analyze_system(
        cfm=500,
        diameter_inches=6,
        height_ft=20,
        length_ft=25,
        temp_flue_gas_f=400,
        temp_outside_f=70,
        fittings_dict=fittings
    )
    
    print(f"\nTheoretical Draft: {result['theoretical_draft_inwc']:.4f} in w.c.")
    print(f"Gas Velocity: {result['velocity_fps']:.2f} ft/s")
    print(f"\nPressure Losses:")
    print(f"  Friction: {result['loss_breakdown']['friction']:.4f} in w.c.")
    print(f"  Fittings: {result['loss_breakdown']['total_fittings']:.4f} in w.c.")
    print(f"  Total Loss: {result['pressure_loss_inwc']:.4f} in w.c.")
    print(f"\nAvailable Draft: {result['available_draft_inwc']:.4f} in w.c.")
    
    # Automatic diameter selection
    print("\n" + "=" * 60)
    print("AUTOMATIC DIAMETER SELECTION")
    print("=" * 60)
    print("Finding smallest diameter with minimum 0.02 in w.c. available draft")
    
    system_config = {
        'length_ft': 25,
        'fittings': fittings
    }
    
    selected = calc.select_diameter(
        cfm=500,
        height_ft=20,
        temp_flue_gas_f=400,
        temp_outside_f=70,
        system_config=system_config,
        min_available_draft_inwc=0.02
    )
    
    if selected['diameter_inches']:
        print(f"\nSelected Diameter: {selected['diameter_inches']} inches")
        print(f"Velocity: {selected['velocity_fps']:.2f} ft/s")
        print(f"Available Draft: {selected['available_draft_inwc']:.4f} in w.c.")
        
        print("\nAll diameter options:")
        print(f"{'Dia (in)':<10} {'Velocity (fps)':<15} {'Loss (in wc)':<15} {'Avail (in wc)':<15} {'OK?':<5}")
        print("-" * 65)
        for opt in selected['all_options']:
            ok = "✓" if opt['meets_requirement'] else "✗"
            print(f"{opt['diameter_inches']:<10} {opt['velocity_fps']:<15.2f} "
                  f"{opt['pressure_loss_inwc']:<15.4f} {opt['available_draft_inwc']:<15.4f} {ok:<5}")
    else:
        print(f"\nError: {selected['error']}")
    
    print("\n" + "=" * 60)
    print("Available fitting types:")
    print("=" * 60)
    for fitting_name, k_factor in calc.fittings.items():
        print(f"  {fitting_name:<25} K = {k_factor}")
    
    print("\n" + "=" * 70)
    print("COMBUSTION ANALYSIS - CFM CALCULATION")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("Example 1: Natural Gas Furnace")
    print("-" * 70)
    print("Given:")
    print("  - Fuel Input: 100 MBH (100,000 BTU/hr)")
    print("  - CO2 Reading: 9.0%")
    print("  - Flue Gas Temperature: 400°F")
    
    gas_result = calc.cfm_from_combustion(
        mbh=100,
        co2_percent=9.0,
        temp_f=400,
        fuel_type='natural_gas'
    )
    
    print(f"\nResults:")
    print(f"  Mass Flow Rate: {gas_result['mass_flow_lbm_hr']:.2f} lbm/hr")
    print(f"  Gas Density at {gas_result['temp_f']}°F: {gas_result['density_lbm_ft3']:.6f} lbm/ft³")
    print(f"  Volumetric Flow Rate: {gas_result['cfm']:.1f} CFM")
    
    print("\n" + "-" * 70)
    print("Example 2: LP Gas (Propane) Water Heater")
    print("-" * 70)
    print("Given:")
    print("  - Fuel Input: 100 MBH (100,000 BTU/hr)")
    print("  - CO2 Reading: 10.5%")
    print("  - Flue Gas Temperature: 400°F")
    
    lp_result = calc.cfm_from_combustion(
        mbh=100,
        co2_percent=10.5,
        temp_f=400,
        fuel_type='lp_gas'
    )
    
    print(f"\nResults:")
    print(f"  M Factor: {lp_result['M_factor']:.4f} lb/1000 BTU")
    print(f"  Mass Flow Rate: {lp_result['mass_flow_lbm_hr']:.2f} lb/hr")
    print(f"  Gas Density at {lp_result['temp_f']}°F: {lp_result['density_lbm_ft3']:.6f} lb/ft³")
    print(f"  Volumetric Flow Rate: {lp_result['cfm']:.1f} CFM")
    
    print("\n" + "-" * 70)
    print("Example 3: Oil-Fired Boiler")
    print("-" * 70)
    print("Given:")
    print("  - Fuel Input: 200 MBH (200,000 BTU/hr)")
    print("  - CO2 Reading: 12.0%")
    print("  - Flue Gas Temperature: 500°F")
    
    oil_result = calc.cfm_from_combustion(
        mbh=200,
        co2_percent=12.0,
        temp_f=500,
        fuel_type='oil'
    )
    
    print(f"\nResults:")
    print(f"  Mass Flow Rate: {oil_result['mass_flow_lbm_hr']:.2f} lbm/hr")
    print(f"  Gas Density at {oil_result['temp_f']}°F: {oil_result['density_lbm_ft3']:.6f} lbm/ft³")
    print(f"  Volumetric Flow Rate: {oil_result['cfm']:.1f} CFM")
    
    print("\n" + "-" * 70)
    print("CO2 Percentage Impact on CFM (100 MBH Gas Furnace at 400°F)")
    print("-" * 70)
    print(f"{'CO2 %':<10} {'Mass Flow (lbm/hr)':<25} {'CFM':<20}")
    print("-" * 70)
    
    for co2 in [7.0, 8.0, 9.0, 10.0, 11.0]:
        result = calc.cfm_from_combustion(100, co2, 400, 'natural_gas')
        print(f"{co2:<10.1f} {result['mass_flow_lbm_hr']:<25.2f} {result['cfm']:<20.1f}")
    
    print("\nNote: Lower CO2 = More excess air = Higher CFM")
    print("      Higher CO2 = Less excess air = Lower CFM (more efficient)")
    
    print("\n" + "=" * 70)
    print("COMPLETE SYSTEM DESIGN WITH COMBUSTION ANALYSIS")
    print("=" * 70)
    
    print("\nScenario: Size chimney for 100 MBH gas furnace")
    print("  - CO2: 9.0%")
    print("  - Flue Gas Temp: 400°F")
    print("  - Outside Temp: 70°F")
    print("  - Height: 20 ft")
    print("  - Configuration: 25 ft total, 2× 90° elbows, cap")
    
    # Calculate CFM from combustion
    combustion = calc.cfm_from_combustion(100, 9.0, 400, 'natural_gas')
    cfm_calculated = combustion['cfm']
    
    print(f"\nStep 1 - Calculate CFM from combustion:")
    print(f"  M = 0.705 × (0.159 + (10.72 / {combustion['co2_percent']}))")
    print(f"  M = {combustion['M_factor']:.4f} lb/1000 BTU")
    print(f"  Mass flow = {combustion['M_factor']:.4f} × {combustion['mbh']} = {combustion['mass_flow_lbm_hr']:.2f} lb/hr")
    print(f"  Mass flow = {combustion['mass_flow_lbm_min']:.4f} lb/min")
    print(f"  CFM = {combustion['mass_flow_lbm_min']:.4f} / {combustion['density_lbm_ft3']:.6f}")
    print(f"  CFM = {cfm_calculated:.1f}")
    
    # Select diameter
    system_config_combustion = {
        'length_ft': 25,
        'fittings': {
            '90_elbow': 2,
            'termination_cap': 1,
            'entrance': 1,
            'exit': 1
        }
    }
    
    selected_combustion = calc.select_diameter(
        cfm=cfm_calculated,
        height_ft=20,
        temp_flue_gas_f=400,
        temp_outside_f=70,
        system_config=system_config_combustion,
        min_available_draft_inwc=0.02
    )
    
    print(f"\nStep 2 - Select diameter:")
    if selected_combustion['diameter_inches']:
        print(f"  Selected: {selected_combustion['diameter_inches']} inches")
        print(f"  Velocity: {selected_combustion['velocity_fps']:.2f} ft/s")
        print(f"  Theoretical Draft: {selected_combustion['theoretical_draft_inwc']:.4f} in w.c.")
        print(f"  Pressure Loss: {selected_combustion['pressure_loss_inwc']:.4f} in w.c.")
        print(f"  Available Draft: {selected_combustion['available_draft_inwc']:.4f} in w.c.")
    else:
        print(f"  Error: {selected_combustion['error']}")
    
    print("\n" + "=" * 70)
