#!/bin/env python

import time
import carelink_client2
import http.client
import urllib
import json

client = carelink_client2.CareLinkClient(tokenFile="logindata.json")
if client.init():
    client.printUserInfo()
    carelinkDictObject = client.getRecentData()


    unitsLeft = carelinkDictObject['reservoirRemainingUnits']
    isSensorConected=carelinkDictObject['sensorState']!='NO_DATA_FROM_PUMP'
    glicemia = round(carelinkDictObject['lastSG']['sg'] / 18, 1)
    activeInsulin = carelinkDictObject['activeInsulin']['amount']
    battery = carelinkDictObject['gstBatteryLevel']
    deviceIsInRange = carelinkDictObject['conduitMedicalDeviceInRange']
    sensorDurationHours = carelinkDictObject['sensorDurationHours']
    sensorDurationDays=sensorDurationHours//24
    sensorDurationHoursOnly=sensorDurationHours%24

    if sensorDurationDays <= 1: 
        senzorDuration=f"{sensorDurationHours}h"
    else:
        senzorDuration=f"{sensorDurationDays}d {sensorDurationHoursOnly}h"

    nextCalibration = carelinkDictObject['timeToNextCalibHours']
    suspended = 'DA' if carelinkDictObject['lastAlarm'][
        'messageId'] == 'BC_SID_LOW_SG_INSULIN_DELIVERY_SUSPENDED_SINCE_X_CHECK_BG' else 'NE'
    trend = 'Pada' if carelinkDictObject['lastSGTrend'] == 'DOWN' else 'Raste' if carelinkDictObject['lastSGTrend'] == 'DOWN' else 'Mirno'

    averageSG=round(carelinkDictObject['averageSG'] / 18, 1)
    timeInRange='-'
    belowHypoLimit=str(carelinkDictObject['belowHypoLimit'])+'%'
    aboveHyperLimit=str(carelinkDictObject['aboveHyperLimit'])+'%'

    if carelinkDictObject['timeInRange']:
        timeInRange=str(carelinkDictObject['timeInRange'])+'%'



    messages = []

    if deviceIsInRange & isSensorConected & bool(glicemia):
        messages.append(f"Glikemija {str(glicemia)}\n")
        messages.append(f"Serzor traje jos {str(senzorDuration)}")
        messages.append(f"Sledeca kalibracija za {str(nextCalibration)}h")
    else:
           messages.append(f"Senzor nije povezan\n")
           for sg in carelinkDictObject['sgs']:
                if sg:
                    glicemia = round(sg['sg'] / 18, 1)
                    messages.append(f"Poslednja glikemija {str(glicemia)}\n")
                    break


    if carelinkDictObject['lastAlarm'][
        'messageId'] == 'BC_SID_LOW_SG_INSULIN_DELIVERY_SUSPENDED_SINCE_X_CHECK_BG':
        messages.append(f"Pumpica je suspendovana")


    if len(carelinkDictObject['pumpBannerState']) > 0 and carelinkDictObject['pumpBannerState'][0]['type'] == 'TEMP_BASAL':
        temporalni=carelinkDictObject['pumpBannerState'][0]['timeRemaining']
        messages.append(f"Temporalni tece jos {str(temporalni)} min\n")

    if activeInsulin != -1.0:
        messages.append(f"Aktivni insulin {str(activeInsulin)}")
        messages.append(f"Preostalo jedinica {str(unitsLeft)}")
        messages.append(f"Baterija {str(battery)}%\n")


    messages.append(f"HbA1c {str(averageSG)}")

    if carelinkDictObject['timeInRange']:
        messages.append(f"U normali je {str(timeInRange)}")
        messages.append(f"Niska {str(belowHypoLimit)}")
        messages.append(f"Visoka {str(aboveHyperLimit)}")

with open('carelink_latestdata.json', 'r') as openfile:
    previousData = json.load(openfile)

json_object = json.dumps(carelinkDictObject, indent=4)
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
