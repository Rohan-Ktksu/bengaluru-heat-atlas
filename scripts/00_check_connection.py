r"""Run this first: sign in to Earth Engine and verify the account connection.

From the project folder in PowerShell:
    .\.venv\Scripts\python.exe scripts\00_check_connection.py

Requires a registered Google Cloud project with the Earth Engine API enabled.
"""

import ee


def main():
    # This is the project ID from Google Cloud, not its display name or number.
    project_id = input("Enter your registered Google Cloud project ID: ").strip()
    if not project_id:
        raise SystemExit("A project ID is required. Register Earth Engine first, then rerun.")

    # Opens Google's sign-in flow when no reusable credentials are available.
    # Complete sign-in in your own browser. Never paste tokens into this chat.
    ee.Authenticate(auth_mode="localhost")

    # Associate Earth Engine requests with your registered project.
    ee.Initialize(project=project_id)

    # ee.Number creates a remote calculation. getInfo asks Google to run it.
    result = ee.Number(1).add(1).getInfo()
    if result != 2:
        raise RuntimeError(f"Unexpected connection-check response: {result!r}")

    print("Connection successful. Earth Engine returned:", result)
    print("Next milestone: define the Bengaluru pilot boundary and inspect available Landsat scenes.")


if __name__ == "__main__":
    main()
