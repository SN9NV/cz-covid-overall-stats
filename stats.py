from requests import get
from datetime import datetime
import json
from jinja2 import Template
from sys import argv

def download_data(force_download=False):
    if force_download:
        cases = get("https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/osoby.min.json").json()
        recovered = get("https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/vyleceni.min.json").json()
        deaths = get("https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/umrti.min.json").json()

        with open("cases.json", "w") as f:
            json.dump(cases, f)
        with open("recovered.json", "w") as f:
            json.dump(recovered, f)
        with open("deaths.json", "w") as f:
            json.dump(deaths, f)
    else:
        with open("cases.json") as f:
            cases = json.load(f)
        with open("recovered.json") as f:
            recovered = json.load(f)
        with open("deaths.json") as f:
            deaths = json.load(f)

    return {
        "last_updated": datetime.fromisoformat(cases["modified"]),
        "cases": cases["data"],
        "recovered": recovered["data"],
        "deaths": deaths["data"],
    }


def parse_template_file(filename="stats_wikipedia.template"):
    with open(filename) as f:
        return Template(f.read())


def between_age(age, start_age, end_age):
    if end_age is None:
        return start_age <= age
    
    return start_age <= age <= end_age


def total_in_age_range(data, start_age, end_age):
    male = 0
    female = 0
    unknown = 0

    for person in data:
        if person["vek"] is None:
            unknown += 1
        elif between_age(person["vek"], start_age, end_age):
            if person["pohlavi"] == "M":
                male += 1
            else:
                female += 1

    return male, female, unknown


def process_age_group(raw_data, start_age, end_age):
    cases_male, cases_female, cases_unknown = total_in_age_range(raw_data["cases"], start_age, end_age)
    recovered_male, recovered_female, recovered_unknown = total_in_age_range(raw_data["recovered"], start_age, end_age)
    deaths_male, deaths_female, deaths_unknown = total_in_age_range(raw_data["deaths"], start_age, end_age)

    return {
        "age_range": f"{start_age}+" if end_age is None else f"{start_age} - {end_age}",
        "cases_male": cases_male,
        "cases_female": cases_female,
        "cases_unknown": cases_unknown,
        "cases_total": cases_male + cases_female + cases_unknown,
        "recovered_male": recovered_male,
        "recovered_female": recovered_female,
        "recovered_unknown": recovered_unknown,
        "recovered_total": recovered_male + recovered_female + recovered_unknown,
        "deaths_male": deaths_male,
        "deaths_female": deaths_female,
        "deaths_unknown": deaths_unknown,
        "deaths_total": deaths_male + deaths_female + deaths_unknown,
    }


def main():
    raw_data = download_data(len(argv) >= 2 and argv[1] == "-f")
    template = parse_template_file()

    age_ranges = (
        (0, 14),
        (15, 24),
        (25, 34),
        (35, 44),
        (45, 54),
        (55, 64),
        (65, 74),
        (75, 84),
        (85, None),
    )

    age_groups = [
        process_age_group(raw_data, start_date, end_date)
        for start_date, end_date in age_ranges
    ]

    processed_data = {
        "last_updated": raw_data["last_updated"].strftime("%-d %B %Y"),
        "age_groups": age_groups,
        "total": {
            "cases_male": sum([g["cases_male"] for g in age_groups]),
            "cases_female": sum([g["cases_male"] for g in age_groups]),
            "cases_unknown": sum([g["cases_male"] for g in age_groups]),
            "cases_total": sum([g["cases_total"] for g in age_groups]),
            "recovered_male": sum([g["recovered_male"] for g in age_groups]),
            "recovered_female": sum([g["recovered_female"] for g in age_groups]),
            "recovered_unknown": sum([g["recovered_unknown"] for g in age_groups]),
            "recovered_total": sum([g["recovered_total"] for g in age_groups]),
            "deaths_male": sum([g["deaths_male"] for g in age_groups]),
            "deaths_female": sum([g["deaths_female"] for g in age_groups]),
            "deaths_unknown": sum([g["deaths_unknown"] for g in age_groups]),
            "deaths_total": sum([g["deaths_total"] for g in age_groups]),
        },
    }

    print(template.render(processed_data))


if __name__ == "__main__":
    main()
