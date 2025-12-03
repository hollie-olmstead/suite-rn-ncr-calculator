import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Net Cost Recovery Simulator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling (Suite RN Branding) ---
# Red Nucleus Red: #D00000
# Reference Blue: #00558c
# Reference Green: #98c15c
st.markdown("""
    <style>
    /* Main Background */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1400px;
    }
    
    /* Headers */
    h1 {
        color: #333;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
    }
    h2, h3, h4 {
        color: #444;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Hide Sidebar completely */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    
    /* Buttons - General Reset */
    .stButton>button {
        border-radius: 4px;
        font-weight: 600;
        width: 100%;
    }

    /* Primary Button (Save Scenario) - Red */
    [data-testid="baseButton-primary"] {
        background-color: #D00000 !important;
        border-color: #D00000 !important;
        color: white !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background-color: #A00000 !important;
        border-color: #A00000 !important;
        color: white !important;
    }

    /* Secondary Button (Reset Defaults) - White/Gray */
    [data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        color: #495057 !important;
    }
    [data-testid="baseButton-secondary"]:hover {
        border-color: #D00000 !important;
        color: #D00000 !important;
        background-color: #fff !important;
    }
    
    /* Metric Cards (Top Row) */
    .metric-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 4px solid #ccc; /* Default border */
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 2rem;
        color: #212529;
        font-weight: 700;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #fff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff;
        border-bottom: 2px solid #D00000;
        color: #D00000;
        font-weight: bold;
    }
    
    /* Custom Alert/Success */
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)

# --- Mock Database for HCPCS ---
MOCK_DB = {
    "J1453": {
        "brand": "VARUBI",
        "generic": "Fosaprepitant",
        "dosage": "150 mg",
        "wac": 285.00
    },
    "J9355": {
        "brand": "HERCEPTIN",
        "generic": "Trastuzumab",
        "dosage": "150 mg vial",
        "wac": 1500.00
    },
    "J0897": {
        "brand": "XGEVA",
        "generic": "Denosumab",
        "dosage": "120 mg",
        "wac": 2500.00
    },
    "J9035": {
        "brand": "AVASTIN",
        "generic": "Bevacizumab",
        "dosage": "10 mg",
        "wac": 800.00
    },
    "J3490": {
        "brand": "Unclassified",
        "generic": "N/A",
        "dosage": "N/A",
        "wac": 5000.00
    }
}

# --- Site of Care Scenarios ---
SCENARIOS = {
    "Physician Office": {
        "discount": 0.0,
        "markup": 10,
        "mix": {"medicare": 40, "commercial": 50, "medicaid": 10},
        "description": "Standard ASP+6% reimbursement. WAC-based cost."
    },
    "Hospital Outpatient (Non-340B)": {
        "discount": 5.0, # GPO
        "markup": 50, # Higher overhead/chargemaster
        "mix": {"medicare": 50, "commercial": 35, "medicaid": 15},
        "description": "Higher commercial markups. Standard Medicare."
    },
    "340B Hospital": {
        "discount": 25.0, # 340B Discount
        "markup": 50,
        "mix": {"medicare": 50, "commercial": 30, "medicaid": 20},
        "description": "Deep acquisition cost discounts. High commercial markup."
    },
    "ASC": {
        "discount": 2.0,
        "markup": 20,
        "mix": {"medicare": 45, "commercial": 45, "medicaid": 10},
        "description": "Moderate markup and discounts."
    }
}

# --- Header ---
header_col1, header_col2 = st.columns([2.5, 1]) # Adjusted ratio to push buttons right
with header_col1:
    st.title("Net Cost Recovery Simulator")
with header_col2:
    st.write("") # Spacer
    st.write("") 
    # Use small gap to keep buttons close
    btn_col1, btn_col2 = st.columns(2, gap="small")
    with btn_col1:
        if st.button("Reset Defaults"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    with btn_col2:
        if st.button("Save Scenario", type="primary"):
            st.toast("Scenario Saved Successfully!", icon="✅")

# --- Layout: Inputs (Left) vs Analysis (Right) ---
# We need to define inputs FIRST to get values for calculation
# But we want to display Summary Metrics at the top.
# So we will render the layout structure, but populate metrics AFTER calculation.
# To do this in Streamlit, we can use placeholders or just calculate first (if inputs allow).
# Inputs need to be rendered to be interactive.
# Strategy: Render Inputs -> Calculate -> Render Metrics (at top using container) -> Render Charts.

# Create a container for the top metrics row
metrics_container = st.container()

st.markdown("---")

col_inputs, col_analysis = st.columns([1, 2], gap="large")

with col_inputs:
    st.subheader("Scenario Inputs")
    tab_general, tab_mix, tab_advanced = st.tabs(["General", "Mix", "Advanced"])

    with tab_general:
        # Site of Care Selector
        selected_scenario = st.selectbox("Select Site of Care", options=list(SCENARIOS.keys()))

        # Auto-fill logic based on selection change
        if 'last_scenario' not in st.session_state:
            st.session_state['last_scenario'] = selected_scenario

        if st.session_state['last_scenario'] != selected_scenario:
            # Update inputs
            scenario_data = SCENARIOS[selected_scenario]
            st.session_state['discount_percent'] = scenario_data['discount']
            st.session_state['commercial_markup_pct'] = scenario_data['markup']
            st.session_state['medicare_mix'] = scenario_data['mix']['medicare']
            st.session_state['commercial_mix'] = scenario_data['mix']['commercial']
            st.session_state['medicaid_mix'] = scenario_data['mix']['medicaid']
            st.session_state['last_scenario'] = selected_scenario
            st.success(f"Applied settings for {selected_scenario}")

        st.info(SCENARIOS[selected_scenario]['description'])
        
        st.markdown("#### Product")
        hcpcs_input = st.text_input("Enter HCPCS Code", placeholder="e.g., J1453").strip().upper()
        
        if 'product_details' not in st.session_state:
            st.session_state['product_details'] = None

        if st.button("Search Product"):
            if hcpcs_input in MOCK_DB:
                product = MOCK_DB[hcpcs_input]
                st.session_state['wac_val'] = product['wac']
                st.session_state['product_details'] = product
                st.success(f"Loaded: {product['brand']}")
            else:
                st.warning("Code not found. Using current WAC.")
                st.session_state['product_details'] = None

        # Display Product Details if loaded
        if st.session_state['product_details']:
            p = st.session_state['product_details']
            st.markdown(f"""
            **{p['brand']}** ({p['generic']})  
            **Dosage:** {p['dosage']}  
            **WAC Price:** ${p['wac']:,.2f}
            """)
        
        st.markdown("#### Pricing")
        if 'wac_val' not in st.session_state:
            st.session_state['wac_val'] = 5000.0

        wac = st.number_input("Drug Acquisition Cost (WAC) $", value=st.session_state['wac_val'], step=100.0, format="%.2f")
        st.session_state['wac_val'] = wac

    with tab_mix:
        st.markdown("#### Payer Mix")
        # Smart Feature: Auto-Load Regional Data
        if st.button("📍 Auto-Load Regional Data (Zip: 19103)"):
            st.session_state['medicare_mix'] = 65
            st.session_state['commercial_mix'] = 25
            st.session_state['medicaid_mix'] = 10
            st.success("Loaded data for Philadelphia, PA (19103)")

        # Initialize session state for sliders if not set
        if 'medicare_mix' not in st.session_state:
            st.session_state['medicare_mix'] = 40
        if 'commercial_mix' not in st.session_state:
            st.session_state['commercial_mix'] = 50
        if 'medicaid_mix' not in st.session_state:
            st.session_state['medicaid_mix'] = 10

        # Payer Mix Sliders
        medicare_pct = st.slider("Medicare Volume %", 0, 100, st.session_state['medicare_mix'], key='medicare_mix_slider')
        commercial_pct = st.slider("Commercial Volume %", 0, 100, st.session_state['commercial_mix'], key='commercial_mix_slider')
        medicaid_pct = st.slider("Medicaid/Other %", 0, 100, st.session_state['medicaid_mix'], key='medicaid_mix_slider')

        # Update session state from sliders (to keep sync)
        st.session_state['medicare_mix'] = medicare_pct
        st.session_state['commercial_mix'] = commercial_pct
        st.session_state['medicaid_mix'] = medicaid_pct

        # Validation
        total_mix = medicare_pct + commercial_pct + medicaid_pct
        if total_mix != 100:
            st.warning(f"⚠️ Total Mix is {total_mix}%. Ideally should be 100%.")

    with tab_advanced:
        st.markdown("#### Discounts")
        if 'discount_percent' not in st.session_state:
            st.session_state['discount_percent'] = 0.0

        discount_percent = st.slider("Contract Discount/Rebate %", 0.0, 30.0, st.session_state['discount_percent'], 0.1, key='discount_slider')
        st.session_state['discount_percent'] = discount_percent
        
        prompt_pay_discount = st.slider("Prompt Pay Discount %", 0.0, 5.0, 0.0, 0.1)

        st.markdown("#### Commercial Settings")
        comm_contract_type = st.radio("Contract Basis", ["WAC + %", "ASP + %"])
        
        if 'commercial_markup_pct' not in st.session_state:
            st.session_state['commercial_markup_pct'] = 10
            
        commercial_markup_pct = st.slider("Avg Commercial Mark-up %", 0, 100, st.session_state['commercial_markup_pct'], key='markup_slider')
        st.session_state['commercial_markup_pct'] = commercial_markup_pct
        
        bad_debt_pct = st.slider("Uncollected Copay/Bad Debt %", 0.0, 20.0, 0.0, 0.5)

        st.markdown("#### Medicare Settings")
        asp_value = st.number_input("Current ASP (if different from WAC)", value=wac, step=100.0, format="%.2f")
        apply_sequestration = st.checkbox("Apply Sequestration (2% cut on 80%)", value=True)
        
        st.markdown("#### Vial Wastage")
        calculate_wastage = st.checkbox("Calculate Vial Wastage?")
        if calculate_wastage:
            vial_size = st.number_input("Vial Size (mg)", value=100.0)
            avg_dose = st.number_input("Avg Patient Dose (mg)", value=450.0)
            comm_pays_waste = st.checkbox("Commercial Pays for Waste?", value=False)
        else:
            vial_size = 1.0
            avg_dose = 1.0
            comm_pays_waste = False

# --- Calculation Logic ---

# 0. Wastage Factors
if calculate_wastage and vial_size > 0:
    import math
    billable_units = math.ceil(avg_dose / vial_size)
    # Cost is per vial (assuming WAC is per vial for simplicity in this mode)
    # If WAC is per vial:
    units_used = billable_units # You buy full vials
    
    cost_multiplier = billable_units
    medicare_reimb_multiplier = billable_units # Medicare pays for waste
    commercial_reimb_multiplier = billable_units if comm_pays_waste else (avg_dose / vial_size) 
    
    if not comm_pays_waste:
        commercial_reimb_multiplier = avg_dose / vial_size
else:
    cost_multiplier = 1.0
    medicare_reimb_multiplier = 1.0
    commercial_reimb_multiplier = 1.0

# 1. Cost Basis
total_wac_cost = wac * cost_multiplier
total_discount_pct = (discount_percent + prompt_pay_discount) / 100
cost_basis = total_wac_cost * (1 - total_discount_pct)

# 2. Reimbursement Rates

# Medicare (ASP + 6%)
asp_unit = asp_value 
medicare_allowable_unit = asp_unit * 1.06
medicare_allowable_total = medicare_allowable_unit * medicare_reimb_multiplier

gov_portion = medicare_allowable_total * 0.80
patient_portion = medicare_allowable_total * 0.20

if apply_sequestration:
    gov_portion = gov_portion * (1 - 0.02)

# Bad Debt on Patient Portion
patient_portion_collected = patient_portion * (1 - (bad_debt_pct / 100))

reimb_medicare = gov_portion + patient_portion_collected

# Commercial
if comm_contract_type == "WAC + %":
    comm_base = wac
else:
    comm_base = asp_value

comm_allowable_unit = comm_base * (1 + (commercial_markup_pct / 100))
comm_allowable_total = comm_allowable_unit * commercial_reimb_multiplier

# Bad Debt on Commercial
reimb_commercial = comm_allowable_total * (1 - (bad_debt_pct / 100))

# Medicaid (Flat WAC)
reimb_medicaid = (wac * cost_multiplier) * 1.00 

# 3. Weighted Average Reimbursement
if total_mix > 0:
    weight_medicare = medicare_pct / total_mix
    weight_commercial = commercial_pct / total_mix
    weight_medicaid = medicaid_pct / total_mix
else:
    weight_medicare = 0
    weight_commercial = 0
    weight_medicaid = 0

weighted_reimb = (reimb_medicare * weight_medicare) + \
                 (reimb_commercial * weight_commercial) + \
                 (reimb_medicaid * weight_medicaid)

# 4. Net Recovery
net_recovery = weighted_reimb - cost_basis
margin_percent = (net_recovery / cost_basis) * 100 if cost_basis > 0 else 0

# --- Render Top Summary Metrics ---
COLOR_COST = "#00558c" # Updated Blue
COLOR_REIMB = "#98c15c" # Updated Green
COLOR_NEGATIVE = "#D00000" # Red for negative margin

with metrics_container:
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown(f"""
            <div class="metric-container" style="border-top-color: {COLOR_COST};">
                <div class="metric-label">Cost Basis</div>
                <div class="metric-value">${cost_basis:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with m_col2:
        st.markdown(f"""
            <div class="metric-container" style="border-top-color: {COLOR_REIMB};">
                <div class="metric-label">Avg Reimbursement</div>
                <div class="metric-value">${weighted_reimb:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with m_col3:
        color = COLOR_REIMB if net_recovery >= 0 else COLOR_NEGATIVE
        st.markdown(f"""
            <div class="metric-container" style="border-top-color: {color};">
                <div class="metric-label">Net Recovery</div>
                <div class="metric-value" style="color: {color};">${net_recovery:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with m_col4:
        color = COLOR_REIMB if margin_percent >= 0 else COLOR_NEGATIVE
        st.markdown(f"""
            <div class="metric-container" style="border-top-color: {color};">
                <div class="metric-label">Margin %</div>
                <div class="metric-value" style="color: {color};">{margin_percent:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

# --- Render Analysis Charts (Right Column) ---
with col_analysis:
    st.subheader("Annual Analysis")
    
    # Data for Bar Chart
    data = {
        'Category': ['Cost Basis', 'Avg Reimbursement'],
        'Amount': [cost_basis, weighted_reimb],
        'Color': ['Cost', 'Reimbursement']
    }
    df_chart = pd.DataFrame(data)
    
    fig_bar = px.bar(
        df_chart, 
        x='Category', 
        y='Amount', 
        color='Color',
        color_discrete_map={'Cost': COLOR_COST, 'Reimbursement': COLOR_REIMB},
        text_auto='$.2s'
    )
    fig_bar.update_layout(
        showlegend=False, 
        plot_bgcolor='rgba(0,0,0,0)', 
        yaxis_title="Amount ($)",
        font=dict(family="Helvetica Neue, Arial", size=14),
        height=350
    )
    fig_bar.update_traces(width=0.4) # Center columns and make them thinner
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gauge Chart (Smaller)
    gauge_color = COLOR_REIMB if margin_percent >= 0 else COLOR_NEGATIVE
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = margin_percent,
        title = {'text': "Margin %"},
        number = {'suffix': "%", 'font': {'color': gauge_color}},
        gauge = {
            'axis': {'range': [-20, 40]}, 
            'bar': {'color': gauge_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e9ecef",
            'steps': [
                {'range': [-20, 0], 'color': '#ffebee'}, # Light Red
                {'range': [0, 40], 'color': '#e8f5e9'}   # Light Green
            ],
            'threshold': {
                'line': {'color': "#333", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    fig_gauge.update_layout(
        height=250, 
        margin=dict(l=20, r=20, t=30, b=20),
        font=dict(family="Helvetica Neue, Arial")
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Detailed Breakdown
    with st.expander("See Calculation Details"):
        st.write(f"**WAC:** ${wac:,.2f}")
        if calculate_wastage:
            st.write(f"**Wastage Analysis:** Vial {vial_size}mg | Dose {avg_dose}mg -> **{billable_units} Billable Units**")
            st.write(f"**Total Cost Basis:** ${cost_basis:,.2f} (Includes {discount_percent + prompt_pay_discount}% discounts)")
        else:
            st.write(f"**Discount:** {discount_percent + prompt_pay_discount}% -> **Cost Basis:** ${cost_basis:,.2f}")
        
        st.markdown("---")
        st.write("**Reimbursement Logic:**")
        st.write(f"- Medicare (ASP+6% {'- 2% Seq' if apply_sequestration else ''}): ${reimb_medicare:,.2f}")
        st.write(f"- Commercial ({comm_contract_type} + {commercial_markup_pct}%): ${reimb_commercial:,.2f}")
        st.write(f"- Medicaid (Flat): ${reimb_medicaid:,.2f}")
        st.write(f"**Weighted Avg:** ${weighted_reimb:,.2f}")
