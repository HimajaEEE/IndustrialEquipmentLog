# Industrial Equipment Event Log Analysis and Reporting System

## 1. Project Overview

This project implements an Industrial Equipment Event Log Analysis and Reporting System using Python.

The system reads machine information and machine-event information from CSV files, validates the records, detects duplicate and invalid records, checks event timestamp ordering, detects operating anomalies, calculates machine-wise statistics, and generates the required CSV reports.

The input files are:

- `machine_master.csv`
- `machine_events.csv`

The generated output files are:

- `machine_summary.csv`
- `anomalies.csv`
- `rejected_records.csv`

The implementation follows the requirements specified in the assessment and is designed to process both normal and large event datasets.

---

## 2. Programming Language and Libraries

### Programming Language

Python 3

### Python Standard Library Modules Used

The program uses only Python standard-library functionality:

- `csv` - for reading and writing CSV files
- `dataclasses` - for structured record representation
- `typing` - for type-related support

No external libraries, databases, graphical user interfaces, network services, or third-party services are required.

---

## 3. Program Structure

The program follows a modular design. Different functions are responsible for parsing, validation, anomaly detection, statistics, and report generation.

### Required Functions

The implementation provides the following required logical interfaces:

```text
parseMachineRecord(csvRow, lineNumber)

parseEventRecord(csvRow, lineNumber)

validateMachine(machineRecord)

validateEvent(eventRecord, validMachines)

detectAnomalies(eventRecord, machineRecord)