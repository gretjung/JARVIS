import asyncio
import os
import tempfile
import winsound

from winsdk.windows.media.speechsynthesis import SpeechSynthesizer
from winsdk.windows.storage.streams import DataReader


async def main():
    synth = SpeechSynthesizer()

    # หาเสียงภาษาไทย
    voices = SpeechSynthesizer.all_voices

    thai_voice = None

    for voice in voices:
        print(f"VOICE: {voice.language} | {voice.display_name}")
        if voice.language.lower() == "th-th":
            thai_voice = voice
            break

    if thai_voice is None:
        print("ERROR: Thai voice not found")
        return

    print()
    print("SELECTED:", thai_voice.display_name)

    synth.voice = thai_voice

    text = "สวัสดีครับ ผมคือจาร์วิส ระบบเสียงภาษาไทยพร้อมใช้งานแล้ว"

    print("Synthesizing...")

    stream = await synth.synthesize_text_to_stream_async(text)

    # อ่านข้อมูลเสียงจาก WinRT stream
    input_stream = stream.get_input_stream_at(0)
    reader = DataReader(input_stream)

    size = stream.size
    await reader.load_async(size)

    buffer = reader.read_buffer(size)

    # ดึง bytes
    data = bytes(buffer)

    reader.close()
    input_stream.close()
    stream.close()

    # บันทึกเป็น WAV ชั่วคราว
    path = os.path.join(
        tempfile.gettempdir(),
        "jarvis_pattara_test.wav"
    )

    with open(path, "wb") as f:
        f.write(data)

    print("WAV:", path)
    print("Playing...")

    winsound.PlaySound(
        path,
        winsound.SND_FILENAME
    )

    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())