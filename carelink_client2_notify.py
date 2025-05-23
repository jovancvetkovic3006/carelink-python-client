#!/bin/env python

import time
import carelink_client2
import json
from datetime import datetime
import os
import subprocess

# ========== CONFIGURATION ==========
DATA_FILE = "carelink_latestdata.json"
# ===================================

def send_notification(title, message):
    try:
        subprocess.run([
            'termux-notification',
            '--title', title,
            '--content', message,
            '--priority', 'high'
        ])
    except Exception as e:
        print("Notification error:", e)

try:
    client = carelink_client2.CareLinkClient(tokenFile="logindata.json")
    if client.init():
        client.printUserInfo()
        recentData = client.getRecentData()
        patientData = recentData.get('patientData', {})

        unitsLeft = patientData.get('reservoirRemainingUnits', 0)
        glicemia = round(patientData['lastSG']['sg'] / 18, 1) if 'lastSG' in patientData else 0

        sensorState = patientData.get('lastSG', {}).get('sensorState', 'UNKNOWN')
        timestamp = patientData.get('lastSG', {}).get('timestamp')
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        lastTime = dt.strftime("%B %d, %Y u %I:%M")

        isSensorConnected = patientData.get('conduitSensorInRange', False)
        activeInsulin = round(patientData.get('activeInsulin', {}).get('amount', -1.0), 1)

        sensorBattery = patientData.get('gstBatteryLevel', 0)
        pumpBattery = patientData.get('conduitBatteryLevel', 0)

        deviceIsInRange = patientData.get('conduitSensorInRange', False)
        trend_raw = patientData.get('lastSGTrend', '')
        trend = '⚠️ pada' if trend_raw == 'DOWN' else 'raste' if trend_raw == 'UP' else 'miran'
        averageSG = round(patientData.get('averageSG', 0) / 18, 1)
        timeInRange = "-"
        belowHypoLimit = f"{patientData.get('belowHypoLimit', 0)}%"
        aboveHyperLimit = f"{patientData.get('aboveHyperLimit', 0)}%"

        if 'timeInRange' in patientData:
            timeInRange = f"{patientData['timeInRange']}%"

        messages = []

        messages.append(f"📅 {lastTime}")
        messages.append(f"🩸 Glikemija: {glicemia} mmol/L")
        messages.append(f"📈 Trend: {trend}")

        if deviceIsInRange and isSensorConnected and bool(glicemia):
            duration = patientData.get('sensorDurationMinutes', 0)
            messages.append(f"🕒 Senzor: {duration//1440}d {(duration%1440)//60}h {(duration%1440)%60}m")

            calibration = patientData.get('timeToNextCalibrationMinutes', 0)
            messages.append(f"🎯 Sledeća kalibracija: {calibration//60}h {calibration%60}m")

            if sensorState == 'CHANGE_SENSOR':
                messages.append("⚠️ Potrebna zamena senzora")

            banner = patientData.get('pumpBannerState', [])
            if banner and banner[0].get('type') == 'TEMP_BASAL':
                temporalni = banner[0].get('timeRemaining', 0)
                messages.append(f"💡 Temporalna bazalna: još {temporalni} min")

            if activeInsulin != -1.0:
                messages.append(f"💉 Aktivni insulin: {activeInsulin} U")

        else:
            messages.append("⚠️ Senzor nije povezan")
            for sg in patientData.get('sgs', []):
                if sg:
                    glicemia = round(sg['sg'] / 18, 1)
                    messages.append(f"📊 Poslednja glikemija: {glicemia} mmol/L")
                    messages.append(f"🕓 Poslednja sinhronizacija: {lastTime}")
                    break

        if patientData.get('pumpSuspended', False):
            messages.append("⛔ Pumpica je suspendovana")

        messages.append(f"🧪 HbA1c (prosečna): {averageSG}")
        messages.append(f"✅ U normali: {timeInRange}")
        messages.append(f"⬇️ Niska: {belowHypoLimit}")
        messages.append(f"⬆️ Visoka: {aboveHyperLimit}")

        messages.append(
            f"{'⚠️ ' if unitsLeft < 20 else ''}Insulin u rezervoaru: {unitsLeft} U")

        messages.append(
            f"{'⚠️ ' if sensorBattery < 10 else ''}Baterija senzora: {sensorBattery}%")

        messages.append(
            f"{'⚠️ ' if pumpBattery < 10 else ''}Baterija pumpice: {pumpBattery}%")

        
        # Load previous data if available
        previousData = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as openfile:
                    previousData = json.load(openfile)
            except Exception as e:
                print("Greška pri čitanju prethodnih podataka:", e)

        # Save new data
        try:
            with open(DATA_FILE, "w") as outfile:
                json.dump(patientData, outfile, indent=4)
        except Exception as e:
            print("Greška pri snimanju novih podataka:", e)

        # Send local notification using Termux API
        send_notification("CareLink Update", '\n'.join(messages))

    else:
        print("Neuspela autentifikacija sa CareLink.")
except Exception as ex:
    print("Neočekvana greška:", ex)
