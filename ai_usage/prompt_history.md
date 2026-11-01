
import argparse
from pathlib import Path
from data_generator import generate
from excursion_detector import detect
from compliance_engine import run as compliance
from validator import validate
from exporter import export
from sql_exporter import export as export_sql

def main():
    p=argparse.ArgumentParser(description='Generate and evaluate synthetic cold-chain shipment compliance data')
    p.add_argument('--shipments',type=int,default=5000); p.add_argument('--loggers',type=int,default=1000)
    p.add_argument('--seed',type=int,default=20261022); p.add_argument('--db',default='cold_chain.db')
    p.add_argument('--skip-export',action='store_true'); args=p.parse_args()
    print('Generation:',generate(args.shipments,args.loggers,args.seed,args.db,True))
    print('Excursion reports:',detect(args.db))
    print('Compliance reports:',compliance(args.db))
    validation = validate(args.db)

    print('Validation:', validation)

    if not validation['structural_checks_pass']:
        raise SystemExit(
            'Validation failed. Export cancelled.'
        )
    if not args.skip_export:
        export(args.db); export_sql(args.db)
if __name__=='__main__': main()
…
Your current main.py is a good starting point. You already have a modular pipeline with separate components for generation, excursion detection, compliance, validation and exports.

I recommend keeping your existing implementation and gradually organizing it, rather than rewriting everything.

1. Your current architecture
Your existing execution flow is:

main.py

Command-line entry point
1. data_generator.py

Generates shipments, loggers and synthetic data
2. excursion_detector.py

Detects temperature excursions
3. compliance_engine.py

Evaluates shipment compliance
4. validator.py

Checks data integrity and business rules
5. exporter.py + sql_exporter.py

Exports validated results
This is a sensible architecture for your project.

2. Recommended folder structure based on your actual imports
I would reorganize your files like this:

cold_chain_project_complete/
│
├── main.py
│
├── src/
│   ├── __init__.py
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   └── data_generator.py
│   │
│   ├── detection/
│   │   ├── __init__.py
│   │   └── excursion_detector.py
│   │
│   ├── compliance/
│   │   ├── __init__.py
│   │   └── compliance_engine.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validator.py
│   │
│   ├── exports/
│   │   ├── __init__.py
│   │   ├── exporter.py
│   │   └── sql_exporter.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── id_generator.py
│       ├── datetime_utils.py
│       └── logging_config.py
│
├── database/
│   ├── schema.sql
│   └── migrations/
│
├── config/
│   ├── settings.yaml
│   └── temperature_rules.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── tests/
│   ├── test_generator.py
│   ├── test_excursion_detector.py
│   ├── test_compliance.py
│   ├── test_validator.py
│   └── test_reproducibility.py
│
├── requirements.txt
├── README.md
└── .gitignore
This is a target structure. Some modules, such as id_generator.py and datetime_utils.py, should only be added if their responsibilities are not already implemented elsewhere.

3. Updated main.py
After moving your modules into src/, your imports will change.

I also recommend improving the argument validation and error handling.


    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--db", default="cold_chain.db")
    parser.add_argument("--skip-export", action="store_true")

    args = parser.parse_args()

    if args.shipments <= 0 or args.loggers <= 0:
        parser.error("Shipments and loggers must be positive integers.")

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n=== COLD CHAIN SIMULATION ===")

    print("\n1. Generating synthetic data...")
    generation_result = generate(
        args.shipments,
        args.loggers,
        args.seed,
        str(db_path),
        True
    )
    print("Generation:", generation_result)

    print("\n2. Detecting temperature excursions...")
    excursion_result = detect(str(db_path))
    print("Excursion reports:", excursion_result)

    print("\n3. Evaluating compliance...")
    compliance_result = compliance(str(db_path))
    print("Compliance reports:", compliance_result)

    print("\n4. Validating dataset...")
    validation = validate(str(db_path))
    print("Validation:", validation)

    if not validation.get("structural_checks_pass", False):
        raise SystemExit("Validation failed. Export cancelled.")

    print("\n5. Exporting results...")

    if not args.skip_export:
        export(str(db_path))
        export_sql(str(db_path))
        print("Exports completed.")

    print("\n=== SIMULATION COMPLETED ===")


if __name__ == "__main__":
    main()


Important: This updated entry point assumes your existing functions accept the same arguments and return compatible results as in your original code. Check their implementations before replacing your current file. Also, the structural_checks_pass condition should only gate exports if all mandatory validation categories are covered by that check or separately checked.

4. Add lifecycle and custody modules next
Based on our previous architecture review, these are the next modules I would add:

src/
├── lifecycle/
│   ├── __init__.py
│   ├── status_manager.py
│   ├── status_history.py
│   ├── custody_manager.py
│   ├── route_manager.py
│   └── event_manager.py
Their responsibilities:

File

Responsibility

status_manager.py

Validate allowed status transitions

status_history.py

Insert and retrieve historical status events

custody_manager.py

Manage custody handoffs

route_manager.py

Manage route and stop events

event_manager.py

Shared event recording and correction logic

Don't create empty files just for appearance. Implement and test each module before connecting it to main.py.

5. First, inspect your current project
Open PowerShell in your project directory and run:

tree /F

Then run:

Get-ChildItem -File

This will show us the actual files before we move anything.

My recommendation: Do not move or rename your existing modules yet. First share the output of tree /F. I can then map each existing file into the new structure, identify missing modules and give you safe PowerShell commands without breaking your currently working project.

loggers
In your cold-chain project, loggers are the physical temperature-monitoring devices attached to shipments.

You currently have a default of 1,000 loggers in your main.py:

parser.add_argument("--loggers", type=int, default=1000)

Recommended logger module structure
src/
└── loggers/
    ├── __init__.py
    ├── logger_generator.py
    ├── logger_assignment.py
    ├── logger_calibration.py
    ├── logger_events.py
    └── logger_validator.py
File

Responsibility

logger_generator.py

Generate 1,000 physical logger records

logger_assignment.py

Assign loggers to shipments

logger_calibration.py

Manage calibration dates and uncertainty

logger_events.py

Record activation, removal and malfunction

logger_validator.py

Validate assignments and logger relationships

Recommended logger database tables
1. Loggers

logger_id
serial_number
manufacturer
model
accuracy
created_at
status
2. Logger_Assignments

assignment_id
logger_id
shipment_id
assigned_at
removed_at
assignment_status
3. Calibration_Records

calibration_id
logger_id
calibration_date
expiry_date
uncertainty
certificate_reference
4. Logger_Events

logger_event_id
logger_id
assignment_id
event_type
event_time
recorded_at
remarks
Important relationship
One physical logger can be reused across multiple shipments, but its assignments must have separate records.

LOGGER-001
    |
    ├── Assignment 001 → SHP-001
    |
    ├── Assignment 002 → SHP-005
    |
    └── Assignment 003 → SHP-010
Temperature readings should reference assignment_id, so historical readings remain linked to the correct shipment.

One important question: Are you asking me to add a loggers/ folder to your project structure, or do you want the complete Python code for generating and assigning 1,000 loggers?

excursions
In your cold-chain project, excursions represent periods when shipment temperatures go outside the permitted temperature range.

For example, if a product must remain between 2°C and 8°C, a reading of 10°C may indicate a temperature excursion, depending on your detection and duration rules.

1. Recommended excursions folder structure
src/
└── detection/
    ├── __init__.py
    ├── excursion_detector.py
    ├── excursion_classifier.py
    ├── duration_calculator.py
    ├── excursion_validator.py
    ├── ground_truth.py
    └── excursion_repository.py
2. Responsibilities of each file
File

Responsibility

excursion_detector.py

Identify readings outside permitted limits

excursion_classifier.py

Classify excursion type: HIGH or LOW

duration_calculator.py

Calculate excursion start, end and duration

excursion_validator.py

Validate detected excursion records

ground_truth.py

Maintain independently generated expected excursion labels

excursion_repository.py

Save and retrieve excursion records

3. Recommended database tables
A. Excursions

excursion_id       PRIMARY KEY
shipment_id        FOREIGN KEY
assignment_id      FOREIGN KEY
excursion_type
start_time
end_time
duration_minutes
min_observed_temp
max_observed_temp
severity
detection_status
detected_at
B. Excursion_Readings

excursion_reading_id    PRIMARY KEY
excursion_id            FOREIGN KEY
reading_id              FOREIGN KEY
This junction table allows you to identify exactly which temperature readings contributed to each excursion.

C. Ground_Truth_Excursions

ground_truth_id
shipment_id
assignment_id
expected_type
expected_start_time
expected_end_time
expected_duration
scenario_id
Keep ground truth separate from detected excursions. Otherwise, your detection algorithm could accidentally use the expected answers.

4. Excursion detection workflow
Temperature readings

Readings linked to logger assignments
Temperature limit validation

Compare readings with applicable product policy
Excursion detection

Identify high and low temperature events
Duration calculation

Determine event start, end and duration
Excursion records

Store detected events and supporting readings
5. Example
Suppose your permitted temperature range is 2°C–8°C.

Time

Temperature

Result

10:00

5°C

Normal

10:10

6°C

Normal

10:20

9°C

High excursion

10:30

11°C

High excursion

10:40

10°C

High excursion

10:50

7°C

Normal

Your detector should identify one continuous high-temperature event, subject to your excursion grouping rules.

Important: Define whether duration is calculated from the first violating reading to the last violating reading, or estimated using sampling intervals. Do not silently interpolate missing readings.

6. Important validation rules
An excursion must belong to a valid shipment and logger assignment.

Its readings must belong to that same assignment.

Start time must not be later than end time.

Duration cannot be negative.

High and low excursion classifications must follow configured limits.

Events must not cross logger assignment boundaries.

Missing readings must be treated as a data-quality concern, not normal temperatures.

Re-running detection should not create duplicate excursion records.

Detection results must remain separate from ground truth.

7. Final recommended structure
For your current project, keep excursion_detector.py as the main detection entry point. Move supporting logic into the other modules gradually rather than replacing the working detector.

Next, share your existing excursion_detector.py code. I can review whether it correctly handles consecutive violations, duration calculation, missing readings, assignment boundaries and duplicate detection.

help me to create a readme file in github repo
Let's create a professional, GitHub-ready README for your Cold-Chain Shipment Compliance System.

The README will explain the project, its architecture, technologies, execution steps, validation process and generated outputs. I'll use your actual main.py workflow and avoid claiming that planned lifecycle modules are already implemented.

Cold-Chain Shipment Compliance System
A Python-based synthetic data generation and compliance monitoring system designed to simulate cold-chain shipments, monitor temperature conditions, detect temperature excursions, evaluate shipment compliance, and validate data integrity.

Project Overview
Cold-chain transportation requires products to remain within specified temperature limits throughout storage and transportation.

This project simulates a cold-chain logistics environment by generating synthetic shipment data, temperature readings, logger information and shipment-related records. It then identifies temperature excursions and evaluates shipment compliance using predefined business rules.

The system also performs structural and data-integrity validation before exporting the generated results.

Key Features
Synthetic Data Generation: Generate configurable numbers of shipments and temperature loggers.

Temperature Monitoring: Simulate temperature readings for shipment monitoring.

Excursion Detection: Identify temperature readings outside permitted limits.

Excursion Analysis: Calculate excursion duration and generate excursion reports.

Compliance Evaluation: Evaluate shipment compliance based on temperature and data-quality rules.

Data Validation: Validate database relationships, structural integrity and business rules.

Reproducibility: Use a configurable random seed to support repeatable data generation.

Data Export: Export results into CSV and SQL formats.

SQLite Database: Store generated data and evaluation results in a relational database.

Technology Stack
Technology	Purpose
Python	Core application logic
SQLite	Relational database
SQL	Database queries and data management
Pandas	Data processing and analysis, where used
NumPy	Numerical operations, where used
Argparse	Command-line configuration
Git and GitHub	Version control and project management
Project Architecture
cold_chain_project_complete/
│
├── main.py
├── data_generator.py
├── excursion_detector.py
├── compliance_engine.py
├── validator.py
├── exporter.py
├── sql_exporter.py
│
├── cold_chain.db
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── tests/
│
├── requirements.txt
├── README.md
└── .gitignore
The structure above represents the current modular pipeline at a high level. Update it as the codebase is reorganized.

System Workflow
       Configuration
             |
             v
    Synthetic Data Generation
             |
             v
     Temperature Monitoring
             |
             v
      Excursion Detection
             |
             v
     Compliance Evaluation
             |
             v
       Data Validation
             |
       +-----+------+
       |            |
    Valid         Invalid
       |            |
       v            v
     Export       Stop Export
       |
       v
   CSV and SQL
Installation and Setup
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
2. Navigate to the project directory
cd cold_chain_project_complete
3. Create a virtual environment
Windows:

python -m venv venv
Activate it:

venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
Running the Project
Run the complete simulation using default settings:

python main.py
Default configuration:

Parameter	Default
Shipments	5,000
Temperature loggers	1,000
Random seed	20261022
Database	cold_chain.db
Custom execution
Generate 5,000 shipments and 1,000 loggers:

python main.py --shipments 5000 --loggers 1000
Generate a smaller dataset:

python main.py --shipments 100 --loggers 20
Use a custom random seed:

python main.py --seed 12345
Specify a database filename:

python main.py --db custom_cold_chain.db
Skip data exports:

python main.py --skip-export
Processing Pipeline
1. Data Generation
The data_generator.py module generates synthetic cold-chain data, including shipment and logger information.

2. Excursion Detection
The excursion_detector.py module identifies temperature excursions based on configured temperature thresholds and detection rules.

3. Compliance Evaluation
The compliance_engine.py module evaluates shipment compliance using the generated data and applicable business rules.

4. Data Validation
The validator.py module checks the structural integrity and relationships within the generated database.

Exporting is cancelled if the required structural validation check fails.

5. Data Export
The export modules generate the supported output formats:

exporter.py – CSV exports.

sql_exporter.py – SQL exports.

Validation and Data Integrity
The project includes a validation stage to help ensure the generated dataset is structurally consistent before export.

Important validation areas include:

Primary key uniqueness.

Foreign key relationships.

Shipment and logger assignment consistency.

Temperature reading relationships.

Excursion record integrity.

Compliance report consistency.

Data completeness and business-rule validation.

Reproducibility
The project supports configurable random seeds.

Example:

python main.py --shipments 5000 --loggers 1000 --seed 20261022
Using the same seed, configuration, generator version and controlled execution order is important for reproducing synthetic datasets.

Generated Outputs
Depending on the export implementation, the project generates:

Shipment records.

Product and lot records.

Logger information.

Temperature readings.

Excursion reports.

Compliance reports.

Validation results.

CSV and SQL exports.

Project Objectives
Simulate a realistic synthetic cold-chain transportation environment.

Generate traceable shipment and temperature-monitoring data.

Identify temperature excursions.

Evaluate shipment compliance.

Validate database relationships and business rules.

Produce reproducible datasets for testing and analysis.

Future Enhancements
Shipment lifecycle event history.

Append-only shipment status tracking.

Custody handoff history.

Route and transportation event tracking.

Logger assignment and calibration history.

Improved excursion analysis and data-quality monitoring.

Automated test coverage.

Compliance reporting and visualization dashboard.

Running Tests
If the test suite is configured:

python -m pytest tests/
Limitations
The dataset is synthetic and does not represent actual shipment operations.

Compliance results depend on configured temperature policies and evaluation rules.

Generated records should not be interpreted as real-world regulatory certification.

Reproducibility depends on controlling the complete generation configuration and execution process.

Author
Vaishnav Teja

GitHub: <YOUR_GITHUB_PROFILE_URL>

This project was developed as a synthetic cold-chain data generation, temperature excursion detection and shipment compliance evaluation system.

3. How to add this README to GitHub
Open your project in VS Code.

Open the existing README.md file.

Replace its content with the README above.

Replace the GitHub URL placeholders with your actual links.

Save the file.

Then run:

git add README.md
git commit -m "Improve project README documentation"
git push origin main

My suggestion: Add a project architecture diagram and screenshots of the validation output to your GitHub README. These will make the repository easier for recruiters and technical reviewers to understand.




2 °C⋮⋮⋮⋮