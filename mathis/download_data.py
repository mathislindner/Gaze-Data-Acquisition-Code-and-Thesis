import pupilcloud
from pupilcloud import Api, ApiException
import zipfile

api = pupilcloud.Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com")
recording_folder = "mathis/recordings/"

try:
    # Returns the current logged in user based on auth token
    data = api.get_profile().result
    print(data)
except ApiException as e:
    print("Exception when calling AuthApi->get_profile: %s\n" % e)


#download recording by id 
def download_recording(recording_id):
    try:
        # Returns the current logged in user based on auth token
        data = api.download_recording(recording_id).result
        print(data)
    except ApiException as e:
        print("Exception when calling AuthApi->get_profile: %s\n" % e)
