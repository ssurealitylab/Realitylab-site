#!/usr/bin/env python3
"""
Simple Qwen2.5-3B Fine-tuning on Reality Lab Dataset
Minimal dependencies version
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
    DataCollatorForLanguageModeling
)
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_reality_lab_dataset():
    """Load Reality Lab dataset"""
    dataset_path = "reality_lab_dataset/instruction_dataset.json"
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Format for training
    formatted_data = []
    for item in data:
        # Create instruction-following format
        text = f"### 질문: {item['instruction']}\n### 답변: {item['output']}"
        formatted_data.append({"text": text})
    
    logger.info(f"Loaded {len(formatted_data)} training examples")
    return Dataset.from_list(formatted_data)

def main():
    """Simple fine-tuning main function"""
    print("🚀 Reality Lab Simple Fine-tuning 시작!")
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    output_dir = "./reality_lab_qwen"
    
    # Load tokenizer
    print("📝 토크나이저 로딩...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right"
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model with 8-bit quantization
    print("🤖 모델 로딩... (8-bit quantization)")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        load_in_8bit=True  # Use 8-bit quantization to save memory
    )
    
    # Load dataset
    print("📊 데이터셋 준비...")
    dataset = load_reality_lab_dataset()
    
    # Tokenization function
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=512
        )
    
    # Tokenize dataset
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Training arguments (very light settings)
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=1,  # Just 1 epoch for quick test
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=5e-6,  # Very low learning rate
        logging_steps=5,
        save_steps=50,
        save_strategy="steps",
        report_to=None,
        dataloader_num_workers=0,
        fp16=False,  # Disable FP16 to avoid gradient scaling issues
        remove_unused_columns=False,
        warmup_steps=5,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Initialize trainer
    print("⚙️ 트레이너 설정...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    # Start training
    print("🔥 파인튜닝 시작!")
    trainer.train()
    
    # Save model
    print("💾 모델 저장...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    print("🎉 파인튜닝 완료!")
    
    # Quick test
    print("\n🧪 모델 테스트:")
    model.eval()
    
    test_prompt = "### 질문: Reality Lab에 대해 설명해주세요.\n### 답변: "
    inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    print(f"📝 AI 답변: {response}")

if __name__ == "__main__":
    main()