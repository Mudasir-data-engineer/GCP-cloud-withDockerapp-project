import json
import os

def validate_data(file_path):
    required_fields = [
        "temperature", "humidity", "timestamp", "activity_level",
        "heart_rate", "rumination_minutes", "location_x", "location_y",
        "milk_yield", "is_ruminating", "sensor_id_transformed"
    ]
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data = json.loads(line)
                for field in required_fields:
                    if field not in data:
                        print(f"Missing field: {field} in record: {data}")
                        return False
            except json.JSONDecodeError:
                print(f"Invalid JSON format in file: {file_path}")
                return False
    print(f"All records in {file_path} are valid.")
    return True

# Example: validate all batch files in a specific folder
def validate_batch_files(batch_folder):
    # Ensure the folder exists
    if not os.path.exists(batch_folder):
        print(f"Error: The folder {batch_folder} does not exist!")
        return
    
    # List all files in the folder
    files = os.listdir(batch_folder)
    
    # Only check .ndjson files
    batch_files = [file for file in files if file.endswith('.ndjson')]

    # Check each batch file
    for batch_file in batch_files:
        file_path = os.path.join(batch_folder, batch_file)
        validate_data(file_path)

# Set the folder where the batch files are located
if __name__ == "__main__":
    batch_folder = 'C:/Users/hp/Desktop/smaxtec-project/cow_data'  # Replace with your actual batch folder path
    validate_batch_files(batch_folder)
