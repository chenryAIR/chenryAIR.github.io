# Created by Chad Henry
# Created 6.7.2025
# Last modified 6.11.2025
# Purpose: Prepare the data for the Airbnb analysis and dashboard.

# Import necessary libraries
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from statsmodels.api import Logit, add_constant
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------------------------------------
# 1. Load and Explore the Data
# ---------------------------------------------

# Load preprocessed Airbnb dataset
df = pd.read_csv('airBNB_clean.csv')

# Quick inspection of structure and missingness
print(df.info())
print(df.head())
print(df.describe())
print(df.isnull().mean() * 100)  # % missing in each column

# Set treatment variable: whether the listing had a review within the past 90 days
df['recent_review'] = df['days_since_last_review90']

# Drop listings with missing price values (n ≈ 300)
df = df[~df['price'].isna()]

# ---------------------------------------------
# 2. Estimate Propensity Scores
# ---------------------------------------------

# Define covariates to match on (confounders)
match_covariates = [
    'prior_booked',            # prior demand
    'total_avail',             # listing availability in April
    'price',                   # listing price
    'review_scores_rating',    # average review rating
    'number_of_reviews'        # volume of past reviews
]

# Standardize covariates to improve distance-based matching
scaler = StandardScaler()
X = scaler.fit_transform(df[match_covariates])

# Fit logistic regression to estimate propensity scores (P(recent_review = 1 | covariates))
ps_model = LogisticRegression()
ps_model.fit(X, df['recent_review'])

# Save propensity scores
df['propensity_score'] = ps_model.predict_proba(X)[:, 1]

# ---------------------------------------------
# 3. Perform Nearest Neighbor Matching
# ---------------------------------------------

# Separate treatment and control groups
treated = df[df['recent_review'] == 1].copy()
control = df[df['recent_review'] == 0].copy()

# Fit nearest neighbors on control group using propensity score
nn = NearestNeighbors(n_neighbors=1)
nn.fit(control[['propensity_score']])

# Match each treated case to its nearest control
distances, indices = nn.kneighbors(treated[['propensity_score']])

# Extract matched controls and align indices with treated
matched_control = control.iloc[indices.flatten()].copy()
matched_control.index = treated.index

# Combine matched treatment and control groups
matched_df = pd.concat([treated, matched_control])

# ---------------------------------------------
# 4. Visualize Propensity Score Distributions
# ---------------------------------------------

sns.histplot(treated['propensity_score'], color='blue', label='Treated', kde=True)
sns.histplot(matched_control['propensity_score'], color='red', label='Matched Control', kde=True)
plt.legend()
plt.title("Propensity Score Distribution")
plt.show()

# ---------------------------------------------
# 5. Check Covariate Balance Before and After Matching
# ---------------------------------------------

before = df.groupby('recent_review')[match_covariates].mean()
after = matched_df.groupby('recent_review')[match_covariates].mean()

print("Covariate Means Before Matching:\n", before)
print("\nCovariate Means After Matching:\n", after)

print("Number of cases after matching:", len(matched_df))
print("Treated:", matched_df['recent_review'].sum())
print("Control:", len(matched_df) - matched_df['recent_review'].sum())

# ---------------------------------------------
# 6. Estimate Treatment Effect Using Logistic Regression
# ---------------------------------------------

# Model outcome (booked_yes) using only recent_review indicator in matched data
X_logit = add_constant(matched_df[['recent_review']])
y_logit = matched_df['booked_yes']

model = Logit(y_logit, X_logit).fit()
print(model.summary())

# Report the risk difference (difference in booking rates)
treatment_mean = matched_df[matched_df['recent_review'] == 1]['booked_yes'].mean()
control_mean = matched_df[matched_df['recent_review'] == 0]['booked_yes'].mean()
print(f"Treatment effect (risk difference): {treatment_mean - control_mean:.3f}")

# ---------------------------------------------
# 7. Compute Standardized Mean Differences (SMDs)
# ---------------------------------------------

def compute_smd(df, treatment_col, covariates):
    """
    Calculate standardized mean differences for covariates
    between treatment and control groups.
    """
    treated = df[df[treatment_col] == 1]
    control = df[df[treatment_col] == 0]
    
    smd_results = []
    for cov in covariates:
        mean_treat = treated[cov].mean()
        mean_control = control[cov].mean()
        var_treat = treated[cov].var()
        var_control = control[cov].var()
        pooled_std = np.sqrt((var_treat + var_control) / 2)
        smd = (mean_treat - mean_control) / pooled_std
        smd_results.append({
            'Covariate': cov,
            'SMD': smd,
            'Mean_Treated': mean_treat,
            'Mean_Control': mean_control,
            'Pooled_Std': pooled_std
        })

    return pd.DataFrame(smd_results)

# Run and display SMDs
smd_df = compute_smd(matched_df, treatment_col='recent_review', covariates=match_covariates)
print(smd_df)
