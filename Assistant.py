#!/usr/bin/python
from gtts import gTTS
import os, datetime, time, requests, cv2, pyautogui
import openweathermapy.core as owm	
import speech_recognition as sr
import face_recognition

from pyicloud import PyiCloudService
import click

def speak(message):
	"""
	Args: string to be spoken
	"""
	audio_message = gTTS(text=message, lang="en")
	audio_message.save("audio_message.mp3")
	os.system("mpg321 audio_message.mp3")

def check_meridians(userSpeech):
	"""
	Called by set_alarm to check which meridians are in input, reprompting if necessary
	Returns: am or pm
	"""
	if "a.m." in userSpeech:
		meridian = "am"
	elif "p.m." in userSpeech:
		meridian = "pm"
	else:
		speak("a m or p m?")
		meridian = check_meridians(recognize_speech())
	return meridian

def set_alarm():
	"""
	Called by interpret request to set alarm
	Returns: hour, min, median for alarm
	"""
	# prompt for alarm time
	userSpeech = 0
	while userSpeech == 0:
		speak("For when would you like to set the alarm?")
		userSpeech = recognize_speech()
	# set hour and min with respect to colon location
	colonLoc = userSpeech.find(":")
	alarm_hour = int(userSpeech[0:colonLoc])
	alarm_min = int(userSpeech[(colonLoc+1):(colonLoc+3)])
	# find meridian, reprompting if necessary
	alarm_meridian = check_meridians(userSpeech)
	return alarm_hour, alarm_min, alarm_meridian
		
def check_alarm(cur_hour, cur_min, cur_meridian, cur_daytime, alarm_hour, alarm_min, alarm_meridian, alarm_set, playlist, city="boston"):
	if (cur_hour, cur_min, cur_meridian, alarm_set) ==	(alarm_hour, alarm_min, alarm_meridian, True):
		spotify_playlist(playlist)
		time.sleep(220)
		temp, description, wind = get_weather(city)
		speak(f"Good {cur_daytime}, Landon. It is currently {cur_hour} {cur_min} {cur_meridian} with a temperature of {temp} degrees.")
		return False
	else: return True
		
def get_time():
	"""
	Returns: time_hour, time_min, meridian, daytime
	"""
	time = str(datetime.datetime.now().time())
	time_hour = int(time[0:2])
	time_min = int(time[3:5])
	# set times
	if time_hour in range(5,12): 
		daytime = "Morning"
	elif time_hour in range(12, 17):
		daytime = "Afternoon"
	elif time_hour in range(17,21):
		daytime = "Evening"
	elif time_hour >= 21 or time_hour < 5:
		daytime = "Night"
	else: daytime = "Invalid Daytime"
	# convert times and set meridian
	if time_hour > 12:
		time_hour = time_hour - 12
		meridian = "pm"
	elif time_hour == 12: 
		meridian = "pm"
	else:
		meridian = "am"
	# set o'clocks
	time_min = set_oclocks(time_min)
	return time_hour, time_min, meridian, daytime

def set_oclocks(time_min):
	if time_min == 0:
		time_min = "o'clock"
	elif time_min < 10:
		time_min = f"o{time_min}"
	return(time_min)	

def get_weather(city):
	"""
	Args: city
	Returns: temp, description, wind
	"""
	api_key = 'cd227c4b9f1b8441f2bd23a04459f623' 
	# Specifications
	city, units = 'boston', 'imperial'
	url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units={units}&APPID={api_key}'
	response = requests.get(url).json() 
	# Save weather data
	temp=(response['main'].get('temp'))
	description=(response['weather'][0].get('description'))
	wind=(response['wind'].get('speed'))	
	return temp, description, wind

## SPEECH ##
def recognize_speech():
	# from https://realpython.com/python-speech-recognition/
	r = sr.Recognizer()
	mic = sr.Microphone()
	with mic as source:
		r.adjust_for_ambient_noise(source, duration=0.5)
		#os.system("mpg321 ActiveSound.mp3")
		print("SPEAK")
		audio = r.listen(source)	
	print('RECOGNIZING')
	try:
		userSpeech = r.recognize_google(audio)
		print("SPEECH DETECTION:", userSpeech)
	except:
		print("SPEECH DETECTION: No speech detected")
		return(0)
	return userSpeech
	
def interpret_request(userSpeech):
	alarmPhrases = ["alarm"]
	weatherPhrases = ["whats it like outside", "what is it like outside", "weather"]
	temperaturePhrases = ["temperature"]
	timePhrases = ["what time is it", "what is the time", "whats the time", "what's the time", "what the time"]
	musicPhrases = ["play something chill"]
	
	# initialize variables
	alarm_hour, alarm_min, alarm_meridian, alarm_set = 0,0,0,False
	
	try:
		for phrase in temperaturePhrases:
			if phrase in userSpeech:
				temp, description, wind = get_weather(city)
				message = f"It is currently {temp} degrees"
		
		for phrase in alarmPhrases:
			if phrase in userSpeech:
				alarm_hour, alarm_min, alarm_meridian = set_alarm()
				alarm_set = True
				message = f"Alarm set for {alarm_hour} {alarm_min} {alarm_meridian}"
				
		for phrase in weatherPhrases:
			if phrase in userSpeech:
				temp, description, wind = get_weather(city)
				message = f"The weather is {description} with a temperature of {temp} degrees and wind of {wind} miles per hour"
					
		for phrase in timePhrases:
			if phrase in userSpeech:
				time_hour, time_min, meridian, daytime = get_time()
				message = f"It is currently {time_hour} {time_min} {meridian}"
		
		if "play something chill" in userSpeech:
			spotify_playlist("lo-fi beats")
		
		if "no" in userSpeech:
			message = "Ok! See you later"
			
		try:			
			speak(message)
		except: print("INTERPRETER: No message to speak")
	except:
		print("INTERPRETER: No valid input detected")
	return alarm_hour, alarm_min, alarm_meridian, alarm_set
	
## iCLOUD ##
def validate_icloud():
	api = PyiCloudService('landjbs@gmail.com', 'REd#rED@1577?!?')
	print("Two-factor authentication required. Your trusted devices are:")
	devices = api.trusted_devices
	for i, device in enumerate(devices):
		print("  %s: %s" % (i, device.get('deviceName',
			"SMS to %s" % device.get('phoneNumber'))))
	
	if not api.send_verification_code(device[0]):
		print("Failed to send verification code")
	code = click.prompt('Please enter validation code')
	if not api.validate_verification_code(device, code):
		print("Failed to verify verification code")	
	print("iCloud Validated")
	
## SPOTIFY ##
def spotify_playlist(playlist):
	pyautogui.moveTo(100, 200)
	# open spotlight search
	pyautogui.hotkey("command","space")
	# search for spotify
	pyautogui.typewrite("spotify")
	# click enter
	pyautogui.press("enter")
	# focus on search bar and delete anything that might already be in it
	pyautogui.hotkey("command","l")
	pyautogui.press("delete")
	# search for playlist name given by user
	pyautogui.typewrite(playlist)
	pyautogui.press("enter")
	# click on the top playlist	
	pyautogui.click(317, 276, button="left")
#	# open spotlight search
#	pyautogui.hotkey("command","space")
#	# go back to terminal
#	pyautogui.typewrite("terminal")
#	pyautogui.press("enter")	
	return True
	
		
def initializeAssistant():
	# set basic variables
	authorizedUsers = ["Landon Smith"]
	allUsers = ["Landon Smith", "Ethan Fields", "Nick Medrano"]
	userImages = ["landon.jpg", "ethan.jpg", "nick.jpg"]
	playlistSelection = ["lo-fi beats", "smack my bitch up", "giving bad people good ideas"]
	
	api = PyiCloudService('landjbs@gmail.com', 'REd#rED@1577?!?')
	city = "boston"
	spotifyOn = False
	alarm_hour, alarm_min, alarm_meridian, alarm_set = 0,0,0,False
	
	video_capture = cv2.VideoCapture(0)
	
	known_face_encodings = []
	known_face_names = []
	
	# Load a samples pictures and learn how to recognize them.
	for userNum, image in enumerate(userImages):
		cur_image = face_recognition.load_image_file(image)
		known_face_encodings.append(face_recognition.face_encodings(cur_image)[0])
		known_face_names.append(allUsers[userNum])
	
	# Initialize some variables
	face_locations = []
	face_encodings = []
	face_names = []
	process_this_frame = True

	namesList = []
	iteration = 0
	while True:
		# get current time
		cur_hour, cur_min, cur_meridian, cur_daytime = get_time()
		
		# reinitialize names list every 10000 captured frame (a little over 10 minutes)
		if iteration > 10000: namesList=[]
		
		# Grab a single frame of video
		ret, frame = video_capture.read()
		
		# Resize frame of video to 1/4 size for faster face recognition processing
		small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

		# Convert the image from BGR color (from OpenCV) to RGB color (from face_recognition)
		rgb_small_frame = small_frame[:, :, ::-1]

		# Only process every other frame of video to save time
		if process_this_frame:
			# Find all the faces and face encodings in the current frame of video
			face_locations = face_recognition.face_locations(rgb_small_frame)
			face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

			numFaces = (len(face_locations))

			face_names = []
			for face_encoding in face_encodings:
				# See if the face is a match for the known face(s)
				matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
				name = "Unknown"
				# If a match was found in known_face_encodings, just use the first one.
				if True in matches:
					first_match_index = matches.index(True)
					playlist = playlistSelection[first_match_index]
					name = known_face_names[first_match_index]
					
					if not name in namesList:
						namesList.append(name)
						firstName = (name.split())[0]
						try:
							if numFaces <= 2 and spotifyOn == False: spotifyOn = spotify_playlist(playlist)
						except:
							print("No playlist assigned to user")
						if name in authorizedUsers:
							# prompt user for request
							speak(f"Welcome back {firstName}")
							#userSpeech = recognize_speech()
							#alarm_hour, alarm_min, alarm_meridian, alarm_set = interpret_request(userSpeech)
						else:
							speak(f"Good {cur_daytime}, {firstName}")
				else:
					print("Unknown user detected.")			
		
		# check alarm
		#alarm_set = check_alarm(cur_hour, cur_min, cur_meridian, alarm_hour, alarm_min, alarm_meridian, alarm_set, playlist="productive morning", city="boston")
		
		# MANUAL ALARM SET
		alarm_set = check_alarm(cur_hour, cur_min, cur_meridian, cur_daytime, alarm_hour=9, alarm_min=20, alarm_meridian="am", alarm_set=True, playlist="productive morning", city="boston")
							
		# implement alarm ring bool var where it keeps trying to wake user up every couple min after the alarm has registered and until it sees user face			
				
		iteration += 1
	# Release handle to the webcam
	video_capture.release()
	cv2.destroyAllWindows()
	
initializeAssistant()