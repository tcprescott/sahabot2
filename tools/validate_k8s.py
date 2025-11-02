#!/usr/bin/env python3
"""
Kubernetes deployment validation script.

This script validates the Kubernetes manifests and configuration before deployment.
"""

import sys
import yaml
from pathlib import Path


def validate_yaml_file(file_path: Path, allow_multiple_docs: bool = False) -> bool:
    """
    Validate a YAML file.
    
    Args:
        file_path: Path to YAML file
        allow_multiple_docs: Whether to allow multiple YAML documents
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with open(file_path) as f:
            if allow_multiple_docs:
                list(yaml.safe_load_all(f))
            else:
                yaml.safe_load(f)
        print(f"✓ {file_path.name} is valid")
        return True
    except yaml.YAMLError as e:
        print(f"✗ {file_path.name} has YAML syntax errors:")
        print(f"  {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path.name} validation failed:")
        print(f"  {e}")
        return False


def check_secrets_customized(secrets_path: Path) -> bool:
    """
    Check if secrets have been customized from template values.
    
    Args:
        secrets_path: Path to secrets.yaml
        
    Returns:
        bool: True if secrets appear customized, False otherwise
    """
    template_values = [
        "CHANGE_ME",
        "CHANGE_ME_IN_PRODUCTION",
        "CHANGE_ME_LONG_RANDOM_STRING",
    ]
    
    try:
        with open(secrets_path) as f:
            content = f.read()
            
        found_templates = [v for v in template_values if v in content]
        
        if found_templates:
            print(f"⚠ {secrets_path.name} contains template values:")
            for val in found_templates:
                print(f"  - {val}")
            print("  Please update these values before deploying to production.")
            return False
        else:
            print(f"✓ {secrets_path.name} appears to be customized")
            return True
    except Exception as e:
        print(f"✗ Could not check {secrets_path.name}: {e}")
        return False


def check_deployment_image(deployment_path: Path) -> bool:
    """
    Check if deployment image is customized.
    
    Args:
        deployment_path: Path to deployment.yaml
        
    Returns:
        bool: True if image is customized, False otherwise
    """
    try:
        with open(deployment_path) as f:
            deployment = yaml.safe_load(f)
        
        containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        if not containers or not isinstance(containers, list):
            print(f"✗ {deployment_path.name} does not contain any containers in spec.template.spec.containers")
            return False
        
        image = containers[0].get('image')
        if not image:
            print(f"✗ {deployment_path.name} first container does not specify an image")
            return False
        
        if 'YOUR_REGISTRY_NAME' in image:
            print(f"⚠ {deployment_path.name} uses placeholder registry name:")
            print(f"  {image}")
            print("  Please update with your actual Digital Ocean registry name.")
            return False
        else:
            print(f"✓ {deployment_path.name} image is customized: {image}")
            return True
    except Exception as e:
        print(f"✗ Could not check {deployment_path.name} image: {e}")
        return False


def main():
    """Main validation function."""
    print("Kubernetes Deployment Validation")
    print("=" * 50)
    print()
    
    k8s_dir = Path(__file__).parent.parent / 'k8s'
    
    if not k8s_dir.exists():
        print(f"✗ k8s directory not found at {k8s_dir}")
        sys.exit(1)
    
    all_valid = True
    
    # Validate YAML syntax
    print("Validating YAML syntax...")
    print("-" * 50)
    
    manifests = [
        ('namespace.yaml', False),
        ('secrets.yaml', False),
        ('deployment.yaml', False),
        ('service.yaml', False),
        ('mysql.yaml', True),  # Multi-document
    ]
    
    for filename, allow_multiple in manifests:
        file_path = k8s_dir / filename
        if file_path.exists():
            if not validate_yaml_file(file_path, allow_multiple):
                all_valid = False
        else:
            print(f"⚠ {filename} not found (optional)")
    
    print()
    
    # Check configuration
    print("Checking configuration...")
    print("-" * 50)
    
    secrets_path = k8s_dir / 'secrets.yaml'
    if secrets_path.exists():
        if not check_secrets_customized(secrets_path):
            all_valid = False
    
    deployment_path = k8s_dir / 'deployment.yaml'
    if deployment_path.exists():
        if not check_deployment_image(deployment_path):
            all_valid = False
    
    print()
    
    # Validate GitHub Actions workflows
    print("Validating GitHub Actions workflows...")
    print("-" * 50)
    
    workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
    workflows = [
        'build-container.yml',
        'deploy-k8s.yml',
    ]
    
    for workflow in workflows:
        workflow_path = workflows_dir / workflow
        if workflow_path.exists():
            if not validate_yaml_file(workflow_path):
                all_valid = False
        else:
            print(f"⚠ {workflow} not found")
    
    print()
    print("=" * 50)
    
    if all_valid:
        print("✓ All validations passed!")
        print()
        print("Next steps:")
        print("1. Ensure GitHub secrets are configured:")
        print("   - DIGITALOCEAN_ACCESS_TOKEN")
        print("   - DIGITALOCEAN_REGISTRY_NAME")
        print("   - DIGITALOCEAN_CLUSTER_ID")
        print("2. Push to main branch to trigger build and deploy")
        print("3. Or deploy manually following k8s/README.md")
        return 0
    else:
        print("✗ Some validations failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
