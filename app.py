import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go

# Load model
with open('outputs/credit_scorecard_model.pkl', 'rb') as f:
    model = pickle.load(f)

# WoE mappings
woe_maps = {
    'term': {"36 months": 0.3747, "60 months": -0.8639},
    'sub_grade': {f"{g}{n}": float(i) for i, (g, n) in 
        enumerate([("A",1),("A",2),("A",3),("A",4),("A",5),
                   ("B",1),("B",2),("B",3),("B",4),("B",5),
                   ("C",1),("C",2),("C",3),("C",4),("C",5),
                   ("D",1),("D",2),("D",3),("D",4),("D",5),
                   ("E",1),("E",2),("E",3),("E",4),("E",5),
                   ("F",1),("F",2),("F",3),("F",4),("F",5),
                   ("G",1),("G",2),("G",3),("G",4),("G",5)])},
    'home_ownership': {"MORTGAGE": 0.1736, "RENT": -0.1813, 
                       "OWN": 0.2, "OTHER": -0.5},
    'verification_status': {"Not Verified": 0.3690, 
                            "Source Verified": 0.0345, 
                            "Verified": -0.2},
    'purpose': {"debt_consolidation": -0.098, "credit_card": 0.144,
                "home_improvement": 0.073, "other": -0.509,
                "major_purchase": 0.1, "medical": -0.2, 
                "small_business": -0.8}
}

# Score calculation
factor = 20 / np.log(2)
offset = 600 - factor * np.log(50)


# WoE mappings from your notebook
st.set_page_config(page_title="Credit Risk Scorecard💲", layout="wide")
st.title("Credit Risk Scorecard")
st.markdown("### Borrower Assessment Tool")

# Input fields
col1, col2, col3 = st.columns(3)

with col1:
    loan_amnt = st.number_input("Loan Amount ($)", 500, 40000, 10000)
    term = st.selectbox("Term", ["24 months","36 months", "60 months"])
    int_rate = st.slider("Interest Rate (%)", 5.0, 30.0, 13.0)
    installment = st.number_input("Monthly Installment ($)", 50, 1500, 300)

with col2:
    sub_grade = st.selectbox("Sub Grade", 
        [f"{g}{n}" for g in "ABCDEFG" for n in range(1,6)])
    home_ownership = st.selectbox("Home Ownership", 
        ["RENT", "MORTGAGE", "OWN", "OTHER"])
    annual_inc = st.number_input("Annual Income ($)", 0, 500000, 60000)
    verification_status = st.selectbox("Verification Status", 
        ["Not Verified", "Verified", "Source Verified"])

with col3:
    purpose = st.selectbox("Loan Purpose", 
        ["debt_consolidation", "credit_card", "home_improvement", 
         "other", "major_purchase", "medical", "small_business"])
    dti = st.slider("DTI Ratio", 0.0, 40.0, 15.0)
    inq_last_6mths = st.slider("Inquiries Last 6 Months", 0, 10, 1)
    revol_util = st.slider("Revolving Utilization (%)", 0.0, 100.0, 50.0)

st.markdown("---")
calculate = st.button("Calculate Credit Score", type="primary")


if calculate:

    # Build WoE feature vector
    features = np.array([[
        woe_maps['term'].get(term, 0),
        woe_maps['sub_grade'].get(sub_grade, 0),
        woe_maps['home_ownership'].get(home_ownership, 0),
        woe_maps['verification_status'].get(verification_status, 0),
        woe_maps['purpose'].get(purpose, 0),
        np.log(int_rate + 0.0001) * -0.5,
        np.log(dti + 0.0001) * -0.3,
        np.log(loan_amnt + 0.0001) * 0.1,
        np.log(installment + 0.0001) * -0.2,
        np.log(inq_last_6mths + 0.0001) * -0.3,
        np.log(annual_inc + 0.0001) * 0.2,
        np.log(revol_util + 0.0001) * -0.1
    ]])

    prob = model.predict_proba(features)[0][1]
    score = offset + factor * np.log((1 - prob) / prob)
    score = np.clip(score, 300, 850)

    # Decision
    if score >= 560:
        decision = "APPROVE"
        color = "green"
        risk = "Low Risk"
    elif score >= 530:
        decision = "REVIEW"
        color = "orange"
        risk = "Medium Risk"
    else:
        decision = "REJECT"
        color = "red"
        risk = "High Risk"

    # Display results
    col1, col2, col3 = st.columns(3)
    col1.metric("Credit Score", f"{score:.0f}")
    col2.metric("Decision", decision)
    col3.metric("Default Probability", f"{prob*100:.1f}%")

    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        gauge={
            'axis': {'range': [300, 850]},
            'bar': {'color': color},
            'steps': [
                {'range': [300, 530], 'color': '#ffcccc'},
                {'range': [530, 560], 'color': '#fff3cc'},
                {'range': [560, 850], 'color': '#ccffcc'}
            ]
        },
        title={'text': "Credit Score"}
    ))
    st.plotly_chart(fig, use_container_width=True)

# Risk Explainer
    st.markdown("### What's affecting your score?")
    factors = {
        "Interest Rate": int_rate * -2,
        "DTI Ratio": dti * -0.5,
        "Sub Grade": list("ABCDEFG").index(sub_grade[0]) * -5,
        "Loan Term": -20 if term == "60 months" else 10,
        "Inquiries": inq_last_6mths * -3,
        "Revolving Utilization": revol_util * -0.2
    }
    factors_df = pd.DataFrame.from_dict(
        factors, orient='index', columns=['Impact']
    ).sort_values('Impact')

    fig2 = go.Figure(go.Bar(
        x=factors_df['Impact'],
        y=factors_df.index,
        orientation='h',
        marker_color=['red' if x < 0 else 'green' 
                      for x in factors_df['Impact']]
    ))
    fig2.update_layout(title="Score Impact by Factor")
    st.plotly_chart(fig2, use_container_width=True)

    # SAMA/CBUAE Regulatory Flag
    st.markdown("### Regulatory Compliance (GCC)")
    if dti > 33:
        st.error("SAMA Flag: DTI exceeds 33% threshold — loan restricted")
    else:
        st.success("SAMA Compliant: DTI within acceptable limits")

    if prob > 0.4:
        st.error("CBUAE Flag: Default probability exceeds 40% threshold")
    else:
        st.success("CBUAE Compliant: Default probability within limits")    
st.markdown("---")
st.markdown("### Batch Scoring")
uploaded_file = st.file_uploader("Upload CSV of borrowers", type="csv")

if uploaded_file:
    batch_df = pd.read_csv(uploaded_file)
    
    # Apply same WoE transformations
    batch_features = np.column_stack([
        batch_df['term'].map(woe_maps['term']).fillna(0),
        batch_df['sub_grade'].map(woe_maps['sub_grade']).fillna(0),
        batch_df['home_ownership'].map(woe_maps['home_ownership']).fillna(0),
        batch_df['verification_status'].map(woe_maps['verification_status']).fillna(0),
        batch_df['purpose'].map(woe_maps['purpose']).fillna(0),
        np.log(batch_df['int_rate'] + 0.0001) * -0.5,
        np.log(batch_df['dti'] + 0.0001) * -0.3,
        np.log(batch_df['loan_amnt'] + 0.0001) * 0.1,
        np.log(batch_df['installment'] + 0.0001) * -0.2,
        np.log(batch_df['inq_last_6mths'] + 0.0001) * -0.3,
        np.log(batch_df['annual_inc'] + 0.0001) * 0.2,
        np.log(batch_df['revol_util'] + 0.0001) * -0.1
    ])

    probs = model.predict_proba(batch_features)[:, 1]
    scores = offset + factor * np.log((1 - probs) / probs)
    scores = np.clip(scores, 300, 850)

    batch_df['Credit_Score'] = scores.astype(int)
    batch_df['Default_Probability'] = (probs * 100).round(1).astype(str) + '%'
    batch_df['Decision'] = pd.cut(scores, 
        bins=[0, 530, 560, 850], 
        labels=['REJECT', 'REVIEW', 'APPROVE'])

    #st.dataframe(batch_df[['Credit_Score', 'Default_Probability', 'Decision']])

    def color_row(row):
        if row['Decision'] == 'APPROVE':
            return ['background-color: #1a5c1a; color: white'] * len(row)
        elif row['Decision'] == 'REJECT':
            return ['background-color: #7a0000; color: white'] * len(row)
        else:
            return ['background-color: #7a5c00; color: white'] * len(row)

    styled_df = batch_df[['Credit_Score', 'Default_Probability', 'Decision']].style.apply(
        color_row, axis=1
    )
    st.dataframe(styled_df)
    
    csv = batch_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results", csv, "batch_scores.csv", "text/csv")

