import os
import io
import time
from dotenv import load_dotenv
from ..models import Asset
import assemblyai as aai
import re
import logging
import time

from google.cloud import speech_v1p1beta1 as speech


class VideoProvider:
    def __init__(self, file_path):
        self.file_path = file_path

    def generate_transcript(self):
        raise NotImplementedError()

    def generate_diarized_transcript(self):
        raise NotImplementedError()

    def get_content(self, diarize=False):
        if diarize:
            assets = self.generate_diarized_transcript()
        else:
            assets = self.generate_transcript()
        return assets


class LocalVideoProvider(VideoProvider):
    def __init__(self, file_path):
        super().__init__(file_path)

    def generate_transcript(self):
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(self.file_path)
        return result["text"]

    def generate_diarized_transcript(
        self,
        no_stem=True,
        suppress_numerals=False,
        whisper_model="medium.en",
        batch_size=8,
        language=None,
    ):
        import torch
        from deepmultilingualpunctuation import PunctuationModel
        from pydub import AudioSegment
        from nemo.collections.asr.models.msdd_models import NeuralDiarizer
        from .lib.diarization.transcription_helpers import (
            transcribe_batched,
            transcribe,
        )
        from .lib.diarization.helpers import (
            wav2vec2_langs,
            filter_missing_timestamps,
            punct_model_langs,
            create_config,
            get_words_speaker_mapping,
            get_realigned_ws_mapping_with_punctuation,
            get_sentences_speaker_mapping,
            get_speaker_aware_transcript,
            write_srt,
            cleanup,
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"

        module_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the path for the temporary outputs
        temp_path = os.path.join(module_dir, "lib/diarization/temp_outputs")
        os.makedirs(temp_path, exist_ok=True)

        mtypes = {"cpu": "int8", "cuda": "float16"}

        if no_stem:
            return_code = os.system(
                f'python3 -m demucs.separate -n htdemucs --two-stems=vocals "{self.file_path}" -o "{temp_path}"'
            )

            if return_code != 0:
                logging.warning(
                    "Source splitting failed, using original audio file. Use --no_stem argument to disable it."
                )
                vocal_target = self.file_path
            else:
                vocal_target = os.path.join(
                    temp_path,
                    "htdemucs",
                    os.path.splitext(os.path.basename(self.file_path))[0],
                    "vocals.wav",
                )
        else:
            vocal_target = self.file_path

        if batch_size != 0:
            whisper_results, language = transcribe_batched(
                vocal_target,
                language,
                batch_size,
                whisper_model,
                mtypes[device],
                suppress_numerals,
                device,
            )
        else:
            whisper_results, language = transcribe(
                vocal_target,
                language,
                whisper_model,
                mtypes[device],
                suppress_numerals,
                device,
            )

        if language in wav2vec2_langs:
            alignment_model, metadata = whisperx.load_align_model(
                language_code=language, device=device
            )
            result_aligned = whisperx.align(
                whisper_results, alignment_model, metadata, vocal_target, device
            )
            word_timestamps = filter_missing_timestamps(
                result_aligned["word_segments"],
                initial_timestamp=whisper_results[0].get("start"),
                final_timestamp=whisper_results[-1].get("end"),
            )
            # clear gpu vram
            del alignment_model
            torch.cuda.empty_cache()
        else:
            assert (
                batch_size
                == 0  # TODO: add a better check for word timestamps existence
            ), (
                f"Unsupported language: {language}, use --batch_size to 0"
                " to generate word timestamps using whisper directly and fix this error."
            )
            word_timestamps = []
            for segment in whisper_results:
                for word in segment["words"]:
                    word_timestamps.append(
                        {"word": word[2], "start": word[0], "end": word[1]}
                    )

        # convert audio to mono for NeMo combatibility
        sound = AudioSegment.from_file(vocal_target).set_channels(1)
        sound.export(os.path.join(temp_path, "mono_file.wav"), format="wav")

        # Initialize NeMo MSDD diarization model
        msdd_model = NeuralDiarizer(cfg=create_config(temp_path)).to(device)
        msdd_model.diarize()

        del msdd_model
        torch.cuda.empty_cache()

        speaker_ts = []

        with open(os.path.join(temp_path, "pred_rttms", "mono_file.rttm"), "r") as f:
            lines = f.readlines()
            for line in lines:
                line_list = line.split(" ")
                s = int(float(line_list[5]) * 1000)
                e = s + int(float(line_list[8]) * 1000)
                speaker_ts.append([s, e, int(line_list[11].split("_")[-1])])

        wsm = get_words_speaker_mapping(word_timestamps, speaker_ts, "start")

        if language in punct_model_langs:
            # restoring punctuation in the transcript to help realign the sentences
            punct_model = PunctuationModel(model="kredor/punctuate-all")

            words_list = list(map(lambda x: x["word"], wsm))

            labled_words = punct_model.predict(words_list)

            ending_puncts = ".?!"
            model_puncts = ".,;:!?"

            # We don't want to punctuate U.S.A. with a period. Right?
            is_acronym = lambda x: re.fullmatch(r"\b(?:[a-zA-Z]\.){2,}", x)

            for word_dict, labeled_tuple in zip(wsm, labled_words):
                word = word_dict["word"]
                if (
                    word
                    and labeled_tuple[1] in ending_puncts
                    and (word[-1] not in model_puncts or is_acronym(word))
                ):
                    word += labeled_tuple[1]
                    if word.endswith(".."):
                        word = word.rstrip(".")
                    word_dict["word"] = word

        else:
            logging.warning(
                f"Punctuation restoration is not available for {language} language. Using the original punctuation."
            )

        wsm = get_realigned_ws_mapping_with_punctuation(wsm)
        ssm = get_sentences_speaker_mapping(wsm, speaker_ts)

        txt_output = io.StringIO()
        get_speaker_aware_transcript(ssm, txt_output)
        txt_output.seek(0)
        txt_transcript = txt_output.read()

        srt_output = io.StringIO()
        write_srt(ssm, srt_output)
        srt_output.seek(0)
        srt_transcript = srt_output.read()

        cleanup(temp_path)

        return [Asset(content=txt_transcript), Asset(content=srt_transcript)]

    def get_content(self, diarize=False):
        if diarize:
            assets = self.generate_diarized_transcript()
        else:
            assets = self.generate_transcript()
        return assets


class AssemblyAIVideoProvider(VideoProvider):
    def __init__(self, file_path):
        super().__init__(file_path)

        load_dotenv()
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

    def generate_transcript(self):
        transcriber = aai.Transcriber()

        start_time = time.time()
        transcript = transcriber.transcribe(self.file_path)
        end_time = time.time()

        print(f"Transcription time: {end_time - start_time} seconds")

        return transcript.text

    def generate_diarized_transcript(self):
        config = aai.TranscriptionConfig(speaker_labels=True)

        transcriber = aai.Transcriber()

        start_time = time.time()
        transcript = transcriber.transcribe(self.file_path, config=config)
        end_time = time.time()

        print(f"Diarization time: {end_time - start_time} seconds")

        utterances = []
        for utterance in transcript.utterances:
            utterances.append(f"Speaker {utterance.speaker}: {utterance.text}")

        return [Asset(content="\n".join(utterances))]


class GoogleCloudVideoProvider:
    def __init__(self, file_path):

        self.file_path = file_path
        print("Loading env.")
        load_dotenv()
        print("Loading client.")
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        print(cred_path)
        self.client = speech.SpeechClient.from_service_account_json(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        print("Loading client: ", self.client)
        # Set up the diarization config
        diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True, min_speaker_count=2, max_speaker_count=10
        )
        # Assign the diarization config to the recognition config
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code="en-US",
            diarization_config=diarization_config,  # Use the diarization config here
        )

    def generate_transcript(self):
        with io.open(self.file_path, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

        start_time = time.time()
        response = self.client.recognize(config=self.config, audio=audio)
        end_time = time.time()

        print(f"Transcription time: {end_time - start_time} seconds")

        # Concatenate the results from the response
        transcript = " ".join(
            result.alternatives[0].transcript for result in response.results
        )
        return transcript

    def generate_diarized_transcript(self):
        print("Generating transcript from file: ", self.file_path)
        with io.open(self.file_path, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

        start_time = time.time()
        response = self.client.recognize(config=self.config, audio=audio)
        end_time = time.time()

        print(f"Diarization time: {end_time - start_time} seconds")

        # Process the response to format the diarized transcript
        utterances = []
        for result in response.results:
            # Only consider the last result as it has all words with speaker tags
            words_info = (
                result.alternatives[0].words if result == response.results[-1] else []
            )
            for word_info in words_info:
                utterances.append(f"Speaker {word_info.speaker_tag}: {word_info.word}")

        return utterances
