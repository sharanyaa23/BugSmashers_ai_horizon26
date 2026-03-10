import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "server"))

from server.models.train_model import main

if __name__ == "__main__":
    print("\n🚀 Starting Traffic Forecasting Model Training...")
    print("This will use Hugging Face's Chronos T5 model\n")
    main()
