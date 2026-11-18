Pi Node Monitor updated source package

Files:
- app.py
- windows-helper/windows-agent.py

Changes:
- Removed Services, Horizon, and Service Manager tabs.
- Moved Horizon report details into the Protocol tab.
- Kept service Start / Stop / Restart controls on Overview.
- Added an Overview availability summary with manual refresh.
- Added a Docker Logs tab using Supervisor logs for horizon, stellar-core,
  postgresql, and rpc.
- Added log service selection, approximate output-size choices, manual refresh,
  and client-side text filtering.

Important:
- The log size selector uses Supervisor's byte-based tail output, so the actual
  number of displayed lines varies with message length.
- Logs are read-only. No node service is restarted by viewing logs.
- This package has not been installed into or tested against the user's live
  Docker environment. Test it in the separate C:\test app project first.
