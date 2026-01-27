"""
Test script for verifying synonym generation functionality.
This allows testing the synonym_generator agent without running the full Power BI pipeline.

Usage:
    python test_synonym_generator.py --mode <mode>

Modes:
    unit         - Test individual field synonym generation
    quality      - Run quality checks on generated synonyms
    integration  - Test with actual TMDL files and full linguistic pipeline
    batch        - Generate synonyms for all fields in dataset
    compare      - Compare LLM-generated vs hard-coded synonyms
"""

import argparse
import json
import os
import sys
from typing import List, Dict
from colorama import init, Fore, Style

# Initialize colorama for Windows color support
init()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.synonym_generator import agent_generate_synonyms, batch_generate_synonyms
from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from discovery.linguistic import generate_linguistic_metadata
from config.settings import SEMANTIC_MODEL_PATH


class SynonymTester:
    """Comprehensive testing suite for synonym generation."""
    
    def __init__(self):
        self.test_results = []
        self.errors = []
    
    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{text.center(80)}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")
    
    def mode_unit_tests(self):
        """Run unit tests on individual field examples."""
        self.print_header("UNIT TESTS - Individual Field Synonym Generation")
        
        # Test cases: (field_name, is_measure, expected_characteristics)
        test_cases = [
            ("sales", True, ["should contain numeric terms like revenue, total"]),
            ("total_cost", True, ["should contain expense, amount"]),
            ("quantity", True, ["should contain count, volume"]),
            ("product_name", False, ["should contain item, sku", "should NOT contain numeric terms"]),
            ("country", False, ["should contain region, market", "should NOT contain total, count"]),
            ("order_date", False, ["should contain time, period", "should NOT contain sum, amount"]),
        ]
        
        print(f"Testing {len(test_cases)} sample fields...\n")
        
        for field_name, is_measure, expectations in test_cases:
            field_type = "MEASURE" if is_measure else "DIMENSION"
            print(f"{Fore.YELLOW}Testing: {field_name} ({field_type}){Style.RESET_ALL}")
            
            try:
                synonyms = agent_generate_synonyms(field_name, is_measure)
                
                print(f"  Generated synonyms: {synonyms}")
                
                # Basic validations
                if len(synonyms) < 2:
                    self.print_error(f"  Too few synonyms generated: {len(synonyms)}")
                    self.errors.append(f"{field_name}: Insufficient synonyms")
                else:
                    self.print_success(f"  Generated {len(synonyms)} synonyms")
                
                # Check for original field name variants
                clean_name = field_name.lower().replace("_", " ")
                if field_name.lower() not in synonyms and clean_name not in synonyms:
                    self.print_warning(f"  Original field name not in synonyms")
                
                # Manual check prompts
                print(f"  {Fore.CYAN}Expectations:{Style.RESET_ALL}")
                for expectation in expectations:
                    print(f"    - {expectation}")
                
                self.test_results.append({
                    "field": field_name,
                    "type": field_type,
                    "synonyms": synonyms,
                    "count": len(synonyms),
                    "passed": True
                })
                
            except Exception as e:
                self.print_error(f"  Failed: {str(e)}")
                self.errors.append(f"{field_name}: {str(e)}")
                self.test_results.append({
                    "field": field_name,
                    "type": field_type,
                    "passed": False,
                    "error": str(e)
                })
            
            print()
        
        # Summary
        passed = sum(1 for r in self.test_results if r.get("passed"))
        total = len(self.test_results)
        
        self.print_header("UNIT TEST SUMMARY")
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if self.errors:
            print(f"\n{Fore.RED}Errors:{Style.RESET_ALL}")
            for error in self.errors:
                print(f"  - {error}")
    
    def mode_quality_checks(self):
        """Run quality checks on generated synonyms."""
        self.print_header("QUALITY CHECKS")
        
        test_fields = [
            {"name": "sales_amount", "is_measure": True},
            {"name": "product_category", "is_measure": False},
            {"name": "unit_price", "is_measure": True},
            {"name": "customer_country", "is_measure": False},
        ]
        
        print("Checking synonym quality...\n")
        
        # Prohibited terms for dimensions (numeric indicators)
        numeric_terms = ["total", "sum", "count", "avg", "average", "amount", "value", "qty", "quantity"]
        
        issues = []
        
        for field in test_fields:
            field_name = field["name"]
            is_measure = field["is_measure"]
            
            print(f"{Fore.YELLOW}Checking: {field_name}{Style.RESET_ALL}")
            
            try:
                synonyms = agent_generate_synonyms(field_name, is_measure)
                
                # Check 1: Duplication
                if len(synonyms) != len(set(synonyms)):
                    issues.append(f"{field_name}: Contains duplicate synonyms")
                    self.print_warning(f"  Contains duplicates")
                else:
                    self.print_success(f"  No duplicates")
                
                # Check 2: Empty or None values
                if any(not s or s.strip() == "" for s in synonyms):
                    issues.append(f"{field_name}: Contains empty synonyms")
                    self.print_error(f"  Contains empty values")
                else:
                    self.print_success(f"  No empty values")
                
                # Check 3: Numeric leakage to dimensions
                if not is_measure:
                    leaked_numeric = [s for s in synonyms if any(term in s for term in numeric_terms)]
                    if leaked_numeric:
                        issues.append(f"{field_name}: Numeric terms in dimension: {leaked_numeric}")
                        self.print_error(f"  NUMERIC LEAKAGE: {leaked_numeric}")
                    else:
                        self.print_success(f"  No numeric leakage")
                
                # Check 4: Synonym count
                if len(synonyms) < 2:
                    issues.append(f"{field_name}: Too few synonyms ({len(synonyms)})")
                    self.print_warning(f"  Too few synonyms: {len(synonyms)}")
                elif len(synonyms) > 15:
                    issues.append(f"{field_name}: Too many synonyms ({len(synonyms)})")
                    self.print_warning(f"  Too many synonyms: {len(synonyms)}")
                else:
                    self.print_success(f"  Good synonym count: {len(synonyms)}")
                
                print(f"  Synonyms: {synonyms}\n")
                
            except Exception as e:
                issues.append(f"{field_name}: Generation failed - {str(e)}")
                self.print_error(f"  Failed: {str(e)}\n")
        
        # Summary
        self.print_header("QUALITY CHECK SUMMARY")
        if issues:
            print(f"{Fore.YELLOW}Found {len(issues)} issues:{Style.RESET_ALL}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            self.print_success("All quality checks passed!")
    
    def mode_integration_test(self):
        """Test with actual TMDL files and full linguistic pipeline."""
        self.print_header("INTEGRATION TEST - Full Pipeline with LLM Synonyms")
        
        print("Loading TMDL files...\n")
        
        try:
            # Load the actual semantic model
            tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
            self.print_success(f"Loaded TMDL from {SEMANTIC_MODEL_PATH}")
            
            # Extract semantic index
            index = extract_semantic_index(tmdl)
            self.print_success(f"Extracted semantic index")
            
            # Count fields
            total_fields = sum(len(table["columns"]) for table in index["tables"].values())
            print(f"\n{Fore.CYAN}Dataset Statistics:{Style.RESET_ALL}")
            print(f"  Tables: {len(index['tables'])}")
            print(f"  Total Fields: {total_fields}")
            
            # Generate linguistic metadata (this will use the new LLM agent)
            print(f"\n{Fore.YELLOW}Generating linguistic metadata with LLM synonyms...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}(This will make multiple LLM API calls){Style.RESET_ALL}\n")
            
            linguistic = generate_linguistic_metadata(index)
            self.print_success("Generated linguistic metadata")
            
            # Analyze results
            entities = linguistic["entities"]
            print(f"\n{Fore.CYAN}Results:{Style.RESET_ALL}")
            print(f"  Total Entities: {len(entities)}")
            
            # Sample some entities to show
            print(f"\n{Fore.CYAN}Sample Generated Synonyms:{Style.RESET_ALL}")
            sample_count = min(10, len(entities))
            for i, (entity_id, entity) in enumerate(list(entities.items())[:sample_count]):
                kind = entity["kind"]
                terms = entity["terms"]
                term_preview = ", ".join(terms[:5])
                if len(terms) > 5:
                    term_preview += f" ... ({len(terms)} total)"
                
                print(f"  {entity_id} ({kind}): {term_preview}")
            
            # Save to file for review
            output_path = "test_linguistic_output.json"
            with open(output_path, "w") as f:
                json.dump(linguistic, f, indent=2)
            
            self.print_success(f"\nFull output saved to: {output_path}")
            
        except Exception as e:
            self.print_error(f"Integration test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def mode_batch_generate(self):
        """Generate and save synonyms for all fields in the dataset."""
        self.print_header("BATCH GENERATION - Generate Synonyms for All Fields")
        
        print("Loading semantic model...\n")
        
        try:
            tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
            index = extract_semantic_index(tmdl)
            
            # Collect all fields
            all_fields = []
            for table_name, table_info in index["tables"].items():
                for col_name, col_meta in table_info["columns"].items():
                    is_measure = col_name in table_info.get("measures", {})
                    all_fields.append({
                        "table": table_name,
                        "name": col_name,
                        "is_measure": is_measure,
                        "data_type": col_meta.get("dataType")
                    })
            
            print(f"Found {len(all_fields)} fields across {len(index['tables'])} tables")
            print(f"{Fore.YELLOW}This will make {len(all_fields)} LLM API calls...{Style.RESET_ALL}\n")
            
            proceed = input("Proceed? (y/n): ")
            if proceed.lower() != 'y':
                print("Cancelled.")
                return
            
            # Generate synonyms for all
            results = {}
            for i, field in enumerate(all_fields, 1):
                field_id = f"{field['table']}.{field['name']}"
                print(f"[{i}/{len(all_fields)}] Generating: {field_id}...", end=" ")
                
                try:
                    synonyms = agent_generate_synonyms(
                        field_name=field["name"],
                        is_measure=field["is_measure"],
                        data_type=field["data_type"]
                    )
                    results[field_id] = {
                        "field": field["name"],
                        "table": field["table"],
                        "is_measure": field["is_measure"],
                        "data_type": field["data_type"],
                        "synonyms": synonyms
                    }
                    print(f"{Fore.GREEN}✓{Style.RESET_ALL} ({len(synonyms)} synonyms)")
                except Exception as e:
                    print(f"{Fore.RED}✗ {str(e)}{Style.RESET_ALL}")
                    results[field_id] = {
                        "field": field["name"],
                        "table": field["table"],
                        "error": str(e)
                    }
            
            # Save results
            output_path = "batch_synonyms_output.json"
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            
            self.print_success(f"\nBatch results saved to: {output_path}")
            
            # Summary
            successful = sum(1 for r in results.values() if "synonyms" in r)
            failed = len(results) - successful
            
            print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
            print(f"  Successful: {successful}/{len(results)}")
            print(f"  Failed: {failed}/{len(results)}")
            
        except Exception as e:
            self.print_error(f"Batch generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def mode_compare(self):
        """Compare LLM-generated synonyms with hard-coded ones."""
        self.print_header("COMPARISON - LLM vs Hard-Coded Synonyms")
        
        # Hard-coded reference synonyms (from old implementation)
        measure_synonyms = {
            "amount": ["amount", "value", "total"],
            "sales": ["sales", "revenue", "turnover"],
            "cost": ["cost", "expense"],
            "price": ["price", "rate"],
            "quantity": ["qty", "count", "amount", "volume"],
            "forecast": ["prediction", "expected", "demand"],
        }
        
        dimension_synonyms = {
            "product": ["product", "item", "sku", "commodity"],
            "country": ["country", "region", "market", "geo"],
            "date": ["date", "time", "period", "day"],
            "person": ["person", "employee", "salesperson"],
            "factory": ["plant", "site", "location", "facility"],
            "batch": ["lot", "run"],
            "campaign": ["promo", "marketing"],
        }
        
        print("Comparing LLM-generated synonyms with hard-coded references...\n")
        
        # Test measures
        print(f"{Fore.CYAN}MEASURES:{Style.RESET_ALL}\n")
        for field_name, hardcoded in measure_synonyms.items():
            print(f"{Fore.YELLOW}{field_name}:{Style.RESET_ALL}")
            
            # Generate LLM synonyms
            llm_synonyms = agent_generate_synonyms(field_name, is_measure=True)
            
            print(f"  Hard-coded: {hardcoded}")
            print(f"  LLM-generated: {llm_synonyms}")
            
            # Find differences
            hardcoded_set = set(hardcoded)
            llm_set = set(llm_synonyms)
            
            added = llm_set - hardcoded_set
            removed = hardcoded_set - llm_set
            
            if added:
                print(f"  {Fore.GREEN}+ New: {list(added)}{Style.RESET_ALL}")
            if removed:
                print(f"  {Fore.YELLOW}- Missing: {list(removed)}{Style.RESET_ALL}")
            if not added and not removed:
                print(f"  {Fore.GREEN}✓ Identical{Style.RESET_ALL}")
            
            print()
        
        # Test dimensions
        print(f"{Fore.CYAN}DIMENSIONS:{Style.RESET_ALL}\n")
        for field_name, hardcoded in dimension_synonyms.items():
            print(f"{Fore.YELLOW}{field_name}:{Style.RESET_ALL}")
            
            # Generate LLM synonyms
            llm_synonyms = agent_generate_synonyms(field_name, is_measure=False)
            
            print(f"  Hard-coded: {hardcoded}")
            print(f"  LLM-generated: {llm_synonyms}")
            
            # Find differences
            hardcoded_set = set(hardcoded)
            llm_set = set(llm_synonyms)
            
            added = llm_set - hardcoded_set
            removed = hardcoded_set - llm_set
            
            if added:
                print(f"  {Fore.GREEN}+ New: {list(added)}{Style.RESET_ALL}")
            if removed:
                print(f"  {Fore.YELLOW}- Missing: {list(removed)}{Style.RESET_ALL}")
            if not added and not removed:
                print(f"  {Fore.GREEN}✓ Identical{Style.RESET_ALL}")
            
            print()


def main():
    parser = argparse.ArgumentParser(description="Test synonym generation functionality")
    parser.add_argument(
        "--mode",
        choices=["unit", "quality", "integration", "batch", "compare"],
        required=True,
        help="Test mode to run"
    )
    
    args = parser.parse_args()
    
    tester = SynonymTester()
    
    if args.mode == "unit":
        tester.mode_unit_tests()
    elif args.mode == "quality":
        tester.mode_quality_checks()
    elif args.mode == "integration":
        tester.mode_integration_test()
    elif args.mode == "batch":
        tester.mode_batch_generate()
    elif args.mode == "compare":
        tester.mode_compare()


if __name__ == "__main__":
    main()
