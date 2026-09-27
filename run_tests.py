from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import csv


# ------------------------------------------------------------
# PROJECT / TEST-CASE LOCATIONS
# ------------------------------------------------------------

project_folder = Path(__file__).resolve().parent
testcase_folder = Path.home() / "Downloads" / "testcase"
main_file = project_folder / "main.py"


# ------------------------------------------------------------
# FIND FILE
# Works whether Windows displays the extension or not.
# ------------------------------------------------------------

def find_file(folder, base_name):
    possible_names = [
        base_name,
        base_name + ".csv",
        base_name + ".txt",
    ]

    for name in possible_names:
        file_path = folder / name

        if file_path.exists():
            return file_path

    return None


# ------------------------------------------------------------
# READ TEXT FILE
# ------------------------------------------------------------

def read_text_file(file_path):
    return file_path.read_text(
        encoding="utf-8",
        errors="replace"
    ).strip()


# ------------------------------------------------------------
# READ CSV FILE
# ------------------------------------------------------------

def read_csv_file(file_path):
    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        reader = csv.reader(file)

        rows = []

        for row in reader:
            rows.append(row)

        return rows


# ------------------------------------------------------------
# COMPARE TWO CSV FILES
# ------------------------------------------------------------

def compare_csv_files(expected_file, actual_file):

    if not actual_file.exists():
        return False, "Generated file was not created."

    expected_rows = read_csv_file(expected_file)
    actual_rows = read_csv_file(actual_file)

    # Compare number of rows.
    if len(expected_rows) != len(actual_rows):
        return (
            False,
            f"Row count differs. "
            f"Expected {len(expected_rows)}, "
            f"Actual {len(actual_rows)}."
        )

    # Compare each row in order.
    for row_number, (expected_row, actual_row) in enumerate(
        zip(expected_rows, actual_rows),
        start=1
    ):

        if expected_row != actual_row:

            return (
                False,
                "First difference found at row "
                f"{row_number}.\n"
                f"Expected: {expected_row}\n"
                f"Actual:   {actual_row}"
            )

    return True, "All rows match."


# ------------------------------------------------------------
# COMPARE CONSOLE OUTPUT
# ------------------------------------------------------------

def compare_console_output(expected_file, actual_output):

    expected_output = read_text_file(expected_file)

    if expected_output == actual_output.strip():
        return True, "Console output matches."

    return (
        False,
        "Console output differs.\n\n"
        "EXPECTED:\n"
        + expected_output
        + "\n\nACTUAL:\n"
        + actual_output.strip()
    )


# ------------------------------------------------------------
# RUN ONE TEST CASE
# ------------------------------------------------------------

def run_test_case(test_number):

    test_folder = testcase_folder / f"testcase{test_number}"

    if not test_folder.exists():
        return "ERROR", ["Test-case folder not found."]

    machine_master = find_file(
        test_folder,
        "machine_master"
    )

    machine_events = find_file(
        test_folder,
        "machine_events"
    )

    expected_console = find_file(
        test_folder,
        "expected_console_output"
    )

    if machine_master is None:
        return "ERROR", ["machine_master file not found."]

    if machine_events is None:
        return "ERROR", ["machine_events file not found."]

    if expected_console is None:
        return "ERROR", [
            "expected_console_output file not found."
        ]

    # Expected CSV files are optional because the assignment says
    # each test-case folder "may contain" them.
    expected_summary = find_file(
        test_folder,
        "expected_machine_summary"
    )

    expected_anomalies = find_file(
        test_folder,
        "expected_anomalies"
    )

    expected_rejected = find_file(
        test_folder,
        "expected_rejected_records"
    )

    with tempfile.TemporaryDirectory() as temp_folder:

        temp_path = Path(temp_folder)

        # Copy the current main.py.
        shutil.copy2(
            main_file,
            temp_path / "main.py"
        )

        # Copy test-case inputs into temporary folder.
        shutil.copy2(
            machine_master,
            temp_path / "machine_master.csv"
        )

        shutil.copy2(
            machine_events,
            temp_path / "machine_events.csv"
        )

        # Run the program.
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=temp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        actual_console = result.stdout.strip()

        problems = []

        # --------------------------------------------------------
        # PROGRAM EXECUTION CHECK
        # --------------------------------------------------------

        if result.returncode != 0:

            problems.append(
                "PROGRAM ERROR:\n"
                + result.stderr.strip()
            )

            return "ERROR", problems

        # --------------------------------------------------------
        # CONSOLE OUTPUT CHECK
        # --------------------------------------------------------

        console_ok, console_message = compare_console_output(
            expected_console,
            actual_console
        )

        if not console_ok:
            problems.append(
                "CONSOLE OUTPUT:\n" + console_message
            )

        # --------------------------------------------------------
        # MACHINE SUMMARY CHECK
        # --------------------------------------------------------

        if expected_summary is not None:

            actual_summary = temp_path / "machine_summary.csv"

            summary_ok, summary_message = compare_csv_files(
                expected_summary,
                actual_summary
            )

            if not summary_ok:
                problems.append(
                    "machine_summary.csv:\n"
                    + summary_message
                )

        else:
            problems.append(
                "expected_machine_summary.csv "
                "was not supplied for this test case."
            )

        # --------------------------------------------------------
        # ANOMALIES CHECK
        # --------------------------------------------------------

        if expected_anomalies is not None:

            actual_anomalies = temp_path / "anomalies.csv"

            anomalies_ok, anomalies_message = compare_csv_files(
                expected_anomalies,
                actual_anomalies
            )

            if not anomalies_ok:
                problems.append(
                    "anomalies.csv:\n"
                    + anomalies_message
                )

        else:
            problems.append(
                "expected_anomalies.csv "
                "was not supplied for this test case."
            )

        # --------------------------------------------------------
        # REJECTED RECORDS CHECK
        # --------------------------------------------------------

        if expected_rejected is not None:

            actual_rejected = temp_path / "rejected_records.csv"

            rejected_ok, rejected_message = compare_csv_files(
                expected_rejected,
                actual_rejected
            )

            if not rejected_ok:
                problems.append(
                    "rejected_records.csv:\n"
                    + rejected_message
                )

        else:
            problems.append(
                "expected_rejected_records.csv "
                "was not supplied for this test case."
            )

        # --------------------------------------------------------
        # FINAL STATUS
        # --------------------------------------------------------

        # If expected CSV files are not supplied, don't mark the
        # test as failed merely because those files are unavailable.
        real_comparison_problems = []

        for problem in problems:
            if "was not supplied" not in problem:
                real_comparison_problems.append(problem)

        if real_comparison_problems:
            return "DIFFERENCE", problems

        return "PASS", problems


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("INDUSTRIAL EQUIPMENT LOG - COMPLETE TEST RUNNER")
    print("=" * 70)
    print()

    if not main_file.exists():
        print("ERROR: main.py was not found.")
        return

    if not testcase_folder.exists():
        print()
        print("ERROR: Test-case folder was not found:")
        print(testcase_folder)
        print()
        return

    results = []

    for test_number in range(1, 10):

        print(
            f"Running Test Case {test_number}..."
        )

        status, messages = run_test_case(
            test_number
        )

        results.append(
            (test_number, status)
        )

        if status == "PASS":
            print(
                f"Test Case {test_number}: PASS"
            )

        elif status == "DIFFERENCE":
            print(
                f"Test Case {test_number}: DIFFERENCE"
            )

            print()

            for message in messages:
                if "was not supplied" not in message:
                    print(message)
                    print()

        else:
            print(
                f"Test Case {test_number}: ERROR"
            )

            print()

            for message in messages:
                print(message)
                print()

        print("-" * 70)

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)

    for test_number, status in results:

        print(
            f"Test Case {test_number}: {status}"
        )

    passed = sum(
        1 for _, status in results
        if status == "PASS"
    )

    differences = sum(
        1 for _, status in results
        if status == "DIFFERENCE"
    )

    errors = sum(
        1 for _, status in results
        if status == "ERROR"
    )

    print()
    print(f"Passed: {passed}")
    print(f"Differences: {differences}")
    print(f"Errors: {errors}")

    print("=" * 70)


if __name__ == "__main__":
    main()