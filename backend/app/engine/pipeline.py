"""
PriceWise AI Engine - Training Pipeline
Generates synthetic training data and fine-tunes models
"""

import json
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class TrainingExample:
    """Single training example for requirement parsing"""
    input_query: str
    expected_output: Dict
    category: str
    difficulty: str  # easy, medium, hard

class SyntheticDataGenerator:
    """
    Generates synthetic training data for the AI engine.
    No real user data needed - creates realistic shopping scenarios.
    """

    CATEGORIES = ["smartphone", "laptop", "headphones", "tablet", "smartwatch", "camera", "tv"]

    BRANDS = {
        "smartphone": ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Nothing", "Google", "Motorola"],
        "laptop": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI"],
        "headphones": ["Sony", "Bose", "JBL", "Sennheiser", "Apple", "Samsung"]
    }

    PRIORITIES = ["camera", "battery", "performance", "display", "value", "build quality"]

    USE_CASES = ["gaming", "photography", "work", "streaming", "social media", "travel", "student"]

    MUST_HAVES = ["5G", "wireless charging", "water resistance", "AMOLED", "fast charging", 
                  "headphone jack", "expandable storage", "dual SIM"]

    BUDGET_RANGES = {
        "smartphone": [(5000, 15000), (15000, 30000), (30000, 50000), (50000, 80000), (80000, 150000)],
        "laptop": [(20000, 40000), (40000, 70000), (70000, 100000), (100000, 150000)],
        "headphones": [(1000, 3000), (3000, 8000), (8000, 15000), (15000, 40000)]
    }

    TEMPLATES = {
        "simple": [
            "I need a {category} under {budget}",
            "Best {category} for {use_case} under {budget}",
            "{category} with good {priority} under {budget}",
            "Looking for {category}, budget {budget}",
        ],
        "detailed": [
            "I want a {category} with great {priority} and {priority2} for {use_case}. Budget is {budget}. Prefer {brand} but avoid {avoid_brand}.",
            "Need {category} under {budget}. Must have {must_have} and {must_have2}. Using for {use_case}. {priority} is most important.",
            "Looking for {category} around {budget}. Want {brand} or {brand2}. Need {must_have}. Will use for {use_case} and {use_case2}.",
            "Best {category} for {use_case} under {budget}? Want good {priority} and {priority2}. Not {avoid_brand}. Urgent need.",
        ],
        "conversational": [
            "Hey, I'm shopping for a {category}. My budget is around {budget}. I mainly use it for {use_case}. What do you recommend?",
            "Help me find a {category}. I had a {avoid_brand} before and hated it. Want something with good {priority} this time. Budget {budget}.",
            "My {category} broke. Need replacement ASAP. Budget {budget}. Must have {must_have}. What should I buy?",
            "Thinking of getting a {category} for {use_case}. Budget is {budget}. Is {brand} good or should I look at {brand2}?",
        ],
        "ambiguous": [
            "Something good under {budget}",
            "Best phone for me?",
            "What should I buy?",
            "Need a new gadget",
            "Recommend something good",
        ]
    }

    def generate_examples(self, count: int = 1000) -> List[TrainingExample]:
        """Generate synthetic training examples"""
        examples = []

        for _ in range(count):
            category = random.choice(self.CATEGORIES)
            difficulty = random.choice(["easy", "medium", "hard", "conversational", "ambiguous"])

            if difficulty == "ambiguous":
                template = random.choice(self.TEMPLATES["ambiguous"])
                budget_range = random.choice(self.BUDGET_RANGES.get(category, [(1000, 50000)]))
                budget = random.randint(budget_range[0], budget_range[1])

                query = template.format(budget=budget)
                expected = {
                    "category": "unknown",
                    "budget_max": budget,
                    "confidence": 0.3
                }
            else:
                template_pool = self.TEMPLATES.get(difficulty, self.TEMPLATES["simple"])
                template = random.choice(template_pool)

                budget_range = random.choice(self.BUDGET_RANGES.get(category, [(1000, 50000)]))
                budget = random.randint(budget_range[0], budget_range[1])
                priority = random.choice(self.PRIORITIES)
                priority2 = random.choice([p for p in self.PRIORITIES if p != priority])
                use_case = random.choice(self.USE_CASES)
                use_case2 = random.choice([u for u in self.USE_CASES if u != use_case])
                brand = random.choice(self.BRANDS.get(category, ["Unknown"]))
                brand2 = random.choice([b for b in self.BRANDS.get(category, ["Unknown"]) if b != brand])
                avoid_brand = random.choice([b for b in self.BRANDS.get(category, ["Unknown"]) if b != brand])
                must_have = random.choice(self.MUST_HAVES)
                must_have2 = random.choice([m for m in self.MUST_HAVES if m != must_have])

                query = template.format(
                    category=category,
                    budget=budget,
                    priority=priority,
                    priority2=priority2,
                    use_case=use_case,
                    use_case2=use_case2,
                    brand=brand,
                    brand2=brand2,
                    avoid_brand=avoid_brand,
                    must_have=must_have,
                    must_have2=must_have2
                )

                expected = {
                    "category": category,
                    "budget_max": budget,
                    "priorities": [priority, priority2],
                    "use_cases": [use_case] if "use_case2" not in template else [use_case, use_case2],
                    "must_haves": [must_have] if "must_have2" not in template else [must_have, must_have2],
                    "preferred_brands": [brand] if "brand2" not in template else [brand, brand2],
                    "avoided_brands": [avoid_brand] if "avoid_brand" in template else [],
                    "confidence": 0.9 if difficulty in ["simple", "detailed"] else 0.7
                }

            examples.append(TrainingExample(
                input_query=query,
                expected_output=expected,
                category=category,
                difficulty=difficulty
            ))

        return examples

    def generate_verdict_training_data(self, count: int = 500) -> List[Dict]:
        """Generate training data for verdict generation"""
        data = []

        verdicts = ["BUY", "WAIT", "DONT_BUY", "COMPARE"]

        for _ in range(count):
            match_score = random.uniform(30, 98)
            budget_score = random.uniform(0.3, 1.0)
            priority_score = random.uniform(0.3, 1.0)
            must_have_score = random.uniform(0, 1.0)

            # Determine verdict based on scores
            if match_score >= 85 and budget_score >= 0.8:
                verdict = "BUY"
            elif match_score >= 70:
                verdict = "COMPARE"
            elif match_score >= 50:
                verdict = "WAIT"
            else:
                verdict = "DONT_BUY"

            # Add some noise
            if random.random() < 0.1:
                verdict = random.choice(verdicts)

            data.append({
                "match_score": round(match_score, 1),
                "budget_score": round(budget_score, 2),
                "priority_score": round(priority_score, 2),
                "must_have_score": round(must_have_score, 2),
                "verdict": verdict,
                "reasoning": self._generate_reasoning(verdict, match_score, budget_score, priority_score)
            })

        return data

    def _generate_reasoning(self, verdict: str, match_score: float, budget_score: float, 
                           priority_score: float) -> List[str]:
        """Generate reasoning for verdict training"""
        reasoning = []

        if verdict == "BUY":
            reasoning.append(f"Excellent match score of {match_score}%")
            if budget_score >= 0.9:
                reasoning.append("Well within budget")
            if priority_score >= 0.9:
                reasoning.append("Priority requirements fully met")
        elif verdict == "WAIT":
            reasoning.append(f"Moderate match score of {match_score}%")
            if budget_score < 0.8:
                reasoning.append("Slightly over budget")
            reasoning.append("Better deals expected in upcoming sales")
        elif verdict == "DONT_BUY":
            reasoning.append(f"Poor match score of {match_score}%")
            if priority_score < 0.5:
                reasoning.append("Priority requirements not met")
            reasoning.append("Better alternatives available")
        else:
            reasoning.append(f"Good match score of {match_score}%")
            reasoning.append("Worth comparing with alternatives")

        return reasoning

    def generate_price_history_training_data(self, count: int = 300) -> List[Dict]:
        """Generate training data for fake discount detection"""
        data = []

        for _ in range(count):
            is_fake = random.random() < 0.3  # 30% fake

            base_price = random.randint(10000, 150000)

            if is_fake:
                # Fake discount: inflated MRP
                mrp = int(base_price * random.uniform(1.3, 1.8))
                current_price = int(base_price * random.uniform(0.9, 1.1))
                discount = round((1 - current_price / mrp) * 100, 1)
            else:
                # Real discount
                mrp = int(base_price * random.uniform(1.1, 1.3))
                current_price = int(base_price * random.uniform(0.7, 0.95))
                discount = round((1 - current_price / mrp) * 100, 1)

            data.append({
                "mrp": mrp,
                "current_price": current_price,
                "discount_percent": discount,
                "is_fake": is_fake,
                "true_discount": round((1 - current_price / base_price) * 100, 1) if base_price > 0 else 0
            })

        return data

    def generate_review_training_data(self, count: int = 500) -> List[Dict]:
        """Generate training data for fake review detection"""
        data = []

        fake_phrases = [
            "Good product. Value for money. Must buy.",
            "Excellent product. Highly recommended. Great quality.",
            "Nice product. Worth buying. Go for it.",
            "Awesome product. Best in class. Fully satisfied.",
            "Great product. Amazing quality. Totally worth it."
        ]

        real_phrases = [
            "Camera is good in daylight but struggles in low light. Battery lasts about 6-7 hours with heavy use.",
            "I have been using this for 3 months. The display is crisp but the phone heats up during gaming. Camera is decent.",
            "Bought this for my photography work. The 48MP sensor captures good detail but the portrait mode is hit or miss.",
            "Good laptop for programming. The keyboard is comfortable for long coding sessions. Battery gives 8 hours.",
            "After 2 weeks of use, I can say the build quality is solid. However, the charging speed is slower than advertised."
        ]

        for _ in range(count):
            is_fake = random.random() < 0.4  # 40% fake

            if is_fake:
                text = random.choice(fake_phrases)
                length = len(text)
                has_specific = False
                generic_ratio = random.uniform(0.6, 1.0)
            else:
                text = random.choice(real_phrases)
                length = len(text)
                has_specific = True
                generic_ratio = random.uniform(0.0, 0.4)

            data.append({
                "text": text,
                "length": length,
                "has_specific_details": has_specific,
                "generic_phrase_ratio": round(generic_ratio, 2),
                "is_fake": is_fake
            })

        return data

    def save_to_files(self, output_dir: str = "training_data"):
        """Save all generated data to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Requirement parsing data
        req_examples = self.generate_examples(1000)
        with open(f"{output_dir}/requirement_parsing.jsonl", "w") as f:
            for ex in req_examples:
                f.write(json.dumps({
                    "input": ex.input_query,
                    "output": ex.expected_output,
                    "category": ex.category,
                    "difficulty": ex.difficulty
                }) + "\n")

        # Verdict generation data
        verdict_data = self.generate_verdict_training_data(500)
        with open(f"{output_dir}/verdict_generation.json", "w") as f:
            json.dump(verdict_data, f, indent=2)

        # Price intelligence data
        price_data = self.generate_price_history_training_data(300)
        with open(f"{output_dir}/price_intelligence.json", "w") as f:
            json.dump(price_data, f, indent=2)

        # Review trust data
        review_data = self.generate_review_training_data(500)
        with open(f"{output_dir}/review_trust.jsonl", "w") as f:
            for item in review_data:
                f.write(json.dumps(item) + "\n")

        print(f"Training data saved to {output_dir}/")
        print(f"  - requirement_parsing.jsonl: {len(req_examples)} examples")
        print(f"  - verdict_generation.json: {len(verdict_data)} examples")
        print(f"  - price_intelligence.json: {len(price_data)} examples")
        print(f"  - review_trust.jsonl: {len(review_data)} examples")


class ModelTrainer:
    """
    Training pipeline for fine-tuning models.
    Uses LoRA for efficient fine-tuning of open-source LLMs.
    """

    def __init__(self, base_model: str = "meta-llama/Llama-3.1-8B"):
        self.base_model = base_model
        self.output_dir = "models/pricewise-finetuned"

    def prepare_training_data(self, data_file: str, output_file: str):
        """Convert training data to instruction format"""
        import json

        instructions = []

        with open(data_file, "r") as f:
            for line in f:
                data = json.loads(line)

                instruction = {
                    "instruction": "Parse this shopping query into structured requirements.",
                    "input": data["input"],
                    "output": json.dumps(data["output"])
                }
                instructions.append(instruction)

        with open(output_file, "w") as f:
            for inst in instructions:
                f.write(json.dumps(inst) + "\n")

        print(f"Prepared {len(instructions)} training examples")

    def train_lora(self, train_file: str, epochs: int = 3, batch_size: int = 4):
        """
        Fine-tune model using LoRA (Low-Rank Adaptation).
        Requires minimal GPU memory.
        """
        # This is a template - actual training requires transformers, peft, trl
        training_script = f"""
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
import torch

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "{self.base_model}",
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("{self.base_model}")

# Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Training arguments
args = TrainingArguments(
    output_dir="{self.output_dir}",
    num_train_epochs={epochs},
    per_device_train_batch_size={batch_size},
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True
)

# Train
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    args=args
)

trainer.train()
model.save_pretrained("{self.output_dir}")
"""

        with open("train_lora.py", "w") as f:
            f.write(training_script)

        print(f"Training script saved to train_lora.py")
        print(f"Run: python train_lora.py")

    def evaluate_model(self, test_file: str):
        """Evaluate model on test set"""
        # Template for evaluation
        print("Evaluation script template generated")
        print("Metrics: accuracy, precision, recall, F1 for each component")


# Example usage
if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    generator.save_to_files("training_data")

    trainer = ModelTrainer()
    trainer.prepare_training_data("training_data/requirement_parsing.jsonl", 
                                   "training_data/instruction_format.jsonl")
