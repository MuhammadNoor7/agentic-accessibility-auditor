from pathlib import Path
from src.parser import parse_dataset_folder

root = Path(__file__).resolve().parent
parsed_root = root / "data" / "parsed"

result = parse_dataset_folder(output_root=parsed_root)
print(result)
