
import asyncio
import sys
import os
import logging

# Add current directory to sys.path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("debug_script")

async def test_flow():
    logger.info("--- 1. Testing Routing Logic ---")
    try:
        from app.chat.smart_router import route_message, ToolIntent, RoutingTarget
        from app.core.models import User
        
        # Mock user
        mock_user = User(id=1, username="debug_user", active_persona="standard")
        
        # Test routing
        msg = "kedi çiz"
        decision = route_message(msg, user=mock_user)
        logger.info(f"Message: '{msg}'")
        logger.info(f"Target: {decision.target}")
        logger.info(f"Tool Intent: {decision.tool_intent}")
        logger.info(f"Blocked: {decision.blocked}")
        
        if decision.target != RoutingTarget.IMAGE:
            logger.error("❌ Routing FAILED: Expected IMAGE target.")
        else:
            logger.info("✅ Routing SUCCESS.")
            
    except Exception as e:
        logger.error(f"❌ Routing Exception: {e}")
        return

    logger.info("\n--- 2. Testing Image Prompt Building ---")
    try:
        # We need to mock settings or env vars if real API calls are made
        # Assuming environment is set up correctly in the shell context
        
        from app.chat.processor import build_image_prompt
        
        logger.info("Calling build_image_prompt('kedi çiz')...")
        prompt = await build_image_prompt("kedi çiz")
        logger.info(f"Generated Prompt: '{prompt}'")
        logger.info("✅ Prompt Build SUCCESS.")
        
    except Exception as e:
        logger.error(f"❌ Prompt Build Exception: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_flow())
