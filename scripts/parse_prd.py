#!/usr/bin/env python3

"""
PRD Parser for LEARN-X Project

This script parses a PRD text file and generates a tasks.json file with structured tasks.
"""

import json
import os
import re
import sys
from datetime import datetime

# Default paths
DEFAULT_PRD_PATH = '../learn-x-prd.txt'
DEFAULT_OUTPUT_DIR = '../tasks'
DEFAULT_OUTPUT_FILE = 'tasks.json'


def parse_prd(prd_path):
    """Parse the PRD file and extract tasks."""
    try:
        with open(prd_path, 'r') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading PRD file: {e}")
        sys.exit(1)
    
    # Extract sections
    sections = {}
    current_section = None
    section_content = []
    
    for line in content.split('\n'):
        if line.startswith('##') and not line.startswith('###'):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(section_content)
            
            # Start new section
            current_section = line.strip('# ').strip()
            section_content = []
        else:
            if current_section:
                section_content.append(line)
    
    # Save the last section
    if current_section:
        sections[current_section] = '\n'.join(section_content)
    
    # Extract tasks from the "Detailed Tasks" section
    tasks = []
    task_id = 1
    
    if "Detailed Tasks" in sections:
        detailed_tasks = sections["Detailed Tasks"]
        
        # Extract high-level tasks (marked with ###)
        high_level_tasks = re.findall(r'### ([^\n]+)', detailed_tasks)
        
        for i, high_level_task in enumerate(high_level_tasks):
            # Add the high-level task
            tasks.append({
                "id": task_id,
                "title": high_level_task,
                "status": "pending",
                "priority": 1,
                "dependencies": [],
                "description": f"Implement {high_level_task}",
                "details": f"# {high_level_task}\n\nImplement the {high_level_task} as described in the PRD.\n\n## Implementation Details:\n- Follow the architecture guidelines\n- Ensure security and performance requirements are met\n- Write comprehensive tests\n\n## Acceptance Criteria:\n- Code is well-documented\n- Tests pass\n- Follows project coding standards",
                "subtasks": []
            })
            
            # Extract subtasks (bullet points after the high-level task)
            subtask_pattern = r'### ' + re.escape(high_level_task) + r'\s*\n([\s\S]*?)(?=### |$)'
            subtask_section_match = re.search(subtask_pattern, detailed_tasks)
            
            if subtask_section_match:
                subtask_section = subtask_section_match.group(1)
                subtasks = re.findall(r'- ([^\n]+)', subtask_section)
                
                for j, subtask in enumerate(subtasks):
                    task_id += 1
                    tasks.append({
                        "id": task_id,
                        "title": subtask,
                        "status": "pending",
                        "priority": 2,
                        "dependencies": [task_id - j - 1],  # Depend on previous task or high-level task
                        "description": subtask,
                        "details": f"# {subtask}\n\nImplement this subtask as part of the {high_level_task} feature.\n\n## Implementation Details:\n- Follow the architecture guidelines\n- Ensure proper integration with other components\n- Write unit tests\n\n## Acceptance Criteria:\n- Code is well-documented\n- Tests pass\n- Follows project coding standards",
                        "subtasks": []
                    })
            
            task_id += 1
    
    # Extract implementation phases for additional tasks
    phases = []
    for phase_name in ["Phase 1: Foundation", "Phase 2: Core Functionality", 
                      "Phase 3: Advanced Features", "Phase 4: Polish and Integration"]:
        if phase_name in sections.get("Implementation Phases", ""):
            phase_pattern = r'### ' + re.escape(phase_name) + r'[^\n]*\n([\s\S]*?)(?=### |$)'
            phase_match = re.search(phase_pattern, sections.get("Implementation Phases", ""))
            if phase_match:
                phase_content = phase_match.group(1)
                phases.append((phase_name, phase_content))
    
    # Create additional tasks from phases
    for phase_name, phase_content in phases:
        # Extract tasks from bullet points
        phase_tasks = re.findall(r'- ([^\n]+)', phase_content)
        for phase_task in phase_tasks:
            # Check if this task is already covered in detailed tasks
            if not any(phase_task.lower() in task["title"].lower() for task in tasks):
                task_id += 1
                tasks.append({
                    "id": task_id,
                    "title": phase_task,
                    "status": "pending",
                    "priority": 3,
                    "dependencies": [],
                    "description": f"Implement {phase_task}",
                    "details": f"# {phase_task}\n\nImplement this task as part of {phase_name}.\n\n## Implementation Details:\n- Follow the architecture guidelines\n- Ensure proper integration with other components\n- Write appropriate tests\n\n## Acceptance Criteria:\n- Code is well-documented\n- Tests pass\n- Follows project coding standards",
                    "subtasks": []
                })
    
    return tasks


def save_tasks(tasks, output_dir, output_file):
    """Save tasks to a JSON file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save tasks to JSON file
    output_path = os.path.join(output_dir, output_file)
    try:
        with open(output_path, 'w') as file:
            json.dump({"tasks": tasks}, file, indent=2)
        print(f"Tasks saved to {output_path}")
    except Exception as e:
        print(f"Error saving tasks: {e}")
        sys.exit(1)


def generate_task_files(tasks, output_dir):
    """Generate individual task files."""
    for task in tasks:
        task_file = os.path.join(output_dir, f"task-{task['id']}.md")
        try:
            with open(task_file, 'w') as file:
                file.write(f"# Task ID: {task['id']}\n")
                file.write(f"# Title: {task['title']}\n")
                file.write(f"# Status: {task['status']}\n")
                file.write(f"# Dependencies: {', '.join(map(str, task['dependencies']))}\n")
                file.write(f"# Priority: {task['priority']}\n")
                file.write(f"# Description: {task['description']}\n\n")
                file.write(f"# Details:\n{task['details']}\n\n")
                file.write(f"# Test Strategy:\n- Write unit tests for all functionality\n- Ensure integration tests cover key workflows\n- Validate against requirements")
        except Exception as e:
            print(f"Error generating task file for task {task['id']}: {e}")


def main():
    """Main function to parse PRD and generate tasks."""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set paths relative to script directory
    prd_path = os.path.join(script_dir, DEFAULT_PRD_PATH)
    output_dir = os.path.join(script_dir, DEFAULT_OUTPUT_DIR)
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        prd_path = sys.argv[1]
    
    # Parse PRD and generate tasks
    tasks = parse_prd(prd_path)
    
    # Save tasks to JSON file
    save_tasks(tasks, output_dir, DEFAULT_OUTPUT_FILE)
    
    # Generate individual task files
    generate_task_files(tasks, output_dir)
    
    print(f"Generated {len(tasks)} tasks successfully!")


if __name__ == "__main__":
    main()
