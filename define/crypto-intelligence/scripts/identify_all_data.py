"""
Identify all data files in the crypto intelligence system.

This script scans all data directories and provides a comprehensive report
of all data files, their sizes, and last modified dates.
"""
import os
import json
from pathlib import Path
from datetime import datetime


def get_file_info(file_path):
    """Get file information."""
    stats = os.stat(file_path)
    return {
        'path': str(file_path),
        'size_bytes': stats.st_size,
        'size_mb': round(stats.st_size / (1024 * 1024), 2),
        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
        'type': file_path.suffix
    }


def scan_directory(base_path, category):
    """Scan directory for files."""
    files = []
    path = Path(base_path)
    
    if not path.exists():
        return files
    
    for file_path in path.rglob('*'):
        if file_path.is_file():
            info = get_file_info(file_path)
            info['category'] = category
            files.append(info)
    
    return files


def main():
    """Main function."""
    print("="*80)
    print("CRYPTO INTELLIGENCE - DATA FILE INVENTORY")
    print("="*80)
    print()
    
    base_dir = Path(__file__).parent.parent
    
    # Define all data locations
    data_locations = {
        'Main Data': 'data',
        'Cache': 'data/cache',
        'Performance': 'data/performance',
        'Reputation': 'data/reputation',
        'Output': 'output',
        'Credentials': 'credentials',
        'Config': 'config'
    }
    
    all_files = []
    summary = {}
    
    for category, location in data_locations.items():
        full_path = base_dir / location
        files = scan_directory(full_path, category)
        all_files.extend(files)
        
        if files:
            total_size = sum(f['size_mb'] for f in files)
            summary[category] = {
                'count': len(files),
                'total_size_mb': round(total_size, 2)
            }
            
            print(f"\n📁 {category} ({location})")
            print(f"   Files: {len(files)}")
            print(f"   Total Size: {total_size:.2f} MB")
            
            # Show individual files
            for file in sorted(files, key=lambda x: x['size_mb'], reverse=True)[:10]:
                rel_path = Path(file['path']).relative_to(base_dir)
                print(f"   - {rel_path} ({file['size_mb']} MB)")
    
    # Overall summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total_files = len(all_files)
    total_size = sum(f['size_mb'] for f in all_files)
    
    print(f"\nTotal Files: {total_files}")
    print(f"Total Size: {total_size:.2f} MB")
    
    # Group by file type
    print("\nBy File Type:")
    by_type = {}
    for file in all_files:
        ext = file['type'] or 'no_extension'
        if ext not in by_type:
            by_type[ext] = {'count': 0, 'size_mb': 0}
        by_type[ext]['count'] += 1
        by_type[ext]['size_mb'] += file['size_mb']
    
    for ext, info in sorted(by_type.items(), key=lambda x: x[1]['size_mb'], reverse=True):
        print(f"  {ext}: {info['count']} files ({info['size_mb']:.2f} MB)")
    
    # Save detailed report
    report_path = base_dir / 'data' / 'data_inventory_report.json'
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'by_type': by_type,
        'all_files': all_files
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed report saved to: {report_path}")
    print("="*80)


if __name__ == '__main__':
    main()
