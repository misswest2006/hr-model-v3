import os
import pandas as pd
import joblib

from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss,
    accuracy_score
)

from sklearn.calibration import CalibratedClassifierCV


FEATURES = [
    "ISO",
    "Pitcher_HR9",
    "HardHit",
    "FlyBall",
    "BarrelRate",
    "ExitVelocity",
    "LaunchAngle",
    "RecentHRRate",
    "ParkFactor",
    "WindFactor",
    "Matchup",
]


def train():

    print("\n🚀 ADVANCED XGBOOST TRAINING STARTED\n")

    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "historical_hr_training.csv"
    )

    df = pd.read_csv(file_path)

    print(f"📊 Training Rows: {len(df)}")

    X = df[FEATURES]

    y = df["HR_Result"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    # -------------------------
    # BASE XGBOOST MODEL
    # -------------------------

    base_model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42
    )

    # -------------------------
    # SMALL DATASET FALLBACK
    # -------------------------

    if len(df) < 50:

        print("⚠️ Small dataset detected — training without calibration.")

        model = base_model

    else:

        print("✅ Using calibrated probabilities.")

        model = CalibratedClassifierCV(
            base_model,
            method="sigmoid",
            cv=3
        )

    # -------------------------
    # TRAIN MODEL
    # -------------------------

    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]

    preds = (probs >= 0.5).astype(int)

    # -------------------------
    # METRICS
    # -------------------------

    auc = roc_auc_score(y_test, probs)

    loss = log_loss(y_test, probs)

    brier = brier_score_loss(y_test, probs)

    accuracy = accuracy_score(y_test, preds)

    print("\n🔥 MODEL METRICS 🔥\n")

    print(f"AUC: {round(auc, 4)}")

    print(f"Accuracy: {round(accuracy, 4)}")

    print(f"Log Loss: {round(loss, 4)}")

    print(f"Brier Score: {round(brier, 4)}")

    # -------------------------
    # FEATURE IMPORTANCE
    # -------------------------

    print("\n📈 FEATURE IMPORTANCE\n")

    if hasattr(model, "calibrated_classifiers_"):

        fitted_model = model.calibrated_classifiers_[0].estimator

    else:

        fitted_model = model

    importance_df = pd.DataFrame({
        "Feature": FEATURES,
        "Importance": fitted_model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        by="Importance",
        ascending=False
    )

    print(importance_df)

    # -------------------------
    # SAVE MODEL
    # -------------------------

    output_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "models"
    )

    os.makedirs(output_dir, exist_ok=True)

    model_path = os.path.join(
        output_dir,
        "hr_model.pkl"
    )

    joblib.dump(model, model_path)

    print(f"\n✅ XGBoost model saved to:")
    print(model_path)

    # -------------------------
    # SAVE FEATURE IMPORTANCE
    # -------------------------

    importance_path = os.path.join(
        output_dir,
        "feature_importance.csv"
    )

    importance_df.to_csv(
        importance_path,
        index=False
    )

    print("\n✅ Feature importance saved.")

    print("\n🔥 TRAINING COMPLETE 🔥\n")


if __name__ == "__main__":

    train()