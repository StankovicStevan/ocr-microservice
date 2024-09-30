import re
from enum import Enum


class Status(Enum):
    HIGH = 'HIGH'
    LOW = 'LOW'
    WITHIN_VALUES = 'WITHIN_VALUES'


def check_within_range(result, referent_value):
    result = result.replace(',', '.')
    referent_value = referent_value.replace(',', '.')
    result = float(result)

    # Match patterns: 'a - b', '<x', '>x'
    number_pattern = r'\d+(?:\.\d+)?'

    range_match = re.match(fr'({number_pattern})\s*-\s*({number_pattern})', referent_value)
    less_than_match = re.match(fr'<\s*({number_pattern})', referent_value)
    greater_than_match = re.match(fr'>\s*({number_pattern})', referent_value)

    # Check range 'a - b'
    if range_match:
        # print(range_match.groups())
        low, high = map(float, range_match.groups())
        if result > high:
            return Status.HIGH
        elif result < low:
            return Status.LOW
        else:
            return Status.WITHIN_VALUES
        # return low <= result <= high

    # Check '<x'
    elif less_than_match:
        value = float(less_than_match.group(1))
        return Status.WITHIN_VALUES if result < value else Status.HIGH

    # Check '>x'
    elif greater_than_match:
        value = float(greater_than_match.group(1))
        return Status.WITHIN_VALUES if result > value else Status.LOW

    return False


def extract_clean_name(line):
    # Remove leading prefixes and clean up names
    pattern = re.compile(r'^\s*(?:\w+-?\w*\s*)*\s+(.+?)\s*(?:\((.*?)\))?\s*(?:\[(.*?)\])?\s*$')
    match = pattern.search(line)

    if match:
        return match.group(0)
    return None


def preprocess_word(text):
    # Check if the text matches the pattern 'Term ( Description )'
    if re.match(r'^[A-Z][A-Z0-9]*\s*\(.*\)$', text):
        return text
    else:
        words = text.split()
        # Remove the first word if there are multiple words
        pattern_first_word = r'[^a-zA-Z0-9]'

        if len(words) > 1 and (
                len(words[0]) < 3 or (len(words[0]) <= 4 and bool(re.search(r'[^a-zA-Z0-9]', words[0])))):
            # print(f"Usao za analizu {text}")
            text = re.sub(r'^\S+\s*', '', text)
            # print(f"Usao za analizu {text}")

        # Replace special characters except '#' with a single space
        text = re.sub(r'[^\w\s#]+', ' ', text)

        # Normalize multiple spaces to a single space and trim the result
        text = re.sub(r'\s+', ' ', text).strip()

        return text


def extract_data(text):
    analysis_pattern = r"([A-ZČŠŽa-zčšž\-\(\)# ]+)"  # ANALIZA
    result_pattern = r"([\d,.]+)"  # REZULTAT
    reference_pattern = r"([<>]?\s*[\d,.]+(?:\s*-\s*[\d,.]+)?)"  # REF. VREDNOSTI

    # Combined regex to extract all parts
    combined_pattern = rf"\|*\s*{analysis_pattern}\#*\s+{result_pattern}\s*[^\s]*\s+{reference_pattern}"

    # Extract important values using regex
    important_values = []
    values_in_range = []
    values_out_of_range = []
    for match in re.findall(combined_pattern, text):

        analysis, results, referent_values = match
        pattern_valid = re.compile(r'\b\d+([.,]\d+)?\b')
        print(
            f"Analiza: {analysis} , extracted: {preprocess_word(analysis)} and result {results} match: {bool(pattern_valid.fullmatch(results))}")

        analysis = preprocess_word(analysis)

        if len(analysis) > 2 and bool(pattern_valid.fullmatch(results)):
            status = check_within_range(results, referent_values)
            if status == Status.WITHIN_VALUES:
                values_in_range.append({"analysis": analysis, "results": results, "referent_values": referent_values,
                                        "status": status.value})
            else:
                values_out_of_range.append(
                    {"analysis": analysis, "results": results, "referent_values": referent_values,
                     "status": status.value})
            important_values.append((analysis.strip(), results.strip(), referent_values.strip(), status))
        else:
            print(f"WARNING - Given line not scanned properly: {analysis}")

    # Print extracted values
    for row in important_values:
        print(f"ANALYSIS: {row[0]}, RESULT: {row[1]}, REFERENT VALUES: {row[2]}")

    print("****************************")
    print("Bad Analysis")
    print(len(values_out_of_range))
    for row in values_out_of_range:
        print(row)

    print("****************************")
    print("Good Analysis")
    print(len(values_in_range))
    for row in values_in_range:
        print(row)

    return values_out_of_range, values_in_range
