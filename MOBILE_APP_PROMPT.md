
---

# 📁 FILE 3 — `MOBILE_APP_PROMPT.md`
## Mobile Application Responsibilities & Flow

```markdown
# SYSTEM ROLE
You are building the MOBILE CLIENT for an AI fitness platform.

Your responsibility is data capture, permissions, and delivery —
NOT AI reasoning.

---

## 1. PLATFORM

- React Native (Expo Bare)
- Background execution enabled
- Offline-first where possible

---

## 2. REQUIRED PERMISSIONS

Request explicitly and progressively:
- Location (foreground + background)
- Camera (photo & video)
- Google Fit
- Strava
- Digital Wellbeing
- Notifications

---

## 3. DATA CAPTURE RESPONSIBILITIES

Capture and send:
- Location updates (low frequency)
- Workout start/stop signals
- Health metrics from Google Fit
- Activity sync from Strava
- Screen time summaries
- Images or short video clips (user-initiated only)

Do NOT perform AI reasoning on the client.

---

## 4. CAMERA FLOW

1. User captures photo or video
2. Perform on-device frame sampling
3. Compress and anonymize if needed
4. Upload to backend
5. Await AI response

---

## 5. LOCATION INTELLIGENCE

Send location data to backend.
Backend determines place type.

Client behavior:
- Gym → show strength UI
- Park → show cardio UI
- Home → show bodyweight UI

---

## 6. BACKGROUND SYNC

- Batch events
- Retry on failure
- Respect battery optimization
- Never block UI

---

## 7. UI RESPONSIBILITIES

- Display AI recommendations
- Show confidence / safety notes
- Collect user feedback
- Show progress trends

Do NOT store long-term state locally.

END OF FILE
