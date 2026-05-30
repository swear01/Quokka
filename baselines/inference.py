import json
import os
import hashlib
import time
import logging
from functools import wraps
from dotenv import load_dotenv
import requests

# Lazy imports for optional provider SDKs
_openai = None
_Together = None
_anthropic = None
_genai = None
_sglang_utils = None
_AutoTokenizer = None
_Reasoning = None

def _get_openai():
    global _openai
    if _openai is None:
        import openai as mod
        _openai = mod
    return _openai

def _get_together():
    global _Together
    if _Together is None:
        from together import Together as T
        _Together = T
    return _Together

def _get_anthropic():
    global _anthropic
    if _anthropic is None:
        import anthropic as mod
        _anthropic = mod
    return _anthropic

def _get_genai():
    global _genai
    if _genai is None:
        from google import genai as mod
        _genai = mod
    return _genai

def _get_sglang_utils():
    global _sglang_utils
    if _sglang_utils is None:
        from sglang import utils as mod
        _sglang_utils = mod
    return _sglang_utils

def _get_auto_tokenizer():
    global _AutoTokenizer
    if _AutoTokenizer is None:
        from transformers import AutoTokenizer as AT
        _AutoTokenizer = AT
    return _AutoTokenizer

def _get_reasoning():
    global _Reasoning
    if _Reasoning is None:
        from openai.types.shared_params import Reasoning as R
        _Reasoning = R
    return _Reasoning

# Load environment variables from .env file with override
# Search from repo root (baselines/ is one level down from repo root)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.isfile(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    load_dotenv(override=True)

# Together API does not have an official SDK, use requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = None
        try:
            from threading import Lock
            self.lock = Lock()
        except ImportError:
            self.lock = None

    def acquire(self):
        if self.lock:
            self.lock.acquire()
        try:
            now = time.time()
            time_passed = now - self.last_update
            if time_passed >= 60:
                self.tokens = self.requests_per_minute
                self.last_update = now
            if self.tokens > 0:
                self.tokens -= 1
                return True
            wait_time = 60 - time_passed
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_update = time.time()
            self.tokens = self.requests_per_minute - 1
            return True
        finally:
            if self.lock:
                self.lock.release()

def rate_limit(requests_per_minute: int):
    limiter = RateLimiter(requests_per_minute)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator

class AIClient:
    def generate_completion(self, prompt, **kwargs):
        raise NotImplementedError

class OpenAIClient(AIClient):
    def __init__(self, api_key=None, model_name=None):
        openai_mod = _get_openai()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        self.client = openai_mod.OpenAI(api_key=self.api_key)
        self.model_name = model_name

    @retry_on_error()
    def generate_completion(self, prompt, **kwargs):
        model = kwargs.get("model", self.model_name or "gpt-3.5-turbo")
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 2048)
        n = kwargs.get("n", 1)
        messages = kwargs.get("messages")
        presence_penalty = kwargs.get("presence_penalty", 0.0)
        frequency_penalty = kwargs.get("frequency_penalty", 0.0)
        enable_thinking = kwargs.get("enable_thinking", False)
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        
        responses = []
        response_kwargs = {
            "model": model,
            "input": messages,
            "max_output_tokens": max_tokens,
        }
        if model in ["gpt-5.1", "gpt-5.2"]:
            response_kwargs["reasoning"] = {"effort": "none"} if not enable_thinking else {"effort": "low"}
        
        if "o3" in model or "o4" in model: 
            response_kwargs["reasoning"] = {"effort": "low"} 
        
        for _ in range(n):
            response = self.client.responses.create(**response_kwargs)
            responses.append(response.output_text)
        print(responses)
        return responses

class TogetherClient(AIClient):
    def __init__(self, api_key=None, model_name=None):
        Together = _get_together()
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together API key not found")
        self.client = Together(api_key=self.api_key)
        self.model_name = model_name
    @retry_on_error()
    def generate_completion(self, prompt, **kwargs):
        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 2048)
        n = kwargs.get("n", 1)
        messages = kwargs.get("messages")
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "messages": messages,
            "n": n
        }
        if "o4" in model:
            # payload["max_completion_tokens"] = max_tokens
            # o4 does not support temperature
            pass
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature
        response = self.client.chat.completions.create(**payload)
        return [choice.message.content for choice in response.choices]

class ClaudeClient(AIClient):
    def __init__(self, api_key=None, model_name=None):
        anthropic = _get_anthropic()
        if anthropic is None:
            raise ImportError("Please install the 'anthropic' package for Claude support.")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model_name = model_name

    @retry_on_error()
    def generate_completion(self, prompt, **kwargs):
        model = kwargs.get("model", self.model_name or "claude-3-opus-20240229")
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 2048)
        n = kwargs.get("n", 1)
        messages = kwargs.get("messages")
        if messages is not None:
            # Convert OpenAI-style messages to Anthropic format
            system_prompt = ""
            user_content = ""
            for m in messages:
                if m["role"] == "system":
                    system_prompt = m["content"]
                elif m["role"] == "user":
                    user_content += m["content"] + "\n"
            prompt = user_content.strip()
        else:
            system_prompt = ""
        completions = []
        for _ in range(n):
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}]
            )
            completions.append(response.content[0].text if hasattr(response.content[0], 'text') else response.content[0]["text"])
            print(completions[-1])
        return completions

class GeminiClient(AIClient):
    def __init__(self, api_key=None, model_name=None):
        genai = _get_genai()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google Gemini API key not found")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    @retry_on_error()
    @rate_limit(requests_per_minute=15)
    def generate_completion(self, prompt, **kwargs):
        genai = _get_genai()
        completions = []
        model = kwargs.get("model", self.model_name or "gemini-pro")
        for _ in range(kwargs.get("n", 1)):
            if messages := kwargs.get("messages"):
                # Convert messages to content format
                contents = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": msg["content"]}]})
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(
                        max_output_tokens=kwargs.get("max_tokens", 2048),
                        temperature=kwargs.get("temperature", 0.0),
                    )
                )
            else:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        max_output_tokens=kwargs.get("max_tokens", 2048),
                        temperature=kwargs.get("temperature", 0.0),
                    )
                )
            completions.append(response.text)
                
        return completions


class SGLangClient(AIClient):
    def __init__(self, model_name, sglang_addr):
        self.sglang_addr = sglang_addr
        self.model_name = model_name
        AutoTokenizer = _get_auto_tokenizer()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code = True)

    def generate_completion(self, prompt, **kwargs):
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 2048)
        n = kwargs.get("n", 1)
        enable_thinking = kwargs.get("enable_thinking", False)

        
        sampling_params = {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "n": n,
        }
        
        # Add optional sampling parameters if they differ from defaults
        has_thinking_mode = self.model_name in ['Qwen/Qwen3-8B', 'Qwen/Qwen3-4B', 'Qwen/Qwen3-14B', 'Qwen/Qwen3-32B']
        if 'messages' in kwargs:
            if has_thinking_mode:
                prompt = self.tokenizer.apply_chat_template(kwargs['messages'], tokenize=False, add_generation_prompt=True, enable_thinking=enable_thinking)
            else:
                prompt = self.tokenizer.apply_chat_template(kwargs['messages'], tokenize=False, add_generation_prompt=True)
        else:
            if has_thinking_mode:
                prompt = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True, enable_thinking=enable_thinking)
            else:
                prompt = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
        
        json_data = {
            "text": prompt,
            "sampling_params": sampling_params,
        }
        response = requests.post(
            f"{self.sglang_addr}/generate",
            json=json_data,
        )
        
        out = response.json()
        completions = []
        if n > 1:
            for i in range(n):
                llm_resp = out[i]['text']
                completions.append(llm_resp)
        else:
            completions.append(out['text'])
        return completions

    
class DeepSeekClient(AIClient):
    """DeepSeek API client using OpenAI-compatible endpoint."""

    DEFAULT_BASE_URL = "https://api.deepseek.com"

    def __init__(self, api_key=None, model_name=None):
        openai_mod = _get_openai()
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        self.model_name = model_name or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", self.DEFAULT_BASE_URL)
        self.client = openai_mod.OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.reasoning_mode = os.environ.get("DEEPSEEK_REASONING", None)
        if self.reasoning_mode is not None:
            self.reasoning_mode = self.reasoning_mode.lower()
        self.last_timing = {}
        logger.info(
            f"[DeepSeekClient] base_url={self.base_url} model={self.model_name}"
            f" reasoning_mode={self.reasoning_mode or 'api_default'}"
        )

    def _compute_prompt_hash(self, prompt_text):
        return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()[:16]

    def _single_call(self, model, messages, temperature, max_tokens, effective_reasoning, sample_idx, n_total):
        """Make one API call and return (resp_text, metadata)."""
        api_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        if effective_reasoning == "off":
            api_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        start_time = time.time()
        response = self.client.chat.completions.create(**api_kwargs)
        elapsed = time.time() - start_time

        msg = response.choices[0].message
        resp_text = msg.content or ""
        reasoning = (
            getattr(msg, 'reasoning_content', None)
            or getattr(msg, 'model_extra', {}).get('reasoning_content', '')
        )

        usage = getattr(response, 'usage', None)

        meta = {
            "sample_idx": sample_idx,
            "gen_time": elapsed,
            "content_len": len(resp_text),
            "has_reasoning": bool(reasoning),
            "prompt_tokens": getattr(usage, 'prompt_tokens', None) if usage else None,
            "completion_tokens": getattr(usage, 'completion_tokens', None) if usage else None,
            "total_tokens": getattr(usage, 'total_tokens', None) if usage else None,
            "cache_hit": getattr(usage, 'prompt_cache_hit_tokens', None) if usage else None,
            "cache_miss": getattr(usage, 'prompt_cache_miss_tokens', None) if usage else None,
        }

        logger.info(
            f"[DeepSeekResp] model={model}"
            f" reasoning={effective_reasoning or 'default'}"
            f" has_reasoning={bool(reasoning)}"
            f" content_len={len(resp_text)}"
            f" gen_time={elapsed:.2f}s"
            f" sample={sample_idx}/{n_total}"
            f" max_tokens_sent={max_tokens}"
            f" prompt_tokens={meta['prompt_tokens']}"
            f" completion_tokens={meta['completion_tokens']}"
            f" total_tokens={meta['total_tokens']}"
            f" cache_hit={meta['cache_hit']}"
            f" cache_miss={meta['cache_miss']}"
        )

        if not resp_text and reasoning:
            logger.info(
                f"[DeepSeekResp] content empty, using reasoning_content "
                f"len={len(reasoning)}"
            )
            resp_text = reasoning

        return resp_text, meta

    @retry_on_error()
    def generate_completion(self, prompt, **kwargs):
        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", None)
        n = kwargs.get("n", 1)
        messages = kwargs.get("messages")
        reasoning_override = kwargs.get("reasoning_mode", None)
        bon_schedule = kwargs.get("bon_schedule", "sequential")
        bon_parallelism = kwargs.get("bon_parallelism", 8)
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        effective_reasoning = reasoning_override or self.reasoning_mode

        prefix_text = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        prefix_hash = self._compute_prompt_hash(prefix_text)

        wall_start = time.time()
        per_sample_meta = []

        if n <= 1 or bon_schedule == "sequential":
            responses = []
            for sample_idx in range(n):
                resp_text, meta = self._single_call(
                    model, messages, temperature, max_tokens, effective_reasoning, sample_idx, n
                )
                responses.append(resp_text)
                per_sample_meta.append(meta)
                logger.info(
                    f"[DeepSeekCache] model={model}"
                    f" reasoning={effective_reasoning or 'default'}"
                    f" prompt_total_chars={len(prefix_text)}"
                    f" sample={sample_idx}/{n}"
                    f" prefix_sha256={prefix_hash}"
                )
        else:
            # one_prime_parallel: sample0 cold → parallel(sample1..sampleN-1)
            responses = [None] * n
            per_sample_meta = [None] * n

            # Phase 1: sequential cold call
            t0 = time.time()
            resp_text, meta0 = self._single_call(
                model, messages, temperature, max_tokens, effective_reasoning, 0, n
            )
            responses[0] = resp_text
            per_sample_meta[0] = meta0
            logger.info(
                f"[DeepSeekCache] model={model} sample=0/{n} "
                f"prime_cold gen_time={meta0['gen_time']:.2f}s prefix_sha256={prefix_hash}"
            )

            # Phase 2: parallel warm calls
            t_parallel_start = time.time()
            import concurrent.futures
            remaining = n - 1
            workers = min(remaining, bon_parallelism)
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {}
                for j in range(remaining):
                    sample_idx = 1 + j
                    futures[executor.submit(
                        self._single_call,
                        model, messages, temperature, max_tokens,
                        effective_reasoning, sample_idx, n
                    )] = sample_idx

                for future in concurrent.futures.as_completed(futures):
                    sample_idx = futures[future]
                    resp_text, meta = future.result()
                    responses[sample_idx] = resp_text
                    per_sample_meta[sample_idx] = meta
                    logger.info(
                        f"[DeepSeekCache] model={model} sample={sample_idx}/{n} "
                        f"parallel gen_time={meta['gen_time']:.2f}s prefix_sha256={prefix_hash}"
                    )

            t_parallel_end = time.time()

        wall_end = time.time()

        # compute timing aggregates
        gen_times = [m["gen_time"] for m in per_sample_meta if m]
        cache_hits = sum(m.get("cache_hit") or 0 for m in per_sample_meta if m)
        cache_misses = sum(m.get("cache_miss") or 0 for m in per_sample_meta if m)
        completion_tokens = sum(m.get("completion_tokens") or 0 for m in per_sample_meta if m)

        if n > 1 and bon_schedule != "sequential":
            t_gen_cold = gen_times[0] + max(gen_times[1:])
            t_gen_primed = max(gen_times[1:])
        else:
            t_gen_cold = sum(gen_times)
            t_gen_primed = 0.0 if n <= 1 else max(gen_times[1:])

        self.last_timing = {
            "n": n,
            "bon_schedule": bon_schedule,
            "gen_times": gen_times,
            "t_gen_cold": round(t_gen_cold, 3),
            "t_gen_primed": round(t_gen_primed, 3),
            "t_api_sum": round(sum(gen_times), 3),
            "wall_clock": round(wall_end - wall_start, 3),
            "cache_hit_tokens_total": cache_hits,
            "cache_miss_tokens_total": cache_misses,
            "completion_tokens_total": completion_tokens,
            "cache_hit_rate": round(cache_hits / (cache_hits + cache_misses), 4) if (cache_hits + cache_misses) > 0 else 0.0,
        }

        return responses

    
def get_client(client_type, api_key=None, model_name=None, sglang_addr=None, reasoning_mode=None):
    client_type = client_type.lower()
    if client_type == "openai":
        return OpenAIClient(api_key, model_name)
    elif client_type == "together":
        return TogetherClient(api_key, model_name)
    elif client_type in ["claude", "anthropic"]:
        return ClaudeClient(api_key, model_name)
    elif client_type == "gemini":
        return GeminiClient(api_key, model_name)
    elif client_type == "sglang":
        return SGLangClient(model_name, sglang_addr)
    elif client_type == "deepseek":
        return DeepSeekClient(api_key, model_name)
    else:
        raise ValueError(f"Unsupported client type: {client_type}") 