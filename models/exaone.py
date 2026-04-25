from typing import Any

from runpod_flash import Endpoint
from schemas.exaone_schemas import ExaoneRequest, ExaoneResponse
from common.runpod import (
    RUNPOD_GPU,
    RUNPOD_DATACENTER,
    get_runpod_volume,
)


@Endpoint(
    name="exaone",
    gpu=RUNPOD_GPU,
    datacenter=RUNPOD_DATACENTER,
    volume=get_runpod_volume(),
    execution_timeout_ms=0,
    workers=(0, 1),
    idle_timeout=300,
)
async def exaone_infer(input: dict = None, **kwargs) -> ExaoneResponse:
    # Handle both direct call and RunPod handler unpacking
    if input is None:
        input = {}

    # Merge all kwargs into input dict
    input.update(kwargs)

    if not input:
        return {"ok": False, "error": "input is required"}

    data: ExaoneRequest = {"input": input}

    # DEBUG: 요청 데이터 확인
    import json
    print(f"DEBUG: Received data = {json.dumps(data, indent=2, ensure_ascii=False)}")

    import gc
    import os

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from typing import Dict

    inputs: Dict[str, Any] | None = None
    output: torch.Tensor | None = None

    try:
        model_path = "/runpod-volume/exaone-3.5-7.8b"

        if not os.path.exists(model_path):
            return {"ok": False, "error": "model path not found"}

        input_data = data["input"]
        messages = input_data.get("messages")

        # DEBUG: messages 확인
        print(f"DEBUG: messages = {messages}")

        if not messages:
            return {"ok": False, "error": "messages is required"}

        temperature = float(input_data.get("temperature", 0.7))
        do_sample = temperature > 0.0
        total_max_new_tokens = int(input_data.get("max_new_tokens", 8192))

        global_state = globals()
        tokenizer = global_state.get("_tokenizer")
        model = global_state.get("_model")

        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True,
                use_fast=False,
            )
            if tokenizer.pad_token_id is None:
                tokenizer.pad_token_id = tokenizer.eos_token_id
            global_state["_tokenizer"] = tokenizer

        if model is None:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                local_files_only=True,
                device_map="auto",
            )
            model.eval()
            global_state["_model"] = model

        full_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        chunk_size = 512
        prompt_max_length = 4096

        generated_text = ""
        total_generated = 0
        current_prompt = full_prompt

        while total_generated < total_max_new_tokens:
            current_chunk = min(chunk_size, total_max_new_tokens - total_generated)

            inputs = tokenizer(
                current_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=prompt_max_length,
            )

            inputs = {
                k: v.to(model.device if hasattr(model, "device") else "cuda")
                for k, v in inputs.items()
            }

            generate_kwargs: Dict[str, Any] = {
                **inputs,
                "max_new_tokens": current_chunk,
                "do_sample": do_sample,
                "pad_token_id": tokenizer.pad_token_id,
                "eos_token_id": tokenizer.eos_token_id,
                "use_cache": False,
            }

            if do_sample:
                generate_kwargs["temperature"] = temperature

            with torch.inference_mode():
                output = model.generate(**generate_kwargs)

            prompt_length = inputs["input_ids"].shape[1]
            new_tokens = output[0][prompt_length:].detach().cpu()

            if new_tokens.numel() == 0:
                del new_tokens
                del inputs
                del output
                inputs = None
                output = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                break

            new_text = tokenizer.decode(new_tokens, skip_special_tokens=True)

            if not new_text.strip():
                del new_tokens
                del inputs
                del output
                inputs = None
                output = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                break

            generated_text += new_text
            total_generated += len(new_tokens)
            current_prompt = full_prompt + generated_text

            del new_tokens
            del inputs
            del output
            inputs = None
            output = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        return {"ok": True, "text": generated_text}

    except Exception as e:
        return {"ok": False, "error": str(e)}

    finally:
        try:
            del inputs
        except Exception:
            pass
        try:
            del output
        except Exception:
            pass
        try:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass