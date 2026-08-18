"""Fetch this calendar year's contributions in gh-space-shooter's raw format.

GitHub's default contribution window is a rolling 52 weeks, which puts last
year's quiet months on the left. The profile page shows the calendar year, so
we fetch Jan 1 -> today instead and hand the result to gh-space-shooter.
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount contributionLevel }
        }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def main() -> None:
    login = sys.argv[1]
    out_path = sys.argv[2]
    today = datetime.now(timezone.utc).date()
    start = date(today.year, 1, 1)

    proc = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-F", f"login={login}",
            "-F", f"from={start.isoformat()}T00:00:00Z",
            "-F", f"to={today.isoformat()}T23:59:59Z",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    calendar = json.loads(proc.stdout)["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]

    weeks = [
        {
            "days": [
                {
                    "date": day["date"],
                    "count": day["contributionCount"],
                    "level": LEVELS[day["contributionLevel"]],
                }
                for day in week["contributionDays"]
            ]
        }
        for week in calendar["weeks"]
    ]

    with open(out_path, "w") as handle:
        json.dump(
            {
                "username": login,
                "total_contributions": calendar["totalContributions"],
                "weeks": weeks,
            },
            handle,
        )

    print(f"{calendar['totalContributions']} contributions, {len(weeks)} weeks, {start} to {today}")


if __name__ == "__main__":
    main()
