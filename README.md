# Tovala Smart Oven (Home Assistant)

[![hacs][hacsbadge]](https://hacs.xyz)

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg

---

## What this is
A HACS-installable **custom integration** that signs in to Tovala’s cloud and exposes basic entities (remaining time, timer running) and fires a `tovala_timer_finished` event when the timer hits 0.

> **Note:** Tovala does not publish a public API. This integration uses the same HTTPS endpoints that the web app uses.

---

## Install (HACS)

1. In **HACS → Integrations → ⋮ → Custom repositories → Add**  
   - URL: `https://github.com/InfoSecured/ha-tovala`  
   - Category: **Integration**
2. Search for **Tovala Smart Oven** in HACS and **Install**.
3. **Restart Home Assistant**.
4. Go to **Settings → Devices & Services → Add Integration → Tovala Smart Oven** and sign in.

---

## Manual install (alternative)

Copy the `custom_components/tovala/` folder into your Home Assistant `config/custom_components/` directory, restart HA, then add the integration from the UI.

---

## Entities & events (initial)

- `sensor.tovala_time_remaining` — seconds remaining (if available)
- `binary_sensor.tovala_timer_running` — on when remaining > 0
- Event `tovala_timer_finished` with payload `{ oven_id, data }` when remaining crosses to 0

---

## Icon & logo

Add PNGs here (already referenced in `manifest.json`):

```
custom_components/tovala/icons/icon.png   # 256×256 PNG
custom_components/tovala/icons/logo.png   # 512×512 PNG
```

Then **bump the version** in `manifest.json` (e.g., `0.1.2`) and **restart HA**.  
HACS “Pending update” cards may still show a placeholder; that’s normal. The HA **integration card** and **brand picker** will use the files above.

---

## Troubleshooting

### “This integration cannot be added from the UI”
Ensure `manifest.json` contains `"config_flow": true` and you restarted HA after installing.

### “cannot_connect” during sign-in
This means the HTTP POST to Tovala failed **before** the server returned a normal 200/401/403.

1. **Turn on debug logging**:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.tovala: debug
   ```
   Restart HA and try add the integration again.

2. **Check the logs** (Developer Tools → Logs). You should see a line like:
   ```
   Tovala login POST https://api.beta.tovala.com/v0/getToken -> 200, body=...
   ```
   - If the status is **200**: auth succeeded. If the flow still fails, paste the log line into a GitHub issue.
   - If the status is **401/403**: wrong credentials (shows as `auth` in UI).
   - If the status is **0 or a connection error**: the HA host could not reach Tovala (DNS, TLS, or outbound firewall).

3. **Direct curl test** from the HA host:
   ```bash
   curl -i -X POST "https://api.beta.tovala.com/v0/getToken" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "User-Agent: HomeAssistant-Tovala/0.1" \
     -H "Origin: https://my.tovala.com" \
     -H "Referer: https://my.tovala.com/" \
     -H "X-Requested-With: XMLHttpRequest" \
     -H "X-Tovala-AppID: MyTovala" \
     -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD","type":"user"}'
   ```
   If beta fails, try `https://api.tovala.com/v0/getToken`.

> If you get **HTTP 200** via curl but still see `cannot_connect` in the UI, please capture the HA log lines for `custom_components.tovala` and open an issue with the snippet.

---

## Roadmap

- Discover ovens from the account and let you pick one in the config flow
- Poll status and map fields (`remaining`, `state`, `mode`) robustly
- Add device triggers for “Timer finished”
- Config options for poll interval

---

## License
MIT © 2025