#!/usr/bin/env python3
"""
Pull an Open-Meteo Historical Weather (archive) series and record its provenance.

This closes the gap that existed until 2026-08-06: the cached Open-Meteo files in
this repo had no recorded endpoint, no recorded retrieval date, and no hash. Every
pull made with this script writes a sidecar manifest alongside the JSON so the
series can be cited and audited later.

Endpoint: https://archive-api.open-meteo.com/v1/archive
Licence:  CC BY 4.0. Credit Open-Meteo, link the licence, state that you changed
          the data if you did. See open-meteo.com/en/licence.

Usage:
    py fetch_openmeteo_archive.py --lat 40.7381 --lon -74.0425 \
        --start 2025-07-01 --end 2026-07-01 --outdir data

    py fetch_openmeteo_archive.py ... --dry-run     # print the URL, fetch nothing
    py fetch_openmeteo_archive.py --self-test       # validation logic, no network

Pin the model with --models if you need a citable model name; without it
Open-Meteo's `best_match` chooses and the manifest records `best_match`.
"""
import argparse, hashlib, json, os, sys
import datetime as dt
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
DEFAULT_HOURLY = "shortwave_radiation,temperature_2m,precipitation"


def build_url(lat, lon, start, end, hourly, timezone, models=None):
    q = {
        "latitude": lat, "longitude": lon,
        "start_date": start, "end_date": end,
        "hourly": hourly, "timezone": timezone,
    }
    if models:
        q["models"] = models
    return ENDPOINT + "?" + urlencode(q)


def expected_hours(start, end):
    a = dt.date.fromisoformat(start)
    b = dt.date.fromisoformat(end)
    if b < a:
        raise ValueError("end_date is before start_date")
    return ((b - a).days + 1) * 24


def validate(payload, start, end, hourly):
    """Raise on anything that would silently corrupt a downstream analysis."""
    problems = []
    h = payload.get("hourly") or {}
    units = payload.get("hourly_units") or {}
    names = [n.strip() for n in hourly.split(",")]

    if "time" not in h:
        problems.append("response has no hourly.time")
        raise ValueError("; ".join(problems))

    want = expected_hours(start, end)
    got = len(h["time"])
    if got != want:
        problems.append(f"hour count {got}, expected {want}")

    # strictly hourly, no gaps
    ts = [dt.datetime.fromisoformat(x) for x in h["time"]]
    steps = {round((b - a).total_seconds() / 3600, 6) for a, b in zip(ts, ts[1:])}
    if steps and steps != {1.0}:
        problems.append(f"non-hourly steps present: {sorted(steps)[:5]}")

    for n in names:
        if n not in h:
            problems.append(f"requested variable {n} missing from response")
            continue
        if len(h[n]) != got:
            problems.append(f"{n} length {len(h[n])} != time length {got}")
        nulls = sum(1 for v in h[n] if v is None)
        if nulls:
            problems.append(f"{n} has {nulls} nulls; do not zero-fill silently")

    if "shortwave_radiation" in names:
        u = units.get("shortwave_radiation")
        if u != "W/m²":
            problems.append(f"shortwave_radiation unit is {u!r}, expected 'W/m²'")
        neg = sum(1 for v in h.get("shortwave_radiation", []) if v is not None and v < 0)
        if neg:
            problems.append(f"shortwave_radiation has {neg} negative values")

    if problems:
        raise ValueError("; ".join(problems))
    return True


def daylight_boundary_safe(payload):
    """True if no hour stamped 22,23,00,01 carries irradiance.

    If this holds, a whole-hour shift in the response's time frame cannot move
    daylight across a calendar-day boundary, so DAILY sums are frame-independent.
    Open-Meteo's hourly stamps have been observed to shift between otherwise
    identical requests, so this is checked rather than assumed.
    """
    h = payload.get("hourly") or {}
    if "shortwave_radiation" not in h:
        return None
    bad = 0
    for t, v in zip(h["time"], h["shortwave_radiation"]):
        if int(t[11:13]) in (0, 1, 22, 23) and (v or 0) > 0:
            bad += 1
    return bad == 0


def fetch(url, timeout=120):
    with urlopen(url, timeout=timeout) as r:
        return r.read()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--hourly", default=DEFAULT_HOURLY)
    ap.add_argument("--timezone", default="America/New_York")
    ap.add_argument("--models", default=None,
                    help="pin a model, e.g. ecmwf_ifs. Omit to let best_match choose.")
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return _self_test()

    for req in ("lat", "lon", "start", "end"):
        if getattr(a, req) is None:
            ap.error(f"--{req} is required (or use --self-test)")

    url = build_url(a.lat, a.lon, a.start, a.end, a.hourly, a.timezone, a.models)
    print("URL:", url)
    if a.dry_run:
        print(f"dry run, expected hours: {expected_hours(a.start, a.end)}")
        return 0

    retrieved_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    try:
        raw = fetch(url)
    except (URLError, HTTPError) as e:
        print(f"FETCH FAILED: {e}", file=sys.stderr)
        print("Network fetch failed; check connectivity and retry.", file=sys.stderr)
        return 2

    payload = json.loads(raw)
    validate(payload, a.start, a.end, a.hourly)

    os.makedirs(a.outdir, exist_ok=True)
    stem = os.path.join(a.outdir, f"open_meteo_{a.start}_{a.end}")
    with open(stem + ".json", "wb") as f:
        f.write(raw)

    manifest = {
        "schema": "openmeteo_pull_v1",
        "endpoint": ENDPOINT,
        "url": url,
        "retrieved_at_utc": retrieved_at,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "requested": {"latitude": a.lat, "longitude": a.lon, "start_date": a.start,
                      "end_date": a.end, "hourly": a.hourly, "timezone": a.timezone,
                      "models": a.models or "best_match (default, not pinned)"},
        "returned": {k: payload.get(k) for k in
                     ("latitude", "longitude", "elevation", "timezone",
                      "timezone_abbreviation", "utc_offset_seconds")},
        "hours": len(payload["hourly"]["time"]),
        "first_hour": payload["hourly"]["time"][0],
        "last_hour": payload["hourly"]["time"][-1],
        "daily_boundary_safe": daylight_boundary_safe(payload),
        "licence": "CC BY 4.0, https://open-meteo.com/en/licence",
        "attribution": "Weather data by Open-Meteo.com",
        "notes": [
            "Returned lat/lon is the selected model's grid-cell centre, not the "
            "requested point. Cite the returned values.",
            "If models was not pinned, best_match chose and the model name is "
            "unknown. Do not credit ERA5 or Copernicus without pinning.",
            "Hourly timestamps have been observed to shift between otherwise "
            "identical requests. Join on physical UTC, not clock text. Daily sums "
            "are safe when daily_boundary_safe is true.",
        ],
    }
    with open(stem + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"wrote {stem}.json  ({len(raw)} bytes, {manifest['hours']} hours)")
    print(f"wrote {stem}.manifest.json")
    print(f"  returned cell : {manifest['returned']['latitude']}, "
          f"{manifest['returned']['longitude']}  elev {manifest['returned']['elevation']}")
    print(f"  sha256        : {manifest['sha256']}")
    print(f"  boundary safe : {manifest['daily_boundary_safe']}")
    if manifest["daily_boundary_safe"] is False:
        print("  WARNING: irradiance present near midnight. Daily sums are NOT "
              "frame-independent for this pull. Investigate before aggregating.")
    return 0


# --------------------------------------------------------------------- self test
def _synthetic(hours=48, start="2025-07-01", nulls=0, unit="W/m²", bad_step=False):
    t0 = dt.datetime.fromisoformat(start + "T00:00")
    times, sw = [], []
    for i in range(hours):
        step = i + (1 if bad_step and i == 5 else 0)
        times.append((t0 + dt.timedelta(hours=step)).strftime("%Y-%m-%dT%H:%M"))
        hh = (t0 + dt.timedelta(hours=step)).hour
        sw.append(500.0 if 9 <= hh <= 16 else 0.0)
    for i in range(nulls):
        sw[i] = None
    return {"latitude": 40.738136, "longitude": -74.04254, "elevation": 32.0,
            "timezone": "America/New_York", "timezone_abbreviation": "GMT-4",
            "utc_offset_seconds": -14400,
            "hourly_units": {"time": "iso8601", "shortwave_radiation": unit},
            "hourly": {"time": times, "shortwave_radiation": sw}}


def _expect_fail(fn, label):
    try:
        fn()
    except Exception as e:
        print(f"  PASS  {label}  ({str(e)[:60]})")
        return True
    print(f"  FAIL  {label}: expected an exception, got none")
    return False


def _self_test():
    print("build_url / expected_hours")
    u = build_url(40.7381, -74.0425, "2025-07-01", "2026-07-01",
                  "shortwave_radiation", "America/New_York")
    ok = ENDPOINT in u and "start_date=2025-07-01" in u and "models" not in u
    print(f"  {'PASS' if ok else 'FAIL'}  url built, models omitted when unset")
    ok &= expected_hours("2025-07-01", "2026-07-01") == 8784
    print(f"  {'PASS' if expected_hours('2025-07-01','2026-07-01')==8784 else 'FAIL'}"
          f"  366 days -> 8784 hours")
    ok &= "models=ecmwf_ifs" in build_url(1, 2, "2025-01-01", "2025-01-02",
                                          "shortwave_radiation", "UTC", "ecmwf_ifs")
    print("  PASS  models included when set" if ok else "  FAIL  models flag")

    print("validate")
    good = _synthetic()
    validate(good, "2025-07-01", "2025-07-02", "shortwave_radiation")
    print("  PASS  clean payload accepted")
    ok &= _expect_fail(lambda: validate(_synthetic(hours=47), "2025-07-01",
                                        "2025-07-02", "shortwave_radiation"),
                       "short payload rejected")
    ok &= _expect_fail(lambda: validate(_synthetic(nulls=3), "2025-07-01",
                                        "2025-07-02", "shortwave_radiation"),
                       "nulls rejected")
    ok &= _expect_fail(lambda: validate(_synthetic(unit="MJ/m2"), "2025-07-01",
                                        "2025-07-02", "shortwave_radiation"),
                       "wrong unit rejected")
    ok &= _expect_fail(lambda: validate(_synthetic(bad_step=True), "2025-07-01",
                                        "2025-07-02", "shortwave_radiation"),
                       "time gap rejected")
    ok &= _expect_fail(lambda: validate(good, "2025-07-01", "2025-07-02",
                                        "shortwave_radiation,temperature_2m"),
                       "missing requested variable rejected")

    print("daylight_boundary_safe")
    safe = daylight_boundary_safe(good)
    print(f"  {'PASS' if safe else 'FAIL'}  clean payload is boundary safe")
    shifted = _synthetic()
    shifted["hourly"]["shortwave_radiation"][23] = 300.0
    unsafe = daylight_boundary_safe(shifted) is False
    print(f"  {'PASS' if unsafe else 'FAIL'}  midnight irradiance flagged unsafe")
    ok &= bool(safe) and unsafe

    print("\nSELF TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
