from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Choose model size: "gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"
model_name = "gpt2"

print(f"Downloading {model_name}...")

# Load tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Save locally
save_path = "./gpt2_local"
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print(f"✅ Model saved locally at {save_path}")
