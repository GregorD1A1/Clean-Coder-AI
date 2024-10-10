import os
from threading import Thread
import tempfile
import queue
import sys
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from utilities.util_functions import print_formatted

load_dotenv(find_dotenv())
openai_client = OpenAI()


class VoiceRecorder:
    def __init__(self):
        self.microphone_available = True
        self.error_message = ""
        try:
            import sounddevice
            import soundfile
            self.sounddevice = sounddevice
            self.soundfile = soundfile
        except OSError:
            self.microphone_available = False
        self.recording_queue = queue.Queue()
        self.sample_rate = 44100
        self.soundfile_path = tempfile.mktemp(suffix=".wav")
        self.is_recording = False
        self.recording_thread = None

    def record(self):
        with self.soundfile.SoundFile(self.soundfile_path, mode='x', samplerate=self.sample_rate, channels=1) as file:
            with self.sounddevice.InputStream(samplerate=self.sample_rate, channels=1, callback=self.save_sound_callback):
                print('Press Enter to finish recording')
                while self.is_recording:
                    file.write(self.recording_queue.get())

    def save_sound_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.recording_queue.put(indata.copy())

    def start_recording(self):
        if not self.recording_thread or not self.recording_thread.is_alive():
            self.recording_thread = Thread(target=self.record)
            self.recording_thread.start()
            self.is_recording = True

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()

    def transcribe_audio(self):
        with open(self.soundfile_path, "rb") as soundfile:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=soundfile
            )
        os.remove(self.soundfile_path)
        print(transcription.text)
        return transcription.text
