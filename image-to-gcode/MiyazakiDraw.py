import image2gcode
import aimage
import speech_recognition as sr
import pyttsx3
import os

class Voice:
    def __init__(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', 'english')
        self.engine.setProperty('rate', 100)
        self.engine.setProperty('voice', voices[0].id)

    def speak(self, audio):
        self.engine.say(audio)
        self.engine.runAndWait()

#function to recognize voice and return the text
def recognize_voice():
    # obtain audio from the microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        r.pause_threshold = 1
        audio = r.listen(source)
    # recognize speech using Google Speech Recognition
    try:
        print("Google Speech Recognition thinks you said " + r.recognize_google(audio))
        recognizedaudio = r.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        recognizedaudio = None
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        recognizedaudio = None
    return recognizedaudio

def main():
    #MiyazakiVoice = Voice() 
    #MiyazakiVoice.speak("Hello, I am Miyazaki. I am a drawing machine. I can draw anything you want. Please tell me what you want to draw.")
    # recognize voice
    text = None
    while text is None:
        text = recognize_voice()
    
    #MiyazakiVoice.speak("Your command was:"+text+"Starting to draw!")
    key = os.environ.get("stabilitySDK_API_key")
    aimagePica = aimage.Aimage(text, 256, 256, key)
    # get the image from aimage
    image = aimagePica.get_image()
    image.save("output_test.png")
    # image processing
    pic = image2gcode.Piture(image)
    pic.gray_scale()
    gcode = image2gcode.Gcode(pic, 200, 200)
    # generate gcode
    gcode.gen_gcode()
    # send gcode to the drawing machine
    gcode.send_gcode("/dev/ttyUSB0", 115200)

if __name__ == "__main__":
    main()
