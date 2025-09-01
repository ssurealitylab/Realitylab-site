#!/usr/bin/env python3
"""
Qwen2.5-3B Fine-tuning on Reality Lab Dataset
Uses LoRA (Low-Rank Adaptation) for efficient training
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
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QwenFineTuner:
    def __init__(self):
        self.model_name = "Qwen/Qwen2.5-3B-Instruct"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 512
        
        # LoRA Configuration for efficient fine-tuning
        self.lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=16,  # Low rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        )
        
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
    def load_dataset(self, dataset_path="reality_lab_dataset/chatML_format.json"):
        """Load and prepare the Reality Lab dataset"""
        logger.info(f"Loading dataset from {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to training format
        formatted_data = []
        for item in data:
            messages = item["messages"]
            
            # Create a conversational prompt
            conversation = ""
            for msg in messages:
                if msg["role"] == "system":
                    conversation += f"<|im_start|>system\n{msg['content']}<|im_end|>\n"
                elif msg["role"] == "user":
                    conversation += f"<|im_start|>user\n{msg['content']}<|im_end|>\n"
                elif msg["role"] == "assistant":
                    conversation += f"<|im_start|>assistant\n{msg['content']}<|im_end|>"
            
            formatted_data.append({
                "text": conversation
            })
        
        logger.info(f"Loaded {len(formatted_data)} training examples")
        return Dataset.from_list(formatted_data)
    
    def load_model_and_tokenizer(self):
        """Load Qwen2.5-3B model and tokenizer"""
        logger.info(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Set special tokens
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model with 4-bit quantization for memory efficiency
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            load_in_4bit=True,  # 4-bit quantization
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Apply LoRA
        self.model = get_peft_model(self.model, self.lora_config)
        self.model.print_trainable_parameters()
        
        logger.info("Model and tokenizer loaded successfully!")
        
    def tokenize_function(self, examples):
        """Tokenize the dataset"""
        # Tokenize inputs
        model_inputs = self.tokenizer(
            examples["text"],
            max_length=self.max_length,
            truncation=True,
            padding=False
        )
        
        # For causal LM, labels are the same as input_ids
        model_inputs["labels"] = model_inputs["input_ids"].copy()
        
        return model_inputs
    
    def train(self, dataset, output_dir="./qwen_reality_lab_lora"):
        """Fine-tune the model"""
        logger.info("Starting fine-tuning...")
        
        # Tokenize dataset
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Split into train/eval
        train_test = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
        train_dataset = train_test["train"]
        eval_dataset = train_test["test"]
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=2,  # Small batch size for memory
            per_device_eval_batch_size=2,
            gradient_accumulation_steps=4,  # Effective batch size = 2*4 = 8
            learning_rate=5e-5,
            weight_decay=0.01,
            warmup_steps=10,
            logging_steps=5,
            eval_steps=50,
            save_steps=50,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb logging
            dataloader_num_workers=0,
            fp16=True,  # Mixed precision training
            gradient_checkpointing=True,  # Memory optimization
            remove_unused_columns=False,
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True,
            max_length=self.max_length
        )
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
        )
        
        # Start training
        logger.info("Beginning training process...")
        self.trainer.train()
        
        # Save the final model
        self.trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Training completed! Model saved to {output_dir}")
        
    def test_model(self, test_prompts=None):
        """Test the fine-tuned model"""
        if test_prompts is None:
            test_prompts = [
                "Reality Lab에 대해 설명해주세요.",
                "Reality Lab의 구성원은 누구인가요?",
                "Reality Lab에서 발표한 논문을 알려주세요.",
                "연락처를 알려주세요."
            ]
        
        logger.info("Testing fine-tuned model...")
        self.model.eval()
        
        for prompt in test_prompts:
            # Format prompt
            formatted_prompt = f"<|im_start|>system\n당신은 숭실대학교 Reality Lab에 대한 전문 지식을 가진 도움이 되는 어시스턴트입니다.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            # Tokenize
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            print(f"\n🔥 질문: {prompt}")
            print(f"📝 답변: {response}")
            print("-" * 50)

def main():
    """Main training function"""
    print("🚀 Reality Lab Qwen2.5-3B Fine-tuning 시작!")
    
    # Check GPU availability
    if torch.cuda.is_available():
        print(f"✅ GPU 사용: {torch.cuda.get_device_name(0)}")
        print(f"💾 GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("⚠️ CPU 모드로 실행 (매우 느림)")
    
    # Initialize trainer
    trainer = QwenFineTuner()
    
    # Load dataset
    dataset = trainer.load_dataset()
    
    # Load model
    trainer.load_model_and_tokenizer()
    
    # Start training
    trainer.train(dataset)
    
    # Test the model
    trainer.test_model()
    
    print("🎉 파인튜닝 완료! Reality Lab 전용 AI 모델이 준비되었습니다!")

if __name__ == "__main__":
    main()