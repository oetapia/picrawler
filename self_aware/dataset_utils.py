#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Utilities for ML Training

Tools for exporting, analyzing, and preparing collected datasets
for machine learning training.

Features:
- Export to PyTorch/TensorFlow formats
- Dataset splitting (train/val/test)
- Class balancing
- Dataset statistics and visualization
- HTML reports
"""

import os
import csv
import shutil
from pathlib import Path
from collections import defaultdict, Counter
import json


def list_sessions(log_dir="self_aware/logs"):
    """
    List all available dataset sessions.
    
    Args:
        log_dir: Base log directory
    
    Returns:
        list: List of session directories
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return []
    
    sessions = [d for d in log_path.iterdir() 
                if d.is_dir() and d.name.startswith('session_')]
    return sorted(sessions)


def analyze_session(session_dir):
    """
    Analyze a dataset session.
    
    Args:
        session_dir: Path to session directory
    
    Returns:
        dict: Session statistics
    """
    session_path = Path(session_dir)
    
    # Check for required files
    sensor_csv = session_path / "sensor_data.csv"
    manifest_csv = session_path / "photo_manifest.csv"
    photos_dir = session_path / "photos"
    
    stats = {
        'session_name': session_path.name,
        'has_sensor_data': sensor_csv.exists(),
        'has_photos': photos_dir.exists(),
        'has_manifest': manifest_csv.exists(),
    }
    
    # Count sensor entries
    if sensor_csv.exists():
        with open(sensor_csv, 'r') as f:
            stats['sensor_entries'] = sum(1 for _ in f) - 1  # Subtract header
    
    # Count photos and analyze labels
    if manifest_csv.exists():
        labels = []
        with open(manifest_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                labels.append(row.get('label', 'unknown'))
        
        stats['photo_count'] = len(labels)
        stats['label_distribution'] = dict(Counter(labels))
    
    # Calculate size
    if photos_dir.exists():
        total_size = sum(f.stat().st_size for f in photos_dir.glob('*.jpg'))
        stats['photos_size_mb'] = total_size / (1024 * 1024)
    
    if sensor_csv.exists():
        stats['sensor_size_mb'] = sensor_csv.stat().st_size / (1024 * 1024)
    
    return stats


def export_for_pytorch(session_dir, output_dir="dataset_export",
                       train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """
    Export session to PyTorch ImageFolder format.
    
    Creates directory structure:
        output_dir/
        ├── train/
        │   ├── clear_path/
        │   ├── obstacle_close/
        │   └── ...
        ├── val/
        └── test/
    
    Args:
        session_dir: Path to session directory
        output_dir: Output directory name (within session)
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
    
    Returns:
        dict: Export statistics
    """
    session_path = Path(session_dir)
    export_path = session_path / output_dir
    
    # Create split directories
    splits = ['train', 'val', 'test']
    ratios = [train_ratio, val_ratio, test_ratio]
    
    print(f"\n📦 Exporting to PyTorch format...")
    print(f"   Session: {session_path.name}")
    print(f"   Output: {export_path}")
    print(f"   Split: {train_ratio:.0%} train, {val_ratio:.0%} val, {test_ratio:.0%} test\n")
    
    # Read manifest
    manifest_csv = session_path / "photo_manifest.csv"
    if not manifest_csv.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_csv}")
    
    # Group photos by label
    photos_by_label = defaultdict(list)
    with open(manifest_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get('label', 'unknown')
            filename = row.get('filename')
            photos_by_label[label].append(filename)
    
    # Export statistics
    stats = {
        'total_photos': 0,
        'splits': {split: {} for split in splits},
        'labels': list(photos_by_label.keys())
    }
    
    # Process each label
    for label, photos in photos_by_label.items():
        print(f"Processing {label}: {len(photos)} photos")
        
        # Shuffle photos
        import random
        random.shuffle(photos)
        
        # Calculate split indices
        n = len(photos)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        split_photos = {
            'train': photos[:train_end],
            'val': photos[train_end:val_end],
            'test': photos[val_end:]
        }
        
        # Copy photos to split directories
        for split_name, split_photos_list in split_photos.items():
            # Create label directory
            label_dir = export_path / split_name / label
            label_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy photos
            for photo in split_photos_list:
                src = session_path / "photos" / photo
                dst = label_dir / photo
                if src.exists():
                    shutil.copy2(src, dst)
            
            # Update stats
            stats['splits'][split_name][label] = len(split_photos_list)
            stats['total_photos'] += len(split_photos_list)
    
    # Save export metadata
    metadata = {
        'session': session_path.name,
        'export_date': str(Path(export_path).stat().st_mtime),
        'format': 'pytorch_imagefolder',
        'splits': stats['splits'],
        'labels': stats['labels']
    }
    
    with open(export_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Export complete!")
    print(f"  Total photos: {stats['total_photos']}")
    print(f"  Labels: {len(stats['labels'])}")
    for split in splits:
        total = sum(stats['splits'][split].values())
        print(f"  {split}: {total} photos")
    
    return stats


def generate_html_report(session_dir, output_file="dataset_report.html"):
    """
    Generate HTML report with dataset statistics and sample images.
    
    Args:
        session_dir: Path to session directory
        output_file: Output HTML filename
    
    Returns:
        str: Path to generated report
    """
    session_path = Path(session_dir)
    stats = analyze_session(session_dir)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dataset Report - {stats['session_name']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #666;
            margin-top: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .labels {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }}
        .label-badge {{
            background: #4CAF50;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .samples {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .sample-card {{
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .sample-card img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
        }}
        .sample-label {{
            padding: 10px;
            background: #f9f9f9;
            text-align: center;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Dataset Report</h1>
        <p><strong>Session:</strong> {stats['session_name']}</p>
        
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{stats.get('photo_count', 0)}</div>
                <div class="stat-label">Photos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('sensor_entries', 0)}</div>
                <div class="stat-label">Sensor Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(stats.get('label_distribution', {}))}</div>
                <div class="stat-label">Classes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('photos_size_mb', 0):.1f} MB</div>
                <div class="stat-label">Dataset Size</div>
            </div>
        </div>
        
        <h2>Label Distribution</h2>
        <table>
            <tr>
                <th>Label</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
    
    # Add label distribution
    if 'label_distribution' in stats:
        total = sum(stats['label_distribution'].values())
        for label, count in sorted(stats['label_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            html += f"""
            <tr>
                <td>{label}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
    
    html += """
        </table>
        
        <h2>Sample Images</h2>
        <p>First 20 photos from dataset:</p>
        <div class="samples">
"""
    
    # Add sample images
    photos_dir = session_path / "photos"
    if photos_dir.exists():
        manifest_csv = session_path / "photo_manifest.csv"
        if manifest_csv.exists():
            with open(manifest_csv, 'r') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 20:  # Limit to 20 samples
                        break
                    filename = row.get('filename')
                    label = row.get('label', 'unknown')
                    rel_path = f"photos/{filename}"
                    html += f"""
            <div class="sample-card">
                <img src="{rel_path}" alt="{label}">
                <div class="sample-label">{label}</div>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    report_path = session_path / output_file
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"\n✓ HTML report generated: {report_path}")
    return str(report_path)


def print_dataset_summary(log_dir="self_aware/logs"):
    """Print summary of all dataset sessions."""
    sessions = list_sessions(log_dir)
    
    if not sessions:
        print(f"No dataset sessions found in {log_dir}")
        return
    
    print("\n" + "="*70)
    print("  DATASET SESSIONS SUMMARY")
    print("="*70)
    
    for session in sessions:
        stats = analyze_session(session)
        print(f"\n📦 {stats['session_name']}")
        print(f"   Photos: {stats.get('photo_count', 0)}")
        print(f"   Sensor entries: {stats.get('sensor_entries', 0)}")
        print(f"   Size: {stats.get('photos_size_mb', 0):.1f} MB")
        
        if 'label_distribution' in stats:
            labels = ', '.join(stats['label_distribution'].keys())
            print(f"   Labels: {labels}")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN - For testing
# ============================================================================

def main():
    """Main entry point for dataset utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Dataset utilities for ML training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all sessions
  python self_aware/dataset_utils.py --list
  
  # Analyze a session
  python self_aware/dataset_utils.py --analyze session_2026-03-14_04-05-30
  
  # Export to PyTorch format
  python self_aware/dataset_utils.py --export session_2026-03-14_04-05-30
  
  # Generate HTML report
  python self_aware/dataset_utils.py --report session_2026-03-14_04-05-30
        """
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all dataset sessions'
    )
    parser.add_argument(
        '--analyze',
        metavar='SESSION',
        help='Analyze a specific session'
    )
    parser.add_argument(
        '--export',
        metavar='SESSION',
        help='Export session to PyTorch format'
    )
    parser.add_argument(
        '--report',
        metavar='SESSION',
        help='Generate HTML report for session'
    )
    parser.add_argument(
        '--log-dir',
        default='self_aware/logs',
        help='Log directory (default: self_aware/logs)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print_dataset_summary(args.log_dir)
    elif args.analyze:
        session_path = Path(args.log_dir) / args.analyze
        stats = analyze_session(session_path)
        print(json.dumps(stats, indent=2))
    elif args.export:
        session_path = Path(args.log_dir) / args.export
        export_for_pytorch(session_path)
    elif args.report:
        session_path = Path(args.log_dir) / args.report
        generate_html_report(session_path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
