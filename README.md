# Tovala Smart Oven for Home Assistant

[![hacs][hacsbadge]](https://hacs.xyz)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[releases-shield]: https://img.shields.io/github/release/InfoSecured/ha-tovala.svg
[releases]: https://github.com/InfoSecured/ha-tovala/releases
[license-shield]: https://img.shields.io/github/license/InfoSecured/ha-tovala.svg

A **Home Assistant custom integration** that connects to Tovala Smart Ovens via their cloud API. Monitor cooking status, get meal details with images, track cooking history, and receive notifications when your food is ready!

> **Note:** Tovala does not publish a public API. This integration reverse-engineers the mobile app's HTTPS endpoints.

---

## ✨ Features

- 🔥 **Real-time cooking status** - Monitor your oven's current state
- ⏱️ **Timer tracking** - See remaining cook time updated every 10 seconds
- 🍽️ **Meal details** - Get meal name, image, and ingredients for Tovala meals
- 📸 **Meal images** - Display meal photos in notifications and dashboards
- 📜 **Cooking history** - View your last 10 cooking sessions
- 🔔 **Automation ready** - Fire events and use attributes in automations
- 🔍 **Automatic oven discovery** - No manual oven ID configuration needed

---

## 📦 Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=InfoSecured&repository=ha-tovala)

### HACS (Recommended)

1. Open **HACS → Integrations → ⋮ → Custom repositories**
2. Add repository URL: `https://github.com/InfoSecured/ha-tovala`
3. Category: **Integration**
4. Click **Install**
5. **Restart Home Assistant**
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **Tovala Smart Oven** and sign in with your Tovala credentials

### Manual Installation

1. Copy the `custom_components/tovala/` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration from **Settings → Devices & Services**

---

## 📊 Entities

### Sensors

**`sensor.tovala_time_remaining`**
Remaining cook time in seconds.

**Attributes:**
- `cooking_state` - "idle" or "cooking"
- `barcode` - The scanned barcode
- `meal_id` - Tovala meal ID (e.g., 463)
- `meal_title` - Meal name (e.g., "2 Eggs Over Medium on Avocado Toast")
- `meal_subtitle` - Additional meal description
- `meal_image` - Full URL to meal photo
- `meal_ingredients` - List of ingredients
- `estimated_end_time` - ISO timestamp when cooking will finish

**`sensor.tovala_last_cook`**
Shows your most recent cooking session.

**Attributes:**
- `last_cook_barcode` - Barcode of last cook
- `last_cook_meal_id` - Meal ID if it was a Tovala meal
- `last_cook_start_time` - When cooking started
- `last_cook_end_time` - When cooking ended
- `last_cook_status` - "complete" or "canceled"
- `recent_history` - Array of last 10 cooking sessions

### Binary Sensors

**`binary_sensor.tovala_timer_running`**
On when the oven is actively cooking (remaining time > 0).

### Events

**`tovala_timer_finished`**
Fired when the cooking timer reaches zero.

Payload:
```json
{
  "oven_id": "b3d64c11-96db-4ed2-9589-b52fbd0a15b1",
  "data": { "state": "idle", "meal": {...}, ... }
}
```

---

## 🤖 Automation Examples

### Send notification with meal name and image when cooking finishes

**Telegram:**
```yaml
automation:
  - alias: "Tovala Cooking Done"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tovala_time_remaining
        below: 1
        above: -0.3
    action:
      - service: telegram_bot.send_photo
        data:
          url: "{{ state_attr('sensor.tovala_time_remaining', 'meal_image') }}"
          caption: >-
            {% set meal = state_attr('sensor.tovala_time_remaining', 'meal_title') %}
            {{ meal if meal else 'Your oven' }} is done cooking!
```

**iOS/Android Mobile App:**
```yaml
automation:
  - alias: "Tovala Cooking Done - Mobile"
    trigger:
      - platform: state
        entity_id: binary_sensor.tovala_timer_running
        from: "on"
        to: "off"
    action:
      - service: notify.mobile_app_YOUR_DEVICE
        data:
          title: "Tovala Oven"
          message: "{{ state_attr('sensor.tovala_time_remaining', 'meal_title') }} is ready!"
          data:
            image: "{{ state_attr('sensor.tovala_time_remaining', 'meal_image') }}"
```

### Alert when 1 minute remaining

```yaml
automation:
  - alias: "Tovala Almost Done"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tovala_time_remaining
        below: 60
    action:
      - service: notify.notify
        data:
          message: "Your {{ state_attr('sensor.tovala_time_remaining', 'meal_title') }} has 1 minute left!"
```

---

## 🎨 Dashboard Card Example

Using [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom):

```yaml
type: custom:mushroom-template-card
primary: Tovala Oven
secondary: >-
  {% if state_attr('sensor.tovala_time_remaining', 'meal_title') %}
    {{ state_attr('sensor.tovala_time_remaining', 'meal_title') }}
  {% elif states('sensor.tovala_time_remaining') | int > 0 %}
    {{ states('sensor.tovala_time_remaining') | int // 60 }}m {{ states('sensor.tovala_time_remaining') | int % 60 }}s remaining
  {% else %}
    Idle
  {% endif %}
entity: sensor.tovala_time_remaining
icon: mdi:toaster-oven
icon_color: >-
  {% if is_state('binary_sensor.tovala_timer_running', 'on') %}
    orange
  {% else %}
    grey
  {% endif %}
tap_action:
  action: more-info
```

---

## 🔧 Troubleshooting

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.tovala: debug
```

Then **restart Home Assistant** and check logs in **Developer Tools → Logs**.

### "cannot_connect" error

This means Home Assistant cannot reach Tovala's API:

1. **Check your internet connection**
2. **Verify credentials** - Make sure your email/password are correct
3. **Test API access**:
   ```bash
   curl -i -X POST "https://api.beta.tovala.com/v0/getToken" \
     -H "Content-Type: application/json" \
     -H "X-Tovala-AppID: MAPP" \
     -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD","type":"user"}'
   ```
   - If you get HTTP 200, credentials are valid
   - If you get HTTP 401/403, check your email/password
   - If connection fails, check firewall/DNS

### "auth" error

Your credentials are incorrect. Double-check your Tovala email and password.

### No meal details showing

Meal details only appear when:
1. You scan a **Tovala meal barcode** (not manual cooking modes)
2. The meal is in Tovala's database
3. You've reloaded the integration after updating

Manual cooking modes (like "manual-mini-toast-4" or "Bake at 400°") won't have meal details.

---

## 🛣️ Roadmap

- [ ] WebSocket support for real-time updates (currently polls every 10s)
- [ ] Multi-oven support with oven selection in UI
- [ ] Control capabilities (start/stop cooking remotely)
- [ ] Configurable poll interval
- [ ] Device triggers for "Timer Started" and "Timer Finished"

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

MIT © 2025 Jason Lazerus

---

## ⚠️ Disclaimer

This integration is not affiliated with, endorsed by, or supported by Tovala. Use at your own risk. The integration may break if Tovala changes their API.