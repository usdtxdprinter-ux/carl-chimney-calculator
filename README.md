# CARL - Chimney Analysis and Reasoning Layer

**Multi-Appliance Venting System Analyzer**

## 🔥 Overview

CARL (Chimney Analysis and Reasoning Layer) is a professional venting system calculator designed for analyzing multi-appliance chimney configurations. Built for HVAC professionals, engineers, and contractors.

### Key Features

- ✅ **Multi-Appliance Support** - Analyze up to 6 appliances on a common vent
- ✅ **Category-Specific Analysis** - Pre-configured for Category I, II, III, and IV appliances
- ✅ **Complete System Analysis** - Connector + manifold calculations
- ✅ **Multiple Operating Scenarios** - All, all-minus-one, single largest, single smallest
- ✅ **Seasonal Variation Estimates** - Understand draft changes throughout the year
- ✅ **Professional Recommendations** - US Draft Co. product suggestions
- ✅ **ASHRAE Compliant** - Based on industry-standard formulas

## 🚀 Live Demo

**Try CARL:** Update this with your deployed URL

> **Note:** This is a beta version under active development. For production use, please contact US Draft Co.

## 📊 What CARL Calculates

- CFM requirements for each appliance and total system
- Velocity in connectors and common vent (ft/min)
- Theoretical draft (stack effect)
- Pressure losses through fittings and vent length
- Available draft at appliance outlet
- Atmospheric pressure relationship
- Category compliance checking

## ⚠️ Important Disclaimers

### Steady-State Calculation Limitations

These calculations are based on **STEADY-STATE** conditions. Actual draft will vary significantly with:

- Outdoor temperature (seasonal variations)
- Wind conditions  
- Barometric pressure changes
- Building pressure variations

**US Draft Co. draft controls are REQUIRED for consistent year-round performance.**

## 🏢 About US Draft Co.

**US Draft by RM Manifold**  
100 S Sylvania Ave  
Fort Worth, TX 76111  
Phone: 817-393-4029  
Web: www.usdraft.com

## 🔧 Run Locally

```bash
git clone https://github.com/YOUR-USERNAME/carl-chimney-calculator.git
cd carl-chimney-calculator
pip install -r requirements.txt
streamlit run streamlit_carl.py
```

## 📄 License

© 2025 US Draft by RM Manifold

**CARL v1.0 Beta** - For professional venting system design
