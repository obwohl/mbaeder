# Alternative Scheduling Guide

As analyzed in `github_actions_chokepoint_analysis.md`, relying solely on GitHub Actions' internal scheduling queue (via `schedule` cron events) can lead to significant delays and skipped executions, especially on the free tier. When the repository attempts to run the scraper too frequently, GitHub's system often treats the job with low priority or limits execution.

To guarantee that the SWM data scraping occurs precisely and continuously every half hour without relying on GitHub's internal schedule mechanism, you can employ external triggers. This allows you to circumvent the GitHub Actions choke-point while still utilizing GitHub Actions runners for free execution, or alternatively running the execution entirely on a free private machine.

## Option A: External Trigger via cron-job.org (Free)

Instead of waiting for GitHub's internal scheduler, you can use a free, reliable external cron service such as [cron-job.org](https://cron-job.org/) to trigger the GitHub Action manually through the GitHub API via a `workflow_dispatch` event.

### Steps to configure:

1. **Create a GitHub Personal Access Token (PAT):**
   - Go to your GitHub profile settings -> Developer Settings -> Personal access tokens (Fine-grained tokens or Classic).
   - Generate a token with at least `actions:write` (or `repo` scope for classic tokens) access to the repository.

2. **Configure cron-job.org:**
   - Sign up for a free account at cron-job.org.
   - Create a new cron job.
   - **Schedule:** Set it to run every 30 minutes.
   - **URL:** Use the GitHub API endpoint to trigger the workflow. Format:
     `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPOSITORY/actions/workflows/scrape.yml/dispatches`
     *(Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` appropriately)*
   - **HTTP Method:** POST
   - **Headers:** Add the following headers:
     - `Accept`: `application/vnd.github.v3+json`
     - `Authorization`: `Bearer YOUR_PERSONAL_ACCESS_TOKEN`
   - **Request Body:** Use JSON format to specify the branch (typically `main`):
     ```json
     {"ref":"main"}
     ```

This approach guarantees the trigger occurs perfectly on schedule. GitHub Actions generally executes `workflow_dispatch` events immediately, avoiding the scheduled queue delay.

## Option B: Run locally / VPS via Crontab (Free)

If GitHub Actions runners continue to be a bottleneck or you want absolute control, you can bypass GitHub Actions entirely by running the scraper on an "Always Free" VPS instance (like Oracle Cloud Always Free tier) or a local Raspberry Pi.

You can configure a simple cron job on a Linux machine to run the scrape script, process the output, and push the results back to the GitHub repository automatically.

We have provided a convenient setup script in this repository: `setup_local_cron.sh`.

### How to use `setup_local_cron.sh`:

1. Clone your repository onto your Linux machine/VPS.
2. Ensure Python 3 and git are installed (`sudo apt install python3 git`).
3. Make the script executable: `chmod +x setup_local_cron.sh`
4. Run the script: `./setup_local_cron.sh /path/to/your/repo/clone`

The script will automatically configure the local crontab to execute `swm_auslastung.py` and `process_auslastung.py` every half hour and commit the resulting CSV changes back to the repository.
