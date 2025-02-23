import os
import random
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split


def split_dataset(dataset_path: str, val_split: float = 0.1):
    """Split dataset into training and validation sets"""
    dataset_path = Path(dataset_path)

    # Create train/val directories
    for split in ["train", "val"]:
        for dir_type in ["control", "target"]:
            (dataset_path / split / dir_type).mkdir(parents=True, exist_ok=True)

    # Get all sample IDs
    control_files = list((dataset_path / "control").glob("*.png"))
    sample_ids = [f.stem for f in control_files]

    # Split sample IDs
    train_ids, val_ids = train_test_split(
        sample_ids, test_size=val_split, random_state=42
    )

    # Move files to respective directories
    for sample_id in train_ids:
        for dir_type in ["control", "target"]:
            src = dataset_path / dir_type / f"{sample_id}.png"
            dst = dataset_path / "train" / dir_type / f"{sample_id}.png"
            shutil.copy2(src, dst)

    for sample_id in val_ids:
        for dir_type in ["control", "target"]:
            src = dataset_path / dir_type / f"{sample_id}.png"
            dst = dataset_path / "val" / dir_type / f"{sample_id}.png"
            shutil.copy2(src, dst)

    print(f"Dataset split complete:")
    print(f"Training samples: {len(train_ids)}")
    print(f"Validation samples: {len(val_ids)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", type=str, required=True)
    parser.add_argument("--val-split", type=float, default=0.1)
    args = parser.parse_args()

    split_dataset(args.dataset_path, args.val_split)
