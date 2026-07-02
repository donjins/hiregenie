import time
import logging
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.config import settings

logger = logging.getLogger("hiregenie.middleware")
logger.setLevel(logging.INFO)

# Create a handler to output logs to stdout
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Middleware for dynamic model selection based on task complexity.
    Tracks execution time and token usage.
    """
    # 1. Determine Complexity
    is_complex = False
    
    # Restrict complex model routing (gpt-4o) to heavy ranking/synthesis tasks to optimize speed
    for msg in request.messages:
        content = str(msg.content).lower()
        if any(kw in content for kw in ["candidate_ranking_agent", "skill_gap_agent", "rank candidates", "detailed skill gap"]):
            is_complex = True
            break
            
    # 2. Select Model
    chosen_model = "gpt-4o" if is_complex else "gpt-4o-mini"
    
    logger.info(f"[MIDDLEWARE] Selecting model '{chosen_model}' based on task complexity (is_complex={is_complex})")
    
    # 3. Override model on request
    # Initialize the ChatOpenAI client with API key and selected model
    api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""
    if not api_key:
        api_key = "mock-key-for-local-testing"
        
    model_instance = ChatOpenAI(
        model=chosen_model,
        temperature=0.0,
        api_key=api_key
    )
    
    request = request.override(model=model_instance)
    
    # 4. Measure Execution Time
    start_time = time.time()
    try:
        response = handler(request)
    except Exception as e:
        logger.error(f"[MIDDLEWARE] Model call failed: {e}")
        raise e
    duration = time.time() - start_time
    
    # 5. Track Token Usage
    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    if response and response.result:
        # Check last message in result list (usually AIMessage)
        last_msg = response.result[-1]
        
        if hasattr(last_msg, "usage_metadata") and last_msg.usage_metadata:
            metadata = last_msg.usage_metadata
            token_usage = {
                "prompt_tokens": metadata.get("input_tokens", 0),
                "completion_tokens": metadata.get("output_tokens", 0),
                "total_tokens": metadata.get("total_tokens", 0)
            }
        elif hasattr(last_msg, "response_metadata") and "token_usage" in last_msg.response_metadata:
            metadata = last_msg.response_metadata["token_usage"]
            token_usage = {
                "prompt_tokens": metadata.get("prompt_tokens", 0),
                "completion_tokens": metadata.get("completion_tokens", 0),
                "total_tokens": metadata.get("total_tokens", 0)
            }
            
    logger.info(
        f"[MIDDLEWARE] Execution completed in {duration:.4f}s | "
        f"Usage: Prompt={token_usage['prompt_tokens']}, Completion={token_usage['completion_tokens']}, Total={token_usage['total_tokens']}"
    )
    
    return response
