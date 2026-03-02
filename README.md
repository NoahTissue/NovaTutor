# 🤖 Nova: AI Personal Learning Assistant

**University of Florida | Computational Reasoning Group** 
## About The Project
Nova is an AI-powered desktop companion built to provide personalized academic support. By combining natural language processing with real-time computer vision, Nova acts as a 24/7 intelligent tutor. It reads student engagement through facial expressions and dynamically adapts its teaching style to match their emotional state, reducing academic stress and improving performance.

## Current Architecture
The repository contains the core hardware integration and cognitive framework for the Nova prototype:

* **Cognitive Brain:** Powered by Google Gemini 2.5 Flash, tuned to deliver concise, conversational, and encouraging tutoring.
* **Emotion Engine:** Uses OpenCV and DeepFace to scan for emotional feedback (frustration, confusion, joy). Features a custom hardware-optimization layer to prevent Raspberry Pi thermal throttling.
* **Voice Interface:** Completely hands-free. Uses PicoVoice Porcupine for wake-word detection (`"Hey Nova"`), Faster-Whisper for local STT, and ElevenLabs for realistic TTS.
* **Kiosk UI:** A hardware-optimized Flask and Socket.io web server running a state-based visual interface for small touchscreen displays.

## Future Roadmap
Future development will integrate Nova directly with the UF's Canvas LMS. This will allow the device to reference specific courses, upcoming deadlines, and assignments to provide deeply targeted academic support.
