import os
import keyboard
import sounddevice
import soundfile
import tempfile
import queue
import sys
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
openai_client = OpenAI()


class VoiceRecorder:
    def __init__(self):
        self.recording_queue = queue.Queue()
        self.sample_rate = 44100
        self.soundfile_path = tempfile.mktemp(suffix=".wav")
        self.transcribe = False

    def record(self):
        with soundfile.SoundFile(self.soundfile_path, mode='x', samplerate=self.sample_rate, channels=1) as file:
            with sounddevice.InputStream(samplerate=self.sample_rate, channels=1, callback=self.save_sound_callback):
                print('press Ctrl+C to stop the recording')
                while True:
                    file.write(self.recording_queue.get())
                    if keyboard.is_pressed("f"):
                        print("Recording finished")
                        self.transcribe = True
                        break
                    elif keyboard.is_pressed("c"):
                        print("Recording canceled")
                        self.transcribe = False
                        break

    def save_sound_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.recording_queue.put(indata.copy())

    def transcribe_audio(self):
        with open(self.soundfile_path, "rb") as soundfile:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=soundfile
            )
        os.remove(self.soundfile_path)
        print(transcription.text)


if __name__ == "__main__":
    output_string = ""

    while True:
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'enter':
                print(f"\nOutput string: {output_string}")
                break
            elif event.name == 'ctrl':
                recorder = VoiceRecorder()
                print("recording...")
                recorder.record()
                if recorder.transcribe:
                    transcription = recorder.transcribe_audio()
                else:
                    transcription = "---"
                print(f"\nOutput string: {transcription}")
                break
            elif event.name == 'backspace':
                output_string = output_string[:-1]
                sys.stdout.write('\r' + output_string + ' ')
                sys.stdout.write('\r' + output_string)
                sys.stdout.flush()
            else:
                output_string += event.name
                sys.stdout.write('\r' + output_string)
                sys.stdout.flush()