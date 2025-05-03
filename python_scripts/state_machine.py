from enum import Enum, auto
import logging
from datetime import datetime
from python_scripts.dataCleaning import Cleanse, Manipulation
from python_scripts.visualition2 import Project
# Configure logging
logging.basicConfig(
    filename=f"logs/state_machine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class DataState(Enum):
    INITIAL = auto()
    CLEANING = auto()
    MANIPULATION = auto()
    VISUALIZATION = auto()
    FINAL = auto()

class DataStateMachine:
    def __init__(self, data):
        self.data = data
        self.state = DataState.INITIAL  # Start with the initial state
        logging.info("State Machine initialized. Current state: INITIAL")

    def transition_to(self, new_state):
        """Transition to a new state."""
        logging.info(f"Transitioning from {self.state.name} to {new_state.name}")
        self.state = new_state

    def process(self):
        """Process data based on the current state."""
        if self.state == DataState.INITIAL:
            logging.info("Loading data...")
            # Data is already loaded in self.data
            self.transition_to(DataState.CLEANING)

        elif self.state == DataState.CLEANING:
            logging.info("Performing data cleaning...")
            cl = Cleanse(self.data)
            cl.DeleteDupValues()
            logging.info("Duplicates removed.")
            cl.StripSpecialChars()
            logging.info("Special characters stripped.")
            cl.NormalizeColumnValues()
            logging.info("Column values normalized.")
            self.data = cl.data
            self.transition_to(DataState.MANIPULATION)

        elif self.state == DataState.MANIPULATION:
            logging.info("Performing data manipulation...")
            cl = Manipulation(self.data)
            cl.detectAndDeleteOutliers()
            logging.info("Outliers detected and deleted.")
            cl.logTransform('volume')  # Example column
            logging.info("Log transformation applied to 'volume'.")
            self.data = cl.data
            self.transition_to(DataState.FINAL)
        
        #elif self.state == DataState.VISUALIZATION:
         #   logging.info("Performing data visualization...")
          #  Project(self.data["project_name"], self.data["file_name"], self.data["extension"], self.data["option"]).visualize()
           # logging.info("Data visualization complete.")
            #self.transition_to(DataState.FINAL)
        elif self.state == DataState.FINAL:
            logging.info("Finalizing data processing...")
            logging.info("Processing complete. Final state reached.")
        else:
            logging.error("Unknown state encountered!")


