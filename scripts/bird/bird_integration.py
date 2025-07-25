#!/usr/bin/env python3
"""
BIRD Dataset Integration for ViPERSQL

Main entry point for all BIRD dataset processing tasks.
"""

import sys
import argparse
from pathlib import Path

# Add scripts/bird to path
sys.path.append(str(Path(__file__).parent))

from process_bird_dataset import BirdDatasetProcessor
from analyze_bird import analyze_original_bird, test_sampling_strategy, analyze_processed_file
from test_10_samples import test_bird_translation


def main():
    """Main entry point with subcommands"""
    parser = argparse.ArgumentParser(
        description="BIRD Dataset Integration for ViPERSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze original dataset
  python bird_integration.py analyze

  # Test with 10 samples
  python bird_integration.py test --api-key YOUR_KEY

  # Process full dataset
  python bird_integration.py process --samples 200 --api-key YOUR_KEY

  # Check processed results
  python bird_integration.py check --file dataset/BIRD/bird_vietnamese_200.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze original BIRD dataset')
    analyze_parser.add_argument('--file', default='dataset/BIRD/dev.json', help='BIRD dataset file')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test translation with 10 samples')
    test_parser.add_argument('--api-key', help='OpenAI API key')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process BIRD dataset')
    process_parser.add_argument('--api-key', help='OpenAI API key')
    process_parser.add_argument('--samples', type=int, default=200, help='Number of samples')
    process_parser.add_argument('--input-file', default='dataset/BIRD/dev.json', help='Input file')
    process_parser.add_argument('--output-dir', default='dataset/BIRD', help='Output directory')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check processed file')
    check_parser.add_argument('--file', required=True, help='Processed file to check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'analyze':
            print("🔍 Analyzing BIRD Dataset")
            analyze_original_bird(args.file)
            test_sampling_strategy(args.file)
            
        elif args.command == 'test':
            print("🧪 Testing Translation (10 samples)")
            test_bird_translation()
            
        elif args.command == 'process':
            print("🚀 Processing BIRD Dataset")
            if not args.api_key:
                import os
                args.api_key = os.getenv('OPENAI_API_KEY')
                if not args.api_key:
                    print("❌ Error: API key required (use --api-key or set OPENAI_API_KEY)")
                    return 1
            
            processor = BirdDatasetProcessor(args.api_key, args.output_dir)
            processor.run(args.input_file, args.samples)
            
        elif args.command == 'check':
            print("📊 Checking Processed File")
            analyze_processed_file(args.file)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
