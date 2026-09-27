import csv
from dataclasses import dataclass
from typing import Optional


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Machine:
    machine_id: int
    machine_type: str
    minimum_temperature: float
    maximum_temperature: float
    maximum_vibration: float
    location: str


@dataclass
class Event:
    event_id: Optional[int]
    machine_id: Optional[int]
    timestamp: Optional[int]
    status: str
    temperature: Optional[float]
    vibration: Optional[float]
    units_produced: Optional[int]
    defect_count: Optional[int]


@dataclass
class ParseResult:
    success: bool
    record: Optional[object]
    record_id: str
    line_number: int
    reason: Optional[str]


@dataclass
class ValidationResult:
    valid: bool
    reason: Optional[str]


@dataclass
class AnomalyResult:
    anomalies: list


# ============================================================
# PARSING FUNCTIONS
# ============================================================

def parseMachineRecord(csvRow, lineNumber):

    if len(csvRow) != 6:
        machine_id = csvRow[0].strip() if len(csvRow) > 0 else "UNKNOWN"

        return ParseResult(
            False,
            None,
            machine_id if machine_id else "UNKNOWN",
            lineNumber,
            "INCOMPLETE_MACHINE_RECORD"
        )

    fields = [field.strip() for field in csvRow]

    machine_id_text = fields[0]
    machine_type = fields[1]
    minimum_temperature_text = fields[2]
    maximum_temperature_text = fields[3]
    maximum_vibration_text = fields[4]
    location = fields[5]

    try:
        machine_id = int(machine_id_text)
    except ValueError:
        machine_id = None

    try:
        minimum_temperature = float(minimum_temperature_text)
    except ValueError:
        minimum_temperature = None

    try:
        maximum_temperature = float(maximum_temperature_text)
    except ValueError:
        maximum_temperature = None

    try:
        maximum_vibration = float(maximum_vibration_text)
    except ValueError:
        maximum_vibration = None

    machine = {
        "machine_id": machine_id,
        "machine_id_text": machine_id_text,
        "machine_type": machine_type,
        "minimum_temperature": minimum_temperature,
        "maximum_temperature": maximum_temperature,
        "maximum_vibration": maximum_vibration,
        "location": location
    }

    return ParseResult(
        True,
        machine,
        machine_id_text if machine_id_text else "UNKNOWN",
        lineNumber,
        None
    )


def parseEventRecord(csvRow, lineNumber):

    if len(csvRow) != 8:
        event_id = csvRow[0].strip() if len(csvRow) > 0 else "UNKNOWN"

        return ParseResult(
            False,
            None,
            event_id if event_id else "UNKNOWN",
            lineNumber,
            "INCOMPLETE_EVENT_RECORD"
        )

    fields = [field.strip() for field in csvRow]

    event_id_text = fields[0]
    machine_id_text = fields[1]
    timestamp_text = fields[2]
    status = fields[3]
    temperature_text = fields[4]
    vibration_text = fields[5]
    units_produced_text = fields[6]
    defect_count_text = fields[7]

    try:
        event_id = int(event_id_text)
    except ValueError:
        event_id = None

    try:
        machine_id = int(machine_id_text)
    except ValueError:
        machine_id = None

    try:
        timestamp = int(timestamp_text)
    except ValueError:
        timestamp = None

    try:
        temperature = float(temperature_text)
    except ValueError:
        temperature = None

    try:
        vibration = float(vibration_text)
    except ValueError:
        vibration = None

    try:
        units_produced = int(units_produced_text)
    except ValueError:
        units_produced = None

    try:
        defect_count = int(defect_count_text)
    except ValueError:
        defect_count = None

    # Create and actually use the Event object.
    event = Event(
        event_id=event_id,
        machine_id=machine_id,
        timestamp=timestamp,
        status=status,
        temperature=temperature,
        vibration=vibration,
        units_produced=units_produced,
        defect_count=defect_count
    )

    return ParseResult(
        True,
        event,
        event_id_text if event_id_text else "UNKNOWN",
        lineNumber,
        None
    )


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validateMachine(machineRecord):

    machine_id = machineRecord["machine_id"]

    if machine_id is None or machine_id <= 0:
        return ValidationResult(False, "INVALID_MACHINE_ID")

    if machineRecord["machine_type"] == "":
        return ValidationResult(False, "MISSING_MACHINE_TYPE")

    minimum_temperature = machineRecord["minimum_temperature"]
    maximum_temperature = machineRecord["maximum_temperature"]

    if (
        minimum_temperature is None
        or maximum_temperature is None
        or minimum_temperature >= maximum_temperature
    ):
        return ValidationResult(False, "INVALID_TEMPERATURE_LIMITS")

    maximum_vibration = machineRecord["maximum_vibration"]

    if maximum_vibration is None or maximum_vibration <= 0:
        return ValidationResult(False, "INVALID_VIBRATION_LIMIT")

    if machineRecord["location"] == "":
        return ValidationResult(False, "MISSING_LOCATION")

    return ValidationResult(True, None)


def validateEvent(eventRecord, validMachines):

    event_id = eventRecord.event_id

    if event_id is None or event_id <= 0:
        return ValidationResult(False, "INVALID_EVENT_ID")

    machine_id = eventRecord.machine_id

    if machine_id is None or machine_id <= 0:
        return ValidationResult(False, "INVALID_MACHINE_ID")

    if machine_id not in validMachines:
        return ValidationResult(False, "UNKNOWN_MACHINE_ID")

    timestamp = eventRecord.timestamp

    if timestamp is None or timestamp < 0:
        return ValidationResult(False, "INVALID_TIMESTAMP")

    allowed_statuses = {
        "RUNNING",
        "IDLE",
        "MAINTENANCE",
        "STOPPED"
    }

    if eventRecord.status not in allowed_statuses:
        return ValidationResult(False, "INVALID_STATUS")

    if eventRecord.temperature is None:
        return ValidationResult(False, "INVALID_TEMPERATURE")

    vibration = eventRecord.vibration

    if vibration is None or vibration < 0:
        return ValidationResult(False, "INVALID_VIBRATION")

    units_produced = eventRecord.units_produced

    if units_produced is None or units_produced < 0:
        return ValidationResult(False, "INVALID_PRODUCTION_COUNT")

    defect_count = eventRecord.defect_count

    if (
        defect_count is None
        or defect_count < 0
        or defect_count > units_produced
    ):
        return ValidationResult(False, "INVALID_DEFECT_COUNT")

    return ValidationResult(True, None)


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def countMachineIDs(machineRows):

    machineIdCounts = {}

    for lineNumber, row in machineRows:

        parsed = parseMachineRecord(row, lineNumber)

        if not parsed.success:
            continue

        machineRecord = parsed.record
        machine_id = machineRecord["machine_id"]

        if machine_id is None or machine_id <= 0:
            continue

        machineIdCounts[machine_id] = (
            machineIdCounts.get(machine_id, 0) + 1
        )

    return machineIdCounts


def countEventIDs(eventRows):

    eventIdCounts = {}

    for lineNumber, row in eventRows:

        parsed = parseEventRecord(row, lineNumber)

        if not parsed.success:
            continue

        eventRecord = parsed.record
        event_id = eventRecord.event_id

        if event_id is None or event_id <= 0:
            continue

        eventIdCounts[event_id] = (
            eventIdCounts.get(event_id, 0) + 1
        )

    return eventIdCounts


# ============================================================
# MACHINE PROCESSING
# ============================================================

def processMachines(machineRows, machineFileName):

    machineIdCounts = countMachineIDs(machineRows)

    validMachines = {}
    rejectedMachineRecords = []

    for lineNumber, row in machineRows:

        parsed = parseMachineRecord(row, lineNumber)

        if not parsed.success:
            rejectedMachineRecords.append({
                "source_file": machineFileName,
                "line_number": lineNumber,
                "record_id": parsed.record_id,
                "reason_code": parsed.reason
            })
            continue

        machineRecord = parsed.record
        machine_id = machineRecord["machine_id"]

        if machine_id is None or machine_id <= 0:
            rejectedMachineRecords.append({
                "source_file": machineFileName,
                "line_number": lineNumber,
                "record_id": (
                    parsed.record_id
                    if parsed.record_id
                    else "UNKNOWN"
                ),
                "reason_code": "INVALID_MACHINE_ID"
            })
            continue

        if machineIdCounts.get(machine_id, 0) > 1:
            rejectedMachineRecords.append({
                "source_file": machineFileName,
                "line_number": lineNumber,
                "record_id": str(machine_id),
                "reason_code": "DUPLICATE_MACHINE_ID"
            })
            continue

        validation = validateMachine(machineRecord)

        if not validation.valid:
            rejectedMachineRecords.append({
                "source_file": machineFileName,
                "line_number": lineNumber,
                "record_id": str(machine_id),
                "reason_code": validation.reason
            })
            continue

        machine = Machine(
            machine_id=machineRecord["machine_id"],
            machine_type=machineRecord["machine_type"],
            minimum_temperature=machineRecord["minimum_temperature"],
            maximum_temperature=machineRecord["maximum_temperature"],
            maximum_vibration=machineRecord["maximum_vibration"],
            location=machineRecord["location"]
        )

        validMachines[machine.machine_id] = machine

    return validMachines, rejectedMachineRecords


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detectAnomalies(eventRecord, machineRecord):

    anomalies = []

    temperature = eventRecord.temperature
    vibration = eventRecord.vibration

    minimum_temperature = machineRecord["minimum_temperature"]
    maximum_temperature = machineRecord["maximum_temperature"]
    maximum_vibration = machineRecord["maximum_vibration"]

    if temperature < minimum_temperature:

        anomalies.append({
            "event_id": eventRecord.event_id,
            "machine_id": eventRecord.machine_id,
            "timestamp": eventRecord.timestamp,
            "anomaly_code": "LOW_TEMPERATURE",
            "observed_value": temperature,
            "reference_value": minimum_temperature
        })

    elif temperature > maximum_temperature:

        anomalies.append({
            "event_id": eventRecord.event_id,
            "machine_id": eventRecord.machine_id,
            "timestamp": eventRecord.timestamp,
            "anomaly_code": "HIGH_TEMPERATURE",
            "observed_value": temperature,
            "reference_value": maximum_temperature
        })

    if vibration > maximum_vibration:

        anomalies.append({
            "event_id": eventRecord.event_id,
            "machine_id": eventRecord.machine_id,
            "timestamp": eventRecord.timestamp,
            "anomaly_code": "HIGH_VIBRATION",
            "observed_value": vibration,
            "reference_value": maximum_vibration
        })

    return AnomalyResult(anomalies)


# ============================================================
# MACHINE STATISTICS
# ============================================================

def createMachineStats():

    return {
        "accepted_event_count": 0,
        "running_event_count": 0,
        "idle_event_count": 0,
        "maintenance_event_count": 0,
        "stopped_event_count": 0,
        "temperature_sum": 0.0,
        "maximum_vibration": 0.0,
        "latest_units_produced": 0,
        "latest_defect_count": 0,
        "temperature_anomaly_count": 0,
        "vibration_anomaly_count": 0
    }


def updateMachineStats(stats, eventRecord, anomalies):

    stats["accepted_event_count"] += 1

    status = eventRecord.status

    if status == "RUNNING":
        stats["running_event_count"] += 1

    elif status == "IDLE":
        stats["idle_event_count"] += 1

    elif status == "MAINTENANCE":
        stats["maintenance_event_count"] += 1

    elif status == "STOPPED":
        stats["stopped_event_count"] += 1

    stats["temperature_sum"] += eventRecord.temperature

    if eventRecord.vibration > stats["maximum_vibration"]:
        stats["maximum_vibration"] = eventRecord.vibration

    stats["latest_units_produced"] = eventRecord.units_produced
    stats["latest_defect_count"] = eventRecord.defect_count

    for anomaly in anomalies:

        if anomaly["anomaly_code"] in {
            "LOW_TEMPERATURE",
            "HIGH_TEMPERATURE"
        }:
            stats["temperature_anomaly_count"] += 1

        elif anomaly["anomaly_code"] == "HIGH_VIBRATION":
            stats["vibration_anomaly_count"] += 1


# ============================================================
# EVENT PROCESSING
# ============================================================

def processEvents(
    eventRows,
    eventFileName,
    validMachines,
    eventIdCounts,
    machineStats
):

    rejectedEventRecords = []
    allAnomalies = []

    previousAcceptedTimestamps = {}
    acceptedEventRecords = 0

    for lineNumber, row in eventRows:

        parsed = parseEventRecord(row, lineNumber)

        if not parsed.success:

            rejectedEventRecords.append({
                "source_file": eventFileName,
                "line_number": lineNumber,
                "record_id": parsed.record_id,
                "reason_code": parsed.reason
            })

            continue

        # The parser now returns an actual Event object.
        event = parsed.record

        event_id = event.event_id
        machine_id = event.machine_id

        if event_id is None or event_id <= 0:

            rejectedEventRecords.append({
                "source_file": eventFileName,
                "line_number": lineNumber,
                "record_id": (
                    parsed.record_id
                    if parsed.record_id
                    else "UNKNOWN"
                ),
                "reason_code": "INVALID_EVENT_ID"
            })

            continue

        if eventIdCounts.get(event_id, 0) > 1:

            rejectedEventRecords.append({
                "source_file": eventFileName,
                "line_number": lineNumber,
                "record_id": str(event_id),
                "reason_code": "DUPLICATE_EVENT_ID"
            })

            continue

        validation = validateEvent(event, validMachines)

        if not validation.valid:

            rejectedEventRecords.append({
                "source_file": eventFileName,
                "line_number": lineNumber,
                "record_id": str(event_id),
                "reason_code": validation.reason
            })

            continue

        timestamp = event.timestamp

        if machine_id in previousAcceptedTimestamps:

            previousTimestamp = previousAcceptedTimestamps[machine_id]

            if timestamp < previousTimestamp:

                rejectedEventRecords.append({
                    "source_file": eventFileName,
                    "line_number": lineNumber,
                    "record_id": str(event_id),
                    "reason_code": "OUT_OF_ORDER_TIMESTAMP"
                })

                continue

        # Event is accepted from this point onward.
        acceptedEventRecords += 1

        # Only accepted events update the previous timestamp.
        previousAcceptedTimestamps[machine_id] = timestamp

        machine = validMachines[machine_id]

        machineRecordForAnomaly = {
            "machine_id": machine.machine_id,
            "machine_type": machine.machine_type,
            "minimum_temperature": machine.minimum_temperature,
            "maximum_temperature": machine.maximum_temperature,
            "maximum_vibration": machine.maximum_vibration,
            "location": machine.location
        }

        anomalyResult = detectAnomalies(
            event,
            machineRecordForAnomaly
        )

        anomaliesForEvent = anomalyResult.anomalies

        allAnomalies.extend(anomaliesForEvent)

        updateMachineStats(
            machineStats[machine_id],
            event,
            anomaliesForEvent
        )

    return (
        rejectedEventRecords,
        allAnomalies,
        acceptedEventRecords
    )


# ============================================================
# OUTPUT FUNCTIONS
# ============================================================

def writeMachineSummary(validMachines, machineStats):

    header = [
        "machine_id",
        "machine_type",
        "location",
        "accepted_event_count",
        "running_event_count",
        "idle_event_count",
        "maintenance_event_count",
        "stopped_event_count",
        "average_temperature",
        "maximum_vibration",
        "latest_units_produced",
        "latest_defect_count",
        "temperature_anomaly_count",
        "vibration_anomaly_count"
    ]

    with open(
        "machine_summary.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(header)

        for machine in validMachines.values():

            machine_id = machine.machine_id
            stats = machineStats[machine_id]

            if stats["accepted_event_count"] > 0:

                average_temperature = (
                    stats["temperature_sum"]
                    / stats["accepted_event_count"]
                )

            else:
                average_temperature = 0.0

            writer.writerow([
                machine.machine_id,
                machine.machine_type,
                machine.location,
                stats["accepted_event_count"],
                stats["running_event_count"],
                stats["idle_event_count"],
                stats["maintenance_event_count"],
                stats["stopped_event_count"],
                f"{average_temperature:.2f}",
                f"{stats['maximum_vibration']:.2f}",
                stats["latest_units_produced"],
                stats["latest_defect_count"],
                stats["temperature_anomaly_count"],
                stats["vibration_anomaly_count"]
            ])


def writeAnomalies(anomalies):

    header = [
        "event_id",
        "machine_id",
        "timestamp",
        "anomaly_code",
        "observed_value",
        "reference_value"
    ]

    with open(
        "anomalies.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(header)

        for anomaly in anomalies:

            writer.writerow([
                anomaly["event_id"],
                anomaly["machine_id"],
                anomaly["timestamp"],
                anomaly["anomaly_code"],
                anomaly["observed_value"],
                anomaly["reference_value"]
            ])


def writeRejectedRecords(rejectedRecords):

    header = [
        "source_file",
        "line_number",
        "record_id",
        "reason_code"
    ]

    with open(
        "rejected_records.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(header)

        for record in rejectedRecords:

            writer.writerow([
                record["source_file"],
                record["line_number"],
                record["record_id"],
                record["reason_code"]
            ])


# ============================================================
# INPUT READING
# ============================================================

def readCsvRows(fileName):

    rows = []

    try:

        with open(
            fileName,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.reader(file)

            # Skip header.
            next(reader, None)

            for lineNumber, row in enumerate(reader, start=2):

                # Ignore completely blank lines.
                if not row or all(
                    field.strip() == ""
                    for field in row
                ):
                    continue

                rows.append((lineNumber, row))

    except (FileNotFoundError, OSError):

        print(f"Error: Could not open {fileName}")
        return None

    return rows


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():

    machineFileName = "machine_master.csv"
    eventFileName = "machine_events.csv"

    # --------------------------------------------------------
    # STEP 1: Read input files
    # --------------------------------------------------------

    machineRows = readCsvRows(machineFileName)

    if machineRows is None:
        return

    eventRows = readCsvRows(eventFileName)

    if eventRows is None:
        return

    # --------------------------------------------------------
    # STEP 2: Process machine master
    # --------------------------------------------------------

    (
        validMachines,
        rejectedMachineRecords
    ) = processMachines(
        machineRows,
        machineFileName
    )

    # --------------------------------------------------------
    # STEP 3: Prepare machine statistics
    # --------------------------------------------------------

    machineStats = {
        machine_id: createMachineStats()
        for machine_id in validMachines
    }

    # --------------------------------------------------------
    # STEP 4: Count duplicate event IDs
    # --------------------------------------------------------

    eventIdCounts = countEventIDs(eventRows)

    # --------------------------------------------------------
    # STEP 5: Process events
    # --------------------------------------------------------

    (
        rejectedEventRecords,
        allAnomalies,
        acceptedEventRecords
    ) = processEvents(
        eventRows,
        eventFileName,
        validMachines,
        eventIdCounts,
        machineStats
    )

    # --------------------------------------------------------
    # STEP 6: Combine rejected records
    # --------------------------------------------------------

    allRejectedRecords = (
        rejectedMachineRecords
        + rejectedEventRecords
    )

    # --------------------------------------------------------
    # STEP 7: Generate output files
    # --------------------------------------------------------

    writeMachineSummary(
        validMachines,
        machineStats
    )

    writeAnomalies(allAnomalies)

    writeRejectedRecords(allRejectedRecords)

    # --------------------------------------------------------
    # STEP 8: Calculate console anomaly counts
    # --------------------------------------------------------

    temperatureAnomalyEvents = set()
    vibrationAnomalyEvents = set()

    for anomaly in allAnomalies:

        if anomaly["anomaly_code"] in {
            "LOW_TEMPERATURE",
            "HIGH_TEMPERATURE"
        }:

            temperatureAnomalyEvents.add(
                anomaly["event_id"]
            )

        elif anomaly["anomaly_code"] == "HIGH_VIBRATION":

            vibrationAnomalyEvents.add(
                anomaly["event_id"]
            )

    # --------------------------------------------------------
    # STEP 9: Display processing summary
    # --------------------------------------------------------

    print(
        "Total machine records:",
        len(machineRows)
    )

    print(
        "Valid unique machines:",
        len(validMachines)
    )

    print(
        "Rejected machine records:",
        len(rejectedMachineRecords)
    )

    print(
        "Total event records:",
        len(eventRows)
    )

    print(
        "Accepted event records:",
        acceptedEventRecords
    )

    print(
        "Rejected event records:",
        len(rejectedEventRecords)
    )

    print(
        "Temperature anomaly events:",
        len(temperatureAnomalyEvents)
    )

    print(
        "Vibration anomaly events:",
        len(vibrationAnomalyEvents)
    )

    print(
        "Total anomaly records:",
        len(allAnomalies)
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()