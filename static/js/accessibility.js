class TextToSpeechService {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isPlaying = false;
    }
    
    speak(text) {
        if (this.synth.speaking) {
            this.synth.cancel();
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.8;
        utterance.pitch = 1;
        
        this.synth.speak(utterance);
        this.isPlaying = true;
    }
    
    pause() {
        this.synth.pause();
        this.isPlaying = false;
    }
    
    resume() {
        this.synth.resume();
        this.isPlaying = true;
    }
}