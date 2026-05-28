import xml.etree.ElementTree as ET

tree = ET.parse("report.xml")
root = tree.getroot()

slow_tests = []
extra_slow_tests = []

for testcase in root.iter("testcase"):
    name = testcase.attrib["name"]
    classname = testcase.attrib.get("classname", "")
    duration = float(testcase.attrib["time"])

    full_test_name = f"{classname}::{name}"

    print(f"{full_test_name} -> {duration:.2f}s")

    # Between 15s and 60s
    if 15 < duration <= 60:
        slow_tests.append(f"{full_test_name} -> {duration:.2f}s")

    # Greater than 60s
    elif duration > 60:
        extra_slow_tests.append(f"{full_test_name} -> {duration:.2f}s")


with open("report_slow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(slow_tests))

with open("report_extra_slow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(extra_slow_tests))

print(f"\nSaved {len(slow_tests)} slow tests to report_slow.txt")
print(f"Saved {len(extra_slow_tests)} extra slow tests to report_extra_slow.txt")

