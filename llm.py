import time
import os
import json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from avatars.base_avatar import BaseAvatar
from utils.logger import logger

def llm_response(message,avatar_session:'BaseAvatar',datainfo:dict={}):
    try:
        opt = avatar_session.opt
        start = time.perf_counter()
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        end = time.perf_counter()
        logger.info(f"llm Time init: {end-start}s,{message}")
        
        completion = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2",
            messages=[{'role': 'system', 'content': opt.system_prompt},
                    {'role': 'user', 'content': message}],
            stream=True,
            # extra_body={"reasoning": {"enabled": True}} # nemotron-nano might not support reasoning param
        )
        
        result=""
        first = True
        for chunk in completion:
            if len(chunk.choices)>0:
                delta = chunk.choices[0].delta
                
                # Check for reasoning/thought if supported by model
                reasoning = getattr(delta, 'reasoning', None) or getattr(delta, 'thought', None)
                if reasoning:
                    if first:
                        logger.info("AI started reasoning...")
                        if hasattr(avatar_session, 'output') and hasattr(avatar_session.output, 'push_text'):
                            avatar_session.output.push_text(json.dumps({"type": "status", "status": "thinking"}))
                        first = False
                    continue

                msg = delta.content
                if msg is None:
                    continue
                
                if first:
                    end = time.perf_counter()
                    logger.info(f"llm Time to first content chunk: {end-start}s")
                    first = False
                    # Notify frontend we are responding
                    if hasattr(avatar_session, 'output') and hasattr(avatar_session.output, 'push_text'):
                        avatar_session.output.push_text(json.dumps({"type": "status", "status": "speaking"}))

                lastpos=0
                for i, char in enumerate(msg):
                    if char in ",.!;:，。！？：；" :
                        result = result+msg[lastpos:i+1]
                        lastpos = i+1
                        # Push partial sentence immediately for lowest latency
                        logger.info(f"LLM Partial: {result}")
                        avatar_session.put_msg_txt(result,datainfo)
                        # Send text to frontend for real-time captioning
                        if hasattr(avatar_session, 'output') and hasattr(avatar_session.output, 'push_text'):
                            avatar_session.output.push_text(result)
                        result=""
                result = result+msg[lastpos:]
                
        end = time.perf_counter()
        logger.info(f"llm Time to last chunk: {end-start}s")
        if result:
            logger.info(f"LLM Final: {result}")
            avatar_session.put_msg_txt(result,datainfo)
            if hasattr(avatar_session, 'output') and hasattr(avatar_session.output, 'push_text'):
                avatar_session.output.push_text(result)
        
    except Exception as e:
        logger.exception('llm exceptiopn:')
        return   
