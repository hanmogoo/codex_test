# codex_test

## fixed_integrated_monitor.py

`fixed_integrated_monitor.py` is an asynchronous monitor that sends requests defined in `queries.xlsx` to a specified API endpoint. It measures throughput (QPS), success rate and response times while dynamically adjusting concurrency.

### Installing dependencies

Install the required Python libraries using pip:

```bash
pip install aiohttp pandas openpyxl
```

`pandas` uses `openpyxl` to load `.xlsx` files, so it is included above.

### Preparing `queries.xlsx`

Create an Excel file called `queries.xlsx` in the repository root. Use the sheet name `sheet1`. The monitor reads queries from the second column (index `1`), ignoring empty cells. The file might look like this:

| A | B |
|---|---|
| id | query |
| 1 | Hello world |
| 2 | Second question |

Only the text in column B will be used as queries.

### Running the monitor

Execute the script with Python 3:

```bash
python fixed_integrated_monitor.py
```

The script loads `queries.xlsx` and begins sending requests while displaying real-time statistics. Logs and a JSON report are saved in a timestamped folder (e.g., `fixed-gpu-monitor-2023-01-01_12-00`).
