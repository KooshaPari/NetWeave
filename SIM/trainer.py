import tensorflow as tf
import wandb
from datetime import datetime
import numpy as np
from pathlib import Path
import yaml
from typing import Tuple, Dict


class RoadNetworkTrainer:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.setup_training()
        self.setup_wandb()

    def load_config(self, config_path: str) -> Dict:
        """Load training configuration"""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config

    def setup_training(self):
        """Setup training components"""
        # Setup mixed precision
        self.policy = tf.keras.mixed_precision.Policy("mixed_float16")
        tf.keras.mixed_precision.set_global_policy(self.policy)

        # Create models
        self.generator = self.create_generator()
        self.discriminator = self.create_discriminator()

        # Setup optimizers with learning rate scheduling
        self.generator_optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.create_lr_schedule("generator"), beta_1=0.5
        )
        self.discriminator_optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.create_lr_schedule("discriminator"), beta_1=0.5
        )

        # Setup checkpointing
        self.checkpoint = tf.train.Checkpoint(
            generator_optimizer=self.generator_optimizer,
            discriminator_optimizer=self.discriminator_optimizer,
            generator=self.generator,
            discriminator=self.discriminator,
        )
        self.checkpoint_manager = tf.train.CheckpointManager(
            self.checkpoint,
            str(
                Path(self.config["training"]["checkpoint_dir"])
                / datetime.now().strftime("%Y%m%d_%H%M%S")
            ),
            max_to_keep=3,
        )

    def setup_wandb(self):
        """Setup Weights & Biases monitoring"""
        wandb.init(
            project=self.config["wandb"]["project_name"],
            config=self.config,
            name=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

    def create_lr_schedule(
        self, model_type: str
    ) -> tf.keras.optimizers.schedules.LearningRateSchedule:
        """Create learning rate schedule"""
        initial_lr = self.config["training"]["learning_rates"][model_type]
        decay_steps = self.config["training"]["lr_decay_steps"]
        decay_rate = self.config["training"]["lr_decay_rate"]

        return tf.keras.optimizers.schedules.ExponentialDecay(
            initial_lr, decay_steps, decay_rate
        )

    @tf.function
    def train_step(
        self, input_image: tf.Tensor, target: tf.Tensor
    ) -> Tuple[tf.Tensor, tf.Tensor]:
        """Single training step"""
        with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
            # Generator output
            gen_output = self.generator(input_image, training=True)

            # Discriminator outputs
            disc_real_output = self.discriminator([input_image, target], training=True)
            disc_generated_output = self.discriminator(
                [input_image, gen_output], training=True
            )

            # Calculate losses
            gen_loss = self.generator_loss(disc_generated_output, gen_output, target)
            disc_loss = self.discriminator_loss(disc_real_output, disc_generated_output)

        # Calculate gradients
        generator_gradients = gen_tape.gradient(
            gen_loss, self.generator.trainable_variables
        )
        discriminator_gradients = disc_tape.gradient(
            disc_loss, self.discriminator.trainable_variables
        )

        # Apply gradients
        self.generator_optimizer.apply_gradients(
            zip(generator_gradients, self.generator.trainable_variables)
        )
        self.discriminator_optimizer.apply_gradients(
            zip(discriminator_gradients, self.discriminator.trainable_variables)
        )

        return gen_loss, disc_loss

    def train(self, dataset: tf.data.Dataset, epochs: int):
        """Training loop"""
        for epoch in range(epochs):
            print(f"\nEpoch {epoch + 1}/{epochs}")

            # Train
            gen_losses = []
            disc_losses = []
            for batch in dataset:
                g_loss, d_loss = self.train_step(batch["sketch"], batch["target"])
                gen_losses.append(g_loss)
                disc_losses.append(d_loss)

            # Log metrics
            metrics = {
                "generator_loss": float(np.mean(gen_losses)),
                "discriminator_loss": float(np.mean(disc_losses)),
                "epoch": epoch,
            }
            wandb.log(metrics)

            # Save checkpoint
            if (epoch + 1) % self.config["training"]["checkpoint_frequency"] == 0:
                self.checkpoint_manager.save()

                # Generate and log samples
                self.log_samples(dataset)

    def log_samples(self, dataset: tf.data.Dataset):
        """Generate and log sample outputs"""
        for batch in dataset.take(1):
            generated_images = self.generator(batch["sketch"], training=False)

            # Log images to wandb
            wandb.log(
                {
                    "samples": [
                        wandb.Image(batch["sketch"][0], caption="Input Sketch"),
                        wandb.Image(generated_images[0], caption="Generated"),
                        wandb.Image(batch["target"][0], caption="Ground Truth"),
                    ]
                }
            )
            break


class DataAugmentation:
    def __init__(self, config: Dict):
        self.config = config

    @tf.function
    def augment(
        self, sketch: tf.Tensor, target: tf.Tensor
    ) -> Tuple[tf.Tensor, tf.Tensor]:
        """Apply augmentation to training pairs"""
        # Random rotation
        if tf.random.uniform([]) < self.config["augmentation"]["rotation_prob"]:
            angle = tf.random.uniform(
                [],
                minval=-self.config["augmentation"]["max_rotation"],
                maxval=self.config["augmentation"]["max_rotation"],
            )
            sketch = tfa.image.rotate(sketch, angle)
            target = tfa.image.rotate(target, angle)

        # Random flip
        if tf.random.uniform([]) < self.config["augmentation"]["flip_prob"]:
            sketch = tf.image.random_flip_left_right(sketch)
            target = tf.image.random_flip_left_right(target)

        # Random brightness/contrast (only for target)
        if tf.random.uniform([]) < self.config["augmentation"]["brightness_prob"]:
            target = tf.image.random_brightness(target, 0.2)
            target = tf.image.random_contrast(target, 0.8, 1.2)

        return sketch, target


def create_dataset(data_dir: str, config: Dict) -> tf.data.Dataset:
    """Create training dataset with augmentation"""
    augmenter = DataAugmentation(config)

    def load_image_pair(path: str) -> Dict[str, tf.Tensor]:
        # Load and preprocess image pair
        image = tf.io.read_file(path)
        image = tf.image.decode_png(image, channels=1)
        image = tf.cast(image, tf.float32)

        # Split into sketch and target
        width = tf.shape(image)[1]
        sketch = image[:, : width // 2, :]
        target = image[:, width // 2 :, :]

        # Normalize
        sketch = (sketch / 127.5) - 1
        target = (target / 127.5) - 1

        # Augment
        sketch, target = augmenter.augment(sketch, target)

        return {"sketch": sketch, "target": target}

    # Create dataset
    dataset = tf.data.Dataset.list_files(str(Path(data_dir) / "pairs" / "*.png"))
    dataset = dataset.map(load_image_pair, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.shuffle(config["training"]["buffer_size"])
    dataset = dataset.batch(config["training"]["batch_size"])
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


if __name__ == "__main__":
    import argparse
    import tensorflow as tf
    import tensorflow_addons as tfa

    parser = argparse.ArgumentParser(description="Train Road Network GAN")
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--data-dir", type=str, required=True, help="Path to dataset directory"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "gpu", "cpu", "mps"],
        help="Device to use for training",
    )
    args = parser.parse_args()

    # Set up device
    if args.device == "auto":
        if tf.config.list_physical_devices("GPU"):
            device = "gpu"
        elif (
            hasattr(tf.config, "list_physical_devices")
            and len(tf.config.list_physical_devices("MPS")) > 0
        ):
            device = "mps"
        else:
            device = "cpu"
    else:
        device = args.device

    print(f"Using device: {device}")

    # Configure mixed precision based on device
    if device == "gpu":
        policy = tf.keras.mixed_precision.Policy("mixed_float16")
        tf.keras.mixed_precision.set_global_policy(policy)

    # Create trainer
    trainer = RoadNetworkTrainer(args.config)

    # Create dataset
    dataset = create_dataset(args.data_dir, trainer.config)

    # Train
    trainer.train(dataset, trainer.config["training"]["epochs"])

    # Save final model
    trainer.generator.save("generator_final")
    trainer.discriminator.save("discriminator_final")
