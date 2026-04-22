from runpod_flash import Endpoint
from common.runpod import (
    RUNPOD_DATACENTER,
    RUNPOD_GPU,
    get_runpod_volume,
)


@Endpoint(
    name="exaone-main",
    gpu=RUNPOD_GPU,
    datacenter=RUNPOD_DATACENTER,
    volume=get_runpod_volume(),
    execution_timeout_ms=600000,
    workers=(0, 1),
    dependencies=["transformers"],
)
async def exaone_main_infer(data: dict) -> dict:
    import os
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    try:
        model_path = "/runpod-volume/exaone-3.5-7.8b"

        if not os.path.exists(model_path):
            return {"ok": False, "error": "model path not found"}

        global_state = globals()
        tokenizer = global_state.get("_tokenizer")
        model = global_state.get("_model")

        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True,
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
            ).to("cuda")
            model.eval()
            global_state["_model"] = model

        messages = data["input"]["messages"]
        temperature = float(data["input"].get("temperature", 0.0))
        max_new_tokens = int(data["input"].get("max_new_tokens", 8192))
        do_sample = temperature > 0.0

        full_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        inputs = tokenizer(full_prompt, return_tensors="pt").to("cuda")

        generate_kwargs = {
            **inputs,
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }

        if do_sample:
            generate_kwargs["temperature"] = temperature

        with torch.no_grad():
            output = model.generate(**generate_kwargs)

        prompt_length = inputs["input_ids"].shape[1]
        generated_tokens = output[0][prompt_length:]
        text = tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return {"ok": True, "text": text}

    except Exception as e:
        return {"ok": False, "error": str(e)}
