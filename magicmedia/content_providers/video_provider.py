import os
import io
import whisper
from models import Asset
import whisperx
import torch
from deepmultilingualpunctuation import PunctuationModel
import re
import logging

class VideoProvider:
    def __init__(self, file_path):
        self.file_path = file_path

    def generate_transcript(self):
        model = whisper.load_model("base")
        result = model.transcribe(self.file_path)
        return result["text"]

    def generate_diarized_transcript(self, no_stem=True, suppress_numerals=False, whisper_model="medium.en", batch_size=8, language=None, device="cuda" if torch.cuda.is_available() else "cpu"):
        from pydub import AudioSegment
        from nemo.collections.asr.models.msdd_models import NeuralDiarizer
        from .lib.diarization.transcription_helpers import transcribe_batched, transcribe
        from .lib.diarization.helpers import wav2vec2_langs, filter_missing_timestamps, punct_model_langs, create_config, get_words_speaker_mapping, get_realigned_ws_mapping_with_punctuation, get_sentences_speaker_mapping, get_speaker_aware_transcript, write_srt, cleanup

        module_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define the path for the temporary outputs
        temp_path = os.path.join(module_dir, "lib/diarization/temp_outputs")
        os.makedirs(temp_path, exist_ok=True)

        mtypes = {"cpu": "int8", "cuda": "float16"}
        
        if no_stem:
            return_code = os.system(f'python3 -m demucs.separate -n htdemucs --two-stems=vocals "{self.file_path}" -o "{temp_path}"')

            if return_code != 0:
                logging.warning("Source splitting failed, using original audio file. Use --no_stem argument to disable it.")
                vocal_target = self.file_path
            else:
                vocal_target = os.path.join(temp_path,"htdemucs",os.path.splitext(os.path.basename(self.file_path))[0],"vocals.wav")
        else:
            vocal_target = self.file_path

        if batch_size != 0:
            whisper_results, language = transcribe_batched(vocal_target, language, batch_size, whisper_model, mtypes[device], suppress_numerals, device)
        else:
            whisper_results, language = transcribe(vocal_target, language, whisper_model, mtypes[device], suppress_numerals, device)

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
                batch_size == 0  # TODO: add a better check for word timestamps existence
            ), (
                f"Unsupported language: {language}, use --batch_size to 0"
                " to generate word timestamps using whisper directly and fix this error."
            )
            word_timestamps = []
            for segment in whisper_results:
                for word in segment["words"]:
                    word_timestamps.append({"word": word[2], "start": word[0], "end": word[1]})


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