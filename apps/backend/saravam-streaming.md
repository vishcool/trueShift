

Overview
Transform audio into text in real-time with our WebSocket-based streaming API. Built for applications requiring immediate speech processing with minimal delay.

Model Availability: The Streaming API supports Saaras v3 (recommended) with multiple output modes via the mode parameter. Legacy models Saarika v2.5 and Saaras v2.5 are also available but we recommend switching to Saaras v3 for the best accuracy and features.

Supported Modes (Saaras v3)
Mode	Description	Output
transcribe	Standard transcription in the original language	Text in source language
translate	Transcribe and translate to English	English text
verbatim	Word-for-word transcription including filler words and repetitions	Verbatim text in source language
translit	Transcribe and transliterate to Roman script	Romanized text
codemix	Transcribe code-mixed speech (e.g., Hindi-English) naturally	Code-mixed text
Key Benefits
Ultra-Low Latency
Get transcription results in milliseconds, not seconds. Process speech as it happens with near-instantaneous responses.

Multi-Language Support
Support for 10+ Indian languages plus English with high accuracy transcription and translation capabilities.

Advanced Voice Detection
Smart Voice Activity Detection (VAD) with customizable sensitivity for optimal speech boundary detection.

Common Use Cases
Live Transcription: Real-time captions for meetings, webinars, and broadcasts
Voice Assistants: Interactive voice applications with immediate responses
Call Centers: Live call transcription and analysis
Accessibility: Real-time captioning for hearing-impaired users
Audio Format Support: Streaming APIs only support two audio formats:

WAV (wav)
Raw PCM (pcm_s16le, pcm_l16, pcm_raw)
Other formats like MP3, AAC, OGG, etc. are not supported for WebSocket streaming. Find sample audio files in our GitHub cookbook.

Getting Started
Get up and running with streaming in minutes. Simply change the mode parameter to switch between transcription, translation, and other output formats.

Choosing a Mode
Transcribe
Translate
Verbatim
Translit
Codemix
Transcribe audio in the original language.


Python

JavaScript


async with client.speech_to_text_streaming.connect(
    model="saaras:v3",
    mode="transcribe",              # Standard transcription
    language_code="en-IN",
    high_vad_sensitivity=True
) as ws:
    await ws.transcribe(audio=audio_data)
    response = await ws.recv()
    print(f"Transcription: {response}")
Full Example
Here’s a complete working example. Change the mode parameter to switch between any of the supported modes:


Python

JavaScript


import asyncio
import base64
from sarvamai import AsyncSarvamAI
# Load your audio file
with open("path/to/your/audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")
async def basic_transcription():
    # Initialize client with your API key
    client = AsyncSarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")
    # Connect and transcribe — change mode as needed
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        mode="transcribe",
        language_code="en-IN",
        high_vad_sensitivity=True
    ) as ws:
        await ws.transcribe(audio=audio_data)
        response = await ws.recv()
        print(f"Result: {response}")
asyncio.run(basic_transcription())
Enhanced Processing with Voice Detection
Add smart voice activity detection for better accuracy and control:


Python

JavaScript


import asyncio
import base64
from sarvamai import AsyncSarvamAI
with open("path/to/your/audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")
async def enhanced_transcription():
    client = AsyncSarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        mode="transcribe",              # Change mode as needed
        language_code="hi-IN",
        high_vad_sensitivity=True,       # Better voice detection
        vad_signals=True                # Get speech start/end signals
    ) as ws:
        await ws.transcribe(
            audio=audio_data,
            encoding="audio/wav",
            sample_rate=16000
        )
        
        async for message in ws:
            if message.get("type") == "speech_start":
                print("Speech detected")
            elif message.get("type") == "speech_end":
                print("Speech ended")
            elif message.get("type") == "transcript":
                print(f"Result: {message.get('text')}")
                break
asyncio.run(enhanced_transcription())
Instant Processing with Flush Signals
Force immediate processing without waiting for silence detection:


Python

JavaScript


import asyncio
import base64
from sarvamai import AsyncSarvamAI
with open("path/to/your/audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")
async def instant_processing():
    client = AsyncSarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        mode="transcribe",              # Change mode as needed
        language_code="en-IN",
        flush_signal=True               # Enable manual control
    ) as ws:
        await ws.transcribe(
            audio=audio_data,
            encoding="audio/wav",
            sample_rate=16000
        )
        
        # Force immediate processing
        await ws.flush()
        async for message in ws:
            print(f"Result: {message}")
            break
asyncio.run(instant_processing())
Custom Audio Configuration
Optimize for your specific audio setup (e.g., 8kHz telephony audio):


Python

JavaScript


import asyncio
import base64
from sarvamai import AsyncSarvamAI
with open("path/to/your/audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")
async def custom_audio_config():
    client = AsyncSarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        mode="transcribe",              # Change mode as needed
        language_code="kn-IN",
        sample_rate=8000,               # Match your audio
        input_audio_codec="pcm_s16le",  # Specify codec
        high_vad_sensitivity=True
    ) as ws:
        await ws.transcribe(
            audio=audio_data,
            encoding="audio/wav",
            sample_rate=8000             # Must match connection setting
        )
        
        response = await ws.recv()
        print(f"Result: {response}")
asyncio.run(custom_audio_config())
Important: Sample Rate Configuration for 8kHz Audio

When working with 8kHz audio, you must set the sample_rate parameter in both places:

When connecting to the WebSocket (connection parameter)
When sending audio data (transcribe parameter)
Both values must match your audio’s actual sample rate. Mismatched sample rates will result in poor transcription quality or errors.

async with client.speech_to_text_streaming.connect(
    model="saaras:v3",
    mode="transcribe",
    language_code="en-IN",
    sample_rate=8000        # Must match your audio
) as ws:
    await ws.transcribe(
        audio=audio_data,
        sample_rate=8000    # Must match connection setting
    )


For detailed endpoint documentation, see: Speech-to-Text WebSocket | Speech-to-Text Translate WebSocket

API Reference
Connection Parameters
Configure your WebSocket connection with these parameters:

Parameter	Type	Description	Example
language_code	string	Language for speech recognition (STT only)	"en-IN", "hi-IN", "kn-IN"
model	string	Model version to use	"saaras:v3" (recommended), "saarika:v2.5" (legacy), "saaras:v2.5" (legacy)
mode	string	Output mode (saaras:v3 only): transcribe, translate, verbatim, translit, codemix	"transcribe"
sample_rate	integer	Audio sample rate in Hz	8000, 16000
input_audio_codec	string	Audio codec format. Only wav and raw PCM formats (pcm_s16le, pcm_l16, pcm_raw) are supported	"wav", "pcm_s16le"
high_vad_sensitivity	boolean	Enhanced voice activity detection	true, false
vad_signals	boolean	Receive speech start/end events	true, false
flush_signal	boolean	Enable manual buffer flushing	true, false
Audio Data Parameters
When sending audio data to the streaming endpoint:

Parameter	Type	Description	Required
audio	string	Base64-encoded audio data	✅
encoding	string	Audio format	✅
sample_rate	integer	Audio sample rate (16000 Hz recommended). Must match the connection parameter	✅
Response Types
When vad_signals=true, you’ll receive different message types:

For STT:

speech_start: Voice activity detected
speech_end: Voice activity stopped
transcript: Final transcription result
For STTT:

speech_start: Voice activity detected
speech_end: Voice activity stopped
translation: Final translation result
Key Differences: STT vs STTT
Aspect	STT	STTT
Model	saaras:v3 (recommended), saarika:v2.5 (legacy)	saaras:v3 (recommended), saaras:v2.5 (legacy)
Method	transcribe()	translate()
Mode	transcribe, verbatim, translit, codemix (saaras:v3 only)	translate (saaras:v3 only)
Language Code	Required	Not required (auto-detected)
Output Language	Same as input	English only
Best Practices
Audio Quality & Sample Rate:
Use 16kHz sample rate for best results
For 8kHz audio, always set sample_rate=8000 in both connection and transcribe/translate calls
Ensure both sample rate parameters match your actual audio sample rate
Silence Handling:
Use 1 second silence when high_vad_sensitivity=false
Use 0.5 seconds silence when high_vad_sensitivity=true
Continuous Streaming: Send audio data continuously for real-time results
Error Handling: Always implement proper WebSocket error handling
Model Selection:
Use Saaras (saaras:v3) with mode parameter for the best transcription quality and flexible output modes
Use Saarika (saarika:v2.5) for transcription in the original language (legacy)
Use Saaras (saaras:v2.5) for direct translation to English (legacy)
Was this page helpful?
Yes
No
Previous
How to select output mode
Next
Built with
TwinMind
TwinMind

Ask TwinMind
Page icon
Summarize
Disable for this site
Disable for all sites
Streaming Speech-to-Text API | Sarvam API Docs