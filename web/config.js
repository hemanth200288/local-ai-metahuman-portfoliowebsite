window.CONFIG = {
    // Backend API URL (Modal or local)
    // We explicitly set this to 8010 so the frontend on port 8000 can find it.
    API_BASE_URL: "http://localhost:8010", 

    // LiveKit configuration
    LIVEKIT_URL: "wss://local-ai-agent-d0vnbo4x.livekit.cloud",

    // Transport mode: "webrtc" or "livekit"
    TRANSPORT: "livekit" 
};

