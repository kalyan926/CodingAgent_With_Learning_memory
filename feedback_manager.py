"""
Feedback Manager - Handles human feedback requests without circular imports
"""
import time
import asyncio
from typing import Optional, Dict

# Global state for human feedback
feedback_state: Dict = {
    "requested": False,
    "request_id": None,
    "response": None,
    "timestamp": None
}


def set_feedback_request(request_id: str) -> None:
    """Set a feedback request"""
    global feedback_state
    feedback_state["requested"] = True
    feedback_state["request_id"] = request_id
    feedback_state["response"] = None
    feedback_state["timestamp"] = time.time()


def set_feedback_response(feedback: str, accepted: bool) -> None:
    """Set the feedback response"""
    global feedback_state
    feedback_state["response"] = {
        "feedback": feedback,
        "accepted": accepted
    }
    feedback_state["requested"] = False


def get_feedback_state() -> Dict:
    """Get current feedback state"""
    global feedback_state
    return {
        "requested": feedback_state["requested"],
        "request_id": feedback_state["request_id"],
        "timestamp": feedback_state["timestamp"]
    }


def request_feedback_from_ui() -> Dict:
    """Request feedback from UI and wait for response (blocking version for tools)"""
    global feedback_state
    
    # Set feedback request state
    request_id = str(time.time())
    set_feedback_request(request_id)
    
    # Wait for response (with timeout) using non-blocking sleep
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while feedback_state["response"] is None:
        if time.time() - start_time > timeout:
            feedback_state["requested"] = False
            return {"feedback": "", "accepted": False}
        
        # Use shorter sleep to be more responsive
        time.sleep(0.1)
    
    response = feedback_state["response"]
    feedback_state["response"] = None
    
    return response
