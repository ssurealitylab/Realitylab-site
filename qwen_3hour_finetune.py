#!/usr/bin/env python3
"""
Qwen2.5-3B 3-Hour Extended Fine-tuning for Reality Lab
"""

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Reality Lab Qwen2.5-3B Extended Fine-tuning (3 Hours)")
    start_time = time.time()
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    output_dir = "./reality_lab_qwen_3hour"
    
    # Load tokenizer
    print("📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # BitsAndBytes config for 4-bit loading
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load model with 4-bit quantization
    print("🤖 Loading Qwen2.5-3B model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    # Enhanced LoRA configuration for longer training
    lora_config = LoraConfig(
        r=16,  # Higher rank for better learning
        lora_alpha=32,  # Higher alpha
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # More modules
        lora_dropout=0.05,  # Lower dropout for stability
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load Reality Lab dataset
    print("📊 Loading Reality Lab dataset...")
    with open('reality_lab_dataset/instruction_dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Use full dataset and create expanded training data
    formatted_data = []
    
    # Original data
    for item in data:
        text = f"<|im_start|>system\n당신은 Reality Lab 전문 어시스턴트입니다.<|im_end|>\n<|im_start|>user\n{item['instruction']}<|im_end|>\n<|im_start|>assistant\n{item['output']}<|im_end|>"
        formatted_data.append({"text": text})
    
    # Add variations for better learning
    base_info = {
        "name": "Reality Lab",
        "established": "2023년 숭실대학교",
        "director": "김희원 교수님",
        "mission": "Advancing AI to Understand Reality - 현실을 이해하는 AI 발전",
        "research_areas": "로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어",
        "contact": "+82-2-820-0679",
        "address": "서울특별시 동작구 사당로 105, 숭실대학교"
    }
    
    # Generate additional variations
    variations = [
        ("Reality Lab은 언제 설립되었나요?", f"{base_info['name']}은 {base_info['established']}에 설립되었습니다."),
        ("연구실 연락처가 어떻게 되나요?", f"Reality Lab의 연락처는 {base_info['contact']}입니다."),
        ("Reality Lab의 연구 목표는 무엇인가요?", f"Reality Lab의 연구 목표는 '{base_info['mission']}'입니다."),
        ("어떤 연구 분야를 다루나요?", f"Reality Lab에서는 {base_info['research_areas']} 분야를 연구합니다."),
        ("Reality Lab은 어디에 위치해 있나요?", f"Reality Lab은 {base_info['address']}에 위치해 있습니다."),
    ]
    
    for question, answer in variations:
        text = f"<|im_start|>system\n당신은 Reality Lab 전문 어시스턴트입니다.<|im_end|>\n<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n{answer}<|im_end|>"
        formatted_data.append({"text": text})
    
    dataset = Dataset.from_list(formatted_data)
    print(f"📈 Loaded {len(dataset)} training examples")
    
    # Tokenization with longer sequences
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=512,  # Longer sequences for better context
        )
    
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Calculate training steps for ~3 hours
    total_samples = len(tokenized_dataset)
    batch_size = 2
    gradient_accumulation = 4
    effective_batch_size = batch_size * gradient_accumulation
    
    # Estimate steps for 3 hours (assuming ~2 seconds per step)
    target_hours = 3
    estimated_steps_per_hour = 1800  # Conservative estimate
    max_steps = int(target_hours * estimated_steps_per_hour)
    
    epochs_needed = max(1, max_steps * effective_batch_size // total_samples)
    
    print(f"📊 Training plan:")
    print(f"   - Total samples: {total_samples}")
    print(f"   - Effective batch size: {effective_batch_size}")
    print(f"   - Estimated epochs: {epochs_needed}")
    print(f"   - Target training time: {target_hours} hours")
    
    # Training arguments for extended training
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=epochs_needed,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        learning_rate=1e-4,  # Lower learning rate for stability
        weight_decay=0.01,
        warmup_steps=100,
        logging_steps=50,
        save_steps=500,
        save_total_limit=3,
        eval_strategy="no",
        fp16=True,  # Mixed precision for efficiency
        dataloader_num_workers=2,
        remove_unused_columns=False,
        report_to=None,
        load_best_model_at_end=False,
        max_steps=max_steps,  # Limit total steps
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    # Train
    print("🔥 Starting extended LoRA fine-tuning...")
    print(f"⏰ Training started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    trainer.train()
    
    # Save final model
    print("💾 Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Calculate training time
    end_time = time.time()
    training_hours = (end_time - start_time) / 3600
    
    print(f"\n🎉 Extended fine-tuning completed!")
    print(f"⏱️ Total training time: {training_hours:.2f} hours")
    
    # Final test
    print("\n🧪 Final test:")
    model.eval()
    test_prompts = [
        "Reality Lab에 대해 설명해주세요.",
        "연구실의 주요 연구 분야는 무엇인가요?",
        "Reality Lab에 연락하려면 어떻게 해야 하나요?"
    ]
    
    for prompt in test_prompts:
        test_input = f"<|im_start|>system\n당신은 Reality Lab 전문 어시스턴트입니다.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        inputs = tokenizer(test_input, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(f"Q: {prompt}")
        print(f"A: {response.strip()}")
        print("-" * 50)

if __name__ == "__main__":
    main()