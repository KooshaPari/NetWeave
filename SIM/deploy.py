import tensorflow as tf
import coremltools as ct  # For M1 optimization


class RoadNetworkGenerator:
    def __init__(self, model_path: str, device: str = "mps"):
        self.device = device
        if device == "mps":
            # Load and optimize for M1
            self.model = self._load_for_m1(model_path)
        else:
            # Load regular TF model
            self.model = tf.keras.models.load_model(model_path)

    def _load_for_m1(self, model_path):
        # Load TF model
        tf_model = tf.keras.models.load_model(model_path)

        # Convert to Core ML
        mlmodel = ct.convert(
            tf_model,
            inputs=[ct.ImageType(shape=(1, 256, 256, 1))],
            compute_units=ct.ComputeUnit.ALL,  # Use all available compute units
        )

        return mlmodel

    def generate(self, sketch_input):
        """Generate road network from sketch"""
        # Preprocess input
        processed_input = self._preprocess(sketch_input)

        # Generate output
        if self.device == "mps":
            output = self.model.predict({"input_1": processed_input})
        else:
            output = self.model(processed_input, training=False)

        # Postprocess output
        return self._postprocess(output)

    def _preprocess(self, input_image):
        # Normalize and prepare input
        input_image = tf.cast(input_image, tf.float32)
        input_image = (input_image / 127.5) - 1
        return input_image

    def _postprocess(self, output):
        # Convert output to road network format
        output = (output + 1) * 127.5
        output = tf.cast(output, tf.uint8)
        return output


# Usage example
def setup_generator(model_path: str):
    # Check available devices
    if tf.config.list_physical_devices("GPU"):
        device = "gpu"
    elif (
        hasattr(tf.config, "list_physical_devices")
        and len(tf.config.list_physical_devices("MPS")) > 0
    ):
        device = "mps"
    else:
        device = "cpu"

    return RoadNetworkGenerator(model_path, device)
