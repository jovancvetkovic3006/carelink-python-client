#!/bin/env python

import time
import carelink_client2
import http.client
import urllib
import json
from datetime import datetime

client = carelink_client2.CareLinkClient(tokenFile="logindata.json")
if client.init():
    client.printUserInfo()
    recentData = client.getRecentData()
    patientData = recentData['patientData']

    unitsLeft = patientData['reservoirRemainingUnits'] if ('reservoirRemainingUnits' in patientData) else 0
    glicemia = round(patientData['lastSG']['sg'] / 18, 1)

    sensorState = patientData['lastSG']['sensorState']
    timestamp = patientData['lastSG']['timestamp']
    dt = datetime.fromisoformat(timestamp)
    lastTime = dt.strftime("%B %d, %Y u %I:%M") 

    isSensorConected=patientData['conduitSensorInRange']
    activeInsulin = round(patientData['activeInsulin']['amount'], 1)

    sensorBattery = patientData['gstBatteryLevel']
    pumpBattery = patientData['conduitBatteryLevel']
    
    deviceIsInRange = patientData['conduitSensorInRange']
    trend = '⚠️ pada' if patientData['lastSGTrend'] == 'DOWN' else 'raste' if patientData['lastSGTrend'] == 'UP' else 'miran'
    averageSG=round(patientData['averageSG'] / 18, 1)
    timeInRange='-'
    belowHypoLimit=str(patientData['belowHypoLimit'])+'%'
    aboveHyperLimit=str(patientData['aboveHyperLimit'])+'%'

    if patientData['timeInRange']:
        timeInRange=str(patientData['timeInRange'])+'%'


    messages = []

    if deviceIsInRange & isSensorConected & bool(glicemia):
        messages.append(f"Glikemija {str(glicemia)}\n")
        messages.append(f"Trend {str(trend)}\n")
        messages.append(f"Serzor traje jos {str(patientData['sensorDurationMinutes']//1440)}d {str((patientData['sensorDurationMinutes']%1440)//60)}h {str((patientData['sensorDurationMinutes']%1440)%60)}m")
        messages.append(f"Sledeca kalibracija za {str(patientData['timeToNextCalibrationMinutes']//60)}h {str(patientData['timeToNextCalibrationMinutes']%60)}m")
        if sensorState == 'CHANGE_SENSOR':
            messages.append(f"⚠️ Zamenite senzor\n")
            
        if 'pumpBannerState' in patientData:
            if len(patientData['pumpBannerState']) > 0 and patientData['pumpBannerState'][0]['type'] == 'TEMP_BASAL':
                temporalni=patientData['pumpBannerState'][0]['timeRemaining']
                messages.append(f"Temporalni tece jos {str(temporalni)} min\n")

        if activeInsulin != -1.0:
            messages.append(f"Aktivni insulin {str(activeInsulin)}")
    else:
        messages.append(f"⚠️ Senzor nije povezan\n")
        for sg in patientData['sgs']:
            if sg:
                glicemia = round(sg['sg'] / 18, 1)
                messages.append(f"Poslednja glikemija {str(glicemia)}\n")
                messages.append(f"Poslednja sinhronizacija {str(lastTime)}\n")
                break

    if patientData['pumpSuspended']:
        messages.append(f"⚠️ Pumpica je suspendovana")

    messages.append(f"HbA1c {str(averageSG)}")

    if patientData['timeInRange']:
        messages.append(f"U normali je {str(timeInRange)}")
        messages.append(f"Niska {str(belowHypoLimit)}")
        messages.append(f"Visoka {str(aboveHyperLimit)}")

    
    if unitsLeft < 20:
        messages.append(f"⚠️ Preostalo jedinica {str(unitsLeft)}")
    else:
        messages.append(f"Preostalo jedinica {str(unitsLeft)}")

    if sensorBattery < 10:
        messages.append(f"⚠️ Baterija senzora {str(sensorBattery)}%")
    else:
        messages.append(f"Baterija senzora {str(sensorBattery)}%")

    if pumpBattery < 10:
        messages.append(f"⚠️ Baterija pumpice {str(pumpBattery)}%\n")
    else:
        messages.append(f"Baterija pumpice {str(pumpBattery)}%\n")


with open('carelink_latestdata.json', 'r') as openfile:
    previousData = json.load(openfile)

json_object = json.dumps(patientData, indent=4)
with open("carelink_latestdata.json", "w") as outfile:
    outfile.write(json_object)

conn = http.client.HTTPSConnection("api.pushover.net:443")
conn.request("POST", "/1/messages.json",
             urllib.parse.urlencode({
                 "html": 1,
                 "token": "axzpjt4zu82iqv7qqkrzk2im2325db",
                 "user": "u9ca2yvoqzyks38hp6bs51fk2ka3hv",
                 "message": '\n'.join(map(str, messages)),
             }), {"Content-type": "application/x-www-form-urlencoded"})
conn.getresponse()

# crontab -e */10 * * * * sh /home/jovancvetkovic/IdeaProjects/carelink/carelink-python-client/run-push.sh
# crontab -e */10 * * * * python3 /home/jovancvetkovic/IdeaProjects/carelink/carelink-python-client/run-push.sh
# grep "/home/jovancvetkovic/IdeaProjects/carelink/carelink-python-client/carelink_client2_push.py" /var/log/syslog
