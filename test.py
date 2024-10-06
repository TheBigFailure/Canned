from datetime import datetime, date
from time import perf_counter, struct_time
import json


new_obj = {
    1: 2,
    4: 3,
    3: 4,
    1.3: 5,
}
print(new_obj, dict(sorted(new_obj.items(), key=lambda x: x[0])))



quit()

from zoneinfo import ZoneInfo
TZ = ZoneInfo("Australia/Sydney")

dt = datetime.now(tz=TZ)

# exit()


# Testing the time it takes to convert a datetime object to a string, back to a datetime object
# Then, test the time it takes to save the datetime object's attributes to a dictionary, and then convert it back to a datetime object


SAMPLE_TIME: datetime = datetime.now(tz=TZ)
SAMPLE_DATE: date = datetime.now(tz=TZ).date()
RUN: int = 10_000_000
RUN_QTR: int = {int(RUN//4 * n) for n in range(1, 4)}


def test_datetime_conversion_via_str():
    # Test the time it takes to convert a datetime object to a string, back to a datetime object
    start = perf_counter()
    for i in range(RUN):
        d = {"time": SAMPLE_TIME.isoformat()}
        s = json.dumps(d)
        n_d = json.loads(s)
        n_t = datetime.fromisoformat(n_d["time"])
        if i in RUN_QTR:
            print(f"At approx. {i/RUN*100.0:.2f}% of the way through the test (str)")
        assert n_t == SAMPLE_TIME
    end = perf_counter()
    print(f"Time taken to convert datetime object to/from string {end - start:_} seconds, with {(end-start)/RUN*1000:.2e}ms per conversion")


def test_datetime_conversion_via_json():
    # Test the time it takes to convert a datetime object to a string, back to a datetime object
    start = perf_counter()
    for i in range(RUN):
        d = {"time": {
            "year": SAMPLE_TIME.year,
            "month": SAMPLE_TIME.month,
            "day": SAMPLE_TIME.day,
            "hour": SAMPLE_TIME.hour,
            "minute": SAMPLE_TIME.minute,
            "second": SAMPLE_TIME.second,
            "microsecond": SAMPLE_TIME.microsecond,
            "tzinfo": SAMPLE_TIME.tzinfo.__str__(),
        }}
        s = json.dumps(d)
        n_d = json.loads(s)

        n_t = datetime(year=n_d["time"]["year"], month=n_d["time"]["month"], day=n_d["time"]["day"], hour=n_d["time"]["hour"],
                       minute=n_d["time"]["minute"], second=n_d["time"]["second"], microsecond=n_d["time"]["microsecond"],
                       tzinfo=ZoneInfo(n_d["time"]["tzinfo"]))
        if i in RUN_QTR:
            print(f"At approx. {i/RUN*100.0:.2f}% of the way through the test (json)")
        assert n_t == SAMPLE_TIME
    end = perf_counter()
    print(f"Time taken to convert datetime object to/from json {end - start:_} seconds, with {(end-start)/RUN*1000:.2e}ms per conversion")


def test_datetime_conversion_via_json():
    # Test the time it takes to convert a datetime object to a string, back to a datetime object
    start = perf_counter()
    for i in range(RUN):
        d = {"date": {
            "year": SAMPLE_DATE.year,
            "month": SAMPLE_DATE.month,
            "day": SAMPLE_DATE.day,
            "tzinfo": SAMPLE_TIME.tzinfo.__str__(),
        }}
        s = json.dumps(d)
        n_d = json.loads(s)

        n_t = datetime(year=n_d["time"]["year"], month=n_d["time"]["month"], day=n_d["time"]["day"], hour=n_d["time"]["hour"],
                       minute=n_d["time"]["minute"], second=n_d["time"]["second"], microsecond=n_d["time"]["microsecond"],
                       tzinfo=ZoneInfo(n_d["time"]["tzinfo"]))
        if i in RUN_QTR:
            print(f"At approx. {i/RUN*100.0:.2f}% of the way through the test (json)")
        assert n_t == SAMPLE_TIME
    end = perf_counter()
    print(f"Time taken to convert datetime object to/from json {end - start:_} seconds, with {(end-start)/RUN*1000:.2e}ms per conversion")


print("Warming up CPU, please wait...")
for i in range(int(RUN//5)): i*i*i  # To warm up the CPU
print("Completed. Beginning benchmarks.")
#
# test_datetime_conversion_via_json()
# test_datetime_conversion_via_str()
