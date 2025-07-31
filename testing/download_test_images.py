import fiftyone.zoo as foz

# 100 classes spanning animals and common objects
classes = [
    "Cat", "Dog", "Horse", "Cow", "Sheep", "Goat", "Elephant", "Tiger", "Lion", "Bear",
    "Monkey", "Giraffe", "Zebra", "Kangaroo", "Pig", "Chicken", "Duck", "Bird", "Fish", "Butterfly",
    "Spider", "Ant", "Car", "Truck", "Bus", "Train", "Airplane", "Bicycle", "Motorcycle", "Boat",
    "Ship", "Helicopter", "House", "Building", "Bridge", "Tower", "Streetlight", "Traffic light", "Crosswalk", "Stop sign",
    "Bench", "Chair", "Table", "Sofa", "Bed", "Refrigerator", "Microwave", "Oven", "Toaster", "Sink",
    "Toilet", "Bathtub", "Shower", "Washing machine", "TV", "Laptop", "Keyboard", "Mouse", "Smartphone", "Camera",
    "Watch", "Clock", "Book", "Cup", "Glass", "Plate", "Fork", "Knife", "Spoon", "Bowl",
    "Bottle", "Pen", "Pencil", "Scissors", "Umbrella", "Backpack", "Suitcase", "Hat", "Shoe", "Sock",
    "Jeans", "Shirt", "Dress", "Skirt", "Coat", "Jacket", "Tie", "Belt", "Eyeglasses", "Sunglasses",
    "Helmet", "Ball", "Frisbee", "Skateboard", "Surfboard", "Snowboard", "Ski", "Tennis racket", "Baseball bat", "Soccer ball"
]

# Download a 1,000-image subset covering these 100 classes
dataset = foz.load_zoo_dataset(
    "open-images-v7",
    split="train",
    label_types=["detections", "classifications"],
    classes=classes,
    max_samples=1000,
    dataset_dir="open_images_v7_subset"
)
