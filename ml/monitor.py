from pathlib import Path

from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

from ml.train import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    load_data,
    time_split,
)

REPORT_PATH = Path("reports/data_drift_report.html")


def main():
    df = load_data()
    reference, current = time_split(df)
    print(f"reference (train period): {len(reference)} rows")
    print(f"current (test period): {len(current)} rows")

    data_definition = DataDefinition(
        numerical_columns=NUMERIC_FEATURES,
        categorical_columns=CATEGORICAL_FEATURES + [TARGET],
    )
    columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]

    reference_dataset = Dataset.from_pandas(reference[columns], data_definition=data_definition)
    current_dataset = Dataset.from_pandas(current[columns], data_definition=data_definition)

    report = Report(metrics=[DataDriftPreset()])
    snapshot = report.run(current_data=current_dataset, reference_data=reference_dataset)

    REPORT_PATH.parent.mkdir(exist_ok=True)
    snapshot.save_html(str(REPORT_PATH))
    print(f"report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
