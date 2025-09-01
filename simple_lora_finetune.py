#!/usr/bin/env python3
"""
Ultra Simple Qwen2.5-3B LoRA Fine-tuning
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Ultra Simple Reality Lab LoRA Fine-tuning!")
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    output_dir = "./reality_lab_qwen_lora"
    
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
    print("🤖 Loading model with 4-bit quantization...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    # LoRA configuration - very simple
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.1,
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
    
    # Simple format for training
    formatted_data = []
    for item in data[:10]:  # Use only 10 examples for quick test
        text = f"질문: {item['instruction']}\n답변: {item['output']}<|endoftext|>"
        formatted_data.append({"text": text})
    
    dataset = Dataset.from_list(formatted_data)
    print(f"📈 Loaded {len(dataset)} training examples")
    
    # Tokenization
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=256,  # Short sequences
        )
    
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Training arguments - minimal settings
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        logging_steps=1,
        save_steps=10,
        report_to=None,
        remove_unused_columns=False,
        dataloader_num_workers=0,
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
    print("🔥 Starting LoRA fine-tuning...")
    trainer.train()
    
    # Save
    print("💾 Saving LoRA model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Quick test
    print("\n🧪 Quick test:")
    model.eval()
    test_prompt = "질문: Reality Lab에 대해 설명해주세요.\n답변: "
    inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    print(f"📝 Response: {response}")
    
    print("🎉 LoRA fine-tuning completed!")

if __name__ == "__main__":
    main()