# Net Cost Recovery (NCR) Simulator

A Streamlit application for simulating Net Cost Recovery scenarios for pharmaceutical products.

## Features
- **Scenario Modeling**: Simulate various Site of Care scenarios (Physician Office, Hospital Outpatient, 340B, ASC).
- **Interactive Inputs**: Adjust WAC, discounts, payer mix, and commercial markups.
- **Real-time Analysis**: Visualize Cost Basis vs. Reimbursement and Margin %.
- **HCPCS Lookup**: Mock database for product details.

## Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run ncr_app.py
   ```

## Deployment
This app is ready for deployment on Streamlit Cloud.
1. Push this repository to GitHub.
2. Connect your GitHub account to Streamlit Cloud.
3. Select the repository and the main file `ncr_app.py`.
4. Deploy!
