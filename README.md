# Vikings Dashboard

Viking-themed Streamlit dashboard for FMCSA lead management.

## Run locally

```bash
streamlit run viking_dashboard.py
```

Or use the local wrapper command already set up on this machine:

```bash
dashboard
```

## Files

- `viking_dashboard.py`: main Streamlit app
- `9237E6BD-CB0E-4716-BB7C-4410FD292FB3.PNG`: logo asset used by the dashboard
- `FMCSA_RESULTS.csv`: local runtime data file, ignored by Git

## Deploy

Any platform that supports Streamlit can deploy this app with:

- app entrypoint: `viking_dashboard.py`
- Python dependencies from `requirements.txt`

Recommended flow:

1. Initialize Git in this folder
2. Push to GitHub
3. Connect the GitHub repo to a hosting provider
4. Redeploy by pushing updates
