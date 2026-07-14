import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

df = pd.read_csv("app/ml/data/profile_features.csv")
print("Average feature values by profile type (False = fraudulent, True = legitimate):")
print(df.groupby("is_verified_owner")[["name_similarity_score","account_age_score","growth_velocity_score","metadata_completeness_score"]].mean())
