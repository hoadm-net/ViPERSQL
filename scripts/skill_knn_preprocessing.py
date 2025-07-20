#!/usr/bin/env python3
"""
SQL Skills KNN Preprocessing Script

This script preprocesses the std-level/train.json dataset to extract SQL skills
using LLM analysis and creates embeddings using BERT, then saves the results
to std-level/skill_knn_train.json.

Steps:
1. Read training data
2. Use GPT-4o-mini to analyze SQL queries and extract skills
3. Use google-bert/bert-base-uncased to create embeddings for the skills
4. Save results with db_id, question, skills, skills_embedding, and query fields
"""

import json
import os
import sys
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import time
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModel

# Add the parent directory to the Python path to import mint modules
sys.path.append(str(Path(__file__).parent.parent))

from mint.config import ViPERConfig
from mint.llm_interface import LLMInterface


class BERTEmbedder:
    """BERT embedding generator using google-bert/bert-base-uncased."""

    def __init__(self, model_name: str = "google-bert/bert-base-uncased"):
        """Initialize BERT model and tokenizer."""
        print(f"Loading BERT model: {model_name}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()  # Set to evaluation mode

    def encode(self, text: str) -> List[float]:
        """Generate embedding for input text."""
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = outputs.last_hidden_state.mean(dim=1)

            # Convert to list and move to CPU
            return embeddings.cpu().numpy().flatten().tolist()

        except Exception as e:
            print(f"Error generating embedding for text '{text}': {e}")
            # Return zero vector as fallback
            return [0.0] * 768  # BERT base has 768 dimensions


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Preprocess training data to extract SQL skills using LLM analysis"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=None,
        help="Number of samples to process (default: all samples). Use small numbers for testing."
    )
    parser.add_argument(
        "--output_suffix",
        type=str,
        default="",
        help="Suffix to add to output filename for testing (e.g., '_test' -> skill_knn_train_test.json)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API calls in seconds (default: 1.0)"
    )

    return parser.parse_args()

def load_training_data(dataset_path: str, num_samples: int = None) -> List[Dict[str, Any]]:
    """Load training data from JSON file."""
    train_file = Path(dataset_path) / "ViText2SQL" / "std-level" / "train.json"

    if not train_file.exists():
        raise FileNotFoundError(f"Training file not found: {train_file}")

    with open(train_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Limit samples if specified
    if num_samples is not None:
        data = data[:num_samples]
        print(f"Limited to {num_samples} samples for testing")

    print(f"Loaded {len(data)} training samples")
    return data


def extract_skills_from_query(
    question: str,
    query: str,
    llm_interface: LLMInterface,
    template_path: Path
) -> str:
    """Extract SQL skills from a query using LLM analysis."""

    # Load the skill extraction template directly
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Format the prompt
    prompt = template_content.format(
        question=question,
        query=query
    )

    try:
        # Generate skills using the LLM
        response = llm_interface.generate(
            prompt=prompt,
            model="gpt-4.1-nano",
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=200    # Skills should be short
        )

        # Clean up the response (remove extra whitespace, newlines)
        skills = response.strip().replace('\n', ' ').replace('  ', ' ')
        return skills

    except Exception as e:
        print(f"Error extracting skills: {e}")
        return ""


def process_training_data(
    data: List[Dict[str, Any]],
    llm_interface: LLMInterface,
    template_path: Path,
    delay: float = 1.0
) -> List[Dict[str, Any]]:
    """Process training data to extract skills."""

    processed_data = []

    # Process samples with progress bar
    for i in tqdm(range(0, len(data)), desc="Processing samples"):
        item = data[i]

        db_id = item["db_id"]
        question = item["question"]
        query = item["query"]

        # Extract skills using LLM
        skills = extract_skills_from_query(
            question=question,
            query=query,
            llm_interface=llm_interface,
            template_path=template_path
        )

        # Create processed item
        processed_item = {
            "db_id": db_id,
            "question": question,
            "skills": skills,
            "query": query
        }

        processed_data.append(processed_item)

        # Add delay between samples to respect API limits
        time.sleep(delay)

    return processed_data


def save_processed_data(data: List[Dict[str, Any]], output_path: str, suffix: str = ""):
    """Save processed data to JSON file."""
    output_file = Path(output_path)

    # Add suffix to filename if provided
    if suffix:
        stem = output_file.stem
        output_file = output_file.parent / f"{stem}{suffix}.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(data)} processed samples to {output_file}")


def main():
    """Main preprocessing function."""
    # Parse command line arguments
    args = parse_arguments()

    print("Starting SQL Skills KNN Preprocessing...")
    print(f"Processing {args.num_samples if args.num_samples else 'all'} samples")
    if args.output_suffix:
        print(f"Output suffix: {args.output_suffix}")

    # Initialize configuration
    config = ViPERConfig(
        model_name="gpt-4.1-nano",
        temperature=0.1,
        max_tokens=200,
        dataset_path="dataset"
    )

    # Initialize LLM interface
    llm_interface = LLMInterface(config)

    # Initialize BERT embedder
    bert_embedder = BERTEmbedder()

    try:
        # Load training data
        data = load_training_data(config.dataset_path, args.num_samples)

        # Get template path - sử dụng template có SQL cho preprocessing
        template_path = Path(__file__).parent.parent / "templates" / "skill_extraction_with_sql.txt"

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Process data to extract skills
        print("Extracting SQL skills using LLM analysis...")
        processed_data = process_training_data(
            data=data,
            llm_interface=llm_interface,
            template_path=template_path,
            delay=args.delay
        )

        # Create embeddings for skills
        print("Creating embeddings for skills using BERT (google-bert/bert-base-uncased)...")
        for item in tqdm(processed_data, desc="Creating embeddings"):
            skills = item["skills"]
            # Generate embedding using BERT
            embedding = bert_embedder.encode(skills)
            item["skills_embedding"] = embedding

        # Save processed data
        output_path = Path(config.dataset_path) / "ViText2SQL" / "std-level" / "skill_knn_train.json"
        save_processed_data(processed_data, output_path, args.output_suffix)

        print("Preprocessing completed successfully!")

        # Print sample results
        print("\nSample processed data:")
        for i, item in enumerate(processed_data[:3]):
            print(f"\nSample {i+1}:")
            print(f"DB: {item['db_id']}")
            print(f"Question: {item['question']}")
            print(f"Skills: {item['skills']}")
            print(f"Skills Embedding: {item['skills_embedding']}")
            print(f"Query: {item['query']}")

        # Print usage statistics
        print(f"\nProcessing Statistics:")
        print(f"- Total samples processed: {len(processed_data)}")
        print(f"- Delay between samples: {args.delay} seconds")
        if args.num_samples:
            print(f"- Limited to: {args.num_samples} samples (testing mode)")

    except Exception as e:
        print(f"Error during preprocessing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
